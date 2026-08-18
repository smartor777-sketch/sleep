"""API эндпоинты уведомлений пользователя."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import CurrentUser, DatabaseSession
from schemas import NotificationAckResponse, NotificationListResponse, NotificationResponse
from services.notification_service import (
    SCOPE_USER,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_my_notifications(
    current_user: CurrentUser,
    db: DatabaseSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Список уведомлений текущего пользователя + число непрочитанных."""
    items, total, unread = await list_notifications(
        db,
        scope=SCOPE_USER,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
    )


@router.post("/read-all", response_model=NotificationAckResponse)
async def mark_all_read(
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Пометить все уведомления пользователя прочитанными."""
    marked = await mark_all_notifications_read(db, scope=SCOPE_USER, user_id=current_user.id)
    return NotificationAckResponse(ok=True, marked=marked)


@router.post("/{notification_id}/read", response_model=NotificationAckResponse)
async def mark_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Пометить одно уведомление прочитанным."""
    marked = await mark_notification_read(
        db,
        notification_id,
        scope=SCOPE_USER,
        user_id=current_user.id,
    )
    if not marked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return NotificationAckResponse(ok=True, marked=1)