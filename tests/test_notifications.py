"""
tests/test_notifications.py
Tests para sistema de notificaciones del pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from scripts.etl.notifications import (
    EmailNotifier,
    SlackNotifier,
    get_notifier,
)


class TestEmailNotifier:
    """Pruebas para notificador de email."""

    def test_email_notifier_disabled_by_default(self):
        """EmailNotifier debe estar deshabilitado sin configuración."""
        notifier = EmailNotifier()
        assert notifier.enabled is False

    def test_email_notifier_enabled_with_config(self):
        """EmailNotifier debe habilitarse con configuración."""
        notifier = EmailNotifier(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            sender_email="test@example.com",
            sender_password="password",
            recipient_emails=["recipient@example.com"],
        )
        assert notifier.enabled is True
        assert notifier.smtp_server == "smtp.gmail.com"
        assert "recipient@example.com" in notifier.recipient_emails

    def test_failure_alert_not_sent_when_disabled(self):
        """No debe enviar alerta cuando está deshabilitado."""
        notifier = EmailNotifier()
        error = ConnectionError("Test error")
        
        result = notifier.send_pipeline_failure_alert(
            error=error,
            operation="Test Operation",
        )
        
        assert result is False

    @patch("smtplib.SMTP")
    def test_failure_alert_sent_when_enabled(self, mock_smtp):
        """Debe enviar alerta cuando está habilitado."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = EmailNotifier(
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="sender@test.com",
            sender_password="pass",
            recipient_emails=["recipient@test.com"],
        )
        
        error = ValueError("Test validation error")
        result = notifier.send_pipeline_failure_alert(
            error=error,
            operation="Test Operation",
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@test.com", "pass")

    @patch("smtplib.SMTP")
    def test_recovery_alert_sent(self, mock_smtp):
        """Debe enviar alerta de recuperación."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = EmailNotifier(
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="sender@test.com",
            sender_password="pass",
            recipient_emails=["recipient@test.com"],
        )
        
        result = notifier.send_recovery_success_alert(
            operation="Test Operation",
            recovery_method="Manual Rollback",
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()

    def test_html_body_generated_correctly(self):
        """Debe generar cuerpo HTML válido."""
        notifier = EmailNotifier(
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="sender@test.com",
            sender_password="pass",
            recipient_emails=["recipient@test.com"],
        )
        
        error = RuntimeError("Test error message")
        body = notifier._build_failure_body(
            error=error,
            operation="Test Op",
            audit_summary={"total_eventos": 10, "eventos_exitosos": 8},
            timestamp=datetime.now(),
        )
        
        assert "RuntimeError" in body
        assert "Test error message" in body
        assert "<html>" in body
        assert "Total eventos: 10" in body


class TestSlackNotifier:
    """Pruebas para notificador Slack."""

    def test_slack_notifier_disabled_by_default(self):
        """SlackNotifier debe estar deshabilitado sin webhook."""
        notifier = SlackNotifier()
        assert notifier.enabled is False

    def test_slack_notifier_enabled_with_webhook(self):
        """SlackNotifier debe habilitarse con webhook."""
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        assert notifier.enabled is True

    def test_slack_alert_not_sent_when_disabled(self):
        """No debe enviar alerta cuando está deshabilitado."""
        notifier = SlackNotifier()
        error = ConnectionError("Test error")
        
        result = notifier.send_pipeline_failure_alert(
            error=error,
            operation="Test",
        )
        
        assert result is False


class TestNotifierFactory:
    """Pruebas para factory de notificadores."""

    def test_get_email_notifier(self):
        """Factory debe retornar EmailNotifier para provider 'email'."""
        notifier = get_notifier("email")
        assert isinstance(notifier, EmailNotifier)

    def test_get_slack_notifier(self):
        """Factory debe retornar SlackNotifier para provider 'slack'."""
        notifier = get_notifier("slack")
        assert isinstance(notifier, SlackNotifier)

    def test_get_unknown_notifier(self):
        """Factory debe retornar None para provider desconocido."""
        notifier = get_notifier("unknown_provider")
        assert notifier is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
