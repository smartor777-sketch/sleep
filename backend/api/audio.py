"""API эндпоинты для аудио."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from dependencies import CurrentUser
from schemas import TranscriptionResponse
from services.transcription_service import (
    TranscriptionPermanentError,
    TranscriptionTransientError,
    transcribe_audio,
)

router = APIRouter(prefix="/audio", tags=["Audio"])
logger = logging.getLogger(__name__)


@router.post("/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    language: str | None = Form(None),
    prompt: str | None = Form(None),
):
    """Принять локально записанное аудио и вернуть текст транскрипции."""
    del current_user

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty",
        )

    try:
        text = await transcribe_audio(
            filename=file.filename or "recording.m4a",
            content=content,
            content_type=file.content_type,
            language=language,
            prompt=prompt,
        )
        return TranscriptionResponse(text=text)
    except TranscriptionPermanentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except TranscriptionTransientError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        logger.error("Transcription config error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription service is not configured",
        ) from e
