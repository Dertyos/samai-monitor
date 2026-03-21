"""Lambda monitor — EventBridge trigger diario.

Flujo:
1. Leer todos los radicados únicos (deduplicados)
2. Para cada radicado: consultar SAMAI, detectar novedades
3. Crear alertas para cada usuario afectado
4. Enviar correos resumen via SES
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

from models import Actuacion, Alerta
from samai_client import SamaiClient, SamaiApiError
from db import (
    obtener_radicados_unicos,
    guardar_actuaciones,
    guardar_alerta,
    actualizar_ultimo_orden,
    obtener_alertas_usuario,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dependencias — instanciadas una vez por cold start
_dynamodb = boto3.resource("dynamodb")
_radicados_table = _dynamodb.Table(os.environ.get("RADICADOS_TABLE", "samai-radicados"))
_actuaciones_table = _dynamodb.Table(os.environ.get("ACTUACIONES_TABLE", "samai-actuaciones"))
_alertas_table = _dynamodb.Table(os.environ.get("ALERTAS_TABLE", "samai-alertas"))
samai_client = SamaiClient()


def handler(event: dict, context: Any) -> dict:
    """Entry point Lambda — EventBridge trigger."""
    logger.info("Monitor iniciado")

    # 1. Obtener radicados únicos
    unicos = obtener_radicados_unicos(_radicados_table)
    logger.info("Radicados únicos a consultar: %d", len(unicos))

    # 2. Para cada radicado, consultar SAMAI
    all_user_alertas: dict[str, list[Alerta]] = {}
    errores = 0

    for corp, radicado in unicos:
        try:
            user_alertas = check_radicado(
                samai_client=samai_client,
                radicados_table=_radicados_table,
                actuaciones_table=_actuaciones_table,
                alertas_table=_alertas_table,
                corporacion=corp,
                radicado=radicado,
            )
            # Merge alertas por usuario
            for user_id, alertas in user_alertas.items():
                all_user_alertas.setdefault(user_id, []).extend(alertas)
        except Exception:
            logger.exception("Error procesando radicado %s", radicado)
            errores += 1

    # 3. Enviar correos
    if all_user_alertas:
        _send_email_alerts(all_user_alertas)

    result = {
        "processed": len(unicos),
        "errors": errores,
        "users_alerted": len(all_user_alertas),
        "total_alertas": sum(len(a) for a in all_user_alertas.values()),
    }
    logger.info("Monitor completado: %s", result)
    return result


def check_radicado(
    *,
    samai_client: SamaiClient,
    radicados_table: Any,
    actuaciones_table: Any,
    alertas_table: Any,
    corporacion: str,
    radicado: str,
) -> dict[str, list[Alerta]]:
    """Consulta SAMAI para un radicado, detecta novedades, crea alertas.

    Retorna dict de userId → lista de alertas generadas.
    """
    from boto3.dynamodb.conditions import Key

    # Buscar todos los usuarios que siguen este radicado (via GSI)
    resp = radicados_table.query(
        IndexName="radicado-index",
        KeyConditionExpression=Key("radicado").eq(radicado),
    )
    all_followers = resp.get("Items", [])
    # Solo monitorear para usuarios con radicado activo
    followers = [f for f in all_followers if f.get("activo", True)]
    if not followers:
        return {}

    # Encontrar el mínimo ultimo_orden entre todos los seguidores activos
    min_orden = min(int(item.get("ultimoOrden", 0)) for item in followers)

    # Consultar SAMAI: solo actuaciones nuevas desde el mínimo
    nuevas = samai_client.get_actuaciones_nuevas(corporacion, radicado, desde_orden=min_orden)
    if not nuevas:
        return {}

    # Guardar actuaciones en DynamoDB
    guardar_actuaciones(actuaciones_table, nuevas)

    max_orden = max(a.orden for a in nuevas)
    now = datetime.now(timezone.utc).isoformat()

    # Para cada usuario, crear alertas solo para las actuaciones que son nuevas para ellos
    user_alertas: dict[str, list[Alerta]] = {}
    for item in followers:
        user_id = item["userId"]
        user_ultimo_orden = int(item.get("ultimoOrden", 0))

        # Filtrar: solo las que son nuevas para este usuario
        nuevas_para_user = [a for a in nuevas if a.orden > user_ultimo_orden]
        if not nuevas_para_user:
            continue

        alertas_user: list[Alerta] = []
        for act in nuevas_para_user:
            alerta = Alerta(
                user_id=user_id,
                radicado=radicado,
                orden=act.orden,
                nombre_actuacion=act.nombre,
                fecha_actuacion=act.fecha,
                anotacion=act.anotacion,
                created_at=now,
                enviado=False,
            )
            guardar_alerta(alertas_table, alerta)
            alertas_user.append(alerta)

        user_alertas[user_id] = alertas_user

        # Actualizar último orden del usuario
        actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden)

    return user_alertas


def _send_email_alerts(user_alertas: dict[str, list[Alerta]]) -> None:
    """Envía correos de alerta via SES."""
    ses = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    sender = os.environ.get("SES_SENDER", "juliansalcedo4@gmail.com")
    cognito = boto3.client("cognito-idp", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    user_pool_id = os.environ.get("USER_POOL_ID", "")

    for user_id, alertas in user_alertas.items():
        try:
            email = _get_user_email(cognito, user_pool_id, user_id)
            if not email:
                logger.warning("No email found for user %s, skipping", user_id)
                continue

            subject, body_html = _build_alert_email(alertas)
            ses.send_email(
                Source=sender,
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Html": {"Data": body_html, "Charset": "UTF-8"}},
                },
            )
            logger.info("Email sent to %s with %d alertas", email, len(alertas))
        except Exception:
            logger.exception("Error sending email to user %s", user_id)


def _get_user_email(cognito: Any, user_pool_id: str, user_id: str) -> str | None:
    """Obtiene email de un usuario desde Cognito."""
    if not user_pool_id:
        return None
    try:
        resp = cognito.admin_get_user(UserPoolId=user_pool_id, Username=user_id)
        for attr in resp.get("UserAttributes", []):
            if attr["Name"] == "email":
                return attr["Value"]
    except Exception:
        logger.exception("Error getting user email for %s", user_id)
    return None


def _build_alert_email(alertas: list[Alerta]) -> tuple[str, str]:
    """Construye subject y body HTML para el correo de alertas."""
    by_radicado: dict[str, list[Alerta]] = {}
    for a in alertas:
        by_radicado.setdefault(a.radicado, []).append(a)

    n_radicados = len(by_radicado)
    n_actuaciones = len(alertas)
    subject = f"SAMAI Monitor: {n_actuaciones} nueva(s) actuación(es) en {n_radicados} proceso(s)"

    rows = ""
    for radicado, rad_alertas in by_radicado.items():
        fmt = f"{radicado[:5]}-{radicado[5:7]}-{radicado[7:9]}-{radicado[9:12]}-{radicado[12:16]}-{radicado[16:21]}-{radicado[21:23]}"
        rows += f'<tr><td colspan="3" style="background:#f0f0f0;padding:8px;font-weight:bold;">{fmt}</td></tr>'
        for a in sorted(rad_alertas, key=lambda x: x.orden, reverse=True):
            fecha = a.fecha_actuacion[:10] if a.fecha_actuacion else ""
            rows += (
                f"<tr>"
                f'<td style="padding:4px 8px;">{a.orden}</td>'
                f'<td style="padding:4px 8px;">{a.nombre_actuacion}</td>'
                f'<td style="padding:4px 8px;">{fecha}</td>'
                f"</tr>"
            )

    body_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<h2 style="color:#1a73e8;">SAMAI Monitor</h2>
<p>Se detectaron <strong>{n_actuaciones}</strong> nueva(s) actuación(es) en <strong>{n_radicados}</strong> proceso(s):</p>
<table style="border-collapse:collapse;width:100%;" border="1" cellpadding="4">
<tr style="background:#1a73e8;color:white;">
<th>Orden</th><th>Actuación</th><th>Fecha</th>
</tr>
{rows}
</table>
<p style="color:#666;font-size:12px;margin-top:20px;">
Este correo fue enviado automáticamente por SAMAI Monitor.
</p>
</body></html>"""

    return subject, body_html
