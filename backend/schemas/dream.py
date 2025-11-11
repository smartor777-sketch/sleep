"""Pydantic схемы для снов"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DreamBase(BaseModel):
    """Базовая схема сна"""
    title: str | None = Field(None, max_length=100)
    content: str = Field(..., min_length=10, max_length=10000)
    emoji: str = Field("", max_length=10)
    comment: str = Field("", max_length=256)


class DreamCreate(DreamBase):
    """Схема для создания сна"""
    pass


class DreamUpdate(BaseModel):
    """Схема для обновления сна"""
    title: str | None = Field(None, max_length=100)
    content: str | None = Field(None, min_length=10, max_length=10000)
    emoji: str | None = Field(None, max_length=10)
    comment: str | None = Field(None, max_length=256)


class DreamResponse(DreamBase):
    """Схема ответа с данными сна"""
    id: UUID
    user_id: UUID
    cover_url: str
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
    has_analysis: bool = False  # Есть ли анализ для этого сна
    
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

