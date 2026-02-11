"""Pydantic схемы для сообщений анализа"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class MessageSend(BaseModel):
    """Отправка сообщения в чат по сну"""
    dream_id: UUID = Field(..., description="ID сна")
    content: str = Field(..., min_length=1, max_length=5000, description="Текст сообщения")


class ChatMessageResponse(BaseModel):
    """Ответ с данными сообщения"""
    id: UUID
    user_id: UUID
    dream_id: UUID | None
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageListResponse(BaseModel):
    """Список сообщений"""
    messages: list[ChatMessageResponse]
    total: int


class ChatMessageTaskResponse(BaseModel):
    """Ответ при отправке сообщения (задача поставлена в очередь)"""
    task_id: str
    status: str = "processing"
    user_message: ChatMessageResponse
