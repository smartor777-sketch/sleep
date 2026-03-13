"""Сервис транскрипции аудио через CometAPI."""

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


class TranscriptionTransientError(Exception):
    """Retryable upstream/provider failure."""


class TranscriptionPermanentError(Exception):
    """Non-retryable upstream/provider failure."""


def _get_api_key() -> str:
    api_key = settings.transcriptions_api_key or settings.embeddings_api_key
    if api_key is None:
        raise RuntimeError("Transcriptions API key is not configured")
    return api_key.get_secret_value()


async def transcribe_audio(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
) -> str:
    """Отправить аудиофайл в CometAPI и вернуть распознанный текст."""
    url = f"{settings.transcriptions_base_url.rstrip('/')}/v1/audio/transcriptions"
    data = {
        "model": settings.transcriptions_model,
        "response_format": "json",
    }
    if language:
        data["language"] = language
    if prompt:
        data["prompt"] = prompt

    files = {
        "file": (
            filename,
            content,
            content_type or "application/octet-stream",
        )
    }
    headers = {"Authorization": f"Bearer {_get_api_key()}"}

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, data=data, files=files, headers=headers)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error from transcription provider: %s - %s",
            e.response.status_code,
            e.response.text,
        )
        status_code = e.response.status_code
        if status_code == 429 or status_code >= 500:
            raise TranscriptionTransientError(
                f"Transcription provider error: {status_code}"
            ) from e
        raise TranscriptionPermanentError(
            f"Transcription provider error: {status_code}"
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error to transcription provider: %s", e)
        raise TranscriptionTransientError("Failed to connect to transcription provider") from e

    text = payload.get("text", "").strip()
    if not text:
        raise TranscriptionPermanentError("Empty transcription result")
    return text
