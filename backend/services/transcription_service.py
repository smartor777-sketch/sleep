"""Сервис транскрипции аудио через CometAPI с поддержкой чанкирования."""

import asyncio
import logging
from dataclasses import dataclass

import httpx

from config import settings
from services.audio_chunking_service import AudioChunkingError, split_audio

logger = logging.getLogger(__name__)

MAX_CONCURRENT_SEGMENTS = 3
SEGMENT_MAX_RETRIES = 3
SEGMENT_RETRY_BACKOFF = 2.0  # seconds, doubles each retry


class TranscriptionTransientError(Exception):
    """Retryable upstream/provider failure."""


class TranscriptionPermanentError(Exception):
    """Non-retryable upstream/provider failure."""


@dataclass
class TranscriptionResult:
    text: str
    partial: bool
    segments_total: int
    segments_ok: int
    segments_failed: int


def _get_api_key() -> str:
    api_key = settings.transcriptions_api_key or settings.embeddings_api_key
    if api_key is None:
        raise RuntimeError("Transcriptions API key is not configured")
    return api_key.get_secret_value()


async def _transcribe_single_segment(
    content: bytes,
    filename: str,
    content_type: str | None,
    language: str | None,
    prompt: str | None,
) -> str:
    """Send one segment to CometAPI with retries."""
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
        "file": (filename, content, content_type or "application/octet-stream")
    }
    headers = {"Authorization": f"Bearer {_get_api_key()}"}

    last_error: Exception | None = None
    for attempt in range(SEGMENT_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, data=data, files=files, headers=headers)
                response.raise_for_status()
                payload = response.json()
                text = payload.get("text", "").strip()
                if not text:
                    raise TranscriptionPermanentError("Empty transcription result")
                return text
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429 or status_code >= 500:
                last_error = e
                if attempt < SEGMENT_MAX_RETRIES - 1:
                    delay = SEGMENT_RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "Segment %s attempt %d/%d failed (%s), retrying in %.1fs",
                        filename, attempt + 1, SEGMENT_MAX_RETRIES, status_code, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                # Retries exhausted for a transient status code
                raise TranscriptionTransientError(
                    f"Segment {filename} failed after {SEGMENT_MAX_RETRIES} retries: {status_code}"
                ) from e
            raise TranscriptionPermanentError(
                f"Transcription provider error: {status_code}"
            ) from e
        except httpx.RequestError as e:
            last_error = e
            if attempt < SEGMENT_MAX_RETRIES - 1:
                delay = SEGMENT_RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    "Segment %s attempt %d/%d network error, retrying in %.1fs",
                    filename, attempt + 1, SEGMENT_MAX_RETRIES, delay,
                )
                await asyncio.sleep(delay)
                continue

    raise TranscriptionTransientError(
        f"Segment {filename} failed after {SEGMENT_MAX_RETRIES} retries"
    ) from last_error


async def transcribe_audio(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
) -> TranscriptionResult:
    """Transcribe audio with automatic chunking for long recordings.

    Short recordings (<=15s) go through as a single request.
    Long recordings are split into 15-sec segments and processed in parallel.
    """
    try:
        segments = split_audio(content, filename)
    except AudioChunkingError as e:
        raise TranscriptionPermanentError(str(e)) from e

    segments_total = len(segments)

    if segments_total == 1:
        text = await _transcribe_single_segment(
            segments[0][0], segments[0][1], content_type, language, prompt,
        )
        return TranscriptionResult(
            text=text,
            partial=False,
            segments_total=1,
            segments_ok=1,
            segments_failed=0,
        )

    # Parallel transcription with concurrency limit
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEGMENTS)
    results: list[str | None] = [None] * segments_total

    async def _process_segment(idx: int, seg_bytes: bytes, seg_name: str) -> None:
        async with semaphore:
            try:
                text = await _transcribe_single_segment(
                    seg_bytes, seg_name, content_type, language, prompt,
                )
                results[idx] = text
            except (TranscriptionTransientError, TranscriptionPermanentError) as e:
                logger.error("Segment %d (%s) failed: %s", idx, seg_name, e)
                results[idx] = None

    tasks = [
        _process_segment(i, seg_bytes, seg_name)
        for i, (seg_bytes, seg_name) in enumerate(segments)
    ]
    await asyncio.gather(*tasks)

    segments_ok = sum(1 for r in results if r is not None)
    segments_failed = segments_total - segments_ok

    if segments_ok == 0:
        raise TranscriptionTransientError(
            f"All {segments_total} segments failed transcription"
        )

    # Join successful segments in order
    text = " ".join(r for r in results if r is not None)

    return TranscriptionResult(
        text=text,
        partial=segments_failed > 0,
        segments_total=segments_total,
        segments_ok=segments_ok,
        segments_failed=segments_failed,
    )
