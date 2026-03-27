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
from samai_client import SamaiClient, SamaiApiError
from rama_judicial_client import RamaJudicialClient, RamaJudicialApiError
from siugj_client import SiugjClient, SiugjApiError
from db import (
    guardar_radicado,
    obtener_radicados_usuario,
    eliminar_radicado,
    obtener_radicado,
    obtener_alertas_usuario,
    eliminar_alertas_radicado,
    marcar_alerta_leida,
    marcar_todas_leidas,
    actualizar_alias,
    toggle_activo,
    actualizar_corporacion,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dependencias — instanciadas una vez por cold start
_dynamodb = boto3.resource("dynamodb")
_radicados_table = _dynamodb.Table(os.environ.get("RADICADOS_TABLE", "samai-radicados"))
_alertas_table = _dynamodb.Table(os.environ.get("ALERTAS_TABLE", "samai-alertas"))
samai_client = SamaiClient()
rj_client = RamaJudicialClient()
siugj_client = SiugjClient()


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

        # PATCH /alertas/read-all (must come BEFORE /alertas/{sk}/read)
        if method == "PATCH" and path == "/alertas/read-all":
            return _patch_read_all(event)

        # PATCH /alertas/{sk}/read
        if method == "PATCH" and "/alertas/" in path and path.endswith("/read"):
            return _patch_alerta_read(event)

        # GET /alertas
        if method == "GET" and path == "/alertas":
            return _get_alertas(event)

        # GET /buscar/{numProceso}
        if method == "GET" and path.startswith("/buscar/"):
            return _get_buscar(event)

        # GET /buscar-rj/{numProceso}
        if method == "GET" and path.startswith("/buscar-rj/"):
            return _get_buscar_rj(event)

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
    fuente = body.get("fuente", "samai")

    # Check duplicado — un mismo radicado puede estar en ambas fuentes
    existing = obtener_radicado(_radicados_table, user_id, norm)
    if existing is not None and existing.fuente == fuente:
        return _response(409, {"error": "Radicado ya registrado"})

    if fuente == "rama_judicial":
        id_proceso = body.get("id_proceso")
        if not id_proceso:
            return _response(400, {"error": "Campo 'id_proceso' requerido para fuente rama_judicial"})
        id_proceso = int(id_proceso)

        try:
            max_orden = rj_client.get_max_cons_actuacion(id_proceso)
        except RamaJudicialApiError:
            logger.warning("No se pudo obtener max_cons de CPNU para %s, usando 0", norm)
            max_orden = 0

        rad = Radicado(
            user_id=user_id,
            radicado=norm,
            corporacion="",
            radicado_formato=formatear_radicado(norm),
            alias=body.get("alias", ""),
            ultimo_orden=max_orden,
            activo=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            fuente="rama_judicial",
            id_proceso=id_proceso,
        )
    elif fuente == "siugj":
        try:
            max_orden = siugj_client.get_max_id(norm)
        except SiugjApiError:
            logger.warning("No se pudo obtener max_id de SIUGJ para %s, usando 0", norm)
            max_orden = 0

        rad = Radicado(
            user_id=user_id,
            radicado=norm,
            corporacion="",
            radicado_formato=formatear_radicado(norm),
            alias=body.get("alias", ""),
            ultimo_orden=max_orden,
            activo=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            fuente="siugj",
        )
    else:
        corp = extraer_corporacion(norm)

        try:
            max_orden = samai_client.get_max_orden(corp, norm)
        except SamaiApiError:
            logger.warning("No se pudo obtener max_orden de SAMAI para %s, usando 0", norm)
            max_orden = 0

        # 2da+ instancia: SAMAI puede usar una corporacion diferente (dígitos [0:5]+[7:9]).
        # Si no se encontraron actuaciones y el radicado no es 1ra instancia, intentar
        # la corporacion alternativa y usarla si retorna datos.
        if max_orden == 0 and norm[-2:] != "00":
            corp_alt = norm[:5] + norm[7:9]
            if corp_alt != corp:
                try:
                    max_orden_alt = samai_client.get_max_orden(corp_alt, norm)
                    if max_orden_alt > 0:
                        logger.info(
                            "Radicado %s: corporacion alternativa %s -> %d actuaciones",
                            norm, corp_alt, max_orden_alt,
                        )
                        corp = corp_alt
                        max_orden = max_orden_alt
                except SamaiApiError:
                    pass

        # Fallback Tribunales SAMAI: si los primeros 7 dígitos no dan resultados, el proceso
        # puede estar en un Tribunal Administrativo con distinto código de corporación.
        # Ej: radicado "11001..." puede estar en Tribunal de Cundinamarca (2500023), no en
        # Juzgado de Bogotá (1100133).
        if max_orden == 0:
            corp_tribunal = samai_client.encontrar_corporacion(norm, excluir=[corp])
            if corp_tribunal:
                try:
                    max_orden = samai_client.get_max_orden(corp_tribunal, norm)
                    corp = corp_tribunal
                except SamaiApiError:
                    pass

        rad = Radicado(
            user_id=user_id,
            radicado=norm,
            corporacion=corp,
            radicado_formato=formatear_radicado(norm),
            alias=body.get("alias", ""),
            ultimo_orden=max_orden,
            activo=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    guardar_radicado(_radicados_table, rad)
    logger.info("Radicado creado: %s (fuente=%s) para usuario %s", norm, fuente, user_id)

    return _response(201, {
        "radicado": rad.radicado,
        "radicadoFormato": rad.radicado_formato,
        "corporacion": rad.corporacion,
        "alias": rad.alias,
        "fuente": rad.fuente,
        "idProceso": rad.id_proceso,
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
            "fuente": r.fuente,
            "idProceso": r.id_proceso,
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
    """GET /radicados/{id}/historial — actuaciones (SAMAI o Rama Judicial)."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")

    rad = obtener_radicado(_radicados_table, user_id, radicado_id)
    if rad is None:
        return _response(404, {"error": "Radicado no encontrado"})

    if rad.fuente == "rama_judicial":
        if rad.id_proceso is None:
            return _response(400, {"error": "Radicado sin id_proceso"})
        actuaciones = rj_client.get_todas_actuaciones(rad.id_proceso)
    elif rad.fuente == "siugj":
        actuaciones = siugj_client.get_actuaciones(rad.radicado)
    else:
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
    """GET /radicados/{id}/detalle — datos completos del proceso (SAMAI o Rama Judicial)."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")

    rad = obtener_radicado(_radicados_table, user_id, radicado_id)
    if rad is None:
        return _response(404, {"error": "Radicado no encontrado"})

    if rad.fuente == "siugj":
        procesos = siugj_client.buscar_por_radicado(rad.radicado)
        p = procesos[0] if procesos else {}
        actuaciones = siugj_client.get_actuaciones(rad.radicado)
        partes = []
        if p.get("actor"):
            partes.append({"nombre": p["actor"], "tipo": "Demandante/Accionante"})
        if p.get("demandado"):
            partes.append({"nombre": p["demandado"], "tipo": "Demandado/Indiciado"})
        return _response(200, {
            "proceso": {
                "despacho": p.get("despacho", ""),
                "ponente": "",
                "tipoProceso": p.get("nombreEspecialidad", ""),
                "claseActuacion": p.get("nombreTipoProceso", ""),
                "fechaUltimaActuacion": actuaciones[0].fecha if actuaciones else "",
            },
            "partes": partes,
            "actuaciones": [
                {
                    "orden": a.orden,
                    "nombre": a.nombre,
                    "fecha": a.fecha,
                    "anotacion": a.anotacion,
                    "estado": a.estado,
                    "decision": a.decision,
                    "docHash": a.doc_hash,
                }
                for a in actuaciones
            ],
            "fuente": "siugj",
        })
    elif rad.fuente == "rama_judicial":
        if rad.id_proceso is None:
            return _response(400, {"error": "Radicado sin id_proceso"})

        detalle = rj_client.get_detalle(rad.id_proceso)
        sujetos = rj_client.get_sujetos(rad.id_proceso)
        actuaciones = rj_client.get_todas_actuaciones(rad.id_proceso)

        return _response(200, {
            "proceso": {
                "despacho": detalle.get("despacho", ""),
                "ponente": detalle.get("ponente", ""),
                "tipoProceso": detalle.get("tipoProceso", ""),
                "claseActuacion": detalle.get("claseProceso", ""),
                "fechaUltimaActuacion": detalle.get("ultimaActualizacion", ""),
            },
            "partes": [
                {
                    "nombre": s.get("nombreRazonSocial", ""),
                    "tipo": s.get("tipoSujeto", ""),
                }
                for s in sujetos
            ],
            "actuaciones": [
                {
                    "orden": a.orden,
                    "nombre": a.nombre,
                    "fecha": a.fecha,
                    "anotacion": a.anotacion,
                    "estado": a.estado,
                    "decision": a.decision,
                    "docHash": a.doc_hash,
                }
                for a in actuaciones
            ],
            "fuente": "rama_judicial",
            "idProceso": rad.id_proceso,
        })
    else:
        try:
            datos_raw = samai_client.get_datos_proceso(rad.corporacion, rad.radicado)
        except SamaiApiError as e:
            logger.warning("SAMAI no disponible para detalle de %s: %s", radicado_id, e)
            return _response(503, {"error": "El servidor de SAMAI no está disponible en este momento. Intenta de nuevo en unos minutos."})

        # Auto-heal: si la corporacion almacenada no retorna datos, buscar la correcta.
        # Ocurre cuando SAMAI estaba caído al registrar el radicado y se guardó la
        # corporacion por defecto (primeros 7 dígitos), que puede no corresponder al
        # tribunal/corporacion real del proceso.
        corp_usada = rad.corporacion
        if not datos_raw:
            logger.info(
                "Corporacion %s no retorna datos para %s — buscando corporacion correcta",
                rad.corporacion, radicado_id,
            )
            try:
                corp_nueva = samai_client.encontrar_corporacion(rad.radicado, excluir=[rad.corporacion])
            except Exception:
                corp_nueva = None
            if corp_nueva and corp_nueva != rad.corporacion:
                logger.info(
                    "Auto-heal: actualizando corporacion %s -> %s para radicado %s",
                    rad.corporacion, corp_nueva, radicado_id,
                )
                actualizar_corporacion(_radicados_table, user_id, radicado_id, corp_nueva)
                corp_usada = corp_nueva
                try:
                    datos_raw = samai_client.get_datos_proceso(corp_nueva, rad.radicado)
                except SamaiApiError:
                    datos_raw = {}

        datos = datos_raw.get("proceso", datos_raw) if isinstance(datos_raw, dict) else {}
        try:
            partes = samai_client.get_sujetos_procesales(corp_usada, rad.radicado)
        except SamaiApiError:
            partes = []
        try:
            actuaciones = samai_client.get_actuaciones(corp_usada, rad.radicado)
        except SamaiApiError:
            actuaciones = []

        return _response(200, {
            "proceso": {
                "despacho": datos.get("Seccion", ""),
                "ponente": datos.get("Ponente", ""),
                "tipoProceso": datos.get("tipoProceso", ""),
                "claseActuacion": datos.get("claseProceso", ""),
                "fechaUltimaActuacion": datos.get("UltimaActuacionDespachoFecha", ""),
            },
            "partes": [
                {
                    "nombre": p.get("NOMBRE", ""),
                    "tipo": p.get("TIPO", ""),
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
                    "docHash": a.doc_hash,
                }
                for a in actuaciones
            ],
            "corporacion": corp_usada,
            "fuente": "samai",
        })


def _patch_read_all(event: dict) -> dict:
    """PATCH /alertas/read-all — marcar todas las alertas como leidas."""
    user_id = _get_user_id(event)
    count = marcar_todas_leidas(_alertas_table, user_id)
    logger.info("Marcadas %d alertas como leidas para usuario %s", count, user_id)
    return _response(200, {"count": count})


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


def _get_buscar_rj(event: dict) -> dict:
    """GET /buscar-rj/{numProceso} — buscar en Rama Judicial (CPNU primero, SIUGJ fallback).

    Flujo transparente: intenta CPNU, si no encuentra intenta SIUGJ.
    Cada resultado incluye campo 'sistema': 'cpnu' | 'siugj' para que el
    frontend pueda mostrar de dónde vino sin que el usuario tenga que elegir.
    """
    num_proceso = _get_path_param(event, "numProceso")
    if not num_proceso or not validar_radicado(num_proceso):
        return _response(400, {"error": "Número de radicado inválido"})

    norm = normalizar_radicado(num_proceso)

    # 1. Intentar CPNU
    try:
        cpnu_procesos = rj_client.buscar_por_radicado(norm)
    except RamaJudicialApiError as e:
        logger.warning("CPNU buscar_por_radicado error: %s", e)
        cpnu_procesos = []

    if cpnu_procesos:
        return _response(200, [
            {
                "idProceso": p.get("idProceso"),
                "despacho": p.get("despacho", ""),
                "departamento": p.get("departamento", ""),
                "sujetosProcesales": p.get("sujetosProcesales", ""),
                "fechaUltimaActuacion": p.get("fechaUltimaActuacion", ""),
                "llaveProceso": p.get("llaveProceso", norm),
                "sistema": "cpnu",
            }
            for p in cpnu_procesos
        ])

    # 2. Fallback: intentar SIUGJ
    try:
        siugj_procesos = siugj_client.buscar_por_radicado(norm)
    except SiugjApiError as e:
        logger.warning("SIUGJ buscar_por_radicado error: %s", e)
        siugj_procesos = []

    if siugj_procesos:
        return _response(200, [
            {
                "idProceso": None,
                "despacho": p.get("despacho", ""),
                "departamento": "",
                "sujetosProcesales": f"{p.get('actor', '')} / {p.get('demandado', '')}".strip(" /"),
                "fechaUltimaActuacion": "",
                "llaveProceso": p.get("codigoUnicoProceso", norm),
                "sistema": "siugj",
            }
            for p in siugj_procesos
        ])

    return _response(200, [])
