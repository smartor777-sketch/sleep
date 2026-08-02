"""Локальная транскрипция аудио через faster-whisper (on-device, свободно).

Модель грузится лениво при первом вызове и переиспользуется дальше.
Выбор модели/точности задаётся через конфиг:
  TRANSCRIPTIONS_PROVIDER=local (default)
  TRANSCRIPTIONS_LOCAL_MODEL=small        (small/turbo/large-v3/...)
  TRANSCRIPTIONS_LOCAL_COMPUTE=int8       (int8/float32/...)
faster-whisper использует PyAV (встроенный ffmpeg), поэтому системный
ffmpeg для декодирования не требуется.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from dataclasses import dataclass
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


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


# Ленивый синглтон модели — грузится один раз, защищён от гонок.
_model: Any = None
_model_lock = threading.Lock()


def _get_model() -> Any:
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
            "Loading faster-whisper model %r (device=cpu, compute=%s)", model_size, compute_type
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


async def transcribe_audio(
    *,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
) -> TranscriptionResult:
    """Транскрибировать аудио on-device через faster-whisper."""
    if not content:
        raise TranscriptionPermanentError("Audio file is empty")

    ext = _guess_ext(filename) or "wav"
    model = _get_model()

    # faster-whisper/PyAV надёжнее открывает файл с корректным расширением.
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        tmp.write(content)
        tmp.close()
        tmp_path = tmp.name

        # WhisperModel.transcribe синхронный, блокирует event loop — запускаем в потоке.
        segments_iter, info = await asyncio.to_thread(
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
                import os
                os.remove(tmp_path)
            except OSError:
                pass

    if not texts:
        raise TranscriptionTransientError("No speech detected in audio")

    result_text = " ".join(seg.text.strip() for seg in texts).strip()
    return TranscriptionResult(
        text=result_text,
        partial=False,
        segments_total=len(texts),
        segments_ok=len(texts),
        segments_failed=0,
    )