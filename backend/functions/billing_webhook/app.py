"""Lambda handler para webhook de Wompi — confirmacion de pago.

Wompi envia eventos cuando una transaccion cambia de estado.
Este handler valida la firma SHA256 y actualiza la suscripcion en DynamoDB.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")
_lambda_client = boto3.client("lambda")
_subscriptions_table = _dynamodb.Table(os.environ.get("BILLING_SUBSCRIPTIONS_TABLE", "samai-billing-subscriptions"))
_events_table = _dynamodb.Table(os.environ.get("BILLING_EVENTS_TABLE", "samai-billing-events"))
_teams_table = _dynamodb.Table(os.environ.get("TEAMS_TABLE", "samai-teams"))
_team_members_table = _dynamodb.Table(os.environ.get("TEAM_MEMBERS_TABLE", "samai-team-members"))
_events_key = os.environ.get("WOMPI_EVENTS_KEY", "")
_monitor_function = os.environ.get("MONITOR_FUNCTION_NAME", "samai-monitor")

TEAM_ELIGIBLE_PLANS = {"plan-firma", "plan-enterprise"}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Recibe POST de Wompi con evento de transaccion."""
    try:
        body = _parse_body(event)
        logger.info("Webhook recibido: event=%s", body.get("event"))

        # Validar firma SHA256
        if not _validate_signature(body):
            logger.warning("Firma invalida en webhook")
            return _response(401, {"error": "Invalid signature"})

        event_type = body.get("event", "")
        if event_type != "transaction.updated":
            return _response(200, {"status": "ignored", "event": event_type})

        txn = body.get("data", {}).get("transaction", {})
        txn_id = txn.get("id", "")
        status = txn.get("status", "")
        reference = txn.get("reference", "")
        amount = txn.get("amount_in_cents", 0)

        logger.info("Transaccion %s: status=%s ref=%s amount=%s", txn_id, status, reference, amount)

        # Idempotencia: verificar si ya procesamos esta transaccion
        existing = _events_table.query(
            IndexName="transaction-id-index",
            KeyConditionExpression=Key("transactionId").eq(txn_id),
        )
        if existing.get("Items"):
            return _response(200, {"status": "duplicate"})

        # Extraer user_id y plan_id del reference
        # Formatos: "sub_{userId}_{planId}_{ts}" o "upg_{userId}_{planId}_{ts}"
        parts = reference.split("_", 3)
        if len(parts) < 3 or parts[0] not in ("sub", "upg"):
            logger.warning("Reference no tiene formato esperado: %s", reference)
            return _response(200, {"status": "ignored_reference"})

        ref_type = parts[0]  # "sub" = nueva suscripcion, "upg" = upgrade
        user_id = parts[1]
        plan_id = parts[2]

        # Guardar evento de pago
        now = datetime.now(timezone.utc)
        ttl = int((now + timedelta(days=365)).timestamp())
        _events_table.put_item(Item={
            "userId": user_id,
            "sk": f"{now.isoformat()}#{txn_id}",
            "transactionId": txn_id,
            "reference": reference,
            "amount": amount,
            "currency": "COP",
            "status": status,
            "planId": plan_id,
            "paymentMethod": txn.get("payment_method_type", ""),
            "createdAt": now.isoformat(),
            "ttl": ttl,
        })

        if status == "APPROVED":
            if ref_type == "upg":
                # Upgrade: buscar suscripcion actual y cambiar el plan, mantener periodo
                existing_subs = _subscriptions_table.query(
                    KeyConditionExpression=Key("userId").eq(user_id),
                ).get("Items", [])
                current = [s for s in existing_subs if s.get("status") in ("active", "trialing")]
                if current:
                    old_plan = current[0]["planId"]
                    # Borrar la suscripcion vieja y crear con el nuevo plan
                    _subscriptions_table.delete_item(Key={"userId": user_id, "planId": old_plan})
                    _subscriptions_table.put_item(Item={
                        "userId": user_id,
                        "planId": plan_id,
                        "status": "active",
                        "wompiTransactionId": txn_id,
                        "currentPeriodStart": current[0].get("currentPeriodStart", now.isoformat()),
                        "currentPeriodEnd": current[0].get("currentPeriodEnd", (now + timedelta(days=30)).isoformat()),
                        "cancelAtPeriodEnd": False,
                        "createdAt": current[0].get("createdAt", now.isoformat()),
                        "updatedAt": now.isoformat(),
                    })
                    logger.info("Upgrade completado: user=%s %s -> %s", user_id, old_plan, plan_id)
                else:
                    logger.warning("Upgrade ref pero sin suscripcion activa: user=%s", user_id)
            else:
                # Nueva suscripcion o renovacion
                # Si habia pendingPlanId (downgrade programado), aplicarlo
                effective_plan = plan_id
                existing_subs = _subscriptions_table.query(
                    KeyConditionExpression=Key("userId").eq(user_id),
                ).get("Items", [])
                for old_sub in existing_subs:
                    pending = old_sub.get("pendingPlanId")
                    if pending:
                        effective_plan = pending
                        logger.info("Aplicando downgrade pendiente: user=%s %s -> %s", user_id, plan_id, pending)
                    # Limpiar suscripciones viejas
                    _subscriptions_table.delete_item(
                        Key={"userId": user_id, "planId": old_sub["planId"]}
                    )

                period_end = now + timedelta(days=30)
                _subscriptions_table.put_item(Item={
                    "userId": user_id,
                    "planId": effective_plan,
                    "status": "active",
                    "wompiTransactionId": txn_id,
                    "currentPeriodStart": now.isoformat(),
                    "currentPeriodEnd": period_end.isoformat(),
                    "cancelAtPeriodEnd": False,
                    "createdAt": now.isoformat(),
                    "updatedAt": now.isoformat(),
                })
                plan_id = effective_plan  # Para el check de equipo abajo
            logger.info("Suscripcion activada: user=%s plan=%s type=%s", user_id, plan_id, ref_type)

            # Si es plan de equipo, marcar equipo como pendingConfirmation
            # para que el owner confirme miembros antes de reactivar a todos
            if plan_id in TEAM_ELIGIBLE_PLANS:
                try:
                    from boto3.dynamodb.conditions import Key as DKey
                    resp = _team_members_table.query(
                        IndexName="userId-index",
                        KeyConditionExpression=DKey("userId").eq(user_id),
                    )
                    memberships = resp.get("Items", [])
                    for m in memberships:
                        _teams_table.update_item(
                            Key={"teamId": m["teamId"]},
                            UpdateExpression="SET pendingConfirmation = :v",
                            ExpressionAttributeValues={":v": True},
                        )
                        logger.info("Equipo %s marcado pendingConfirmation", m["teamId"])
                except Exception:
                    logger.warning("No se pudo marcar equipo como pendingConfirmation")

            # Disparar reactivación de radicados del owner + check de novedades (async)
            try:
                _lambda_client.invoke(
                    FunctionName=_monitor_function,
                    InvocationType="Event",
                    Payload=json.dumps({"action": "reactivate", "userId": user_id}),
                )
                logger.info("Monitor invocado para reactivar radicados de user=%s", user_id)
            except Exception:
                logger.warning("No se pudo invocar monitor para reactivar, se hara en el proximo ciclo")

        elif status in ("DECLINED", "ERROR"):
            # Marcar como fallida si existia
            try:
                _subscriptions_table.update_item(
                    Key={"userId": user_id, "planId": plan_id},
                    UpdateExpression="SET #s = :s, updatedAt = :u",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "past_due", ":u": now.isoformat()},
                    ConditionExpression="attribute_exists(userId)",
                )
            except _subscriptions_table.meta.client.exceptions.ConditionalCheckFailedException:
                pass  # No tenia suscripcion previa

        return _response(200, {"status": "processed", "transaction": txn_id})

    except Exception:
        logger.exception("Error en webhook")
        return _response(500, {"error": "Internal error"})


def _validate_signature(body: dict[str, Any]) -> bool:
    """Valida firma SHA256 del webhook de Wompi."""
    if not _events_key:
        logger.warning("WOMPI_EVENTS_KEY no configurada, omitiendo validacion")
        return True

    sig = body.get("signature", {})
    properties = sig.get("properties", [])
    timestamp = body.get("timestamp", "")  # timestamp esta en el root, no en signature
    checksum = sig.get("checksum", "")

    if not properties or not checksum:
        return False

    # Extraer valores de las propiedades en orden
    values = ""
    data = body.get("data", {})
    for prop in properties:
        keys = prop.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, "")
            else:
                value = ""
                break
        values += str(value)

    concat = f"{values}{timestamp}{_events_key}"
    computed = hashlib.sha256(concat.encode()).hexdigest()
    return computed == checksum


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parsea body del evento."""
    body = event.get("body", "")
    if not body:
        return {}
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")
    return json.loads(body)


def _response(status: int, body: Any = None) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, ensure_ascii=False, default=str) if body else "",
    }
