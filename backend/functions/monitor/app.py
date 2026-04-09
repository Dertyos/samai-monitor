"""Lambda monitor — EventBridge trigger diario.

Flujo:
1. Leer todos los radicados únicos (deduplicados)
2. Para cada radicado: consultar SAMAI, detectar novedades
3. Crear alertas para cada usuario afectado
4. Enviar correos resumen via Resend
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
import resend

from models import Actuacion, Alerta, Radicado
from samai_client import SamaiClient, SamaiApiError
from rama_judicial_client import RamaJudicialClient, RamaJudicialApiError
from siugj_client import SiugjClient, SiugjApiError
from spoa_client import SpoaClient, SpoaApiError
from boto3.dynamodb.conditions import Key

from db import (
    obtener_radicados_unicos,
    guardar_actuaciones,
    guardar_alerta,
    actualizar_ultimo_orden,
    limpiar_pending_init,
    obtener_alertas_usuario,
    obtener_radicados_usuario,
    obtener_team_de_usuario,
    obtener_team,
    obtener_miembros_team,
    contar_procesos_equipo,
    obtener_schedules_por_hora,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dependencias — instanciadas una vez por cold start
_dynamodb = boto3.resource("dynamodb")
_radicados_table = _dynamodb.Table(os.environ.get("RADICADOS_TABLE", "samai-radicados"))
_actuaciones_table = _dynamodb.Table(os.environ.get("ACTUACIONES_TABLE", "samai-actuaciones"))
_alertas_table = _dynamodb.Table(os.environ.get("ALERTAS_TABLE", "samai-alertas"))
_billing_subs_table = _dynamodb.Table(os.environ.get("BILLING_SUBSCRIPTIONS_TABLE", "samai-billing-subscriptions"))
_billing_plans_table = _dynamodb.Table(os.environ.get("BILLING_PLANS_TABLE", "samai-billing-plans"))
_teams_table = _dynamodb.Table(os.environ.get("TEAMS_TABLE", "samai-teams"))
_team_members_table = _dynamodb.Table(os.environ.get("TEAM_MEMBERS_TABLE", "samai-team-members"))
_alert_schedules_table = _dynamodb.Table(os.environ.get("ALERT_SCHEDULES_TABLE", "samai-alert-schedules"))

TEAM_ELIGIBLE_PLANS = {"plan-firma", "plan-enterprise"}
CUSTOM_ALERT_ELIGIBLE_PLANS = {"plan-pro-plus", "plan-firma", "plan-enterprise"}

FREE_PLAN_LIMIT = 5

PLAN_LIMITS: dict[str, int] = {
    "plan-gratuito": 5,
    "plan-pro": 25,
    "plan-pro-plus": 70,
    "plan-firma": 150,
    "plan-enterprise": 1000,
}
samai_client = SamaiClient()
rj_client = RamaJudicialClient()
siugj_client = SiugjClient()
spoa_client = SpoaClient()

# Resend API key — cargada desde SSM en cold start
def _load_resend_api_key() -> str:
    """Carga la API key de Resend desde SSM Parameter Store."""
    ssm_param = os.environ.get("RESEND_API_KEY_SSM", "/samai-monitor/resend-api-key")
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    resp = ssm.get_parameter(Name=ssm_param, WithDecryption=True)
    return resp["Parameter"]["Value"]


try:
    resend.api_key = _load_resend_api_key()
except Exception:
    logger.warning("Could not load Resend API key from SSM — emails will fail")


def _get_user_plan_limit(user_id: str) -> int:
    """Obtiene el límite de procesos del plan activo del usuario.

    Retorna FREE_PLAN_LIMIT (5) si no tiene suscripción activa.
    """
    try:
        resp = _billing_subs_table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
        )
        subs = resp.get("Items", [])
        active = [s for s in subs if s.get("status") in ("active", "trialing")]
        if not active:
            return FREE_PLAN_LIMIT

        plan_id = active[0].get("planId", "")
        limit = PLAN_LIMITS.get(plan_id, FREE_PLAN_LIMIT)

        # Intentar features del plan para límite más preciso
        plan_resp = _billing_plans_table.get_item(Key={"planId": plan_id})
        plan_item = plan_resp.get("Item")
        if plan_item and plan_item.get("features", {}).get("max_processes"):
            limit = int(plan_item["features"]["max_processes"])

        return limit
    except Exception:
        logger.warning("Error consultando plan de %s, usando limite gratuito", user_id)
        return FREE_PLAN_LIMIT


def _get_user_effective_limit(
    user_id: str,
    members_table: Any,
    teams_table: Any,
) -> int:
    """Obtiene el límite efectivo para un usuario.

    Si pertenece a un equipo con suscripción activa → límite del equipo.
    Si no → límite de su plan personal (o 5 si no tiene).
    """
    team_id = obtener_team_de_usuario(members_table, user_id)
    if team_id:
        team = obtener_team(teams_table, team_id)
        if team:
            owner_limit = _get_user_plan_limit(team.owner_user_id)
            # Verificar que el owner tiene plan de equipo activo
            resp = _billing_subs_table.query(
                KeyConditionExpression=Key("userId").eq(team.owner_user_id),
            )
            subs = resp.get("Items", [])
            active = [s for s in subs if s.get("status") in ("active", "trialing")]
            if active and active[0].get("planId", "") in TEAM_ELIGIBLE_PLANS:
                return owner_limit
    # Sin equipo activo → plan personal
    return _get_user_plan_limit(user_id)


def _enforce_plan_limits(radicados_table: Any) -> dict[str, int]:
    """Desactiva radicados que exceden el límite del plan de cada usuario.

    Para cada usuario:
    - Si pertenece a un equipo activo → su límite es el del equipo
    - Si no → límite de su plan personal (gratis = 5)
    Conserva activos solo los primeros N radicados (por createdAt).
    Reactiva radicados previamente desactivados si ahora caben en el plan.

    Retorna dict de userId → cantidad de radicados desactivados.
    """
    # Scan all radicados, group by userId
    resp = radicados_table.scan(
        ProjectionExpression="userId, radicado, activo, createdAt",
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = radicados_table.scan(
            ProjectionExpression="userId, radicado, activo, createdAt",
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    # Group by user
    user_rads: dict[str, list[dict]] = {}
    for item in items:
        uid = item["userId"]
        user_rads.setdefault(uid, []).append(item)

    enforced: dict[str, int] = {}

    for uid, rads in user_rads.items():
        limit = _get_user_effective_limit(uid, _team_members_table, _teams_table)

        # Sort by createdAt ascending — first added = kept active
        rads.sort(key=lambda r: r.get("createdAt", ""))

        for i, rad in enumerate(rads):
            rad_key = {"userId": uid, "radicado": rad["radicado"]}
            if i < limit:
                if not rad.get("activo", True):
                    radicados_table.update_item(
                        Key=rad_key,
                        UpdateExpression="SET activo = :a",
                        ExpressionAttributeValues={":a": True},
                    )
                    logger.info("Reactivado radicado %s de user %s (dentro del limite)", rad["radicado"], uid)
            else:
                if rad.get("activo", True):
                    radicados_table.update_item(
                        Key=rad_key,
                        UpdateExpression="SET activo = :a",
                        ExpressionAttributeValues={":a": False},
                    )
                    enforced.setdefault(uid, 0)
                    enforced[uid] += 1
                    logger.info("Desactivado radicado %s de user %s (excede limite %d)", rad["radicado"], uid, limit)

    return enforced


def _reactivate_and_check_user(user_id: str) -> dict:
    """Reactiva radicados de un usuario tras renovar suscripción y busca novedades.

    1. Recalcula el límite del usuario (puede haber subido de plan)
    2. Reactiva radicados que estaban inactivos (dentro del nuevo límite)
    3. Para cada radicado reactivado, consulta novedades y genera alertas
    4. Envía correo resumen si hay novedades
    """
    limit = _get_user_effective_limit(user_id, _team_members_table, _teams_table)
    rads = obtener_radicados_usuario(_radicados_table, user_id)
    rads.sort(key=lambda r: r.created_at)

    reactivated: list[Radicado] = []
    for i, rad in enumerate(rads):
        if i < limit and not rad.activo:
            _radicados_table.update_item(
                Key={"userId": user_id, "radicado": rad.radicado},
                UpdateExpression="SET activo = :a",
                ExpressionAttributeValues={":a": True},
            )
            reactivated.append(rad)
            logger.info("Reactivado radicado %s de user %s (suscripcion renovada)", rad.radicado, user_id)
        elif i >= limit and rad.activo:
            _radicados_table.update_item(
                Key={"userId": user_id, "radicado": rad.radicado},
                UpdateExpression="SET activo = :a",
                ExpressionAttributeValues={":a": False},
            )

    # Check de novedades para los reactivados
    all_alertas: list[Alerta] = []
    for rad in reactivated:
        try:
            if rad.fuente == "rama_judicial":
                user_alertas = check_radicado_rj(
                    rj_client=rj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    id_proceso=rad.id_proceso,
                    radicado=rad.radicado,
                )
            elif rad.fuente == "siugj":
                user_alertas = check_radicado_siugj(
                    siugj_client=siugj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=rad.radicado,
                )
            elif rad.fuente == "spoa":
                user_alertas = check_radicado_spoa(
                    spoa_client=spoa_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=rad.radicado,
                )
            else:
                user_alertas = check_radicado(
                    samai_client=samai_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    corporacion=rad.corporacion,
                    radicado=rad.radicado,
                )
            for alertas in user_alertas.values():
                all_alertas.extend(alertas)
        except Exception:
            logger.exception("Error chequeando radicado reactivado %s", rad.radicado)

    if all_alertas:
        _send_email_alerts({user_id: all_alertas})

    return {
        "reactivated": len(reactivated),
        "alertas": len(all_alertas),
    }


def handler(event: dict, context: Any) -> dict:
    """Entry point Lambda — EventBridge trigger o invocación por webhook."""
    action = event.get("action")

    # Invocación directa: reactivar radicados de un usuario tras pago
    if action == "reactivate":
        user_id = event.get("userId", "")
        if not user_id:
            return {"error": "userId requerido"}
        logger.info("Reactivacion por pago: user=%s", user_id)
        return _reactivate_and_check_user(user_id)

    # Hourly trigger: procesar alertas personalizadas
    if action == "custom_alert_check":
        return _process_custom_alerts()

    logger.info("Monitor iniciado")

    # 0. Enforce plan limits — desactivar radicados que exceden el plan
    enforced = _enforce_plan_limits(_radicados_table)
    if enforced:
        logger.info("Plan enforcement: %d usuarios afectados, %d radicados desactivados",
                     len(enforced), sum(enforced.values()))

    # 1. Obtener radicados únicos
    unicos = obtener_radicados_unicos(_radicados_table)
    logger.info("Radicados únicos a consultar: %d", len(unicos))

    # 2. Para cada radicado, consultar SAMAI
    all_user_alertas: dict[str, list[Alerta]] = {}
    errores = 0

    for item in unicos:
        radicado = item["radicado"]
        fuente = item["fuente"]
        try:
            if fuente == "rama_judicial":
                user_alertas = check_radicado_rj(
                    rj_client=rj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    id_proceso=item["id_proceso"],
                    radicado=radicado,
                )
            elif fuente == "siugj":
                user_alertas = check_radicado_siugj(
                    siugj_client=siugj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=radicado,
                )
            elif fuente == "spoa":
                user_alertas = check_radicado_spoa(
                    spoa_client=spoa_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=radicado,
                )
            else:
                user_alertas = check_radicado(
                    samai_client=samai_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    corporacion=item["corporacion"],
                    radicado=radicado,
                )
            # Merge alertas por usuario
            for user_id, alertas in user_alertas.items():
                all_user_alertas.setdefault(user_id, []).extend(alertas)
        except Exception:
            logger.exception("Error procesando radicado %s (fuente=%s)", radicado, fuente)
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


def _process_custom_alerts() -> dict:
    """Procesa alertas personalizadas para la hora UTC actual.

    Consulta la tabla de schedules para la hora actual,
    verifica elegibilidad de cada usuario, y chequea sus radicados.
    """
    current_hour = datetime.now(timezone.utc).hour

    # Saltar hora 12 UTC (7 AM COT) — el scan diario completo ya lo cubre
    if current_hour == 12:
        logger.info("Custom alert check: skipping hour 12 (daily scan handles it)")
        return {"skipped": True, "reason": "daily_scan_hour"}

    schedules = obtener_schedules_por_hora(_alert_schedules_table, current_hour)
    if not schedules:
        logger.info("Custom alert check: no users at hour %d UTC", current_hour)
        return {"processed": 0, "users_alerted": 0, "total_alertas": 0}

    logger.info("Custom alert check: %d users at hour %d UTC", len(schedules), current_hour)

    all_user_alertas: dict[str, list[Alerta]] = {}
    processed = 0

    for schedule in schedules:
        user_id = schedule.user_id

        # Verificar que el usuario aun tiene plan elegible
        plan_id = _get_user_active_plan_id(user_id)
        if plan_id not in CUSTOM_ALERT_ELIGIBLE_PLANS:
            logger.info("Custom alert: user %s ya no tiene plan elegible (%s), saltando", user_id, plan_id)
            continue

        alertas = _check_user_radicados(user_id)
        if alertas:
            all_user_alertas[user_id] = alertas
        processed += 1

    if all_user_alertas:
        _send_email_alerts(all_user_alertas)

    result = {
        "processed": processed,
        "users_alerted": len(all_user_alertas),
        "total_alertas": sum(len(a) for a in all_user_alertas.values()),
    }
    logger.info("Custom alert check completado: %s", result)
    return result


def _get_user_active_plan_id(user_id: str) -> str:
    """Obtiene el planId activo del usuario, o cadena vacia si no tiene."""
    try:
        resp = _billing_subs_table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
        )
        subs = resp.get("Items", [])
        active = [s for s in subs if s.get("status") in ("active", "trialing")]
        if active:
            return active[0].get("planId", "")
    except Exception:
        logger.warning("Error consultando plan de %s", user_id)
    return ""


def _check_user_radicados(user_id: str) -> list[Alerta]:
    """Chequea todos los radicados activos de un usuario y retorna alertas generadas."""
    rads = obtener_radicados_usuario(_radicados_table, user_id)
    active_rads = [r for r in rads if r.activo]
    if not active_rads:
        return []

    all_alertas: list[Alerta] = []
    for rad in active_rads:
        try:
            if rad.fuente == "rama_judicial":
                user_alertas = check_radicado_rj(
                    rj_client=rj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    id_proceso=rad.id_proceso,
                    radicado=rad.radicado,
                )
            elif rad.fuente == "siugj":
                user_alertas = check_radicado_siugj(
                    siugj_client=siugj_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=rad.radicado,
                )
            elif rad.fuente == "spoa":
                user_alertas = check_radicado_spoa(
                    spoa_client=spoa_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    radicado=rad.radicado,
                )
            else:
                user_alertas = check_radicado(
                    samai_client=samai_client,
                    radicados_table=_radicados_table,
                    actuaciones_table=_actuaciones_table,
                    alertas_table=_alertas_table,
                    corporacion=rad.corporacion,
                    radicado=rad.radicado,
                )
            for alertas in user_alertas.values():
                all_alertas.extend(alertas)
        except Exception:
            logger.exception("Error chequeando radicado %s de user %s (custom alert)", rad.radicado, user_id)

    return all_alertas


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
    max_act = max(nuevas, key=lambda a: a.orden)
    fecha_ultima = max_act.fecha
    now = datetime.now(timezone.utc).isoformat()

    # Para cada usuario, crear alertas solo para las actuaciones que son nuevas para ellos
    user_alertas: dict[str, list[Alerta]] = {}
    for item in followers:
        user_id = item["userId"]
        user_ultimo_orden = int(item.get("ultimoOrden", 0))
        pending_init = item.get("pendingInit", False)

        # Filtrar: solo las que son nuevas para este usuario
        nuevas_para_user = [a for a in nuevas if a.orden > user_ultimo_orden]
        if not nuevas_para_user:
            continue

        # pendingInit=True: la API falló al registrar el proceso, no conocíamos el estado real.
        # Solo inicializar ultimoOrden sin generar alertas para evitar spam histórico.
        if pending_init:
            logger.info(
                "Radicado %s usuario %s: pendingInit=True, inicializando a orden=%d sin alertar",
                radicado, user_id, max_orden,
            )
            actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)
            limpiar_pending_init(radicados_table, user_id, radicado)
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
        actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)

    return user_alertas


def check_radicado_rj(
    *,
    rj_client: RamaJudicialClient,
    radicados_table: Any,
    actuaciones_table: Any,
    alertas_table: Any,
    id_proceso: int | None,
    radicado: str,
) -> dict[str, list[Alerta]]:
    """Consulta CPNU para un radicado de Rama Judicial, detecta novedades, crea alertas.

    Retorna dict de userId → lista de alertas generadas.
    """
    from boto3.dynamodb.conditions import Key

    if id_proceso is None:
        logger.warning("Radicado %s de rama_judicial sin id_proceso, omitiendo", radicado)
        return {}

    resp = radicados_table.query(
        IndexName="radicado-index",
        KeyConditionExpression=Key("radicado").eq(radicado),
    )
    all_followers = resp.get("Items", [])
    followers = [f for f in all_followers if f.get("activo", True) and f.get("fuente") == "rama_judicial"]
    if not followers:
        return {}

    min_orden = min(int(item.get("ultimoOrden", 0)) for item in followers)

    nuevas = rj_client.get_actuaciones_nuevas(id_proceso, desde_cons=min_orden)
    if not nuevas:
        return {}

    guardar_actuaciones(actuaciones_table, nuevas)

    max_orden = max(a.orden for a in nuevas)
    max_act = max(nuevas, key=lambda a: a.orden)
    fecha_ultima = max_act.fecha
    now = datetime.now(timezone.utc).isoformat()

    user_alertas: dict[str, list[Alerta]] = {}
    for item in followers:
        user_id = item["userId"]
        user_ultimo_orden = int(item.get("ultimoOrden", 0))
        pending_init = item.get("pendingInit", False)

        nuevas_para_user = [a for a in nuevas if a.orden > user_ultimo_orden]
        if not nuevas_para_user:
            continue

        if pending_init:
            logger.info(
                "Radicado %s usuario %s: pendingInit=True, inicializando a orden=%d sin alertar",
                radicado, user_id, max_orden,
            )
            actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)
            limpiar_pending_init(radicados_table, user_id, radicado)
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
                fuente="rama_judicial",
            )
            guardar_alerta(alertas_table, alerta)
            alertas_user.append(alerta)

        user_alertas[user_id] = alertas_user
        actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)

    return user_alertas


def check_radicado_siugj(
    *,
    siugj_client: SiugjClient,
    radicados_table: Any,
    actuaciones_table: Any,
    alertas_table: Any,
    radicado: str,
) -> dict[str, list[Alerta]]:
    """Consulta SIUGJ para un radicado, detecta novedades, crea alertas.

    Mismo patrón que check_radicado_rj pero usa SiugjClient con idRegistro.
    Retorna dict de userId → lista de alertas generadas.
    """
    from boto3.dynamodb.conditions import Key

    resp = radicados_table.query(
        IndexName="radicado-index",
        KeyConditionExpression=Key("radicado").eq(radicado),
    )
    all_followers = resp.get("Items", [])
    followers = [f for f in all_followers if f.get("activo", True) and f.get("fuente") == "siugj"]
    if not followers:
        return {}

    min_orden = min(int(item.get("ultimoOrden", 0)) for item in followers)

    nuevas = siugj_client.get_actuaciones_nuevas(radicado, desde_id=min_orden)
    if not nuevas:
        return {}

    guardar_actuaciones(actuaciones_table, nuevas)

    max_orden = max(a.orden for a in nuevas)
    max_act = max(nuevas, key=lambda a: a.orden)
    fecha_ultima = max_act.fecha
    now = datetime.now(timezone.utc).isoformat()

    user_alertas: dict[str, list[Alerta]] = {}
    for item in followers:
        user_id = item["userId"]
        user_ultimo_orden = int(item.get("ultimoOrden", 0))
        pending_init = item.get("pendingInit", False)

        nuevas_para_user = [a for a in nuevas if a.orden > user_ultimo_orden]
        if not nuevas_para_user:
            continue

        if pending_init:
            logger.info(
                "Radicado %s usuario %s: pendingInit=True, inicializando a orden=%d sin alertar",
                radicado, user_id, max_orden,
            )
            actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)
            limpiar_pending_init(radicados_table, user_id, radicado)
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
                fuente="siugj",
            )
            guardar_alerta(alertas_table, alerta)
            alertas_user.append(alerta)

        user_alertas[user_id] = alertas_user
        actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)

    return user_alertas


def check_radicado_spoa(
    *,
    spoa_client: SpoaClient,
    radicados_table: Any,
    actuaciones_table: Any,
    alertas_table: Any,
    radicado: str,
) -> dict[str, list[Alerta]]:
    """Consulta SPOA para un NUNC, detecta novedades, crea alertas.

    Mismo patrón que check_radicado_siugj pero usa SpoaClient.
    Retorna dict de userId → lista de alertas generadas.
    """
    from boto3.dynamodb.conditions import Key

    resp = radicados_table.query(
        IndexName="radicado-index",
        KeyConditionExpression=Key("radicado").eq(radicado),
    )
    all_followers = resp.get("Items", [])
    followers = [f for f in all_followers if f.get("activo", True) and f.get("fuente") == "spoa"]
    if not followers:
        return {}

    min_orden = min(int(item.get("ultimoOrden", 0)) for item in followers)

    nuevas = spoa_client.get_actuaciones_nuevas(radicado, desde_id=min_orden)
    if not nuevas:
        return {}

    guardar_actuaciones(actuaciones_table, nuevas)

    max_orden = max(a.orden for a in nuevas)
    max_act = max(nuevas, key=lambda a: a.orden)
    fecha_ultima = max_act.fecha
    now = datetime.now(timezone.utc).isoformat()

    user_alertas: dict[str, list[Alerta]] = {}
    for item in followers:
        user_id = item["userId"]
        user_ultimo_orden = int(item.get("ultimoOrden", 0))
        pending_init = item.get("pendingInit", False)

        nuevas_para_user = [a for a in nuevas if a.orden > user_ultimo_orden]
        if not nuevas_para_user:
            continue

        if pending_init:
            logger.info(
                "NUNC %s usuario %s: pendingInit=True, inicializando a orden=%d sin alertar",
                radicado, user_id, max_orden,
            )
            actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)
            limpiar_pending_init(radicados_table, user_id, radicado)
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
                fuente="spoa",
            )
            guardar_alerta(alertas_table, alerta)
            alertas_user.append(alerta)

        user_alertas[user_id] = alertas_user
        actualizar_ultimo_orden(radicados_table, user_id, radicado, max_orden, fecha_ultima)

    return user_alertas


def _send_email_alerts(user_alertas: dict[str, list[Alerta]]) -> None:
    """Envía correos de alerta via Resend."""
    sender = os.environ.get("EMAIL_SENDER", "alertas@alertas-judiciales.dertyos.com")
    cognito = boto3.client("cognito-idp", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    user_pool_id = os.environ.get("USER_POOL_ID", "")

    for user_id, alertas in user_alertas.items():
        try:
            email = _get_user_email(cognito, user_pool_id, user_id)
            if not email:
                logger.warning("No email found for user %s, skipping", user_id)
                continue

            subject, body_html = _build_alert_email(alertas)
            resend.Emails.send({
                "from": f"Alertas Judiciales <{sender}>",
                "to": [email],
                "subject": subject,
                "html": body_html,
            })
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
    subject = f"Alertas Judiciales: {n_actuaciones} nueva(s) actuación(es) en {n_radicados} proceso(s)"

    rows = ""
    for radicado, rad_alertas in by_radicado.items():
        # Use the appropriate portal URL based on source
        rad_fuentes = {a.fuente for a in rad_alertas}
        if "spoa" in rad_fuentes:
            fmt = f"NUNC: {radicado}"
            portal_url = "https://consulta-web.fiscalia.gov.co/"
            portal_label = "Ver en Fiscalía"
        elif "rama_judicial" in rad_fuentes or "siugj" in rad_fuentes:
            fmt = f"{radicado[:5]}-{radicado[5:7]}-{radicado[7:9]}-{radicado[9:12]}-{radicado[12:16]}-{radicado[16:21]}-{radicado[21:23]}"
            portal_url = "https://consultaprocesos.ramajudicial.gov.co/procesos/Index"
            portal_label = "Ver en Rama Judicial"
        else:
            fmt = f"{radicado[:5]}-{radicado[5:7]}-{radicado[7:9]}-{radicado[9:12]}-{radicado[12:16]}-{radicado[16:21]}-{radicado[21:23]}"
            portal_url = f"https://samai.consejodeestado.gov.co/Vistas/Casos/list_procesos.aspx?guid={fmt}"
            portal_label = "Ver en SAMAI"
        rows += (
            f'<tr><td colspan="3" style="background:#f0f0f0;padding:8px;font-weight:bold;">'
            f'{fmt} &nbsp; <a href="{portal_url}" style="font-size:12px;font-weight:normal;">{portal_label}</a>'
            f'</td></tr>'
        )
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
<h2 style="color:#1a73e8;">Alertas Judiciales <small>by Dertyos</small></h2>
<p>Se detectaron <strong>{n_actuaciones}</strong> nueva(s) actuación(es) en <strong>{n_radicados}</strong> proceso(s):</p>
<table style="border-collapse:collapse;width:100%;" border="1" cellpadding="4">
<tr style="background:#1a73e8;color:white;">
<th>Orden</th><th>Actuación</th><th>Fecha</th>
</tr>
{rows}
</table>
<p style="margin-top:20px;">
<a href="https://alertas-judiciales.dertyos.com" style="display:inline-block;background:#1a73e8;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;font-size:14px;">Gestiona tus alertas aquí</a>
</p>
<p style="color:#666;font-size:12px;margin-top:20px;">
Este correo fue enviado automáticamente por Alertas Judiciales by Dertyos.
</p>
</body></html>"""

    return subject, body_html
