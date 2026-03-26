"""Lambda Cognito Custom Email Sender — envía emails via Resend.

Cognito invoca esta Lambda en vez de usar SES para todos los correos:
- Verificación de cuenta (signup)
- Reenvío de código
- Recuperación de contraseña

El código de verificación viene cifrado con AWS Encryption SDK (NO
KMS directo); esta Lambda lo descifra y envía el correo con Resend.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any

import boto3
import resend

import aws_encryption_sdk
from aws_encryption_sdk import CommitmentPolicy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Resend API key — cargada desde SSM en cold start
def _load_resend_api_key() -> str:
    """Carga la API key de Resend desde SSM Parameter Store."""
    ssm_param = os.environ.get("RESEND_API_KEY_SSM", "/samai-monitor/resend-api-key")
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    resp = ssm.get_parameter(Name=ssm_param, WithDecryption=True)
    return resp["Parameter"]["Value"]


try:
    resend.api_key = _load_resend_api_key()
except Exception:
    logger.warning("Could not load Resend API key from SSM — emails will fail")

# AWS Encryption SDK client — Cognito Custom Email Sender V1_0
# usa este SDK para cifrar, NO kms.encrypt() directo.
_enc_client = aws_encryption_sdk.EncryptionSDKClient(
    commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_ALLOW_DECRYPT,
)

_kms_key_arn = os.environ.get("KMS_KEY_ARN", "")
_kms_provider = aws_encryption_sdk.StrictAwsKmsMasterKeyProvider(
    key_ids=[_kms_key_arn],
)

# Trigger sources que manejamos
_SIGNUP_TRIGGERS = {"CustomEmailSender_SignUp", "CustomEmailSender_ResendCode"}
_FORGOT_PASSWORD_TRIGGERS = {"CustomEmailSender_ForgotPassword"}


def handler(event: dict, context: Any) -> dict:
    """Entry point — Cognito Custom Email Sender trigger."""
    trigger = event.get("triggerSource", "")
    request = event.get("request", {})
    email = request.get("userAttributes", {}).get("email", "")
    encrypted_code = request.get("code", "")

    logger.info("Cognito email trigger: %s for %s", trigger, email)

    if not email or not encrypted_code:
        logger.warning("Missing email or code in event, skipping")
        return event

    code = _decrypt_code(encrypted_code)
    sender = os.environ.get("EMAIL_SENDER", "alertas@alertas-judiciales.dertyos.com")

    if trigger in _SIGNUP_TRIGGERS:
        subject = "Alertas Judiciales — Código de verificación"
        body_html = _build_verification_email(code)
    elif trigger in _FORGOT_PASSWORD_TRIGGERS:
        subject = "Alertas Judiciales — Restablecer contraseña"
        body_html = _build_forgot_password_email(code)
    else:
        logger.warning("Unknown trigger source: %s, skipping email", trigger)
        return event

    try:
        resend.Emails.send({
            "from": f"Alertas Judiciales <{sender}>",
            "to": [email],
            "subject": subject,
            "html": body_html,
        })
        logger.info("Email sent to %s for trigger %s", email, trigger)
    except Exception:
        logger.exception("Error sending email to %s", email)

    return event


def _decrypt_code(encrypted_code: str) -> str:
    """Descifra el código de verificación con AWS Encryption SDK.

    Cognito Custom Email Sender V1_0 cifra el código usando
    AWS Encryption SDK, NO kms.encrypt() directo. El ciphertext
    tiene el prefijo AYADe que identifica el formato del SDK.
    """
    ciphertext = base64.b64decode(encrypted_code)
    plaintext, _header = _enc_client.decrypt(
        source=ciphertext,
        key_provider=_kms_provider,
    )
    return plaintext.decode("utf-8")


def _build_verification_email(code: str) -> str:
    """Construye HTML para email de verificación de cuenta."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<h2 style="color:#1a73e8;">Alertas Judiciales <small>by Dertyos</small></h2>
<p>Gracias por registrarte. Tu código de verificación es:</p>
<div style="background:#f5f5f5;border-radius:8px;padding:20px;text-align:center;margin:20px 0;">
  <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a73e8;">{code}</span>
</div>
<p>Ingresa este código en la aplicación para verificar tu cuenta.</p>
<p style="color:#666;font-size:12px;margin-top:30px;">
Si no solicitaste esta verificación, puedes ignorar este correo.
</p>
</body></html>"""


def _build_forgot_password_email(code: str) -> str:
    """Construye HTML para email de recuperación de contraseña."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<h2 style="color:#1a73e8;">Alertas Judiciales <small>by Dertyos</small></h2>
<p>Recibimos una solicitud para restablecer tu contraseña. Tu código es:</p>
<div style="background:#f5f5f5;border-radius:8px;padding:20px;text-align:center;margin:20px 0;">
  <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1a73e8;">{code}</span>
</div>
<p>Ingresa este código en la aplicación para restablecer tu contraseña.</p>
<p style="color:#666;font-size:12px;margin-top:30px;">
Si no solicitaste este cambio, puedes ignorar este correo. Tu contraseña no será modificada.
</p>
</body></html>"""
