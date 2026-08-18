"""Pydantic схемы для пользователя"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    timezone: str = "UTC"


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    first_name: str | None = None
    last_name: str | None = None
    timezone: str | None = None


class UserSettingsUpdate(BaseModel):
    """Схема для обновления настроек пользователя"""
    self_description: str | None = Field(None, max_length=1000)
    timezone: str | None = None
    onboarding_completed: bool | None = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: UUID
    email: EmailStr | None = None
    email_verified: bool
    is_active: bool
    is_admin: bool
    sub_type: str
    sub_expires_at: datetime | None
    self_description: str | None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Публичная схема пользователя (без чувствительных данных)"""
    id: UUID
    first_name: str | None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Профиль пользователя для /users/me"""
    about_me: str | None = None
    onboarding_completed: bool = False


class UserMeResponse(BaseModel):
    """Текущий пользователь"""
    id: UUID
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_anonymous: bool
    is_admin: bool = False
    email_verified: bool = False
    sub_type: str = "free"
    linked_providers: list[str]
    profile: UserProfileResponse

    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(BaseModel):
    """Создание пользователя админом."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None


class AdminUserUpdate(BaseModel):
    """Обновление пользователя админом."""
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None


class AdminUserListItem(BaseModel):
    """Строка списка пользователей для админки."""
    id: UUID
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    is_admin: bool
    is_anonymous: bool
    email_verified: bool
    sub_type: str
    created_at: datetime
    last_login_at: datetime | None = None
    dreams_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    total: int
    items: list[AdminUserListItem]


class AdminStatsResponse(BaseModel):
    total_users: int
    total_dreams: int
    total_analyses: int
    total_anonymous: int
    total_premium: int
    active_last_7d: int
    analysis_queue: int = 0  # Текущий размер очереди анализов (pending + processing)


class AdminResetPasswordResponse(BaseModel):
    user_id: UUID
    email: EmailStr | None = None
    new_password: str


class AdminDeleteUserResponse(BaseModel):
    user_id: UUID
    email: EmailStr | None = None
    message: str


class AdminEmailAuthSetting(BaseModel):
    email_auth_enabled: bool
