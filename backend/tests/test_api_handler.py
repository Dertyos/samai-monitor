"""Tests for api_handler Lambda — TDD: tests primero."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws

from models import Actuacion


@pytest.fixture(autouse=True)
def _mock_get_max_orden():
    """Mock get_max_orden para que POST /radicados no llame a SAMAI."""
    with patch("functions.api_handler.app.samai_client.get_max_orden", return_value=177):
        yield


# Helper: simula evento API Gateway v2
def _make_event(
    method: str = "GET",
    path: str = "/radicados",
    body: dict | None = None,
    path_params: dict | None = None,
    user_id: str = "user-123",
    stage: str = "$default",
) -> dict:
    event = {
        "rawPath": path,
        "requestContext": {
            "http": {"method": method, "path": path},
            "authorizer": {"jwt": {"claims": {"sub": user_id}}},
            "stage": stage,
        },
        "pathParameters": path_params or {},
        "body": json.dumps(body) if body else None,
        "queryStringParameters": {},
    }
    return event


def _context() -> MagicMock:
    return MagicMock()


class TestPostRadicados:
    """POST /radicados — agregar radicado a monitorear."""

    def test_crear_radicado_201(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00", "alias": "Caso Aviles"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 201
        data = json.loads(resp["body"])
        assert data["radicado"] == "73001233300020190034300"
        assert data["corporacion"] == "7300123"

    def test_radicado_invalido_400(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "12345"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 400

    def test_sin_body_400(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="POST", path="/radicados")
        event["body"] = None
        resp = handler(event, _context())
        assert resp["statusCode"] == 400

    def test_duplicado_409(self, dynamodb_resource):
        from functions.api_handler.app import handler

        body = {"radicado": "73001-23-33-000-2019-00343-00"}
        event1 = _make_event(method="POST", path="/radicados", body=body)
        event2 = _make_event(method="POST", path="/radicados", body=body)

        resp1 = handler(event1, _context())
        assert resp1["statusCode"] == 201

        resp2 = handler(event2, _context())
        assert resp2["statusCode"] == 409


class TestGetRadicados:
    """GET /radicados — listar mis radicados."""

    def test_lista_vacia(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="GET", path="/radicados")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data == []

    def test_lista_con_radicados(self, dynamodb_resource):
        from functions.api_handler.app import handler

        # Crear uno primero
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00", "alias": "Caso Aviles"},
        )
        handler(create_event, _context())

        # Listar
        event = _make_event(method="GET", path="/radicados")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert len(data) == 1
        assert data[0]["radicado"] == "73001233300020190034300"


class TestToggleActivo:
    """PATCH /radicados/{id}/toggle — alternar activo/inactivo."""

    def test_toggle_desactiva(self, dynamodb_resource):
        from functions.api_handler.app import handler

        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        event = _make_event(
            method="PATCH",
            path="/radicados/73001233300020190034300/toggle",
            path_params={"id": "73001233300020190034300"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["activo"] is False

    def test_toggle_reactiva(self, dynamodb_resource):
        from functions.api_handler.app import handler

        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        event = _make_event(
            method="PATCH",
            path="/radicados/73001233300020190034300/toggle",
            path_params={"id": "73001233300020190034300"},
        )
        handler(event, _context())
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["activo"] is True

    def test_toggle_inexistente_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(
            method="PATCH",
            path="/radicados/99999999999999999999999/toggle",
            path_params={"id": "99999999999999999999999"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 404


class TestPatchRadicado:
    """PATCH /radicados/{id} — editar alias."""

    def test_actualizar_alias_200(self, dynamodb_resource):
        from functions.api_handler.app import handler

        # Crear
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00", "alias": "Caso Aviles"},
        )
        handler(create_event, _context())

        # Editar alias
        patch_event = _make_event(
            method="PATCH",
            path="/radicados/73001233300020190034300",
            path_params={"id": "73001233300020190034300"},
            body={"alias": "Caso Modificado"},
        )
        resp = handler(patch_event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["alias"] == "Caso Modificado"

    def test_editar_alias_inexistente_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(
            method="PATCH",
            path="/radicados/99999999999999999999999",
            path_params={"id": "99999999999999999999999"},
            body={"alias": "Nuevo alias"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 404


class TestDeleteRadicados:
    """DELETE /radicados/{id} — dejar de monitorear."""

    def test_eliminar_existente_204(self, dynamodb_resource):
        from functions.api_handler.app import handler

        # Crear
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        # Eliminar
        delete_event = _make_event(
            method="DELETE",
            path="/radicados/73001233300020190034300",
            path_params={"id": "73001233300020190034300"},
        )
        resp = handler(delete_event, _context())
        assert resp["statusCode"] == 204

    def test_eliminar_cascade_borra_alertas(self, dynamodb_resource):
        """Al eliminar un radicado, sus alertas asociadas tambien se borran."""
        from functions.api_handler.app import handler

        radicado = "73001233300020190034300"

        # 1. Crear radicado
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        # 2. Insertar alertas manualmente para este usuario+radicado
        alertas_table = dynamodb_resource.Table("samai-alertas")
        for i in range(3):
            alertas_table.put_item(Item={
                "userId": "user-123",
                "sk": f"2026-01-01T00:00:00Z#{radicado}#{i+1}",
                "radicado": radicado,
                "orden": i + 1,
                "nombreActuacion": f"Actuacion {i+1}",
                "fechaActuacion": "2026-01-01",
                "anotacion": "",
                "createdAt": "2026-01-01T00:00:00Z",
                "enviado": False,
            })

        # Verificar que hay 3 alertas
        alertas_resp = alertas_table.query(
            KeyConditionExpression="userId = :u",
            ExpressionAttributeValues={":u": "user-123"},
        )
        assert len(alertas_resp["Items"]) == 3

        # 3. Eliminar radicado — debe hacer cascade delete de alertas
        delete_event = _make_event(
            method="DELETE",
            path=f"/radicados/{radicado}",
            path_params={"id": radicado},
        )
        resp = handler(delete_event, _context())
        assert resp["statusCode"] == 204

        # 4. Verificar que las alertas fueron eliminadas
        alertas_resp = alertas_table.query(
            KeyConditionExpression="userId = :u",
            ExpressionAttributeValues={":u": "user-123"},
        )
        assert len(alertas_resp["Items"]) == 0

    def test_eliminar_inexistente_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        delete_event = _make_event(
            method="DELETE",
            path="/radicados/73001233300020190034300",
            path_params={"id": "73001233300020190034300"},
        )
        resp = handler(delete_event, _context())
        assert resp["statusCode"] == 404


class TestPatchAlertaRead:
    """PATCH /alertas/{sk}/read — marcar alerta como leida."""

    def test_marcar_alerta_leida_200(self, dynamodb_resource):
        from functions.api_handler.app import handler

        alertas_table = dynamodb_resource.Table("samai-alertas")
        sk = "2026-01-01T00:00:00Z#73001233300020190034300#5"
        alertas_table.put_item(Item={
            "userId": "user-123",
            "sk": sk,
            "radicado": "73001233300020190034300",
            "orden": 5,
            "nombreActuacion": "Auto admisorio",
            "fechaActuacion": "2026-01-01",
            "anotacion": "",
            "createdAt": "2026-01-01T00:00:00Z",
            "enviado": False,
            "leido": False,
        })

        event = _make_event(
            method="PATCH",
            path=f"/alertas/{sk}/read",
            path_params={"sk": sk},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 200

        # Verificar que leido=True en DynamoDB
        item = alertas_table.get_item(Key={"userId": "user-123", "sk": sk})["Item"]
        assert item["leido"] is True

    def test_marcar_alerta_inexistente_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(
            method="PATCH",
            path="/alertas/fake-sk/read",
            path_params={"sk": "fake-sk"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 404


class TestMarkAllRead:
    """PATCH /alertas/read-all — marcar todas las alertas como leidas."""

    def test_marca_todas_200(self, dynamodb_resource):
        from functions.api_handler.app import handler

        alertas_table = dynamodb_resource.Table("samai-alertas")
        for i in range(3):
            alertas_table.put_item(Item={
                "userId": "user-123",
                "sk": f"2026-01-01T00:00:00Z#73001233300020190034300#{i+1}",
                "radicado": "73001233300020190034300",
                "orden": i + 1,
                "nombreActuacion": f"Actuacion {i+1}",
                "fechaActuacion": "2026-01-01",
                "anotacion": "",
                "createdAt": "2026-01-01T00:00:00Z",
                "enviado": False,
                "leido": False,
            })

        event = _make_event(method="PATCH", path="/alertas/read-all")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["count"] == 3

        # Verificar que todas estan leidas
        items = alertas_table.query(
            KeyConditionExpression="userId = :u",
            ExpressionAttributeValues={":u": "user-123"},
        )["Items"]
        assert all(item["leido"] for item in items)

    def test_sin_alertas_200(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="PATCH", path="/alertas/read-all")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["count"] == 0


class TestGetAlertas:
    """GET /alertas — listar mis alertas."""

    def test_alertas_vacias(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="GET", path="/alertas")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data == []


class TestGetHistorial:
    """GET /radicados/{id}/historial — actuaciones del proceso via SAMAI."""

    def test_historial_retorna_actuaciones(self, dynamodb_resource):
        from functions.api_handler.app import handler

        # Crear radicado primero
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        # Mock SAMAI client
        mock_actuaciones = [
            Actuacion(
                radicado="73001233300020190034300",
                orden=177,
                nombre="Fijacion estado",
                fecha="2026-03-20T00:00:00",
                anotacion="LMB-",
                registro="2026-03-19T16:31:57.1",
            )
        ]

        with patch(
            "functions.api_handler.app.samai_client"
        ) as mock_client:
            mock_client.get_actuaciones.return_value = mock_actuaciones

            event = _make_event(
                method="GET",
                path="/radicados/73001233300020190034300/historial",
                path_params={"id": "73001233300020190034300"},
            )
            resp = handler(event, _context())

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert len(data) == 1
        assert data[0]["orden"] == 177


class TestGetDetalle:
    """GET /radicados/{id}/detalle — datos completos del proceso via SAMAI."""

    def test_detalle_retorna_datos_proceso_partes_historial(self, dynamodb_resource):
        from functions.api_handler.app import handler

        # Crear radicado primero
        create_event = _make_event(
            method="POST",
            path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00"},
        )
        handler(create_event, _context())

        mock_actuaciones = [
            Actuacion(
                radicado="73001233300020190034300",
                orden=177,
                nombre="Fijacion estado",
                fecha="2026-03-20T00:00:00",
                anotacion="LMB-",
                registro="2026-03-19T16:31:57.1",
                estado="REGISTRADA",
                decision="ADMITE DEMANDA",
            )
        ]
        mock_datos = {
            "proceso": {
                "Seccion": "TRIBUNAL ADMINISTRATIVO DEL TOLIMA",
                "Ponente": "JUAN PEREZ",
                "tipoProceso": "NULIDAD Y RESTABLECIMIENTO",
                "claseProceso": "DEMANDA",
                "UltimaActuacionDespachoFecha": "2026-03-20",
            }
        }
        mock_partes = [
            {"NOMBRE": "JUAN AVILES", "TIPO": "DEMANDANTE"},
            {"NOMBRE": "MUNICIPIO DE IBAGUE", "TIPO": "DEMANDADO"},
        ]

        with patch(
            "functions.api_handler.app.samai_client"
        ) as mock_client:
            mock_client.get_actuaciones.return_value = mock_actuaciones
            mock_client.get_datos_proceso.return_value = mock_datos
            mock_client.get_sujetos_procesales.return_value = mock_partes

            event = _make_event(
                method="GET",
                path="/radicados/73001233300020190034300/detalle",
                path_params={"id": "73001233300020190034300"},
            )
            resp = handler(event, _context())

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["proceso"]["despacho"] == "TRIBUNAL ADMINISTRATIVO DEL TOLIMA"
        assert data["proceso"]["ponente"] == "JUAN PEREZ"
        assert len(data["partes"]) == 2
        assert data["partes"][0]["nombre"] == "JUAN AVILES"
        assert data["partes"][0]["tipo"] == "DEMANDANTE"
        assert len(data["actuaciones"]) == 1
        assert data["actuaciones"][0]["decision"] == "ADMITE DEMANDA"

    def test_detalle_radicado_no_encontrado_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        with patch("functions.api_handler.app.samai_client"):
            event = _make_event(
                method="GET",
                path="/radicados/99999999999999999999999/detalle",
                path_params={"id": "99999999999999999999999"},
            )
            resp = handler(event, _context())

        assert resp["statusCode"] == 404


class TestGetBuscar:
    """GET /buscar/{numProceso} — buscar proceso en SAMAI."""

    def test_buscar_retorna_resultados(self, dynamodb_resource):
        from functions.api_handler.app import handler

        mock_result = [{"NumProceso": "73001233300020190034300", "Corporacion": "7300123"}]

        with patch(
            "functions.api_handler.app.samai_client"
        ) as mock_client:
            mock_client.buscar_proceso.return_value = mock_result

            event = _make_event(
                method="GET",
                path="/buscar/73001233300020190034300",
                path_params={"numProceso": "73001233300020190034300"},
            )
            resp = handler(event, _context())

        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert len(data) == 1


# --- Teams ---


class TestPostTeam:
    def test_sin_plan_firma_403(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="POST", path="/teams", body={"name": "Mi Firma"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 403
        assert "PLAN_REQUIRED" in json.loads(resp["body"])["code"]

    def test_con_plan_firma_201(self, dynamodb_resource):
        from functions.api_handler.app import handler, _billing_subs_table, _billing_plans_table

        _billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-firma", "status": "active",
        })
        _billing_plans_table.put_item(Item={
            "planId": "plan-firma", "name": "Firma", "amount": 79900,
            "features": {"max_processes": 150},
        })

        event = _make_event(method="POST", path="/teams", body={"name": "Mi Firma"})
        resp = handler(event, _context())
        assert resp["statusCode"] == 201
        data = json.loads(resp["body"])
        assert data["name"] == "Mi Firma"
        assert data["ownerUserId"] == "user-123"


class TestGetTeams:
    def test_sin_equipos(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="GET", path="/teams")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        assert json.loads(resp["body"]) == []


class TestEnforcementEquipo:
    def test_equipo_activo_permite(self, dynamodb_resource):
        from functions.api_handler.app import handler, _billing_subs_table, _billing_plans_table, _teams_table, _team_members_table

        _billing_subs_table.put_item(Item={
            "userId": "user-123", "planId": "plan-firma", "status": "active",
        })
        _billing_plans_table.put_item(Item={
            "planId": "plan-firma", "name": "Firma", "amount": 79900,
            "features": {"max_processes": 150},
        })
        _teams_table.put_item(Item={
            "teamId": "team-1", "name": "Firma", "ownerUserId": "user-123", "planId": "plan-firma",
        })
        _team_members_table.put_item(Item={
            "teamId": "team-1", "userId": "user-123", "role": "owner",
        })

        event = _make_event(
            method="POST", path="/radicados",
            body={"radicado": "73001-23-33-000-2019-00343-00", "alias": "Test"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 201

    def test_equipo_inactivo_cae_a_personal(self, dynamodb_resource):
        from functions.api_handler.app import handler, _teams_table, _team_members_table, _radicados_table
        from db import guardar_radicado
        from models import Radicado

        _teams_table.put_item(Item={
            "teamId": "team-1", "name": "Firma", "ownerUserId": "owner-1", "planId": "plan-firma",
        })
        _team_members_table.put_item(Item={
            "teamId": "team-1", "userId": "user-123", "role": "member",
        })

        for i in range(5):
            guardar_radicado(_radicados_table, Radicado(
                user_id="user-123", radicado=f"7300123330002019003430{i}",
                corporacion="7300123", radicado_formato="", activo=True,
                created_at=f"2026-03-{10+i:02d}T10:00:00",
            ))

        event = _make_event(
            method="POST", path="/radicados",
            body={"radicado": "73001-23-33-000-2023-00471-00", "alias": "Excede"},
        )
        resp = handler(event, _context())
        assert resp["statusCode"] == 403
        assert "PLAN_LIMIT" in json.loads(resp["body"])["code"]


class TestInvitationsEndpoints:
    def test_get_invitation_valida(self, dynamodb_resource):
        from functions.api_handler.app import handler, _invitations_table, _teams_table
        import time

        _teams_table.put_item(Item={
            "teamId": "team-1", "name": "Firma Test", "ownerUserId": "user-123", "planId": "plan-firma",
        })
        _invitations_table.put_item(Item={
            "inviteId": "inv-1", "teamId": "team-1", "email": "nuevo@test.com",
            "role": "member", "invitedBy": "user-123", "status": "pending",
            "token": "abc123token", "createdAt": "2026-04-03T10:00:00",
            "ttl": int(time.time()) + 86400,
        })

        event = _make_event(method="GET", path="/invitations/abc123token")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["teamName"] == "Firma Test"
        assert data["email"] == "nuevo@test.com"

    def test_get_invitation_inexistente_404(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="GET", path="/invitations/no-existe")
        resp = handler(event, _context())
        assert resp["statusCode"] == 404

    def test_accept_invitation(self, dynamodb_resource):
        from functions.api_handler.app import handler, _invitations_table, _teams_table, _team_members_table
        import time

        _teams_table.put_item(Item={
            "teamId": "team-1", "name": "Firma Test", "ownerUserId": "owner-1", "planId": "plan-firma",
        })
        _invitations_table.put_item(Item={
            "inviteId": "inv-1", "teamId": "team-1", "email": "user@test.com",
            "role": "member", "invitedBy": "owner-1", "status": "pending",
            "token": "accept-token", "createdAt": "2026-04-03T10:00:00",
            "ttl": int(time.time()) + 86400,
        })

        event = _make_event(method="POST", path="/invitations/accept-token/accept")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["status"] == "accepted"

        from boto3.dynamodb.conditions import Key
        members = _team_members_table.query(
            KeyConditionExpression=Key("teamId").eq("team-1"),
        ).get("Items", [])
        assert any(m["userId"] == "user-123" for m in members)


# ============================================
# Alert Schedules
# ============================================


def _seed_subscription(dynamodb_resource, user_id: str, plan_id: str) -> None:
    """Seed una suscripcion activa para un usuario."""
    table = dynamodb_resource.Table("samai-billing-subscriptions")
    table.put_item(Item={
        "userId": user_id,
        "planId": plan_id,
        "status": "active",
        "currentPeriodStart": "2026-04-01T00:00:00Z",
        "currentPeriodEnd": "2026-05-01T00:00:00Z",
    })


@pytest.mark.unit
class TestAlertSchedule:
    """GET/PUT/DELETE /alert-schedule — alertas personalizadas."""

    def test_get_empty(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="GET", path="/alert-schedule")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"] is None
        assert data["eligible"] is False

    def test_get_eligible_no_schedule(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        event = _make_event(method="GET", path="/alert-schedule")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"] is None
        assert data["eligible"] is True

    def test_put_eligible(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 14})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"]["alertHourCot"] == 14
        assert data["schedule"]["alertHourUtc"] == 19  # (14+5)%24

    def test_put_ineligible_free(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 14})
        resp = handler(event, _context())
        assert resp["statusCode"] == 403

    def test_put_ineligible_pro(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 14})
        resp = handler(event, _context())
        assert resp["statusCode"] == 403

    def test_put_invalid_hour_negative(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-firma")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": -1})
        resp = handler(event, _context())
        assert resp["statusCode"] == 400

    def test_put_invalid_hour_24(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-firma")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 24})
        resp = handler(event, _context())
        assert resp["statusCode"] == 400

    def test_put_conflict_7am(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-enterprise")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 7})
        resp = handler(event, _context())
        assert resp["statusCode"] == 400
        data = json.loads(resp["body"])
        assert "7:00 AM" in data["error"]

    def test_put_update_existing(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        # Crear
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 14})
        handler(event, _context())
        # Actualizar
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 20})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"]["alertHourCot"] == 20
        assert data["schedule"]["updatedAt"] != ""

    def test_delete_existing(self, dynamodb_resource):
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        # Crear
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 14})
        handler(event, _context())
        # Eliminar
        event = _make_event(method="DELETE", path="/alert-schedule")
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        # Verificar que ya no existe
        event = _make_event(method="GET", path="/alert-schedule")
        resp = handler(event, _context())
        data = json.loads(resp["body"])
        assert data["schedule"] is None

    def test_delete_nonexistent(self, dynamodb_resource):
        from functions.api_handler.app import handler

        event = _make_event(method="DELETE", path="/alert-schedule")
        resp = handler(event, _context())
        assert resp["statusCode"] == 404

    def test_put_midnight_wraps_utc(self, dynamodb_resource):
        """hourCot=0 (midnight) -> hourUtc=5."""
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 0})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"]["alertHourUtc"] == 5

    def test_put_late_night_wraps_utc(self, dynamodb_resource):
        """hourCot=22 -> hourUtc=3."""
        from functions.api_handler.app import handler

        _seed_subscription(dynamodb_resource, "user-123", "plan-pro-plus")
        event = _make_event(method="PUT", path="/alert-schedule", body={"hourCot": 22})
        resp = handler(event, _context())
        assert resp["statusCode"] == 200
        data = json.loads(resp["body"])
        assert data["schedule"]["alertHourUtc"] == 3
