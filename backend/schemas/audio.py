"""Pydantic схемы для аудио."""

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str = Field(..., min_length=1)
