"""Tests for billing_webhook — upgrade refs, pendingPlanId."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws
from boto3.dynamodb.conditions import Key


def _make_webhook_event(reference: str, status: str = "APPROVED", txn_id: str = "txn-1") -> dict:
    body = {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": txn_id,
                "status": status,
                "reference": reference,
                "amount_in_cents": 7990000,
                "payment_method_type": "CARD",
            },
        },
        "signature": {
            "properties": [],
            "timestamp": "",
            "checksum": "",
        },
    }
    return {
        "rawPath": "/billing/webhook",
        "requestContext": {"http": {"method": "POST", "path": "/billing/webhook"}, "stage": "$default"},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }


class TestWebhookUpgrade:
    def test_upg_reference_cambia_plan(self, dynamodb_resource, billing_subs_table):
        from functions.billing_webhook.app import handler

        # Suscripcion actual: Pro
        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-1", "planId": "plan-pro", "status": "active",
            "currentPeriodStart": (now - timedelta(days=10)).isoformat(),
            "currentPeriodEnd": (now + timedelta(days=20)).isoformat(),
            "createdAt": (now - timedelta(days=10)).isoformat(),
        })

        # Webhook con upg_ reference
        event = _make_webhook_event("upg_user-1_plan-firma_12345")
        with patch("functions.billing_webhook.app._validate_signature", return_value=True), \
             patch("functions.billing_webhook.app._lambda_client"):
            resp = handler(event, MagicMock())

        assert resp["statusCode"] == 200

        # Verificar que el plan cambio a Firma
        subs = billing_subs_table.query(
            KeyConditionExpression=Key("userId").eq("user-1"),
        ).get("Items", [])
        active = [s for s in subs if s.get("status") == "active"]
        assert len(active) == 1
        assert active[0]["planId"] == "plan-firma"

    def test_sub_reference_crea_nueva_suscripcion(self, dynamodb_resource, billing_subs_table):
        from functions.billing_webhook.app import handler

        event = _make_webhook_event("sub_user-2_plan-pro_12345", txn_id="txn-2")
        with patch("functions.billing_webhook.app._validate_signature", return_value=True), \
             patch("functions.billing_webhook.app._lambda_client"):
            resp = handler(event, MagicMock())

        assert resp["statusCode"] == 200
        subs = billing_subs_table.query(
            KeyConditionExpression=Key("userId").eq("user-2"),
        ).get("Items", [])
        assert len(subs) == 1
        assert subs[0]["planId"] == "plan-pro"
        assert subs[0]["status"] == "active"


class TestWebhookPendingPlanId:
    def test_renovacion_aplica_pending_plan(self, dynamodb_resource, billing_subs_table):
        from functions.billing_webhook.app import handler

        # Suscripcion vencida con pendingPlanId
        billing_subs_table.put_item(Item={
            "userId": "user-3", "planId": "plan-firma", "status": "cancelled",
            "pendingPlanId": "plan-pro",
        })

        event = _make_webhook_event("sub_user-3_plan-firma_12345", txn_id="txn-3")
        with patch("functions.billing_webhook.app._validate_signature", return_value=True), \
             patch("functions.billing_webhook.app._lambda_client"):
            resp = handler(event, MagicMock())

        assert resp["statusCode"] == 200
        subs = billing_subs_table.query(
            KeyConditionExpression=Key("userId").eq("user-3"),
        ).get("Items", [])
        active = [s for s in subs if s.get("status") == "active"]
        assert len(active) == 1
        assert active[0]["planId"] == "plan-pro"  # Se aplico el downgrade pendiente

    def test_idempotencia_txn_duplicada(self, dynamodb_resource):
        from functions.billing_webhook.app import handler, _events_table

        # Guardar evento previo con el mismo txn_id
        _events_table.put_item(Item={
            "userId": "user-1", "sk": "2026-04-03T10:00:00#txn-dup",
            "transactionId": "txn-dup",
        })

        event = _make_webhook_event("sub_user-1_plan-pro_12345", txn_id="txn-dup")
        with patch("functions.billing_webhook.app._validate_signature", return_value=True):
            resp = handler(event, MagicMock())

        assert resp["statusCode"] == 200
        assert json.loads(resp["body"])["status"] == "duplicate"
