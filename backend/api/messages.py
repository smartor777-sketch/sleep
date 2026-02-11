"""API эндпоинты для сообщений чата по снам"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from dependencies import DatabaseSession, CurrentUser
from schemas import (
    MessageSend,
    ChatMessageResponse,
    ChatMessageListResponse,
    ChatMessageTaskResponse,
)
from models import MessageRole
from services.message_service import create_message, get_messages_for_dream
from services.message_task_service import get_message_task_status
from services.dream_service import get_dream_by_id

router = APIRouter(prefix="/messages", tags=["Messages"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatMessageTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    data: MessageSend,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """
    Отправить follow-up сообщение в чат по сну.

    - Сохраняет user-сообщение
    - Запускает Celery-задачу для ответа LLM
    - Возвращает task_id для отслеживания
    """
    # Проверяем что сон существует и принадлежит пользователю
    dream = await get_dream_by_id(db, data.dream_id, current_user)
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found",
        )

    try:
        # Сохраняем user-сообщение
        user_msg = await create_message(
            db,
            user_id=current_user.id,
            dream_id=data.dream_id,
            role=MessageRole.USER.value,
            content=data.content,
        )

        # Запускаем Celery задачу для ответа
        from tasks import reply_to_dream_chat_task
        task = reply_to_dream_chat_task.delay(
            str(current_user.id),
            str(data.dream_id),
        )

        return ChatMessageTaskResponse(
            task_id=task.id,
            status="processing",
            user_message=ChatMessageResponse.model_validate(user_msg),
        )

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message",
        )


@router.get("/dream/{dream_id}", response_model=ChatMessageListResponse)
async def get_dream_messages(
    dream_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Получить сообщения чата по сну.

    - Отфильтровано по dream_id
    - Сортировка по дате (старые первые)
    """
    # Проверяем что сон принадлежит пользователю
    dream = await get_dream_by_id(db, dream_id, current_user)
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found",
        )

    messages, total = await get_messages_for_dream(
        db,
        user_id=current_user.id,
        dream_id=dream_id,
        limit=limit,
        offset=offset,
    )

    return ChatMessageListResponse(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total,
    )


@router.get("/task/{task_id}")
async def get_message_task(task_id: str, current_user: CurrentUser):
    """
    Получить статус задачи ответа LLM для follow-up сообщений.
    """
    return get_message_task_status(task_id)
