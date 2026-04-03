"""Tests for billing_api — upgrade, downgrade, cancel."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws


def _make_event(
    method: str = "GET",
    path: str = "/billing/plans",
    body: dict | None = None,
    user_id: str = "user-123",
) -> dict:
    return {
        "rawPath": path,
        "requestContext": {
            "http": {"method": method, "path": path},
            "authorizer": {"jwt": {"claims": {"sub": user_id}}},
            "stage": "$default",
        },
        "body": json.dumps(body) if body else None,
    }


def _context() -> MagicMock:
    return MagicMock()


def _seed_plans(plans_table):
    plans_table.put_item(Item={
        "planId": "plan-pro", "name": "Pro", "amount": 19900,
        "currency": "cop", "interval": "month", "active": True,
        "features": {"max_processes": 25},
    })
    plans_table.put_item(Item={
        "planId": "plan-firma", "name": "Firma", "amount": 79900,
        "currency": "cop", "interval": "month", "active": True,
        "features": {"max_processes": 150},
    })


class TestUpgrade:
    def test_upgrade_genera_cobro_prorrateado(self, dynamodb_resource, billing_plans_table, billing_subs_table):
        from functions.billing_api.app import handler

        _seed_plans(billing_plans_table)
        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-pro", "status": "active",
            "currentPeriodStart": (now - timedelta(days=10)).isoformat(),
            "currentPeriodEnd": (now + timedelta(days=20)).isoformat(),
        })

        event = _make_event(method="POST", path="/billing/upgrade", body={"planId": "plan-firma"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["upgraded"] is False  # Requiere pago
        assert data["proratedAmount"] > 0
        assert data["reference"].startswith("upg_")
        assert "integrityHash" in data

    def test_upgrade_sin_suscripcion_404(self, dynamodb_resource, billing_plans_table):
        from functions.billing_api.app import handler

        _seed_plans(billing_plans_table)
        event = _make_event(method="POST", path="/billing/upgrade", body={"planId": "plan-firma"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 404

    def test_upgrade_a_plan_menor_400(self, dynamodb_resource, billing_plans_table, billing_subs_table):
        from functions.billing_api.app import handler

        _seed_plans(billing_plans_table)
        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-firma", "status": "active",
            "currentPeriodStart": now.isoformat(),
            "currentPeriodEnd": (now + timedelta(days=30)).isoformat(),
        })

        event = _make_event(method="POST", path="/billing/upgrade", body={"planId": "plan-pro"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 400


class TestDowngrade:
    def test_downgrade_programa_al_fin_periodo(self, dynamodb_resource, billing_plans_table, billing_subs_table):
        from functions.billing_api.app import handler

        _seed_plans(billing_plans_table)
        now = datetime.now(timezone.utc)
        period_end = (now + timedelta(days=20)).isoformat()
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-firma", "status": "active",
            "currentPeriodStart": now.isoformat(),
            "currentPeriodEnd": period_end,
        })

        event = _make_event(method="POST", path="/billing/downgrade", body={"planId": "plan-pro"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["pendingPlanId"] == "plan-pro"
        assert "efectivo" in data["message"].lower() or "programado" in data["message"].lower()

    def test_downgrade_a_plan_mayor_400(self, dynamodb_resource, billing_plans_table, billing_subs_table):
        from functions.billing_api.app import handler

        _seed_plans(billing_plans_table)
        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-pro", "status": "active",
            "currentPeriodStart": now.isoformat(),
            "currentPeriodEnd": (now + timedelta(days=30)).isoformat(),
        })

        event = _make_event(method="POST", path="/billing/downgrade", body={"planId": "plan-firma"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 400


class TestCancelWithVoid:
    def test_cancel_reciente_tarjeta_intenta_void(self, dynamodb_resource, billing_subs_table):
        from functions.billing_api.app import handler

        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-pro", "status": "active",
            "wompiTransactionId": "txn-123",
            "createdAt": (now - timedelta(hours=2)).isoformat(),  # 2h ago
            "currentPeriodEnd": (now + timedelta(days=28)).isoformat(),
        })

        with patch("functions.billing_api.app._void_transaction", return_value=True) as mock_void:
            event = _make_event(method="DELETE", path="/billing/subscription")
            resp = handler(event, _context())

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["refunded"] is True
        mock_void.assert_called_once_with("txn-123")

    def test_cancel_vieja_no_intenta_void(self, dynamodb_resource, billing_subs_table):
        from functions.billing_api.app import handler

        now = datetime.now(timezone.utc)
        billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-pro", "status": "active",
            "wompiTransactionId": "txn-123",
            "createdAt": (now - timedelta(hours=48)).isoformat(),  # 48h ago
            "currentPeriodEnd": (now + timedelta(days=28)).isoformat(),
        })

        with patch("functions.billing_api.app._void_transaction") as mock_void:
            event = _make_event(method="DELETE", path="/billing/subscription")
            resp = handler(event, _context())

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["refunded"] is False
        mock_void.assert_not_called()
