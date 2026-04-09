"""Tests for monitor Lambda — TDD: tests primero."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
from datetime import datetime

import pytest
from moto import mock_aws

from models import Radicado, Actuacion, Alerta, AlertSchedule
from db import (
    guardar_radicado,
    obtener_radicados_usuario,
    obtener_radicado,
    obtener_alertas_usuario,
    obtener_ultimo_orden_local,
    guardar_actuaciones,
    guardar_alert_schedule,
)


USER_A = "user-A"
USER_B = "user-B"
RADICADO = "73001233300020190034300"
CORP = "7300123"


def _make_radicado(user_id: str = USER_A, ultimo_orden: int = 175) -> Radicado:
    return Radicado(
        user_id=user_id,
        radicado=RADICADO,
        corporacion=CORP,
        radicado_formato="73001-23-33-000-2019-00343-00",
        alias="Caso Aviles",
        ultimo_orden=ultimo_orden,
        activo=True,
        created_at="2026-03-20T10:00:00",
    )


def _make_actuacion(orden: int, nombre: str = "Fijacion estado") -> Actuacion:
    return Actuacion(
        radicado=RADICADO,
        orden=orden,
        nombre=nombre,
        fecha=f"2026-03-20T00:00:00",
        anotacion=f"Detalle orden {orden}",
        registro="2026-03-19T16:31:57.1",
        codigo="00000108",
        estado="REGISTRADA",
    )


class TestMonitorCheckRadicado:
    """monitor.check_radicado: consulta SAMAI, detecta novedades, crea alertas."""

    def test_detecta_actuaciones_nuevas(self, dynamodb_resource):
        from functions.monitor.app import check_radicado

        radicados_table = dynamodb_resource.Table("samai-radicados")
        actuaciones_table = dynamodb_resource.Table("samai-actuaciones")
        alertas_table = dynamodb_resource.Table("samai-alertas")

        # User A sigue el radicado, último orden conocido: 175
        guardar_radicado(radicados_table, _make_radicado(USER_A, ultimo_orden=175))

        # SAMAI devuelve actuaciones 175, 176, 177 (2 nuevas)
        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = [
            _make_actuacion(177, "Fijacion estado"),
            _make_actuacion(176, "A la secretaria"),
        ]

        alertas = check_radicado(
            samai_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=actuaciones_table,
            alertas_table=alertas_table,
            corporacion=CORP,
            radicado=RADICADO,
        )

        assert len(alertas) == 1  # 1 usuario con alertas
        assert USER_A in alertas
        assert len(alertas[USER_A]) == 2  # 2 actuaciones nuevas

    def test_sin_novedades_no_genera_alertas(self, dynamodb_resource):
        from functions.monitor.app import check_radicado

        radicados_table = dynamodb_resource.Table("samai-radicados")
        actuaciones_table = dynamodb_resource.Table("samai-actuaciones")
        alertas_table = dynamodb_resource.Table("samai-alertas")

        guardar_radicado(radicados_table, _make_radicado(USER_A, ultimo_orden=177))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = []

        alertas = check_radicado(
            samai_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=actuaciones_table,
            alertas_table=alertas_table,
            corporacion=CORP,
            radicado=RADICADO,
        )

        assert alertas == {}

    def test_multiples_usuarios_mismo_radicado(self, dynamodb_resource):
        from functions.monitor.app import check_radicado

        radicados_table = dynamodb_resource.Table("samai-radicados")
        actuaciones_table = dynamodb_resource.Table("samai-actuaciones")
        alertas_table = dynamodb_resource.Table("samai-alertas")

        # Dos usuarios siguen el mismo radicado con diferentes últimos órdenes
        guardar_radicado(radicados_table, _make_radicado(USER_A, ultimo_orden=175))
        guardar_radicado(radicados_table, _make_radicado(USER_B, ultimo_orden=176))

        mock_client = MagicMock()
        # Retorna todas las nuevas desde el mínimo (175)
        mock_client.get_actuaciones_nuevas.return_value = [
            _make_actuacion(177),
            _make_actuacion(176),
        ]

        alertas = check_radicado(
            samai_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=actuaciones_table,
            alertas_table=alertas_table,
            corporacion=CORP,
            radicado=RADICADO,
        )

        # User A: 2 alertas (176, 177), User B: 1 alerta (177)
        assert USER_A in alertas
        assert len(alertas[USER_A]) == 2
        assert USER_B in alertas
        assert len(alertas[USER_B]) == 1

    def test_actualiza_ultimo_orden_de_usuarios(self, dynamodb_resource):
        from functions.monitor.app import check_radicado

        radicados_table = dynamodb_resource.Table("samai-radicados")
        actuaciones_table = dynamodb_resource.Table("samai-actuaciones")
        alertas_table = dynamodb_resource.Table("samai-alertas")

        guardar_radicado(radicados_table, _make_radicado(USER_A, ultimo_orden=175))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = [_make_actuacion(177)]

        check_radicado(
            samai_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=actuaciones_table,
            alertas_table=alertas_table,
            corporacion=CORP,
            radicado=RADICADO,
        )

        # Verificar que el último orden se actualizó
        rads = obtener_radicados_usuario(radicados_table, USER_A)
        assert rads[0].ultimo_orden == 177


class TestMonitorCheckRadicadoRj:
    """check_radicado_rj: consulta CPNU, detecta novedades, crea alertas."""

    def _make_rj_radicado(self, user_id: str = USER_A, ultimo_orden: int = 3) -> Radicado:
        return Radicado(
            user_id=user_id,
            radicado=RADICADO,
            corporacion="",
            radicado_formato="73001-23-33-000-2019-00343-00",
            alias="Caso RJ",
            ultimo_orden=ultimo_orden,
            activo=True,
            created_at="2026-03-20T10:00:00",
            fuente="rama_judicial",
            id_proceso=149525880,
        )

    def _make_rj_actuacion(self, orden: int) -> Actuacion:
        return Actuacion(
            radicado=RADICADO,
            orden=orden,
            nombre="Envío Expediente",
            fecha="2024-03-05T00:00:00",
            anotacion=f"Detalle orden {orden}",
            registro="2024-03-05T00:00:00",
        )

    def test_detecta_actuaciones_nuevas(self, dynamodb_resource):
        from functions.monitor.app import check_radicado_rj

        radicados_table = dynamodb_resource.Table("samai-radicados")
        actuaciones_table = dynamodb_resource.Table("samai-actuaciones")
        alertas_table = dynamodb_resource.Table("samai-alertas")

        guardar_radicado(radicados_table, self._make_rj_radicado(USER_A, ultimo_orden=3))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = [
            self._make_rj_actuacion(5),
            self._make_rj_actuacion(4),
        ]

        alertas = check_radicado_rj(
            rj_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=actuaciones_table,
            alertas_table=alertas_table,
            id_proceso=149525880,
            radicado=RADICADO,
        )

        assert USER_A in alertas
        assert len(alertas[USER_A]) == 2
        # Todas las alertas tienen fuente="rama_judicial"
        assert all(a.fuente == "rama_judicial" for a in alertas[USER_A])

    def test_sin_id_proceso_retorna_vacio(self, dynamodb_resource):
        from functions.monitor.app import check_radicado_rj

        mock_client = MagicMock()
        result = check_radicado_rj(
            rj_client=mock_client,
            radicados_table=dynamodb_resource.Table("samai-radicados"),
            actuaciones_table=dynamodb_resource.Table("samai-actuaciones"),
            alertas_table=dynamodb_resource.Table("samai-alertas"),
            id_proceso=None,
            radicado=RADICADO,
        )

        assert result == {}
        mock_client.get_actuaciones_nuevas.assert_not_called()

    def test_sin_novedades_no_genera_alertas(self, dynamodb_resource):
        from functions.monitor.app import check_radicado_rj

        radicados_table = dynamodb_resource.Table("samai-radicados")
        guardar_radicado(radicados_table, self._make_rj_radicado(USER_A, ultimo_orden=5))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = []

        alertas = check_radicado_rj(
            rj_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=dynamodb_resource.Table("samai-actuaciones"),
            alertas_table=dynamodb_resource.Table("samai-alertas"),
            id_proceso=149525880,
            radicado=RADICADO,
        )

        assert alertas == {}

    def test_actualiza_ultimo_orden(self, dynamodb_resource):
        from functions.monitor.app import check_radicado_rj

        radicados_table = dynamodb_resource.Table("samai-radicados")
        guardar_radicado(radicados_table, self._make_rj_radicado(USER_A, ultimo_orden=3))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = [self._make_rj_actuacion(5)]

        check_radicado_rj(
            rj_client=mock_client,
            radicados_table=radicados_table,
            actuaciones_table=dynamodb_resource.Table("samai-actuaciones"),
            alertas_table=dynamodb_resource.Table("samai-alertas"),
            id_proceso=149525880,
            radicado=RADICADO,
        )

        rads = obtener_radicados_usuario(radicados_table, USER_A)
        assert rads[0].ultimo_orden == 5


class TestMonitorHandler:
    """handler: orquesta el flujo completo EventBridge → check → alertas."""

    def test_handler_procesa_radicados(self, dynamodb_resource):
        from functions.monitor.app import handler

        radicados_table = dynamodb_resource.Table("samai-radicados")
        guardar_radicado(radicados_table, _make_radicado(USER_A, ultimo_orden=175))

        mock_client = MagicMock()
        mock_client.get_actuaciones_nuevas.return_value = [_make_actuacion(177)]

        with patch("functions.monitor.app.samai_client", mock_client), \
             patch("functions.monitor.app._send_email_alerts") as mock_email:
            result = handler({}, MagicMock())

        assert result["processed"] >= 1
        mock_email.assert_called_once()


class TestSendEmailAlerts:
    """_send_email_alerts: envía correos via Resend."""

    def test_sends_email_via_resend(self, dynamodb_resource):
        from functions.monitor.app import _send_email_alerts

        alerta = Alerta(
            user_id=USER_A,
            radicado=RADICADO,
            orden=177,
            nombre_actuacion="Fijacion estado",
            fecha_actuacion="2026-03-20T00:00:00",
            anotacion="Detalle",
            created_at="2026-03-20T10:00:00",
        )

        with patch("functions.monitor.app._get_user_email", return_value="test@example.com"), \
             patch("functions.monitor.app.resend") as mock_resend:
            _send_email_alerts({USER_A: [alerta]})

        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == ["test@example.com"]
        assert "Alertas Judiciales" in call_args["from"]
        assert "actuación" in call_args["subject"]

    def test_skips_user_without_email(self, dynamodb_resource):
        from functions.monitor.app import _send_email_alerts

        alerta = Alerta(
            user_id=USER_A,
            radicado=RADICADO,
            orden=177,
            nombre_actuacion="Fijacion estado",
            fecha_actuacion="2026-03-20T00:00:00",
            anotacion="Detalle",
            created_at="2026-03-20T10:00:00",
        )

        with patch("functions.monitor.app._get_user_email", return_value=None), \
             patch("functions.monitor.app.resend") as mock_resend:
            _send_email_alerts({USER_A: [alerta]})

        mock_resend.Emails.send.assert_not_called()


# --- Plan limit enforcement ---


class TestEnforcePlanLimits:
    """Cuando una suscripcion vence, solo los primeros 5 radicados (por createdAt) siguen activos."""

    def _patch_monitor_tables(self, billing_subs, billing_plans, team_members, teams):
        """Context manager para patchear las tablas del monitor."""
        return (
            patch("functions.monitor.app._billing_subs_table", billing_subs),
            patch("functions.monitor.app._billing_plans_table", billing_plans),
            patch("functions.monitor.app._team_members_table", team_members),
            patch("functions.monitor.app._teams_table", teams),
        )

    def test_free_user_keeps_first_5(self, radicados_table, billing_subs_table, billing_plans_table, team_members_table, teams_table):
        """Usuario sin suscripcion con 8 radicados: solo primeros 5 quedan activos."""
        from functions.monitor.app import _enforce_plan_limits

        for i in range(8):
            rad = Radicado(
                user_id=USER_A,
                radicado=f"7300123330002019003430{i}",
                corporacion=CORP,
                radicado_formato=f"73001-23-33-000-2019-00343-0{i}",
                alias=f"Caso {i}",
                ultimo_orden=0,
                activo=True,
                created_at=f"2026-03-{10 + i:02d}T10:00:00",
            )
            guardar_radicado(radicados_table, rad)

        patches = self._patch_monitor_tables(billing_subs_table, billing_plans_table, team_members_table, teams_table)
        with patches[0], patches[1], patches[2], patches[3]:
            enforced = _enforce_plan_limits(radicados_table)

        assert USER_A in enforced
        assert enforced[USER_A] == 3  # 8 - 5 = 3 desactivados

        rads = obtener_radicados_usuario(radicados_table, USER_A)
        rads.sort(key=lambda r: r.created_at)
        for r in rads[:5]:
            assert r.activo is True, f"Radicado {r.radicado} deberia estar activo"
        for r in rads[5:]:
            assert r.activo is False, f"Radicado {r.radicado} deberia estar inactivo"

    def test_pro_user_keeps_25(self, radicados_table, billing_subs_table, billing_plans_table, team_members_table, teams_table):
        """Usuario con plan Pro (25) y 8 radicados: todos activos."""
        from functions.monitor.app import _enforce_plan_limits

        for i in range(8):
            rad = Radicado(
                user_id=USER_A,
                radicado=f"7300123330002019003430{i}",
                corporacion=CORP,
                radicado_formato=f"73001-23-33-000-2019-00343-0{i}",
                alias=f"Caso {i}",
                ultimo_orden=0,
                activo=True,
                created_at=f"2026-03-{10 + i:02d}T10:00:00",
            )
            guardar_radicado(radicados_table, rad)

        billing_subs_table.put_item(Item={
            "userId": USER_A,
            "planId": "plan-pro",
            "status": "active",
        })

        patches = self._patch_monitor_tables(billing_subs_table, billing_plans_table, team_members_table, teams_table)
        with patches[0], patches[1], patches[2], patches[3]:
            enforced = _enforce_plan_limits(radicados_table)

        assert USER_A not in enforced
        rads = obtener_radicados_usuario(radicados_table, USER_A)
        assert all(r.activo for r in rads)

    def test_reactivates_when_plan_upgraded(self, radicados_table, billing_subs_table, billing_plans_table, team_members_table, teams_table):
        """Radicados desactivados por limite se reactivan si el plan sube."""
        from functions.monitor.app import _enforce_plan_limits

        for i in range(8):
            rad = Radicado(
                user_id=USER_A,
                radicado=f"7300123330002019003430{i}",
                corporacion=CORP,
                radicado_formato=f"73001-23-33-000-2019-00343-0{i}",
                alias=f"Caso {i}",
                ultimo_orden=0,
                activo=i < 5,
                created_at=f"2026-03-{10 + i:02d}T10:00:00",
            )
            guardar_radicado(radicados_table, rad)

        billing_subs_table.put_item(Item={
            "userId": USER_A,
            "planId": "plan-pro",
            "status": "active",
        })

        patches = self._patch_monitor_tables(billing_subs_table, billing_plans_table, team_members_table, teams_table)
        with patches[0], patches[1], patches[2], patches[3]:
            _enforce_plan_limits(radicados_table)

        rads = obtener_radicados_usuario(radicados_table, USER_A)
        assert all(r.activo for r in rads)


@pytest.mark.unit
class TestProcessCustomAlerts:
    """_process_custom_alerts: hourly check para alertas personalizadas."""

    def _patch_monitor_tables(
        self, radicados, actuaciones, alertas, billing_subs, billing_plans,
        team_members, teams, alert_schedules,
    ):
        return (
            patch("functions.monitor.app._radicados_table", radicados),
            patch("functions.monitor.app._actuaciones_table", actuaciones),
            patch("functions.monitor.app._alertas_table", alertas),
            patch("functions.monitor.app._billing_subs_table", billing_subs),
            patch("functions.monitor.app._billing_plans_table", billing_plans),
            patch("functions.monitor.app._team_members_table", team_members),
            patch("functions.monitor.app._teams_table", teams),
            patch("functions.monitor.app._alert_schedules_table", alert_schedules),
        )

    def test_skips_hour_12(self, dynamodb_resource):
        """Hora 12 UTC (7 AM COT) se salta — el daily scan lo cubre."""
        from functions.monitor.app import _process_custom_alerts

        with patch("functions.monitor.app.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 12
            mock_dt.now.return_value.isoformat.return_value = "2026-04-08T12:00:00+00:00"
            result = _process_custom_alerts()

        assert result["skipped"] is True

    def test_no_users_at_hour(
        self, radicados_table, actuaciones_table, alertas_table,
        billing_subs_table, billing_plans_table, team_members_table,
        teams_table, alert_schedules_table,
    ):
        """Sin usuarios configurados a la hora actual, retorna 0."""
        from functions.monitor.app import _process_custom_alerts

        patches = self._patch_monitor_tables(
            radicados_table, actuaciones_table, alertas_table,
            billing_subs_table, billing_plans_table, team_members_table,
            teams_table, alert_schedules_table,
        )

        with (
            patches[0], patches[1], patches[2], patches[3],
            patches[4], patches[5], patches[6], patches[7],
            patch("functions.monitor.app.datetime") as mock_dt,
        ):
            mock_dt.now.return_value.hour = 15
            mock_dt.now.return_value.isoformat.return_value = "2026-04-08T15:00:00+00:00"
            result = _process_custom_alerts()

        assert result["processed"] == 0

    def test_processes_matching_user(
        self, radicados_table, actuaciones_table, alertas_table,
        billing_subs_table, billing_plans_table, team_members_table,
        teams_table, alert_schedules_table,
    ):
        """Usuario con schedule a hora 17 UTC es procesado cuando la hora es 17."""
        from functions.monitor.app import _process_custom_alerts

        # Setup: usuario con plan pro-plus y schedule a hora 17
        billing_subs_table.put_item(Item={
            "userId": USER_A, "planId": "plan-pro-plus", "status": "active",
        })
        schedule = AlertSchedule(
            user_id=USER_A, alert_hour_utc=17, alert_hour_cot=12,
            created_at="2026-04-08T10:00:00Z",
        )
        guardar_alert_schedule(alert_schedules_table, schedule)

        # Radicado activo sin novedades (samai_client retorna [])
        guardar_radicado(radicados_table, _make_radicado(USER_A, 175))

        patches = self._patch_monitor_tables(
            radicados_table, actuaciones_table, alertas_table,
            billing_subs_table, billing_plans_table, team_members_table,
            teams_table, alert_schedules_table,
        )

        with (
            patches[0], patches[1], patches[2], patches[3],
            patches[4], patches[5], patches[6], patches[7],
            patch("functions.monitor.app.datetime") as mock_dt,
            patch("functions.monitor.app.samai_client") as mock_samai,
        ):
            mock_dt.now.return_value.hour = 17
            mock_dt.now.return_value.isoformat.return_value = "2026-04-08T17:00:00+00:00"
            mock_samai.get_actuaciones_nuevas.return_value = []
            result = _process_custom_alerts()

        assert result["processed"] == 1
        assert result["users_alerted"] == 0

    def test_skips_ineligible_user(
        self, radicados_table, actuaciones_table, alertas_table,
        billing_subs_table, billing_plans_table, team_members_table,
        teams_table, alert_schedules_table,
    ):
        """Usuario que downgraded a plan-pro es saltado aunque tenga schedule."""
        from functions.monitor.app import _process_custom_alerts

        # Setup: usuario con plan-pro (no elegible) pero schedule existente
        billing_subs_table.put_item(Item={
            "userId": USER_A, "planId": "plan-pro", "status": "active",
        })
        schedule = AlertSchedule(
            user_id=USER_A, alert_hour_utc=17, alert_hour_cot=12,
            created_at="2026-04-08T10:00:00Z",
        )
        guardar_alert_schedule(alert_schedules_table, schedule)

        patches = self._patch_monitor_tables(
            radicados_table, actuaciones_table, alertas_table,
            billing_subs_table, billing_plans_table, team_members_table,
            teams_table, alert_schedules_table,
        )

        with (
            patches[0], patches[1], patches[2], patches[3],
            patches[4], patches[5], patches[6], patches[7],
            patch("functions.monitor.app.datetime") as mock_dt,
        ):
            mock_dt.now.return_value.hour = 17
            mock_dt.now.return_value.isoformat.return_value = "2026-04-08T17:00:00+00:00"
            result = _process_custom_alerts()

        assert result["processed"] == 0
