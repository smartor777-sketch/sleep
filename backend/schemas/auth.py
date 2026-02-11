"""Pydantic схемы для аутентификации"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Схема для регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    timezone: str = Field("UTC", max_length=64, description="IANA timezone, e.g. Europe/Moscow")


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


class AnonymousAuthRequest(BaseModel):
    """Схема для анонимной авторизации"""
    device_id: str = Field(..., min_length=8, max_length=128)
    platform: str | None = Field(None, description="ios|android")
    app_version: str | None = Field(None, max_length=32)


class AuthUserResponse(BaseModel):
    """Пользователь в auth-ответах"""
    id: str
    is_anonymous: bool
    email: EmailStr | None = None


class AnonymousAuthResponse(BaseModel):
    """Ответ анонимной авторизации"""
    access_token: str
    refresh_token: str
    user: AuthUserResponse


class LinkRequest(BaseModel):
    """Привязка Google/Apple"""
    provider: str = Field(..., description="google|apple")
    id_token: str = Field(..., min_length=10)


class ProviderIdentityResponse(BaseModel):
    """Данные провайдера"""
    provider: str
    provider_subject: str
    email: EmailStr | None = None


class LinkResponse(BaseModel):
    """Ответ при привязке"""
    linked: bool
    user: AuthUserResponse
    provider_identity: ProviderIdentityResponse
