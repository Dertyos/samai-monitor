"""Tests for Cognito Custom Email Sender Lambda — TDD: tests primero."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


ENCRYPTED_CODE = "AQICAHh...encrypted..."
DECRYPTED_CODE = "123456"
USER_EMAIL = "julian@dertyos.com"


def _make_event(
    trigger_source: str = "CustomEmailSender_SignUp",
    code: str = ENCRYPTED_CODE,
    email: str = USER_EMAIL,
) -> dict:
    return {
        "version": "1",
        "triggerSource": trigger_source,
        "region": "us-east-1",
        "userPoolId": "us-east-1_ABC123",
        "userName": "user-123",
        "callerContext": {"awsSdkVersion": "3.0", "clientId": "client-id"},
        "request": {
            "type": "customEmailSenderRequestV1",
            "code": code,
            "userAttributes": {"email": email},
        },
        "response": {},
    }


class TestCognitoEmailSender:
    """Custom Email Sender: descifra código y envía via Resend."""

    def test_signup_sends_verification_email(self):
        from functions.cognito_email_sender.app import handler

        event = _make_event(trigger_source="CustomEmailSender_SignUp")

        with patch("functions.cognito_email_sender.app._decrypt_code", return_value=DECRYPTED_CODE), \
             patch("functions.cognito_email_sender.app.resend") as mock_resend:
            result = handler(event, MagicMock())

        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == [USER_EMAIL]
        assert DECRYPTED_CODE in call_args["html"]
        assert "verificación" in call_args["subject"].lower() or "verificaci" in call_args["subject"].lower()

    def test_forgot_password_sends_reset_email(self):
        from functions.cognito_email_sender.app import handler

        event = _make_event(trigger_source="CustomEmailSender_ForgotPassword")

        with patch("functions.cognito_email_sender.app._decrypt_code", return_value=DECRYPTED_CODE), \
             patch("functions.cognito_email_sender.app.resend") as mock_resend:
            result = handler(event, MagicMock())

        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == [USER_EMAIL]
        assert DECRYPTED_CODE in call_args["html"]
        assert "contraseña" in call_args["subject"].lower()

    def test_resend_code_sends_verification_email(self):
        from functions.cognito_email_sender.app import handler

        event = _make_event(trigger_source="CustomEmailSender_ResendCode")

        with patch("functions.cognito_email_sender.app._decrypt_code", return_value=DECRYPTED_CODE), \
             patch("functions.cognito_email_sender.app.resend") as mock_resend:
            result = handler(event, MagicMock())

        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert DECRYPTED_CODE in call_args["html"]

    def test_returns_event_unchanged(self):
        from functions.cognito_email_sender.app import handler

        event = _make_event()

        with patch("functions.cognito_email_sender.app._decrypt_code", return_value=DECRYPTED_CODE), \
             patch("functions.cognito_email_sender.app.resend"):
            result = handler(event, MagicMock())

        assert result == event

    def test_unknown_trigger_logs_warning_no_email(self):
        from functions.cognito_email_sender.app import handler

        event = _make_event(trigger_source="CustomEmailSender_Unknown")

        with patch("functions.cognito_email_sender.app._decrypt_code", return_value=DECRYPTED_CODE), \
             patch("functions.cognito_email_sender.app.resend") as mock_resend:
            result = handler(event, MagicMock())

        mock_resend.Emails.send.assert_not_called()

    def test_decrypt_code_calls_kms(self):
        from functions.cognito_email_sender.app import _decrypt_code
        import base64

        mock_kms = MagicMock()
        mock_kms.decrypt.return_value = {"Plaintext": b"123456"}

        encrypted = base64.b64encode(b"some-encrypted-data").decode()
        result = _decrypt_code(mock_kms, encrypted)

        assert result == "123456"
        mock_kms.decrypt.assert_called_once()
