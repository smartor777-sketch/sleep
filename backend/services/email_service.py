"""Сервис для отправки email"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Сервис для отправки email"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password.get_secret_value() if settings.smtp_password else None
        self.smtp_from = settings.smtp_from or settings.smtp_user
    
    def _send_email(self, to: str, subject: str, body: str, html: bool = False):
        """
        Отправить email
        
        Args:
            to: Email получателя
            subject: Тема письма
            body: Содержимое письма
            html: Является ли body HTML
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email send")
            return
        
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.smtp_from
            msg["To"] = to
            msg["Subject"] = subject
            
            if html:
                part = MIMEText(body, "html")
            else:
                part = MIMEText(body, "plain")
            
            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to}")
        
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise
    
    def send_verification_email(self, to: str, token: str, base_url: str = "http://localhost:8000"):
        """
        Отправить письмо для подтверждения email
        
        Args:
            to: Email получателя
            token: Токен верификации
            base_url: Базовый URL приложения
        """
        verification_link = f"{base_url}/api/v1/auth/verify-email?token={token}"
        
        subject = "JungAI - Подтверждение email"
        body = f"""
        <html>
        <body>
            <h2>Добро пожаловать в JungAI!</h2>
            <p>Для подтверждения вашего email перейдите по ссылке:</p>
            <p><a href="{verification_link}">Подтвердить email</a></p>
            <p>Или скопируйте эту ссылку в браузер:</p>
            <p>{verification_link}</p>
            <p>Ссылка действительна в течение 24 часов.</p>
            <br>
            <p>Если вы не регистрировались в JungAI, проигнорируйте это письмо.</p>
        </body>
        </html>
        """
        
        self._send_email(to, subject, body, html=True)
    
    def send_password_reset_email(self, to: str, token: str, base_url: str = "http://localhost:8000"):
        """
        Отправить письмо для сброса пароля
        
        Args:
            to: Email получателя
            token: Токен сброса пароля
            base_url: Базовый URL приложения
        """
        reset_link = f"{base_url}/api/v1/auth/reset-password?token={token}"
        
        subject = "JungAI - Восстановление пароля"
        body = f"""
        <html>
        <body>
            <h2>Восстановление пароля JungAI</h2>
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
        
        self._send_email(to, subject, body, html=True)


# Глобальный экземпляр сервиса
email_service = EmailService()

