"""Сервис для работы с настройками приложения (app_settings)."""

import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AppSetting

logger = logging.getLogger(__name__)

EMAIL_AUTH_ENABLED = "email_auth_enabled"


def _as_str(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


async def get_setting(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(AppSetting.value).where(AppSetting.key == key))
    return result.scalar_one_or_none()


async def get_setting_bool(db: AsyncSession, key: str, default: bool = False) -> bool:
    return _as_bool(await get_setting(db, key), default)


async def set_setting(db: AsyncSession, key: str, value: Any) -> None:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    str_value = _as_str(value)
    if row is None:
        db.add(AppSetting(key=key, value=str_value))
    else:
        row.value = str_value
    await db.commit()


async def email_auth_enabled(db: AsyncSession) -> bool:
    """Включён ли режим авторизации по email."""
    return await get_setting_bool(db, EMAIL_AUTH_ENABLED, default=True)