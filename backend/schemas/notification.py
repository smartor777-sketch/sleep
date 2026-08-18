"""Pydantic схемы для уведомлений"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Уведомление пользователя или администратора."""
    id: UUID
    user_id: UUID | None = None
    scope: str
    type: str
    title: str
    body: str | None = None
    data: dict | None = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationAckResponse(BaseModel):
    ok: bool
    marked: int = 0