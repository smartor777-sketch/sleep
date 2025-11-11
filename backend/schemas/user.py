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
    gpt_role: str | None = Field(None, pattern="^(psychological|esoteric)$")
    self_description: str | None = Field(None, max_length=1000)
    timezone: str | None = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: UUID
    email_verified: bool
    is_active: bool
    is_admin: bool
    sub_type: str
    sub_expires_at: datetime | None
    gpt_role: str
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

