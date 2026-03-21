"""Lambda handler para API Gateway — CRUD de radicados, alertas, búsqueda.

Orquesta: recibe evento HTTP, extrae datos, delega a db.py y samai_client.py.
No contiene lógica de negocio propia.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

from models import Radicado
from radicado_utils import (
    normalizar_radicado,
    formatear_radicado,
    extraer_corporacion,
    validar_radicado,
    RadicadoInvalido,
)
from samai_client import SamaiClient
from db import (
    guardar_radicado,
    obtener_radicados_usuario,
    eliminar_radicado,
    obtener_radicado,
    obtener_alertas_usuario,
    eliminar_alertas_radicado,
    marcar_alerta_leida,
    actualizar_alias,
    toggle_activo,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dependencias — instanciadas una vez por cold start
_dynamodb = boto3.resource("dynamodb")
_radicados_table = _dynamodb.Table(os.environ.get("RADICADOS_TABLE", "samai-radicados"))
_alertas_table = _dynamodb.Table(os.environ.get("ALERTAS_TABLE", "samai-alertas"))
samai_client = SamaiClient()


def _response(status: int, body: Any = None) -> dict:
    """Construye respuesta HTTP para API Gateway v2."""
    resp: dict[str, Any] = {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
    }
    if body is not None:
        resp["body"] = json.dumps(body, ensure_ascii=False, default=str)
    else:
        resp["body"] = ""
    return resp


def _get_user_id(event: dict) -> str:
    """Extrae userId del JWT claim."""
    return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]


def _get_body(event: dict) -> dict:
    """Parsea body JSON del evento."""
    body = event.get("body")
    if not body:
        return {}
    return json.loads(body)


def _get_path_param(event: dict, param: str) -> str:
    """Extrae parámetro de path."""
    return (event.get("pathParameters") or {}).get(param, "")


def handler(event: dict, context: Any) -> dict:
    """Entry point Lambda — router por método y path."""
    http = event["requestContext"]["http"]
    method = http["method"]
    path = event.get("rawPath", http["path"])

    # API Gateway v2 HTTP API includes stage prefix in rawPath (e.g. /prod/radicados)
    # Strip it for clean routing
    stage = event.get("requestContext", {}).get("stage", "")
    if stage and path.startswith(f"/{stage}"):
        path = path[len(f"/{stage}") :] or "/"

    logger.info("Routing: %s %s (stage=%s)", method, path, stage)

    try:
        # POST /radicados
        if method == "POST" and path == "/radicados":
            return _post_radicado(event)

        # GET /radicados
        if method == "GET" and path == "/radicados":
            return _get_radicados(event)

        # PATCH /radicados/{id}/toggle
        if method == "PATCH" and path.endswith("/toggle"):
            return _patch_toggle(event)

        # PATCH /radicados/{id}
        if method == "PATCH" and path.startswith("/radicados/") and "/detalle" not in path and "/historial" not in path:
            return _patch_radicado(event)

        # DELETE /radicados/{id}
        if method == "DELETE" and path.startswith("/radicados/"):
            return _delete_radicado(event)

        # GET /radicados/{id}/detalle
        if method == "GET" and "/detalle" in path:
            return _get_detalle(event)

        # GET /radicados/{id}/historial
        if method == "GET" and "/historial" in path:
            return _get_historial(event)

        # PATCH /alertas/{sk}/read
        if method == "PATCH" and "/alertas/" in path and path.endswith("/read"):
            return _patch_alerta_read(event)

        # GET /alertas
        if method == "GET" and path == "/alertas":
            return _get_alertas(event)

        # GET /buscar/{numProceso}
        if method == "GET" and path.startswith("/buscar/"):
            return _get_buscar(event)

        return _response(404, {"error": "Ruta no encontrada"})

    except Exception:
        logger.exception("Error no manejado")
        return _response(500, {"error": "Error interno"})


def _post_radicado(event: dict) -> dict:
    """POST /radicados — agregar radicado a monitorear."""
    user_id = _get_user_id(event)
    body = _get_body(event)

    raw = body.get("radicado", "")
    if not raw:
        return _response(400, {"error": "Campo 'radicado' requerido"})

    if not validar_radicado(raw):
        return _response(400, {"error": f"Radicado inválido: {raw}"})

    norm = normalizar_radicado(raw)
    corp = extraer_corporacion(norm)

    # Check duplicado
    existing = obtener_radicado(_radicados_table, user_id, norm)
    if existing is not None:
        return _response(409, {"error": "Radicado ya registrado"})

    rad = Radicado(
        user_id=user_id,
        radicado=norm,
        corporacion=corp,
        radicado_formato=formatear_radicado(norm),
        alias=body.get("alias", ""),
        ultimo_orden=0,
        activo=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    guardar_radicado(_radicados_table, rad)
    logger.info("Radicado creado: %s para usuario %s", norm, user_id)

    return _response(201, {
        "radicado": rad.radicado,
        "radicadoFormato": rad.radicado_formato,
        "corporacion": rad.corporacion,
        "alias": rad.alias,
    })


def _get_radicados(event: dict) -> dict:
    """GET /radicados — listar mis radicados."""
    user_id = _get_user_id(event)
    radicados = obtener_radicados_usuario(_radicados_table, user_id)
    return _response(200, [
        {
            "radicado": r.radicado,
            "radicadoFormato": r.radicado_formato,
            "corporacion": r.corporacion,
            "alias": r.alias,
            "ultimoOrden": r.ultimo_orden,
            "activo": r.activo,
        }
        for r in radicados
    ])


def _patch_toggle(event: dict) -> dict:
    """PATCH /radicados/{id}/toggle — alternar activo/inactivo."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")
    new_val = toggle_activo(_radicados_table, user_id, radicado_id)
    if new_val is None:
        return _response(404, {"error": "Radicado no encontrado"})
    logger.info("Toggle activo=%s para radicado %s", new_val, radicado_id)
    return _response(200, {"activo": new_val})


def _patch_radicado(event: dict) -> dict:
    """PATCH /radicados/{id} — actualizar alias."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")
    body = json.loads(event.get("body") or "{}")
    alias = body.get("alias", "")

    if actualizar_alias(_radicados_table, user_id, radicado_id, alias):
        logger.info("Alias actualizado: %s para radicado %s", alias, radicado_id)
        rad = obtener_radicado(_radicados_table, user_id, radicado_id)
        if rad:
            return _response(200, rad.to_dynamo())
    return _response(404, {"error": "Radicado no encontrado"})


def _delete_radicado(event: dict) -> dict:
    """DELETE /radicados/{id} — dejar de monitorear."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")

    if eliminar_radicado(_radicados_table, user_id, radicado_id):
        # Cascade: eliminar alertas asociadas a este radicado
        deleted_alertas = eliminar_alertas_radicado(_alertas_table, user_id, radicado_id)
        logger.info(
            "Radicado eliminado: %s para usuario %s (cascade: %d alertas)",
            radicado_id, user_id, deleted_alertas,
        )
        return _response(204)
    return _response(404, {"error": "Radicado no encontrado"})


def _get_historial(event: dict) -> dict:
    """GET /radicados/{id}/historial — actuaciones via SAMAI API."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")

    rad = obtener_radicado(_radicados_table, user_id, radicado_id)
    if rad is None:
        return _response(404, {"error": "Radicado no encontrado"})

    actuaciones = samai_client.get_actuaciones(rad.corporacion, rad.radicado)
    return _response(200, [
        {
            "orden": a.orden,
            "nombre": a.nombre,
            "fecha": a.fecha,
            "anotacion": a.anotacion,
            "estado": a.estado,
            "decision": a.decision,
        }
        for a in actuaciones
    ])


def _get_detalle(event: dict) -> dict:
    """GET /radicados/{id}/detalle — datos completos del proceso."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")

    rad = obtener_radicado(_radicados_table, user_id, radicado_id)
    if rad is None:
        return _response(404, {"error": "Radicado no encontrado"})

    datos = samai_client.get_datos_proceso(rad.corporacion, rad.radicado)
    partes = samai_client.get_sujetos_procesales(rad.corporacion, rad.radicado)
    actuaciones = samai_client.get_actuaciones(rad.corporacion, rad.radicado)

    return _response(200, {
        "proceso": {
            "despacho": datos.get("Despacho", ""),
            "ponente": datos.get("Ponente", ""),
            "tipoProceso": datos.get("TipoProceso", ""),
            "claseActuacion": datos.get("ClaseActuacion", ""),
            "fechaUltimaActuacion": datos.get("FechaUltimaActuacion", ""),
        },
        "partes": [
            {
                "nombre": p.get("NomSujeto", ""),
                "tipo": p.get("TipoSujeto", ""),
            }
            for p in partes
        ],
        "actuaciones": [
            {
                "orden": a.orden,
                "nombre": a.nombre,
                "fecha": a.fecha,
                "anotacion": a.anotacion,
                "estado": a.estado,
                "decision": a.decision,
            }
            for a in actuaciones
        ],
    })


def _patch_alerta_read(event: dict) -> dict:
    """PATCH /alertas/{sk}/read — marcar una alerta como leida."""
    user_id = _get_user_id(event)
    sk = _get_path_param(event, "sk")
    if marcar_alerta_leida(_alertas_table, user_id, sk):
        logger.info("Alerta marcada como leida: %s para usuario %s", sk, user_id)
        return _response(200, {"ok": True})
    return _response(404, {"error": "Alerta no encontrada"})


def _get_alertas(event: dict) -> dict:
    """GET /alertas — listar mis alertas."""
    user_id = _get_user_id(event)
    alertas = obtener_alertas_usuario(_alertas_table, user_id)
    return _response(200, [
        {
            "sk": a.sk,
            "radicado": a.radicado,
            "orden": a.orden,
            "nombreActuacion": a.nombre_actuacion,
            "fechaActuacion": a.fecha_actuacion,
            "anotacion": a.anotacion,
            "createdAt": a.created_at,
            "leido": a.leido,
        }
        for a in alertas
    ])


def _get_buscar(event: dict) -> dict:
    """GET /buscar/{numProceso} — buscar proceso en SAMAI."""
    num_proceso = _get_path_param(event, "numProceso")
    resultados = samai_client.buscar_proceso(num_proceso)
    return _response(200, resultados)
