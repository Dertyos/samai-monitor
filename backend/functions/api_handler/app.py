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

from models import Radicado, Etiqueta, Team, TeamMember, TeamInvitation
from radicado_utils import (
    normalizar_radicado,
    formatear_radicado,
    extraer_corporacion,
    extraer_especialidad,
    validar_radicado,
    parse_ciudad,
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
    actualizar_metadata,
    guardar_etiqueta,
    obtener_etiquetas_usuario,
    actualizar_etiqueta,
    eliminar_etiqueta,
    actualizar_etiquetas_radicado,
    quitar_etiqueta_de_radicados,
    eliminar_cuenta_usuario,
    crear_team,
    obtener_team,
    obtener_teams_usuario,
    agregar_miembro_team,
    obtener_miembros_team,
    eliminar_miembro_team,
    obtener_team_de_usuario,
    contar_procesos_equipo,
    confirmar_team,
    guardar_invitacion,
    obtener_invitacion_por_token,
    obtener_invitaciones_por_email,
    obtener_invitaciones_equipo,
    marcar_invitacion_aceptada,
    eliminar_invitacion,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dependencias — instanciadas una vez por cold start
_cognito = boto3.client("cognito-idp")
_user_pool_id = os.environ.get("USER_POOL_ID", "")
_dynamodb = boto3.resource("dynamodb")
_radicados_table = _dynamodb.Table(os.environ.get("RADICADOS_TABLE", "samai-radicados"))
_alertas_table = _dynamodb.Table(os.environ.get("ALERTAS_TABLE", "samai-alertas"))
_etiquetas_table = _dynamodb.Table(os.environ.get("ETIQUETAS_TABLE", "samai-etiquetas"))
_billing_subs_table = _dynamodb.Table(os.environ.get("BILLING_SUBSCRIPTIONS_TABLE", "samai-billing-subscriptions"))
_billing_plans_table = _dynamodb.Table(os.environ.get("BILLING_PLANS_TABLE", "samai-billing-plans"))
_teams_table = _dynamodb.Table(os.environ.get("TEAMS_TABLE", "samai-teams"))
_team_members_table = _dynamodb.Table(os.environ.get("TEAM_MEMBERS_TABLE", "samai-team-members"))
_lambda_client = boto3.client("lambda")
_monitor_function = os.environ.get("MONITOR_FUNCTION_NAME", "samai-monitor")
_invitations_table = _dynamodb.Table(os.environ.get("TEAM_INVITATIONS_TABLE", "samai-team-invitations"))
_email_sender = os.environ.get("EMAIL_SENDER", "notificaciones-judiciales@dertyos.com")
_frontend_url = os.environ.get("FRONTEND_URL", "https://alertas-judiciales.dertyos.com")

# Resend — cargado lazy para no fallar si SSM no está disponible
_resend_api_key: str | None = None


def _get_resend():
    """Carga Resend API key desde SSM (lazy, una vez)."""
    global _resend_api_key
    if _resend_api_key is None:
        try:
            import resend
            ssm = boto3.client("ssm")
            resp = ssm.get_parameter(
                Name=os.environ.get("RESEND_API_KEY_SSM", "/samai-monitor/resend-api-key"),
                WithDecryption=True,
            )
            _resend_api_key = resp["Parameter"]["Value"]
            resend.api_key = _resend_api_key
        except Exception:
            logger.warning("No se pudo cargar Resend API key")
            return None
    import resend
    return resend
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


# Límites por defecto del plan gratuito
FREE_PLAN_LIMIT = 5

# Mapa de límites por planId (fallback si el plan no tiene features.max_processes)
PLAN_LIMITS: dict[str, int] = {
    "plan-gratuito": 5,
    "plan-pro": 25,
    "plan-pro-plus": 70,
    "plan-firma": 150,
    "plan-enterprise": 1000,
}

PLAN_NAMES: dict[str, str] = {
    "plan-gratuito": "Gratuito",
    "plan-pro": "Pro",
    "plan-pro-plus": "Pro +",
    "plan-firma": "Firma",
    "plan-enterprise": "Enterprise",
}


def _get_user_plan(user_id: str) -> dict | None:
    """Obtiene el plan activo del usuario desde billing tables.

    Retorna dict con planId, name, processLimit, o None si no tiene suscripción (plan gratuito).
    """
    try:
        from boto3.dynamodb.conditions import Key as DKey

        resp = _billing_subs_table.query(
            KeyConditionExpression=DKey("userId").eq(user_id),
        )
        subs = resp.get("Items", [])
        active = [s for s in subs if s.get("status") in ("active", "trialing")]
        if not active:
            return None

        plan_id = active[0].get("planId", "")
        process_limit = PLAN_LIMITS.get(plan_id, FREE_PLAN_LIMIT)
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # Intentar obtener features del plan para límite más preciso
        plan_resp = _billing_plans_table.get_item(Key={"planId": plan_id})
        plan_item = plan_resp.get("Item")
        if plan_item and plan_item.get("features", {}).get("max_processes"):
            process_limit = int(plan_item["features"]["max_processes"])
        if plan_item and plan_item.get("name"):
            plan_name = plan_item["name"]

        return {"planId": plan_id, "name": plan_name, "processLimit": process_limit}
    except Exception:
        logger.warning("Error consultando plan del usuario %s, usando límite gratuito", user_id)
        return None


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

        # PATCH /radicados/{id}/etiquetas
        if method == "PATCH" and path.endswith("/etiquetas"):
            return _patch_radicado_etiquetas(event)

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

        # GET /etiquetas
        if method == "GET" and path == "/etiquetas":
            return _get_etiquetas(event)

        # POST /etiquetas
        if method == "POST" and path == "/etiquetas":
            return _post_etiqueta(event)

        # PATCH /etiquetas/{id}
        if method == "PATCH" and path.startswith("/etiquetas/"):
            return _patch_etiqueta(event)

        # DELETE /etiquetas/{id}
        if method == "DELETE" and path.startswith("/etiquetas/"):
            return _delete_etiqueta(event)

        # DELETE /cuenta
        if method == "DELETE" and path == "/cuenta":
            return _delete_cuenta(event)

        # GET /billing/status
        if method == "GET" and path == "/billing/status":
            return _get_billing_status(event)

        # --- Teams ---
        # POST /teams
        if method == "POST" and path == "/teams":
            return _post_team(event)

        # GET /teams
        if method == "GET" and path == "/teams":
            return _get_teams(event)

        # POST /teams/{teamId}/members
        if method == "POST" and "/teams/" in path and path.endswith("/members"):
            return _post_team_member(event)

        # DELETE /teams/{teamId}/members/{uid}
        if method == "DELETE" and "/teams/" in path and "/members/" in path:
            return _delete_team_member(event)

        # POST /teams/{teamId}/confirm
        if method == "POST" and "/teams/" in path and path.endswith("/confirm"):
            return _post_team_confirm(event)

        # GET /invitations/{token}
        if method == "GET" and path.startswith("/invitations/") and not path.endswith("/accept"):
            return _get_invitation(event)

        # POST /invitations/{token}/accept
        if method == "POST" and path.startswith("/invitations/") and path.endswith("/accept"):
            return _post_accept_invitation(event)

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

    # Enforcement de límite de plan
    # Enforcement de límite: si el usuario pertenece a un equipo con suscripción
    # activa, contar TODOS los radicados de TODOS los miembros (dedup) vs límite
    # del equipo. Si no, contar radicados personales vs plan personal.
    team_id = obtener_team_de_usuario(_team_members_table, user_id)

    if team_id:
        team = obtener_team(_teams_table, team_id)
        if team:
            owner_plan = _get_user_plan(team.owner_user_id)
            if owner_plan and owner_plan["planId"] in TEAM_ELIGIBLE_PLANS:
                # Equipo activo — contar contra límite del equipo
                process_limit = owner_plan["processLimit"]
                process_count = contar_procesos_equipo(
                    _team_members_table, _radicados_table, team_id
                )
                if process_count >= process_limit:
                    return _response(403, {
                        "error": f"El equipo ha alcanzado el límite de {process_limit} procesos.",
                        "code": "PLAN_LIMIT_REACHED",
                        "current": process_count,
                        "limit": process_limit,
                    })
                # Equipo activo con espacio — permitir (skip personal check)
            else:
                # Equipo inactivo (suscripción vencida) — caer a plan personal
                team_id = None

    if not team_id:
        # Sin equipo o equipo inactivo: contar personal vs plan personal
        current_radicados = obtener_radicados_usuario(_radicados_table, user_id)
        process_count = len(current_radicados)
        plan = _get_user_plan(user_id)
        process_limit = plan.get("processLimit", 5) if plan else 5
        plan_name = plan.get("name", "Gratuito") if plan else "Gratuito"
        if process_count >= process_limit:
            return _response(403, {
                "error": f"Has alcanzado el límite de tu plan {plan_name} ({process_limit} procesos). "
                         "Upgrade tu plan para monitorear más procesos.",
                "code": "PLAN_LIMIT_REACHED",
                "current": process_count,
                "limit": process_limit,
            })

    if fuente == "rama_judicial":
        id_proceso = body.get("id_proceso")
        if not id_proceso:
            return _response(400, {"error": "Campo 'id_proceso' requerido para fuente rama_judicial"})
        id_proceso = int(id_proceso)

        pending_init = False
        try:
            max_orden = rj_client.get_max_cons_actuacion(id_proceso)
        except RamaJudicialApiError:
            logger.warning("No se pudo obtener max_cons de CPNU para %s, usando 0", norm)
            max_orden = 0
            pending_init = True  # No se pudo confirmar el estado actual

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
            pending_init=pending_init,
            despacho=body.get("despacho", ""),
            ciudad=body.get("ciudad", ""),
            especialidad=extraer_especialidad(norm),
        )
    elif fuente == "siugj":
        pending_init = False
        try:
            max_orden = siugj_client.get_max_id(norm)
        except SiugjApiError:
            logger.warning("No se pudo obtener max_id de SIUGJ para %s, usando 0", norm)
            max_orden = 0
            pending_init = True  # No se pudo confirmar el estado actual

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
            pending_init=pending_init,
            despacho=body.get("despacho", ""),
            especialidad=extraer_especialidad(norm),
        )
    else:
        corp = extraer_corporacion(norm)
        api_error = False  # True si alguna llamada lanzó excepción (vs respuesta vacía)

        try:
            max_orden = samai_client.get_max_orden(corp, norm)
        except SamaiApiError:
            logger.warning("No se pudo obtener max_orden de SAMAI para %s, usando 0", norm)
            max_orden = 0
            api_error = True

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
                        api_error = False  # Confirmado
                except SamaiApiError:
                    api_error = True

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
                    api_error = False  # Confirmado
                except SamaiApiError:
                    api_error = True

        # pending_init=True cuando la API falló y no pudimos determinar el estado real.
        # El monitor inicializará ultimoOrden sin generar alertas en la primera ejecución.
        pending_init = api_error and max_orden == 0

        # Capturar metadata del proceso para filtros
        despacho = body.get("despacho", "")  # puede venir del resultado de búsqueda
        ciudad = ""
        instancia = ""
        vigente = ""
        fecha_inicio = ""
        try:
            datos = samai_client.get_datos_proceso(corp, norm)
            datos_proc = datos.get("proceso", datos) if isinstance(datos, dict) else {}
            if isinstance(datos_proc, dict):
                if not despacho:
                    despacho = datos_proc.get("Seccion", "")
                ciudad = parse_ciudad(datos_proc.get("cityName", ""))
                instancia = datos_proc.get("claseProceso", "")
                vigente = datos_proc.get("Vigente", "")
                fecha_inicio = datos_proc.get("FECHAPROC", "")
        except SamaiApiError:
            logger.warning("No se pudo obtener metadata SAMAI para %s", norm)

        rad = Radicado(
            user_id=user_id,
            radicado=norm,
            corporacion=corp,
            radicado_formato=formatear_radicado(norm),
            alias=body.get("alias", ""),
            ultimo_orden=max_orden,
            activo=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            pending_init=pending_init,
            despacho=despacho,
            ciudad=ciudad,
            especialidad=extraer_especialidad(norm),
            instancia=instancia,
            vigente=vigente,
            fecha_inicio_proceso=fecha_inicio,
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
        "despacho": rad.despacho,
        "ciudad": rad.ciudad,
        "especialidad": rad.especialidad,
        "instancia": rad.instancia,
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
            "fechaUltimaActuacion": r.fecha_ultima_actuacion,
            "createdAt": r.created_at,
            "etiquetas": r.etiquetas,
            "despacho": r.despacho,
            "ciudad": r.ciudad,
            "especialidad": r.especialidad,
            "instancia": r.instancia,
            "vigente": r.vigente,
            "fechaInicioProceso": r.fecha_inicio_proceso,
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

        # Lazy enrichment para rama_judicial
        if not rad.despacho:
            meta = {
                "despacho": detalle.get("despacho", ""),
                "especialidad": extraer_especialidad(rad.radicado),
                "instancia": detalle.get("claseProceso", ""),
            }
            try:
                actualizar_metadata(_radicados_table, user_id, radicado_id, meta)
                logger.info("Lazy enrichment (RJ): metadata actualizada para %s", radicado_id)
            except Exception:
                logger.warning("No se pudo actualizar metadata RJ para %s", radicado_id)

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

        # Auto-heal: si la corporacion almacenada no retorna datos útiles, buscar la correcta.
        # Ocurre cuando SAMAI estaba caído al registrar el radicado y se guardó la
        # corporacion por defecto (primeros 7 dígitos), que puede no corresponder al
        # tribunal/corporacion real del proceso.
        # Condición: falsy ([], {}, None) O dict con "Seccion" vacío (proceso no existe en esa corp).
        _datos_check = datos_raw.get("proceso", datos_raw) if isinstance(datos_raw, dict) else {}
        _sin_datos = not datos_raw or not (
            isinstance(_datos_check, dict) and _datos_check.get("Seccion", "").strip()
        )
        corp_usada = rad.corporacion
        if _sin_datos:
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

        # Lazy enrichment: si el radicado no tiene metadata, guardarla como side-effect
        if not rad.despacho and isinstance(datos, dict):
            meta = {
                "despacho": datos.get("Seccion", ""),
                "ciudad": parse_ciudad(datos.get("cityName", "")),
                "especialidad": extraer_especialidad(rad.radicado),
                "instancia": datos.get("claseProceso", ""),
                "vigente": datos.get("Vigente", ""),
                "fechaInicioProceso": datos.get("FECHAPROC", ""),
            }
            try:
                actualizar_metadata(_radicados_table, user_id, radicado_id, meta)
                logger.info("Lazy enrichment: metadata actualizada para %s", radicado_id)
            except Exception:
                logger.warning("No se pudo actualizar metadata para %s", radicado_id)

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


# --- Etiquetas ---


def _get_etiquetas(event: dict) -> dict:
    """GET /etiquetas — listar etiquetas del usuario."""
    user_id = _get_user_id(event)
    etiquetas = obtener_etiquetas_usuario(_etiquetas_table, user_id)
    return _response(200, [
        {
            "etiquetaId": e.etiqueta_id,
            "nombre": e.nombre,
            "color": e.color,
            "createdAt": e.created_at,
        }
        for e in etiquetas
    ])


def _post_etiqueta(event: dict) -> dict:
    """POST /etiquetas — crear etiqueta."""
    user_id = _get_user_id(event)
    body = _get_body(event)

    nombre = body.get("nombre", "").strip()
    if not nombre:
        return _response(400, {"error": "Campo 'nombre' requerido"})

    color = body.get("color", "#6b7280").strip()

    etiqueta = Etiqueta(
        user_id=user_id,
        etiqueta_id=Etiqueta.generar_id(),
        nombre=nombre,
        color=color,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    guardar_etiqueta(_etiquetas_table, etiqueta)
    logger.info("Etiqueta creada: %s (%s) para usuario %s", nombre, etiqueta.etiqueta_id, user_id)

    return _response(201, {
        "etiquetaId": etiqueta.etiqueta_id,
        "nombre": etiqueta.nombre,
        "color": etiqueta.color,
        "createdAt": etiqueta.created_at,
    })


def _patch_etiqueta(event: dict) -> dict:
    """PATCH /etiquetas/{id} — editar nombre/color."""
    user_id = _get_user_id(event)
    etiqueta_id = _get_path_param(event, "id")
    body = _get_body(event)

    nombre = body.get("nombre", "").strip()
    color = body.get("color", "").strip()
    if not nombre or not color:
        return _response(400, {"error": "Campos 'nombre' y 'color' requeridos"})

    if actualizar_etiqueta(_etiquetas_table, user_id, etiqueta_id, nombre, color):
        logger.info("Etiqueta actualizada: %s para usuario %s", etiqueta_id, user_id)
        return _response(200, {"etiquetaId": etiqueta_id, "nombre": nombre, "color": color})
    return _response(404, {"error": "Etiqueta no encontrada"})


def _delete_etiqueta(event: dict) -> dict:
    """DELETE /etiquetas/{id} — eliminar etiqueta + limpiar de radicados."""
    user_id = _get_user_id(event)
    etiqueta_id = _get_path_param(event, "id")

    if eliminar_etiqueta(_etiquetas_table, user_id, etiqueta_id):
        count = quitar_etiqueta_de_radicados(_radicados_table, user_id, etiqueta_id)
        logger.info(
            "Etiqueta eliminada: %s para usuario %s (limpiada de %d radicados)",
            etiqueta_id, user_id, count,
        )
        return _response(204)
    return _response(404, {"error": "Etiqueta no encontrada"})


def _patch_radicado_etiquetas(event: dict) -> dict:
    """PATCH /radicados/{id}/etiquetas — asignar etiquetas a un radicado."""
    user_id = _get_user_id(event)
    radicado_id = _get_path_param(event, "id")
    body = _get_body(event)

    etiquetas = body.get("etiquetas", [])
    if not isinstance(etiquetas, list):
        return _response(400, {"error": "Campo 'etiquetas' debe ser una lista"})

    if actualizar_etiquetas_radicado(_radicados_table, user_id, radicado_id, etiquetas):
        logger.info("Etiquetas actualizadas para radicado %s: %s", radicado_id, etiquetas)
        return _response(200, {"etiquetas": etiquetas})
    return _response(404, {"error": "Radicado no encontrado"})


def _delete_cuenta(event: dict) -> dict:
    """DELETE /cuenta — eliminar cuenta y todos los datos del usuario."""
    user_id = _get_user_id(event)

    # 1. Eliminar datos de DynamoDB
    counts = eliminar_cuenta_usuario(
        _radicados_table, _alertas_table, _etiquetas_table, user_id,
    )
    logger.info("Datos eliminados para %s: %s", user_id, counts)

    # 2. Eliminar usuario de Cognito
    try:
        _cognito.admin_delete_user(
            UserPoolId=_user_pool_id,
            Username=user_id,
        )
        logger.info("Usuario Cognito eliminado: %s", user_id)
    except Exception:
        logger.exception("Error eliminando usuario Cognito %s", user_id)
        return _response(500, {"error": "Error eliminando cuenta. Contacte soporte."})

    return _response(200, {"deleted": counts})


def _get_billing_status(event: dict) -> dict:
    """GET /billing/status — plan actual, uso y límites del usuario.

    Si el usuario pertenece a un equipo activo, muestra el plan del equipo.
    """
    user_id = _get_user_id(event)
    radicados = obtener_radicados_usuario(_radicados_table, user_id)
    process_count = len(radicados)

    # Verificar si pertenece a un equipo activo
    team_id = obtener_team_de_usuario(_team_members_table, user_id)
    if team_id:
        team = obtener_team(_teams_table, team_id)
        if team:
            owner_plan = _get_user_plan(team.owner_user_id)
            if owner_plan and owner_plan["planId"] in TEAM_ELIGIBLE_PLANS:
                team_count = contar_procesos_equipo(_team_members_table, _radicados_table, team_id)
                return _response(200, {
                    "plan": owner_plan["planId"],
                    "planName": f"{owner_plan['name']} (equipo: {team.name})",
                    "processLimit": owner_plan["processLimit"],
                    "processCount": team_count,
                    "teamId": team_id,
                    "teamName": team.name,
                })

    # Plan personal
    plan = _get_user_plan(user_id)
    if plan:
        return _response(200, {
            "plan": plan["planId"],
            "planName": plan["name"],
            "processLimit": plan["processLimit"],
            "processCount": process_count,
        })

    return _response(200, {
        "plan": "plan-gratuito",
        "planName": "Gratuito",
        "processLimit": FREE_PLAN_LIMIT,
        "processCount": process_count,
    })


# ============================================
# TEAMS
# ============================================

TEAM_ELIGIBLE_PLANS = {"plan-firma", "plan-enterprise"}
MAX_TEAM_MEMBERS: dict[str, int] = {
    "plan-firma": 5,
    "plan-enterprise": 30,
}


def _extract_team_id(path: str) -> str:
    """Extrae teamId de paths como /teams/{teamId}/..."""
    parts = path.strip("/").split("/")
    # /teams/{teamId} or /teams/{teamId}/members etc.
    if len(parts) >= 2 and parts[0] == "teams":
        return parts[1]
    return ""


def _is_team_member(team_id: str, user_id: str) -> bool:
    """Verifica si un usuario es miembro de un equipo."""
    members = obtener_miembros_team(_team_members_table, team_id)
    return any(m.user_id == user_id for m in members)


def _is_team_owner(team_id: str, user_id: str) -> bool:
    """Verifica si un usuario es owner del equipo."""
    team = obtener_team(_teams_table, team_id)
    if team is None:
        return False
    return team.owner_user_id == user_id


def _post_team(event: dict) -> dict:
    """POST /teams — crear equipo."""
    user_id = _get_user_id(event)
    body = _get_body(event)

    name = body.get("name", "").strip()
    if not name:
        return _response(400, {"error": "Campo 'name' requerido"})

    # Verificar que el usuario tenga plan Firma o Enterprise activo
    plan = _get_user_plan(user_id)
    if not plan or plan["planId"] not in TEAM_ELIGIBLE_PLANS:
        return _response(403, {
            "error": "Se requiere plan Firma o Enterprise para crear equipos",
            "code": "PLAN_REQUIRED",
        })

    # Verificar que no tenga otro equipo como owner
    existing_teams = obtener_teams_usuario(_team_members_table, _teams_table, user_id)
    owned = [t for t in existing_teams if t.owner_user_id == user_id]
    if owned:
        return _response(409, {"error": "Ya tienes un equipo creado"})

    team_id = Team.generar_id()
    now = datetime.now(timezone.utc).isoformat()

    team = Team(
        team_id=team_id,
        name=name,
        owner_user_id=user_id,
        plan_id=plan["planId"],
        created_at=now,
    )
    crear_team(_teams_table, team)

    # Auto-agregar owner como miembro
    owner_member = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role="owner",
        joined_at=now,
    )
    agregar_miembro_team(_team_members_table, owner_member)

    logger.info("Equipo creado: %s por user %s", team_id, user_id)
    return _response(201, team.to_dynamo())


def _resolve_user_email(user_id: str) -> str:
    """Resuelve el email de un usuario via Cognito. Retorna userId si falla."""
    try:
        resp = _cognito.admin_get_user(UserPoolId=_user_pool_id, Username=user_id)
        for attr in resp.get("UserAttributes", []):
            if attr["Name"] == "email":
                return attr["Value"]
    except Exception:
        pass
    return user_id


def _get_teams(event: dict) -> dict:
    """GET /teams — listar equipos del usuario con estado activo/inactivo."""
    user_id = _get_user_id(event)
    teams = obtener_teams_usuario(_team_members_table, _teams_table, user_id)
    result = []
    for t in teams:
        data = t.to_dynamo()
        owner_plan = _get_user_plan(t.owner_user_id)
        active = bool(owner_plan and owner_plan["planId"] in TEAM_ELIGIBLE_PLANS)
        data["active"] = active
        data["pendingConfirmation"] = t.pending_confirmation
        data["processLimit"] = owner_plan["processLimit"] if owner_plan else 0
        data["processCount"] = contar_procesos_equipo(_team_members_table, _radicados_table, t.team_id)
        members_raw = obtener_miembros_team(_team_members_table, t.team_id)
        members_data = []
        for m in members_raw:
            md = m.to_dynamo()
            md["email"] = _resolve_user_email(m.user_id)
            members_data.append(md)
        data["members"] = members_data
        invites = obtener_invitaciones_equipo(_invitations_table, t.team_id)
        data["pendingInvitations"] = [
            {"email": inv.email, "inviteId": inv.invite_id, "status": inv.status, "createdAt": inv.created_at}
            for inv in invites if inv.status == "pending"
        ]
        result.append(data)
    return _response(200, result)


def _send_team_email(to: str, subject: str, html: str) -> None:
    """Envía un email via Resend. No lanza excepciones."""
    r = _get_resend()
    if not r:
        logger.warning("Resend no disponible, email no enviado a %s", to)
        return
    try:
        r.Emails.send({
            "from": _email_sender,
            "to": [to],
            "subject": subject,
            "html": html,
        })
    except Exception:
        logger.warning("Error enviando email a %s", to)


def _post_team_member(event: dict) -> dict:
    """POST /teams/{teamId}/members — invitar miembro por email.

    Si el email está registrado en Cognito → agregar al equipo + email de notificación.
    Si no está registrado → guardar invitación pendiente + email de invitación.
    """
    user_id = _get_user_id(event)
    http = event["requestContext"]["http"]
    path = http["path"]
    stage = event.get("requestContext", {}).get("stage", "")
    raw_path = event.get("rawPath", path)
    if stage and raw_path.startswith(f"/{stage}"):
        raw_path = raw_path[len(f"/{stage}"):]
    team_id = _extract_team_id(raw_path)

    if not team_id:
        return _response(400, {"error": "teamId requerido"})

    if not _is_team_owner(team_id, user_id):
        return _response(403, {"error": "Solo el dueño del equipo puede invitar miembros"})

    body = _get_body(event)
    email = body.get("email", "").strip().lower()
    if not email:
        return _response(400, {"error": "Campo 'email' requerido"})

    team = obtener_team(_teams_table, team_id)
    if team is None:
        return _response(404, {"error": "Equipo no encontrado"})

    # Verificar límite de miembros (incluyendo invitaciones pendientes)
    max_members = MAX_TEAM_MEMBERS.get(team.plan_id, 5)
    members = obtener_miembros_team(_team_members_table, team_id)
    pending_invites = [
        inv for inv in obtener_invitaciones_equipo(_invitations_table, team_id)
        if inv.status == "pending"
    ]
    if len(members) + len(pending_invites) >= max_members:
        return _response(403, {
            "error": f"El equipo ya tiene el máximo de {max_members} miembros (incluyendo invitaciones pendientes)",
            "code": "TEAM_MEMBER_LIMIT",
        })

    # Si ya hay invitación pendiente para este email en este equipo, eliminarla (reenvío)
    existing_invites = obtener_invitaciones_por_email(_invitations_table, email)
    for inv in existing_invites:
        if inv.team_id == team_id:
            eliminar_invitacion(_invitations_table, inv.invite_id)

    # Buscar si el email está registrado en Cognito
    target_user_id = None
    try:
        resp = _cognito.list_users(
            UserPoolId=_user_pool_id,
            Filter=f'email = "{email}"',
            Limit=1,
        )
        users = resp.get("Users", [])
        if users:
            target_user_id = users[0]["Username"]
    except Exception:
        logger.exception("Error buscando usuario por email")
        return _response(500, {"error": "Error buscando usuario"})

    now = datetime.now(timezone.utc)

    if target_user_id:
        # Usuario registrado → verificar que no sea ya miembro
        if _is_team_member(team_id, target_user_id):
            return _response(409, {"error": "El usuario ya es miembro del equipo"})

        # Agregar directamente
        member = TeamMember(
            team_id=team_id,
            user_id=target_user_id,
            role="member",
            joined_at=now.isoformat(),
        )
        agregar_miembro_team(_team_members_table, member)

        # Verificar plan personal
        member_plan = _get_user_plan(target_user_id)
        has_personal_plan = member_plan is not None and member_plan["planId"] != "plan-gratuito"

        # Email de notificación
        _send_team_email(
            to=email,
            subject=f"Te agregaron al equipo {team.name} — Alertas Judiciales",
            html=f"""
            <h2>Te agregaron a un equipo</h2>
            <p>Ahora eres parte del equipo <strong>{team.name}</strong> en Alertas Judiciales.</p>
            <p>Todos tus radicados ahora cuentan contra el limite compartido del equipo.</p>
            {"<p><strong>Nota:</strong> Tienes un plan " + member_plan["name"] + " activo. Ya no lo necesitas porque estas cubierto por el equipo. Puedes cancelarlo desde tu perfil.</p>" if has_personal_plan else ""}
            <p><a href="{_frontend_url}/dashboard">Ir al dashboard</a></p>
            """,
        )

        logger.info("Miembro %s agregado a equipo %s (registrado)", target_user_id, team_id)
        response_data = member.to_dynamo()
        response_data["added"] = True
        return _response(201, response_data)

    else:
        # Usuario NO registrado → crear invitación pendiente
        from datetime import timedelta

        invitation = TeamInvitation(
            invite_id=TeamInvitation.generar_id(),
            team_id=team_id,
            email=email,
            role="member",
            invited_by=user_id,
            status="pending",
            token=TeamInvitation.generar_token(),
            created_at=now.isoformat(),
            ttl=int((now + timedelta(days=7)).timestamp()),
        )
        guardar_invitacion(_invitations_table, invitation)

        # Email de invitación
        invite_url = f"{_frontend_url}/invite/{invitation.token}"
        _send_team_email(
            to=email,
            subject=f"Te invitaron al equipo {team.name} — Alertas Judiciales",
            html=f"""
            <h2>Te invitaron a un equipo</h2>
            <p>Te invitaron a unirte al equipo <strong>{team.name}</strong> en Alertas Judiciales.</p>
            <p>Alertas Judiciales monitorea procesos en SAMAI y te notifica cuando hay novedades.</p>
            <p><a href="{invite_url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:white;border-radius:8px;text-decoration:none;">Aceptar invitacion</a></p>
            <p style="color:#6b7280;font-size:0.85rem;">Esta invitacion expira en 7 dias.</p>
            """,
        )

        logger.info("Invitacion creada para %s al equipo %s (no registrado)", email, team_id)
        return _response(201, {
            "invited": True,
            "email": email,
            "message": f"Invitacion enviada a {email}. La invitacion expira en 7 dias.",
        })


def _delete_team_member(event: dict) -> dict:
    """DELETE /teams/{teamId}/members/{uid} — quitar miembro."""
    user_id = _get_user_id(event)
    http = event["requestContext"]["http"]
    path = http["path"]
    stage = event.get("requestContext", {}).get("stage", "")
    raw_path = event.get("rawPath", path)
    if stage and raw_path.startswith(f"/{stage}"):
        raw_path = raw_path[len(f"/{stage}"):]

    parts = raw_path.strip("/").split("/")
    # /teams/{teamId}/members/{uid}
    if len(parts) < 4:
        return _response(400, {"error": "Path incompleto"})
    team_id = parts[1]
    target_uid = parts[3]

    # Solo el owner puede quitar miembros (o el propio miembro puede salir)
    if user_id != target_uid and not _is_team_owner(team_id, user_id):
        return _response(403, {"error": "No autorizado"})

    # No se puede quitar al owner
    if _is_team_owner(team_id, target_uid):
        return _response(400, {"error": "No se puede quitar al dueño del equipo"})

    removed = eliminar_miembro_team(_team_members_table, team_id, target_uid)
    if not removed:
        return _response(404, {"error": "Miembro no encontrado"})

    logger.info("Miembro %s removido de equipo %s", target_uid, team_id)
    return _response(200, {"deleted": True})


def _post_team_confirm(event: dict) -> dict:
    """POST /teams/{teamId}/confirm — owner confirma equipo tras renovar suscripción.

    Quita pendingConfirmation y dispara reactivación de radicados de todos los miembros.
    """
    user_id = _get_user_id(event)
    http = event["requestContext"]["http"]
    path = http["path"]
    stage = event.get("requestContext", {}).get("stage", "")
    raw_path = event.get("rawPath", path)
    if stage and raw_path.startswith(f"/{stage}"):
        raw_path = raw_path[len(f"/{stage}"):]
    team_id = _extract_team_id(raw_path)

    if not team_id:
        return _response(400, {"error": "teamId requerido"})

    if not _is_team_owner(team_id, user_id):
        return _response(403, {"error": "Solo el dueño del equipo puede confirmar"})

    team = obtener_team(_teams_table, team_id)
    if team is None:
        return _response(404, {"error": "Equipo no encontrado"})

    if not team.pending_confirmation:
        return _response(200, {"status": "already_confirmed"})

    # Quitar flag
    confirmar_team(_teams_table, team_id)

    # Reactivar radicados de todos los miembros (async, via monitor)
    members = obtener_miembros_team(_team_members_table, team_id)
    for member in members:
        if member.user_id == user_id:
            continue  # El owner ya fue reactivado por el webhook
        try:
            _lambda_client.invoke(
                FunctionName=_monitor_function,
                InvocationType="Event",
                Payload=json.dumps({"action": "reactivate", "userId": member.user_id}),
            )
        except Exception:
            logger.warning("No se pudo invocar monitor para reactivar user=%s", member.user_id)

    logger.info("Equipo %s confirmado por owner %s, %d miembros reactivandose", team_id, user_id, len(members))
    return _response(200, {"status": "confirmed", "membersReactivated": len(members) - 1})


# ============================================
# INVITACIONES
# ============================================


def _get_invitation(event: dict) -> dict:
    """GET /invitations/{token} — consultar una invitación por token (público, sin auth)."""
    http = event["requestContext"]["http"]
    path = http["path"]
    stage = event.get("requestContext", {}).get("stage", "")
    raw_path = event.get("rawPath", path)
    if stage and raw_path.startswith(f"/{stage}"):
        raw_path = raw_path[len(f"/{stage}"):]

    parts = raw_path.strip("/").split("/")
    if len(parts) < 2:
        return _response(400, {"error": "Token requerido"})
    token = parts[1]

    invitation = obtener_invitacion_por_token(_invitations_table, token)
    if invitation is None:
        return _response(404, {"error": "Invitacion no encontrada o expirada"})

    team = obtener_team(_teams_table, invitation.team_id)
    return _response(200, {
        "token": invitation.token,
        "teamName": team.name if team else "",
        "email": invitation.email,
        "status": invitation.status,
        "createdAt": invitation.created_at,
    })


def _post_accept_invitation(event: dict) -> dict:
    """POST /invitations/{token}/accept — aceptar una invitación (requiere auth)."""
    user_id = _get_user_id(event)
    http = event["requestContext"]["http"]
    path = http["path"]
    stage = event.get("requestContext", {}).get("stage", "")
    raw_path = event.get("rawPath", path)
    if stage and raw_path.startswith(f"/{stage}"):
        raw_path = raw_path[len(f"/{stage}"):]

    parts = raw_path.strip("/").split("/")
    if len(parts) < 2:
        return _response(400, {"error": "Token requerido"})
    token = parts[1]

    invitation = obtener_invitacion_por_token(_invitations_table, token)
    if invitation is None:
        return _response(404, {"error": "Invitacion no encontrada o expirada"})

    # Verificar que no sea ya miembro
    if _is_team_member(invitation.team_id, user_id):
        marcar_invitacion_aceptada(_invitations_table, invitation.invite_id)
        return _response(200, {"status": "already_member"})

    # Agregar al equipo
    now = datetime.now(timezone.utc).isoformat()
    member = TeamMember(
        team_id=invitation.team_id,
        user_id=user_id,
        role=invitation.role,
        joined_at=now,
    )
    agregar_miembro_team(_team_members_table, member)
    marcar_invitacion_aceptada(_invitations_table, invitation.invite_id)

    team = obtener_team(_teams_table, invitation.team_id)
    logger.info("Invitacion aceptada: user=%s equipo=%s", user_id, invitation.team_id)
    return _response(200, {
        "status": "accepted",
        "teamId": invitation.team_id,
        "teamName": team.name if team else "",
    })
