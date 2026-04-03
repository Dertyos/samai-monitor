"""Lambda handler para Billing API — planes, suscripciones, facturas, config Wompi.

Endpoints:
  GET  /billing/plans          — listar planes
  GET  /billing/subscription   — suscripcion activa del usuario
  POST /billing/subscribe      — registrar intent de suscripcion (pre-widget)
  DELETE /billing/subscription — cancelar suscripcion
  GET  /billing/invoices       — historial de pagos
  GET  /billing/wompi-config   — public key + integrity hash para el widget
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")
_plans_table = _dynamodb.Table(os.environ.get("BILLING_PLANS_TABLE", "samai-billing-plans"))
_subscriptions_table = _dynamodb.Table(os.environ.get("BILLING_SUBSCRIPTIONS_TABLE", "samai-billing-subscriptions"))
_events_table = _dynamodb.Table(os.environ.get("BILLING_EVENTS_TABLE", "samai-billing-events"))

_wompi_public_key = os.environ.get("WOMPI_PUBLIC_KEY", "")
_wompi_integrity_key = os.environ.get("WOMPI_INTEGRITY_KEY", "")
_wompi_sandbox = os.environ.get("WOMPI_SANDBOX", "true").lower() == "true"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Entry point — router por metodo y path."""
    http = event["requestContext"]["http"]
    method = http["method"]
    path = event.get("rawPath", http["path"])

    stage = event.get("requestContext", {}).get("stage", "")
    if stage and path.startswith(f"/{stage}"):
        path = path[len(f"/{stage}"):] or "/"

    logger.info("Billing API: %s %s", method, path)

    try:
        if method == "GET" and path == "/billing/plans":
            return _get_plans()

        if method == "GET" and path == "/billing/subscription":
            return _get_subscription(event)

        if method == "POST" and path == "/billing/subscribe":
            return _post_subscribe(event)

        if method == "DELETE" and path == "/billing/subscription":
            return _delete_subscription(event)

        if method == "GET" and path == "/billing/invoices":
            return _get_invoices(event)

        if method == "GET" and path == "/billing/wompi-config":
            return _get_wompi_config(event)

        return _response(404, {"error": "Ruta no encontrada"})

    except Exception:
        logger.exception("Error en billing API")
        return _response(500, {"error": "Error interno"})


def _get_user_id(event: dict) -> str:
    return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]


def _get_body(event: dict) -> dict:
    body = event.get("body")
    if not body:
        return {}
    return json.loads(body)


def _get_plans() -> dict:
    """GET /billing/plans — listar planes activos."""
    resp = _plans_table.scan()
    items = resp.get("Items", [])
    plans = [
        {
            "id": item["planId"],
            "name": item.get("name", ""),
            "amount": int(item.get("amount", 0)),
            "currency": item.get("currency", "cop"),
            "interval": item.get("interval", "month"),
            "trialDays": int(item.get("trialDays", 0)),
            "features": item.get("features", {}),
        }
        for item in items
        if item.get("active", True)
    ]
    plans.sort(key=lambda p: p["amount"])
    return _response(200, plans)


def _get_subscription(event: dict) -> dict:
    """GET /billing/subscription — suscripcion activa del usuario."""
    user_id = _get_user_id(event)
    resp = _subscriptions_table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
    )
    subs = resp.get("Items", [])
    active = [s for s in subs if s.get("status") in ("active", "trialing")]

    if not active:
        return _response(200, {"subscription": None})

    sub = active[0]
    return _response(200, {
        "subscription": {
            "planId": sub.get("planId", ""),
            "status": sub.get("status", ""),
            "currentPeriodStart": sub.get("currentPeriodStart", ""),
            "currentPeriodEnd": sub.get("currentPeriodEnd", ""),
            "cancelAtPeriodEnd": sub.get("cancelAtPeriodEnd", False),
        }
    })


def _post_subscribe(event: dict) -> dict:
    """POST /billing/subscribe — generar reference + integrity hash para Wompi widget."""
    user_id = _get_user_id(event)
    body = _get_body(event)
    plan_id = body.get("planId", "")

    if not plan_id:
        return _response(400, {"error": "planId requerido"})

    # Verificar que no tiene suscripcion activa
    resp = _subscriptions_table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
    )
    active = [s for s in resp.get("Items", []) if s.get("status") in ("active", "trialing")]
    if active:
        return _response(409, {"error": "Ya tienes una suscripcion activa"})

    # Obtener plan
    plan_resp = _plans_table.get_item(Key={"planId": plan_id})
    plan = plan_resp.get("Item")
    if not plan:
        return _response(404, {"error": "Plan no encontrado"})

    amount_cents = int(plan.get("amount", 0)) * 100  # COP a centavos
    if amount_cents == 0:
        return _response(400, {"error": "No puedes suscribirte al plan gratuito"})

    # Generar reference unica
    ts = int(datetime.now(timezone.utc).timestamp())
    reference = f"sub_{user_id}_{plan_id}_{ts}"

    # Generar integrity hash: reference + amount_in_cents + COP + integrity_key
    integrity_concat = f"{reference}{amount_cents}COP{_wompi_integrity_key}"
    integrity_hash = hashlib.sha256(integrity_concat.encode()).hexdigest()

    return _response(200, {
        "reference": reference,
        "amountInCents": amount_cents,
        "currency": "COP",
        "integrityHash": integrity_hash,
        "publicKey": _wompi_public_key,
        "planName": plan.get("name", ""),
    })


def _delete_subscription(event: dict) -> dict:
    """DELETE /billing/subscription — cancelar suscripcion."""
    user_id = _get_user_id(event)
    resp = _subscriptions_table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
    )
    active = [s for s in resp.get("Items", []) if s.get("status") in ("active", "trialing")]
    if not active:
        return _response(404, {"error": "No tienes suscripcion activa"})

    sub = active[0]
    now = datetime.now(timezone.utc).isoformat()
    _subscriptions_table.update_item(
        Key={"userId": user_id, "planId": sub["planId"]},
        UpdateExpression="SET #s = :s, cancelAtPeriodEnd = :c, updatedAt = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "cancelled", ":c": True, ":u": now},
    )

    return _response(200, {"message": "Suscripcion cancelada. Activa hasta fin del periodo."})


def _get_invoices(event: dict) -> dict:
    """GET /billing/invoices — historial de pagos aprobados."""
    user_id = _get_user_id(event)
    resp = _events_table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,
        Limit=50,
    )
    invoices = [
        {
            "date": item.get("createdAt", ""),
            "amount": int(item.get("amount", 0)) // 100,  # centavos a COP
            "status": item.get("status", ""),
            "transactionId": item.get("transactionId", ""),
            "paymentMethod": item.get("paymentMethod", ""),
            "reference": item.get("reference", ""),
        }
        for item in resp.get("Items", [])
        if item.get("status") == "APPROVED"
    ]
    return _response(200, invoices)


def _get_wompi_config(event: dict) -> dict:
    """GET /billing/wompi-config — public key para inicializar el widget."""
    return _response(200, {
        "publicKey": _wompi_public_key,
        "sandbox": _wompi_sandbox,
    })


def _response(status: int, body: Any = None) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, ensure_ascii=False, default=str) if body else "",
    }
