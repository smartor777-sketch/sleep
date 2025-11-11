"""Pydantic схемы для аутентификации"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Схема для регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """Схема для входа"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Схема ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Схема для обновления токена"""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Схема для запроса восстановления пароля"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Схема для сброса пароля"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ResendVerificationRequest(BaseModel):
    """Схема для повторной отправки письма подтверждения"""
    email: EmailStr


class MessageResponse(BaseModel):
    """Общая схема для сообщений"""
    message: str


class OAuth2CallbackResponse(BaseModel):
    """Схема ответа при OAuth2 callback"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool

