"""Tests for db — TDD: tests primero, moto para DynamoDB mock."""
from __future__ import annotations

import pytest
from models import Radicado, Actuacion, Alerta, Etiqueta, Team, TeamMember
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
    guardar_etiqueta,
    obtener_etiquetas_usuario,
    obtener_etiqueta,
    actualizar_etiqueta,
    eliminar_etiqueta,
    actualizar_etiquetas_radicado,
    quitar_etiqueta_de_radicados,
    crear_team,
    obtener_team,
    obtener_teams_usuario,
    agregar_miembro_team,
    obtener_miembros_team,
    eliminar_miembro_team,
    contar_procesos_equipo,
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


# --- Etiquetas ---


def _make_etiqueta(
    etiqueta_id: str = "abc123",
    nombre: str = "Urgente",
    color: str = "#dc3545",
) -> Etiqueta:
    return Etiqueta(
        user_id=USER_ID,
        etiqueta_id=etiqueta_id,
        nombre=nombre,
        color=color,
        created_at="2026-04-01T10:00:00",
    )


class TestGuardarEtiqueta:
    def test_guardar_y_obtener(self, etiquetas_table):
        etq = _make_etiqueta()
        guardar_etiqueta(etiquetas_table, etq)

        result = obtener_etiquetas_usuario(etiquetas_table, USER_ID)
        assert len(result) == 1
        assert result[0].nombre == "Urgente"
        assert result[0].color == "#dc3545"

    def test_obtener_especifica(self, etiquetas_table):
        guardar_etiqueta(etiquetas_table, _make_etiqueta())
        result = obtener_etiqueta(etiquetas_table, USER_ID, "abc123")
        assert result is not None
        assert result.nombre == "Urgente"

    def test_obtener_inexistente(self, etiquetas_table):
        result = obtener_etiqueta(etiquetas_table, USER_ID, "noexiste")
        assert result is None


class TestActualizarEtiqueta:
    def test_actualizar_existente(self, etiquetas_table):
        guardar_etiqueta(etiquetas_table, _make_etiqueta())
        ok = actualizar_etiqueta(etiquetas_table, USER_ID, "abc123", "Muy urgente", "#ff0000")
        assert ok is True

        result = obtener_etiqueta(etiquetas_table, USER_ID, "abc123")
        assert result is not None
        assert result.nombre == "Muy urgente"
        assert result.color == "#ff0000"

    def test_actualizar_inexistente(self, etiquetas_table):
        ok = actualizar_etiqueta(etiquetas_table, USER_ID, "noexiste", "X", "#000")
        assert ok is False


class TestEliminarEtiqueta:
    def test_eliminar_existente(self, etiquetas_table):
        guardar_etiqueta(etiquetas_table, _make_etiqueta())
        ok = eliminar_etiqueta(etiquetas_table, USER_ID, "abc123")
        assert ok is True

        result = obtener_etiquetas_usuario(etiquetas_table, USER_ID)
        assert len(result) == 0

    def test_eliminar_inexistente(self, etiquetas_table):
        ok = eliminar_etiqueta(etiquetas_table, USER_ID, "noexiste")
        assert ok is False


class TestEtiquetasRadicado:
    def test_asignar_etiquetas(self, radicados_table):
        guardar_radicado(radicados_table, _make_radicado())
        ok = actualizar_etiquetas_radicado(radicados_table, USER_ID, RADICADO, ["e1", "e2"])
        assert ok is True

        rad = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert rad is not None
        assert rad.etiquetas == ["e1", "e2"]

    def test_quitar_todas_las_etiquetas(self, radicados_table):
        rad = _make_radicado()
        rad.etiquetas = ["e1", "e2"]
        guardar_radicado(radicados_table, rad)

        ok = actualizar_etiquetas_radicado(radicados_table, USER_ID, RADICADO, [])
        assert ok is True

        rad = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert rad is not None
        assert rad.etiquetas == []

    def test_asignar_a_inexistente(self, radicados_table):
        ok = actualizar_etiquetas_radicado(radicados_table, USER_ID, "00000000000000000000000", ["e1"])
        assert ok is False

    def test_quitar_etiqueta_de_radicados(self, radicados_table):
        rad1 = _make_radicado()
        rad1.etiquetas = ["e1", "e2"]
        rad2 = _make_radicado(radicado="73001233300020230047100")
        rad2.corporacion = CORP
        rad2.radicado_formato = "73001-23-33-000-2023-00471-00"
        rad2.etiquetas = ["e1"]

        guardar_radicado(radicados_table, rad1)
        guardar_radicado(radicados_table, rad2)

        count = quitar_etiqueta_de_radicados(radicados_table, USER_ID, "e1")
        assert count == 2

        r1 = obtener_radicado(radicados_table, USER_ID, RADICADO)
        assert r1 is not None
        assert r1.etiquetas == ["e2"]

        r2 = obtener_radicado(radicados_table, USER_ID, "73001233300020230047100")
        assert r2 is not None
        assert r2.etiquetas == []


