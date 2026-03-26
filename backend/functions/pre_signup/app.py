"""
PreSignUp Cognito trigger.

Cognito llama este trigger ANTES de crear el usuario.
NO auto-confirmamos para que Cognito envíe el código de verificación
vía CustomEmailSender Lambda. El usuario debe ingresar el código
para confirmar su cuenta antes de poder iniciar sesión.
"""


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    # No auto-confirm: Cognito enviará código 6 dígitos via CustomEmailSender
    return event
