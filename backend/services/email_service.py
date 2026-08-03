"""Сервис для отправки email"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Protocol

import httpx

from config import settings

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Отправляет HTML-письмо, бросает исключение при ошибке."""

    def send(self, to: str, subject: str, html: str) -> None:
        ...


class ResendProvider:
    """Отправка через Resend HTTP API (основной провайдер)."""

    API_URL = "https://api.resend.com/emails"

    def __init__(self):
        key = settings.resend_api_key.get_secret_value() if settings.resend_api_key else None
        self.api_key = key
        self.from_email = settings.resend_from

    def send(self, to: str, subject: str, html: str) -> bool:
        if not self.api_key or not self.from_email:
            logger.warning("Resend not configured (api_key/from), skipping")
            return False
        payload = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        resp = httpx.post(
            self.API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=20,
        )
        if resp.status_code != 200:
            logger.error("Resend failed (%s): %s", resp.status_code, resp.text[:300])
            raise RuntimeError(f"resend_http_{resp.status_code}")
        return True


class UnisenderProvider:
    """Отправка через Unisender HTTP API (fallback 1)."""

    def __init__(self):
        key = (
            settings.unisender_api_key.get_secret_value()
            if settings.unisender_api_key
            else None
        )
        self.api_key = key
        self.from_email = settings.unisender_from
        self.from_name = "InnerCore"
        self.api_url = settings.unisender_api_url

    def send(self, to: str, subject: str, html: str) -> bool:
        if not self.api_key or not self.from_email:
            logger.warning("Unisender not configured (api_key/from), skipping")
            return False
        # Unisender API: минимальный payload, поле email для отправителя
        body = {
            "format": "json",
            "api_key": self.api_key,
            "email": self.from_email,
            "sender_name": self.from_name,
            "subject": subject,
            "body": html,
            "list_id": "",
        }
        resp = httpx.post(f"{self.api_url}/sendEmail", data=body, timeout=20)
        data = {}
        try:
            data = resp.json()
        except Exception:
            pass
        if resp.status_code != 200 or data.get("status") != "ok":
            logger.error(
                "Unisender failed (%s): %s | payload: email=%s",
                resp.status_code, resp.text[:300], self.from_email,
            )
            raise RuntimeError(f"unisender_http_{resp.status_code}")
        return True


class BrevoProvider:
    """Отправка через Brevo (Sendinblue) REST API (fallback 2)."""

    def __init__(self):
        key = settings.brevo_api_key.get_secret_value() if settings.brevo_api_key else None
        self.api_key = key
        self.from_email = settings.brevo_from
        self.from_name = "InnerCore"
        self.api_url = settings.brevo_api_url

    def send(self, to: str, subject: str, html: str) -> bool:
        if not self.api_key or not self.from_email:
            logger.warning("Brevo not configured (api_key/from), skipping")
            return False
        payload = {
            "sender": {"email": self.from_email, "name": self.from_name},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html,
        }
        resp = httpx.post(
            self.api_url,
            json=payload,
            headers={"api-key": self.api_key, "Content-Type": "application/json"},
            timeout=20,
        )
        if resp.status_code != 201:
            logger.error("Brevo failed (%s): %s", resp.status_code, resp.text[:300])
            raise RuntimeError(f"brevo_http_{resp.status_code}")
        return True


class SmtpProvider:
    """Отправка через SMTP (primary — Яндекс и т.п.)."""

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = (
            settings.smtp_password.get_secret_value() if settings.smtp_password else None
        )
        self.from_email = settings.smtp_from or settings.smtp_user
        self.use_ssl = settings.smtp_use_ssl

    def send(self, to: str, subject: str, html: str) -> bool:
        if not self.user or not self.password:
            logger.warning("SMTP not configured (user/password), skipping")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=20) as server:
                    server.login(self.user, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=20) as server:
                    server.starttls()
                    server.login(self.user, self.password)
                    server.send_message(msg)
            logger.info("Email sent via SMTP to %s", to)
            return True
        except Exception as e:
            logger.error("SMTP send failed: %s", e)
            raise RuntimeError(f"smtp_send_failed: {e}")


class EmailService:
    """Отправляет письма: SMTP → Resend → Unisender → Brevo."""

    def __init__(self):
        self.providers: list[EmailProvider] = [
            SmtpProvider(),
            ResendProvider(),
            UnisenderProvider(),
            BrevoProvider(),
        ]

    def _send_email(self, to: str, subject: str, html: str) -> bool:
        for provider in self.providers:
            try:
                if provider.send(to, subject, html):
                    logger.info("Email sent via %s to %s", type(provider).__name__, to)
                    return True
            except Exception as e:
                logger.error(
                    "Provider %s failed to send to %s: %s",
                    type(provider).__name__, to, e,
                )
        raise RuntimeError("No email provider available")

    def send_verification_code(self, to: str, code: str):
        """Отправить 6-значный код подтверждения email."""
        subject = "InnerCore — Код подтверждения"
        html = f"""\
<html>
<body style="font-family: sans-serif; color: #333;">
  <h2>Код подтверждения InnerCore</h2>
  <p>Ваш код:</p>
  <p style="font-size: 32px; letter-spacing: 6px; font-weight: bold; color: #6F42C1;">{code}</p>
  <p>Код действителен 30 минут.</p>
  <br>
  <p style="color: #999; font-size: 12px;">Если вы не регистрировались в InnerCore, проигнорируйте это письмо.</p>
</body>
</html>"""
        self._send_email(to, subject, html)

    def send_verification_email(self, to: str, token: str, base_url: str = "http://localhost:8000"):
        """Отправить письмо для подтверждения email по ссылке."""
        verification_link = f"{base_url}/api/v1/auth/verify-email?token={token}"
        subject = "InnerCore - Подтверждение email"
        html = f"""
        <html>
        <body>
            <h2>Добро пожаловать в InnerCore!</h2>
            <p>Для подтверждения вашего email перейдите по ссылке:</p>
            <p><a href="{verification_link}">Подтвердить email</a></p>
            <p>Или скопируйте эту ссылку в браузер:</p>
            <p>{verification_link}</p>
            <p>Ссылка действительна в течение 24 часов.</p>
            <br>
            <p>Если вы не регистрировались в InnerCore, проигнорируйте это письмо.</p>
        </body>
        </html>
        """
        self._send_email(to, subject, html)

    def send_password_reset_email(self, to: str, token: str, base_url: str = "http://localhost:8000"):
        """Отправить письмо для сброса пароля по ссылке."""
        reset_link = f"{base_url}/api/v1/auth/reset-password?token={token}"
        subject = "InnerCore - Восстановление пароля"
        html = f"""
        <html>
        <body>
            <h2>Восстановление пароля InnerCore</h2>
            <p>Вы запросили восстановление пароля. Для сброса пароля перейдите по ссылке:</p>
            <p><a href="{reset_link}">Сбросить пароль</a></p>
            <p>Или скопируйте эту ссылку в браузер:</p>
            <p>{reset_link}</p>
            <p>Ссылка действительна в течение 1 часа.</p>
            <br>
            <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
        </body>
        </html>
        """
        self._send_email(to, subject, html)


# Глобальный экземпляр сервиса
email_service = EmailService()