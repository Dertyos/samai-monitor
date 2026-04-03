"""
PreSignUp Cognito trigger.

Cognito llama este trigger ANTES de crear el usuario.

Para usuarios federados (Google):
- Auto-confirma el email (Google ya lo verifico).
- Si ya existe un usuario nativo con el mismo email, enlaza ambas
  identidades para que compartan la misma cuenta y datos.

Para usuarios nativos (email+password):
- NO auto-confirma: Cognito envia codigo de verificacion via
  CustomEmailSender Lambda.
"""
from __future__ import annotations

import logging
import os

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cognito = boto3.client("cognito-idp")


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    trigger_source = event.get("triggerSource", "")
    user_attributes = event["request"].get("userAttributes", {})
    user_pool_id = event["userPoolId"]

    # Solo actuar en sign-up externo (Google, etc.)
    if trigger_source != "PreSignUp_ExternalProvider":
        return event

    email = user_attributes.get("email", "")
    if not email:
        logger.warning("Usuario federado sin email, no se puede enlazar")
        return event

    # Auto-confirmar usuario federado (Google ya verifico el email)
    event["response"]["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True

    # Buscar si ya existe un usuario nativo con este email
    try:
        resp = cognito.list_users(
            UserPoolId=user_pool_id,
            Filter=f'email = "{email}"',
            Limit=10,
        )
    except Exception:
        logger.exception("Error buscando usuarios por email %s", email)
        return event

    # Buscar usuario nativo (no federado) existente
    native_user = None
    for user in resp.get("Users", []):
        username = user["Username"]
        # Usuarios federados tienen username tipo "Google_xxx"
        if "_" not in username:
            native_user = username
            break

    if not native_user:
        logger.info("No hay usuario nativo para %s, se creara cuenta nueva", email)
        return event

    # Enlazar la identidad federada al usuario nativo existente
    # event["userName"] tiene formato "Google_1234567890"
    provider_name, provider_user_id = event["userName"].split("_", 1)

    try:
        cognito.admin_link_provider_for_user(
            UserPoolId=user_pool_id,
            DestinationUser={
                "ProviderName": "Cognito",
                "ProviderAttributeValue": native_user,
            },
            SourceUser={
                "ProviderName": provider_name,
                "ProviderAttributeName": "Cognito_Subject",
                "ProviderAttributeValue": provider_user_id,
            },
        )
        logger.info("Enlazado %s -> usuario nativo %s", event["userName"], native_user)
    except Exception:
        logger.exception("Error enlazando %s con %s", event["userName"], native_user)

    return event
