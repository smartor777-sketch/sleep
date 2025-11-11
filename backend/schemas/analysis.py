"""Pydantic схемы для анализа снов"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AnalysisCreate(BaseModel):
    """Схема для создания анализа"""
    dream_id: UUID = Field(..., description="ID сна для анализа")


class AnalysisResponse(BaseModel):
    """Схема ответа с данными анализа"""
    id: UUID
    dream_id: UUID
    user_id: UUID
    result: str | None
    gpt_role: str
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    
    model_config = ConfigDict(from_attributes=True)


class AnalysisTaskResponse(BaseModel):
    """Схема ответа при создании задачи анализа"""
    analysis_id: UUID
    task_id: str
    status: str
    message: str


class AnalysisTaskStatusResponse(BaseModel):
    """Схема для статуса задачи анализа"""
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    result: str | None = None
    error: str | None = None
    progress: int | None = None  # Опционально для прогресса


class AnalysisListResponse(BaseModel):
    """Схема для списка анализов"""
    analyses: list[AnalysisResponse]
    total: int

