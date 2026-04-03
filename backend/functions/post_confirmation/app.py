"""Cognito PostConfirmation trigger — procesa invitaciones pendientes al registrarse.

Cuando un usuario confirma su cuenta (email verification), busca si hay
invitaciones pendientes para su email y lo agrega a los equipos correspondientes.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from models import TeamMember
from db import (
    obtener_invitaciones_por_email,
    marcar_invitacion_aceptada,
    agregar_miembro_team,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")
_invitations_table = _dynamodb.Table(os.environ.get("TEAM_INVITATIONS_TABLE", "samai-team-invitations"))
_team_members_table = _dynamodb.Table(os.environ.get("TEAM_MEMBERS_TABLE", "samai-team-members"))


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Cognito PostConfirmation trigger."""
    trigger = event.get("triggerSource", "")

    # Solo actuar en confirmación de signup, no en forgot-password
    if trigger != "PostConfirmation_ConfirmSignUp":
        return event

    email = event["request"]["userAttributes"].get("email", "")
    user_id = event["userName"]

    if not email:
        return event

    logger.info("PostConfirmation: user=%s email=%s", user_id, email)

    # Buscar invitaciones pendientes para este email
    pending = obtener_invitaciones_por_email(_invitations_table, email)
    if not pending:
        logger.info("Sin invitaciones pendientes para %s", email)
        return event

    now = datetime.now(timezone.utc).isoformat()
    for invitation in pending:
        try:
            member = TeamMember(
                team_id=invitation.team_id,
                user_id=user_id,
                role=invitation.role,
                joined_at=now,
            )
            agregar_miembro_team(_team_members_table, member)
            marcar_invitacion_aceptada(_invitations_table, invitation.invite_id)
            logger.info(
                "Invitacion auto-aceptada: user=%s equipo=%s invite=%s",
                user_id, invitation.team_id, invitation.invite_id,
            )
        except Exception:
            logger.exception("Error procesando invitacion %s", invitation.invite_id)

    return event
