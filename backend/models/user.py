"""Модель пользователя"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class UserRole(str, enum.Enum):
    """Роли пользователей"""
    FREE = "free"
    PREMIUM = "premium"


class GPTRole(str, enum.Enum):
    """Роли для анализа снов"""
    PSYCHOLOGICAL = "psychological"
    ESOTERIC = "esoteric"


class User(Base):
    """Модель пользователя"""
    
    __tablename__ = "users"
    
    # Основные поля
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # nullable для OAuth2
    
    # Персональная информация
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Статусы
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Подписка
    sub_type: Mapped[str] = mapped_column(String(16), default="free", nullable=False)
    sub_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Настройки анализа
    gpt_role: Mapped[str] = mapped_column(String(20), default="psychological", nullable=False)
    self_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Связи
    dreams: Mapped[list["Dream"]] = relationship("Dream", back_populates="user", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

