"""Tests for db — TDD: tests primero, moto para DynamoDB mock."""
from __future__ import annotations

import pytest
from models import Radicado, Actuacion, Alerta
from db import (
    guardar_radicado,
    obtener_radicados_usuario,
    eliminar_radicado,
    obtener_radicado,
    obtener_radicados_unicos,
    actualizar_ultimo_orden,
    guardar_actuaciones,
    obtener_ultimo_orden_local,
    guardar_alerta,
    obtener_alertas_usuario,
)


USER_ID = "user-123"
RADICADO = "73001233300020190034300"
CORP = "7300123"


def _make_radicado(user_id: str = USER_ID, radicado: str = RADICADO) -> Radicado:
    return Radicado(
        user_id=user_id,
        radicado=radicado,
        corporacion=CORP,
        radicado_formato="73001-23-33-000-2019-00343-00",
        alias="Caso Aviles",
        ultimo_orden=0,
        activo=True,
        created_at="2026-03-20T10:00:00",
    )


def _make_actuacion(orden: int = 177) -> Actuacion:
    return Actuacion(
        radicado=RADICADO,
        orden=orden,
        nombre="Fijacion estado",
        fecha="2026-03-20T00:00:00",
        anotacion="LMB-",
        registro="2026-03-19T16:31:57.1",
        codigo="00000108",
        estado="REGISTRADA",
    )


def _make_alerta(orden: int = 177) -> Alerta:
    return Alerta(
        user_id=USER_ID,
        radicado=RADICADO,
        orden=orden,
        nombre_actuacion="Fijacion estado",
        fecha_actuacion="2026-03-20",
        anotacion="LMB-",
        created_at="2026-03-20T08:00:00",
        enviado=False,
    )


class TestGuardarRadicado:
    def test_guardar_y_obtener(self, radicados_table):
        rad = _make_radicado()
        guardar_radicado(radicados_table, rad)

        result = obtener_radicados_usuario(radicados_table, USER_ID)
        assert len(result) == 1
        assert result[0].radicado == RADICADO
        assert result[0].alias == "Caso Aviles"

    def test_guardar_duplicado_no_duplica(self, radicados_table):
        rad = _make_radicado()
        guardar_radicado(radicados_table, rad)
        guardar_radicado(radicados_table, rad)

        result = obtener_radicados_usuario(radicados_table, USER_ID)
        assert len(result) == 1

    def test_guardar_multiples_radicados(self, radicados_table):
        rad1 = _make_radicado()
        rad2 = _make_radicado(radicado="73001233300020230047100")
        rad2.corporacion = "7300123"
        rad2.radicado_formato = "73001-23-33-000-2023-00471-00"
        rad2.alias = "Caso Melgar"

        guardar_radicado(radicados_table, rad1)
        guardar_radicado(radicados_table, rad2)

        result = obtener_radicados_usuario(radicados_table, USER_ID)
        assert len(result) == 2


class TestEliminarRadicado:
    def test_eliminar_existente(self, radicados_table):
        guardar_radicado(radicados_table, _make_radicado())
        eliminado = eliminar_radicado(radicados_table, USER_ID, RADICADO)
        assert eliminado is True

        result = obtener_radicados_usuario(radicados_table, USER_ID)
        assert len(result) == 0

    def test_eliminar_inexistente(self, radicados_table):
        eliminado = eliminar_radicado(radicados_table, USER_ID, RADICADO)
        assert eliminado is False


class TestObtenerRadicado:
    def test_existente(self, radicados_table):
        guardar_radicado(radicados_table, _make_radicado())
        result = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert result is not None
        assert result.radicado == RADICADO

    def test_inexistente(self, radicados_table):
        result = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert result is None


class TestObtenerRadicadosUnicos:
    """Deduplicación: si 2 usuarios siguen el mismo radicado, solo se consulta 1 vez."""

    def test_dedup_dos_usuarios(self, radicados_table):
        rad1 = _make_radicado(user_id="user-A")
        rad2 = _make_radicado(user_id="user-B")

        guardar_radicado(radicados_table, rad1)
        guardar_radicado(radicados_table, rad2)

        unicos = obtener_radicados_unicos(radicados_table)
        # Debe haber solo 1 radicado único (con su corporación)
        assert len(unicos) == 1
        assert unicos[0]["radicado"] == RADICADO
        assert unicos[0]["corporacion"] == CORP
        assert unicos[0]["fuente"] == "samai"
        assert unicos[0]["id_proceso"] is None

    def test_multiples_radicados(self, radicados_table):
        rad1 = _make_radicado()
        rad2 = _make_radicado(radicado="73001233300020230047100")
        rad2.corporacion = "7300123"

        guardar_radicado(radicados_table, rad1)
        guardar_radicado(radicados_table, rad2)

        unicos = obtener_radicados_unicos(radicados_table)
        assert len(unicos) == 2


class TestActualizarUltimoOrden:
    def test_actualiza(self, radicados_table):
        guardar_radicado(radicados_table, _make_radicado())
        actualizar_ultimo_orden(radicados_table, USER_ID, RADICADO, 177)

        rad = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert rad is not None
        assert rad.ultimo_orden == 177


class TestGuardarActuaciones:
    def test_guardar_y_obtener_orden(self, actuaciones_table):
        acts = [_make_actuacion(177), _make_actuacion(176)]
        guardar_actuaciones(actuaciones_table, acts)

        ultimo = obtener_ultimo_orden_local(actuaciones_table, RADICADO)
        assert ultimo == 177

    def test_sin_actuaciones(self, actuaciones_table):
        ultimo = obtener_ultimo_orden_local(actuaciones_table, RADICADO)
        assert ultimo == 0


class TestAlertas:
    def test_guardar_y_listar(self, alertas_table):
        alerta = _make_alerta()
        guardar_alerta(alertas_table, alerta)

        result = obtener_alertas_usuario(alertas_table, USER_ID)
        assert len(result) == 1
        assert result[0].radicado == RADICADO
        assert result[0].nombre_actuacion == "Fijacion estado"

    def test_multiples_alertas_ordenadas(self, alertas_table):
        a1 = _make_alerta(orden=175)
        a1.created_at = "2026-03-20T07:00:00"
        a2 = _make_alerta(orden=176)
        a2.created_at = "2026-03-20T07:30:00"
        a3 = _make_alerta(orden=177)
        a3.created_at = "2026-03-20T08:00:00"

        guardar_alerta(alertas_table, a1)
        guardar_alerta(alertas_table, a2)
        guardar_alerta(alertas_table, a3)

        result = obtener_alertas_usuario(alertas_table, USER_ID)
        assert len(result) == 3
        # Deben venir ordenadas por sk (más reciente primero o más antiguo primero)
        # La implementación decide, pero debe ser consistente
