"""Pydantic схемы для аудио."""

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str = Field(..., min_length=1)
    partial: bool = Field(default=False)
    segments_total: int = Field(default=1, ge=1)
    segments_ok: int = Field(default=1, ge=0)
    segments_failed: int = Field(default=0, ge=0)
