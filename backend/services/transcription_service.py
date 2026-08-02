"""Сервис транскрипции аудио.

Провайдеры (settings.transcriptions_provider):
  "google" — Google Gemini API (аудио на входе -> текст). Бесплатно,
             использует тот же ключ, что и эмбеддинги (embeddings_api_key).
  "local"  — on-device faster-whisper (free, offline, fallback).

Оба провайдера отдают единый TranscriptionResult, поэтому api/audio.py
никак не меняется.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUDIO_PROMPT = (
    "Транскрибируй речь из аудио на русском языке. "
    "Верни только распознанный текст без пояснений."
)


class TranscriptionTransientError(Exception):
    """Отсроченная/транзиентная ошибка (retryable)."""


class TranscriptionPermanentError(Exception):
    """Фатальная ошибка транскрибации (не retryable)."""


@dataclass
class TranscriptionResult:
    text: str
    partial: bool
    segments_total: int
    segments_ok: int
    segments_failed: int


# Ленивый синглтон локальной модели — грузится один раз, защищён от гонок.
_model: Any = None
_model_lock = threading.Lock()


def _get_gemini_key() -> str:
    key = settings.transcriptions_api_key or settings.embeddings_api_key
    if key is None:
        raise TranscriptionPermanentError(
            "Google transcription is not configured (no API key)"
        )
    return key.get_secret_value()


def _get_local_model() -> Any:
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise TranscriptionPermanentError(
                "faster-whisper is not installed (pip install faster-whisper)"
            ) from exc

        model_size = settings.transcriptions_local_model or "small"
        compute_type = settings.transcriptions_local_compute or "int8"
        logger.info(
            "Loading faster-whisper model %r (device=cpu, compute=%s)",
            model_size, compute_type,
        )
        try:
            _model = WhisperModel(
                model_size,
                device="cpu",
                compute_type=compute_type,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to load faster-whisper model %s", model_size)
            raise TranscriptionPermanentError(
                f"Failed to load local transcription model: {exc}"
            ) from exc
    return _model


def _guess_ext(filename: str) -> str:
    lower = (filename or "").lower()
    for ext in (".m4a", ".mp4", ".wav", ".mp3", ".ogg", ".opus", ".webm", ".flac", ".aac"):
        if lower.endswith(ext):
            return ext[1:]
    return "wav"


_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def _transcribe_google(
    *,
    filename: str,
    content: bytes,
    content_type: str | None,
    language: str | None,
    prompt: str | None,
) -> str:
    """Транскрибация через Google Gemini API с цепочкой fallback-моделей.

    Пробует transcriptions_model, затем transcriptions_fallback_models
    по очереди (например gemini-3.6-flash -> gemini-3.6-flash-lite ->
    gemini-3.5-flash) — как в llm_service, для устойчивости на free tier.
    """
    api_key = _get_gemini_key()
    base_url = settings.transcriptions_base_url.rstrip("/")

    ext = _guess_ext(filename)
    mime = content_type or f"audio/{ext}"
    encoded = base64.b64encode(content).decode("ascii")

    user_prompt = prompt or GOOGLE_AUDIO_PROMPT
    if language:
        user_prompt = (
            f"Транскрибируй речь из аудио (язык: {language}). "
            "Верни только распознанный текст без пояснений."
        )

    body = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt},
                    {"inline_data": {"mime_type": mime, "data": encoded}},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 4096,
        },
    }

    models = [settings.transcriptions_model, *settings.transcriptions_fallback_models]
    last_exc: Exception | None = None
    for model in models:
        try:
            return await _generate_once(
                api_key=api_key,
                base_url=base_url,
                model=model,
                body=body,
            )
        except (TranscriptionPermanentError, TranscriptionTransientError) as exc:
            last_exc = exc
            logger.warning(
                "Gemini transcription model %s failed (%s); fallbacks left: %d",
                model, exc, len(models) - models.index(model) - 1,
            )
    raise TranscriptionTransientError(
        f"All Gemini transcription models failed: {last_exc}"
    )


async def _generate_once(
    *,
    api_key: str,
    base_url: str,
    model: str,
    body: dict,
) -> str:
    """Один вызов generateContent с ретраями на транзиентные статусы."""
    url = f"{base_url}/models/{model}:generateContent"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    url,
                    params={"key": api_key},
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in _RETRYABLE_STATUS and attempt < 2:
                logger.warning(
                    "Gemini transcription %s attempt %d/3 failed (%s), retrying",
                    model, attempt + 1, status_code,
                )
                await asyncio.sleep(2 * (attempt + 1))
                last_error = e
                continue
            raise TranscriptionTransientError(
                f"Gemini transcription ({model}) failed ({status_code}): "
                f"{e.response.text[:300]}"
            ) from e
        except httpx.RequestError as e:
            if attempt < 2:
                logger.warning(
                    "Gemini transcription %s network error, retrying: %s",
                    model, e,
                )
                await asyncio.sleep(2 * (attempt + 1))
                last_error = e
                continue
            raise TranscriptionTransientError(
                f"Gemini transcription ({model}) network error: {e}"
            ) from e

        candidates = payload.get("candidates") or []
        if not candidates:
            reason = payload.get("promptFeedback") or {}
            raise TranscriptionPermanentError(
                f"Gemini returned no transcription (blocked): {reason}"
            )
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise TranscriptionTransientError(
                f"Gemini ({model}) returned empty transcription"
            )
        return text

    raise TranscriptionTransientError(
        f"Gemini transcription ({model}) failed after retries: {last_error}"
    )


async def _transcribe_local(
    *,
    filename: str,
    content: bytes,
    content_type: str | None,
    language: str | None,
    prompt: str | None,
) -> str:
    """Транскрибация on-device через faster-whisper."""
    if not content:
        raise TranscriptionPermanentError("Audio file is empty")

    ext = _guess_ext(filename) or "wav"
    model = _get_local_model()

    # faster-whisper/PyAV надёжнее открывает файл с корректным расширением.
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        tmp.write(content)
        tmp.close()
        tmp_path = tmp.name

        segments_iter, _info = await asyncio.to_thread(
            model.transcribe,
            tmp_path,
            language=language if language else None,
            initial_prompt=prompt or None,
            beam_size=5,
            vad_filter=False,
        )
        texts = list(await asyncio.to_thread(list, segments_iter))
    except TranscriptionPermanentError:
        raise
    except Exception as exc:
        logger.error("Local transcription failed: %s", exc)
        raise TranscriptionPermanentError(f"Cannot transcribe audio: {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    if not texts:
        raise TranscriptionTransientError("No speech detected in audio")

    return " ".join(seg.text.strip() for seg in texts).strip()


async def transcribe_audio(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
) -> TranscriptionResult:
    """Транскрибировать аудио через настроенный провайдер."""
    if not content:
        raise TranscriptionPermanentError("Audio file is empty")

    provider = (settings.transcriptions_provider or "google").lower()
    if provider == "google":
        text = await _transcribe_google(
            filename=filename,
            content=content,
            content_type=content_type,
            language=language,
            prompt=prompt,
        )
    elif provider == "local":
        text = await _transcribe_local(
            filename=filename,
            content=content,
            content_type=content_type,
            language=language,
            prompt=prompt,
        )
    else:
        raise TranscriptionPermanentError(
            f"Unknown transcription provider: {provider}"
        )

    return TranscriptionResult(
        text=text,
        partial=False,
        segments_total=1,
        segments_ok=1,
        segments_failed=0,
    )
