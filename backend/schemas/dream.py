"""Pydantic схемы для снов"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DreamBase(BaseModel):
    """Базовая схема сна"""
    title: str | None = Field(None, max_length=64)
    content: str = Field(..., min_length=10, max_length=10000)
    emoji: str = Field("", max_length=10)
    comment: str = Field("", max_length=256)


class DreamCreate(DreamBase):
    """Схема для создания сна"""
    pass


class DreamUpdate(BaseModel):
    """Схема для обновления сна"""
    title: str | None = Field(None, max_length=64)
    content: str | None = Field(None, min_length=10, max_length=10000)
    emoji: str | None = Field(None, max_length=10)
    comment: str | None = Field(None, max_length=256)
    created_at: datetime | None = None


class DreamResponse(DreamBase):
    """Схема ответа с данными сна"""
    id: UUID
    user_id: UUID
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
    has_analysis: bool = False  # Есть ли анализ для этого сна
    analysis_status: str = "saved"
    analysis_error_message: str | None = None
    gradient_color_1: str | None = None
    gradient_color_2: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class DreamListResponse(BaseModel):
    """Схема для списка снов с пагинацией"""
    dreams: list[DreamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DreamSearchResponse(BaseModel):
    """Схема для результатов поиска"""
    dreams: list[DreamResponse]
    total: int
    query: str
    mode: str = "lexical"
