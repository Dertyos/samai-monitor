"""Tests for monitor Lambda — TDD: tests primero."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
from datetime import datetime

import pytest
from moto import mock_aws

from models import Radicado, Actuacion, Alerta
from db import (
    guardar_radicado,
    obtener_radicados_usuario,
    obtener_alertas_usuario,
    obtener_ultimo_orden_local,
    guardar_actuaciones,
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
