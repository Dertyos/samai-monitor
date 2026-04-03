"""Tests for post_confirmation Lambda — auto-acepta invitaciones al registrarse."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from models import TeamInvitation
from db import guardar_invitacion, obtener_miembros_team, obtener_invitaciones_por_email


class TestPostConfirmation:
    def test_procesa_invitaciones_pendientes(self, dynamodb_resource, invitations_table, team_members_table):
        from functions.post_confirmation.app import handler

        # Crear invitacion pendiente
        inv = TeamInvitation(
            invite_id="inv-1", team_id="team-1", email="nuevo@test.com",
            role="member", invited_by="owner-1", status="pending",
            token="abc123", created_at="2026-04-03T10:00:00",
            ttl=int(time.time()) + 86400,
        )
        guardar_invitacion(invitations_table, inv)

        # Simular evento PostConfirmation de Cognito
        event = {
            "triggerSource": "PostConfirmation_ConfirmSignUp",
            "userName": "new-user-id",
            "request": {"userAttributes": {"email": "nuevo@test.com"}},
        }

        with patch("functions.post_confirmation.app._invitations_table", invitations_table), \
             patch("functions.post_confirmation.app._team_members_table", team_members_table):
            result = handler(event, MagicMock())

        # Debe retornar el evento (Cognito lo requiere)
        assert result["userName"] == "new-user-id"

        # Verificar que se agrego como miembro
        members = obtener_miembros_team(team_members_table, "team-1")
        assert any(m.user_id == "new-user-id" for m in members)

        # Verificar que la invitacion se marco como aceptada
        pending = obtener_invitaciones_por_email(invitations_table, "nuevo@test.com")
        assert len(pending) == 0

    def test_ignora_trigger_forgot_password(self, dynamodb_resource):
        from functions.post_confirmation.app import handler

        event = {
            "triggerSource": "PostConfirmation_ForgotPassword",
            "userName": "user-1",
            "request": {"userAttributes": {"email": "user@test.com"}},
        }
        result = handler(event, MagicMock())
        assert result["triggerSource"] == "PostConfirmation_ForgotPassword"

    def test_sin_invitaciones_no_hace_nada(self, dynamodb_resource, invitations_table, team_members_table):
        from functions.post_confirmation.app import handler

        event = {
            "triggerSource": "PostConfirmation_ConfirmSignUp",
            "userName": "user-sin-inv",
            "request": {"userAttributes": {"email": "nadie@test.com"}},
        }

        with patch("functions.post_confirmation.app._invitations_table", invitations_table), \
             patch("functions.post_confirmation.app._team_members_table", team_members_table):
            result = handler(event, MagicMock())

        assert result["userName"] == "user-sin-inv"
