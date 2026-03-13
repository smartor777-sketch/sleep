"""Embedding utilities backed by CometAPI embeddings."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Dream

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = settings.embeddings_model


def serialize_embedding(vec: list[float]) -> str:
    return json.dumps(vec, separators=(",", ":"))


def deserialize_embedding(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    out: list[float] = []
    for item in data:
        try:
            out.append(float(item))
        except Exception:
            return None
    return out


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = float(sum(x * y for x, y in zip(a, b)))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_dream_embedding_text(dream: Dream) -> str:
    parts = [dream.title or "", dream.content, dream.comment or ""]
    return " ".join(p for p in parts if p).strip()


async def request_embedding(text: str) -> list[float]:
    clean = (text or "").strip()
    if not clean:
        return []
    api_key = settings.embeddings_api_key.get_secret_value() if settings.embeddings_api_key else None
    if not api_key:
        raise RuntimeError("EMBEDDINGS_API_KEY is not configured")

    url = f"{settings.embeddings_base_url.rstrip('/')}/v1/embeddings"
    payload = {
        "model": settings.embeddings_model,
        "input": clean,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error("Embedding provider returned %s: %s", exc.response.status_code, exc.response.text)
        raise RuntimeError(f"embedding_http_{exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error("Embedding provider request failed: %s", exc)
        raise RuntimeError("embedding_request_failed") from exc

    data = response.json()
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise RuntimeError("embedding_missing_data")
    embedding = items[0].get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError("embedding_missing_vector")

    out: list[float] = []
    for item in embedding:
        try:
            out.append(float(item))
        except Exception as exc:
            raise RuntimeError("embedding_invalid_vector") from exc
    return out


async def recalculate_dream_embedding(db: AsyncSession, dream: Dream) -> None:
    text = build_dream_embedding_text(dream)
    vec = await request_embedding(text)
    dream.embedding_text = serialize_embedding(vec)
    dream.embedding_model = settings.embeddings_model
    dream.embedding_updated_at = datetime.now(timezone.utc)
    db.add(dream)