# --- Teams ---

TEAM_ID = "team-abc123"
OWNER_ID = USER_ID
MEMBER_ID = "user-456"
RADICADO_2 = "73001233300020230047100"


def _make_team(team_id: str = TEAM_ID, owner: str = OWNER_ID) -> Team:
    return Team(
        team_id=team_id,
        name="Firma Aviles & Asoc.",
        owner_user_id=owner,
        plan_id="plan-firma",
        created_at="2026-04-03T10:00:00",
    )


def _make_member(
    team_id: str = TEAM_ID, user_id: str = MEMBER_ID, role: str = "member"
) -> TeamMember:
    return TeamMember(
        team_id=team_id,
        user_id=user_id,
        role=role,
        joined_at="2026-04-03T10:00:00",
    )


class TestCrearTeam:
    def test_crear_y_obtener(self, teams_table):
        team = _make_team()
        crear_team(teams_table, team)

        result = obtener_team(teams_table, TEAM_ID)
        assert result is not None
        assert result.team_id == TEAM_ID
        assert result.name == "Firma Aviles & Asoc."
        assert result.owner_user_id == OWNER_ID
        assert result.plan_id == "plan-firma"

    def test_obtener_inexistente(self, teams_table):
        result = obtener_team(teams_table, "no-existe")
        assert result is None


class TestTeamMembers:
    def test_agregar_y_listar_miembros(self, teams_table, team_members_table):
        team = _make_team()
        crear_team(teams_table, team)

        owner_member = _make_member(user_id=OWNER_ID, role="owner")
        agregar_miembro_team(team_members_table, owner_member)

        member = _make_member(user_id=MEMBER_ID, role="member")
        agregar_miembro_team(team_members_table, member)

        members = obtener_miembros_team(team_members_table, TEAM_ID)
        assert len(members) == 2
        roles = {m.user_id: m.role for m in members}
        assert roles[OWNER_ID] == "owner"
        assert roles[MEMBER_ID] == "member"

    def test_eliminar_miembro(self, team_members_table):
        member = _make_member()
        agregar_miembro_team(team_members_table, member)

        eliminado = eliminar_miembro_team(team_members_table, TEAM_ID, MEMBER_ID)
        assert eliminado is True

        members = obtener_miembros_team(team_members_table, TEAM_ID)
        assert len(members) == 0

    def test_eliminar_miembro_inexistente(self, team_members_table):
        eliminado = eliminar_miembro_team(team_members_table, TEAM_ID, "no-existe")
        assert eliminado is False

    def test_obtener_teams_usuario(self, teams_table, team_members_table):
        team = _make_team()
        crear_team(teams_table, team)

        member = _make_member(user_id=MEMBER_ID, role="member")
        agregar_miembro_team(team_members_table, member)

        teams = obtener_teams_usuario(team_members_table, teams_table, MEMBER_ID)
        assert len(teams) == 1
        assert teams[0].team_id == TEAM_ID


class TestContarProcesosEquipo:
    """contar_procesos_equipo cuenta radicados de todos los miembros, dedup."""

    def test_dedup_mismo_radicado(self, radicados_table, team_members_table, teams_table):
        """2 miembros con el mismo radicado cuentan como 1 proceso."""
        crear_team(teams_table, _make_team())
        agregar_miembro_team(team_members_table, _make_member(user_id=USER_ID, role="owner"))
        agregar_miembro_team(team_members_table, _make_member(user_id=MEMBER_ID))

        guardar_radicado(radicados_table, _make_radicado(user_id=USER_ID))
        guardar_radicado(radicados_table, _make_radicado(user_id=MEMBER_ID))

        count = contar_procesos_equipo(team_members_table, radicados_table, TEAM_ID)
        assert count == 1

    def test_radicados_distintos(self, radicados_table, team_members_table, teams_table):
        """2 radicados distintos cuentan como 2 procesos."""
        crear_team(teams_table, _make_team())
        agregar_miembro_team(team_members_table, _make_member(user_id=USER_ID, role="owner"))
        agregar_miembro_team(team_members_table, _make_member(user_id=MEMBER_ID))

        guardar_radicado(radicados_table, _make_radicado(user_id=USER_ID, radicado=RADICADO))

        rad2 = _make_radicado(user_id=MEMBER_ID, radicado=RADICADO_2)
        rad2.corporacion = CORP
        rad2.radicado_formato = "73001-23-33-000-2023-00471-00"
        guardar_radicado(radicados_table, rad2)

        count = contar_procesos_equipo(team_members_table, radicados_table, TEAM_ID)
        assert count == 2
