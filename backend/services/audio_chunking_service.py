"""Server-side audio chunking: split long audio into 15-sec segments via pydub."""

import io
import logging
import math

from pydub import AudioSegment

logger = logging.getLogger(__name__)

SEGMENT_DURATION_MS = 15_000  # 15 seconds


class AudioChunkingError(Exception):
    """Failed to decode or split audio."""


def split_audio(content: bytes, filename: str) -> list[tuple[bytes, str]]:
    """Split audio into <=15-sec segments.

    Returns list of (segment_bytes, segment_filename) tuples.
    Short files (<= 15s) are returned as a single segment (original bytes).
    """
    fmt = _guess_format(filename)

    try:
        audio = AudioSegment.from_file(io.BytesIO(content), format=fmt)
    except Exception as e:
        raise AudioChunkingError(f"Cannot decode audio ({fmt}): {e}") from e

    duration_ms = len(audio)
    if duration_ms == 0:
        raise AudioChunkingError("Audio file has zero duration")

    if duration_ms <= SEGMENT_DURATION_MS:
        return [(content, filename)]

    n_segments = math.ceil(duration_ms / SEGMENT_DURATION_MS)
    segments: list[tuple[bytes, str]] = []

    ext = fmt if fmt else "m4a"
    export_fmt = "ipod" if ext == "m4a" else ext

    for i in range(n_segments):
        start = i * SEGMENT_DURATION_MS
        end = min(start + SEGMENT_DURATION_MS, duration_ms)
        chunk = audio[start:end]

        buf = io.BytesIO()
        chunk.export(buf, format=export_fmt)
        seg_bytes = buf.getvalue()

        seg_name = f"segment_{i}.{ext}"
        segments.append((seg_bytes, seg_name))

    logger.info(
        "Split audio %s (%d ms) into %d segments of %d ms",
        filename, duration_ms, len(segments), SEGMENT_DURATION_MS,
    )
    return segments


def _guess_format(filename: str) -> str | None:
    """Guess pydub format from filename extension."""
    lower = filename.lower()
    if lower.endswith(".m4a"):
        return "m4a"
    if lower.endswith(".mp4"):
        return "mp4"
    if lower.endswith(".wav"):
        return "wav"
    if lower.endswith(".mp3"):
        return "mp3"
    if lower.endswith(".ogg") or lower.endswith(".opus"):
        return "ogg"
    if lower.endswith(".webm"):
        return "webm"
    if lower.endswith(".flac"):
        return "flac"
    return None
