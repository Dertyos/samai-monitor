"""
PreSignUp Cognito trigger.

Auto-confirma y auto-verifica el email de cada usuario nuevo,
eliminando el paso de código de verificación en el registro.

Cognito llama este trigger ANTES de crear el usuario.
Retornar autoConfirmUser=True + autoVerifyEmail=True hace que
el usuario quede CONFIRMED de inmediato, sin enviar ningún código.
"""


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    event["response"]["autoConfirmUser"] = True
    event["response"]["autoVerifyEmail"] = True
    return event
