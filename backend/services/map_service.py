"""Dream map projection service."""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import numpy as np
from redis import asyncio as redis_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Dream, DreamArchetype, DreamChunk, DreamSymbol
from schemas.map import (
    DreamMapChunkDetailResponse,
    DreamMapClusterCenter,
    DreamMapClusterResponse,
    DreamMapMetaResponse,
    DreamMapNeighborResponse,
    DreamMapNodeResponse,
    DreamMapResponse,
)
from services.embedding_service import (
    cosine_similarity,
    deserialize_embedding,
    request_embedding,
    serialize_embedding,
)
from services.rag_service import rebuild_dream_memory

logger = logging.getLogger(__name__)

try:
    import umap  # type: ignore
except Exception:  # pragma: no cover
    umap = None

try:
    from sklearn.cluster import DBSCAN  # type: ignore
except Exception:  # pragma: no cover
    DBSCAN = None

MIN_CHUNKS_REQUIRED = 5
DEFAULT_STREAM_BATCH_SIZE = 20
_CACHE_PREFIX = "dream-map:v1"
_PREVIEW_LIMIT = 80

_ARCHETYPE_COLORS = {
    "Самость": "#F4B266",
    "Тень": "#506078",
    "Персона": "#7AA6FF",
    "Анима": "#E88CB7",
    "Анимус": "#5FA8A2",
    "Мать": "#C28EF6",
    "Отец": "#7C92B8",
    "Трикстер": "#F28F3B",
    "Герой": "#59C173",
    "Мудрец": "#8DA0CB",
    "Ребёнок": "#F8C15C",
    "Порог": "#B3B8C3",
    "Noise": "#98A2B3",
}

_ARCHETYPE_HINTS = {
    "вода": "Самость",
    "море": "Самость",
    "океан": "Самость",
    "река": "Самость",
    "дом": "Персона",
    "маска": "Персона",
    "зеркало": "Тень",
    "тень": "Тень",
    "монстр": "Тень",
    "девушка": "Анима",
    "женщина": "Анима",
    "мать": "Мать",
    "отец": "Отец",
    "мужчина": "Анимус",
    "воин": "Герой",
    "дорога": "Герой",
    "мост": "Порог",
    "дверь": "Порог",
    "лестница": "Порог",
    "ребёнок": "Ребёнок",
    "старик": "Мудрец",
    "учитель": "Мудрец",
    "шут": "Трикстер",
    "клоун": "Трикстер",
}

_POSITIVE_TOKENS = {
    "свет", "солнце", "радость", "спокойствие", "красивый", "свобода",
    "любовь", "мягкий", "тихий", "тепло", "hope", "light", "love", "calm",
}
_NEGATIVE_TOKENS = {
    "тьма", "страх", "ужас", "кровь", "смерть", "боль", "тюрьма", "падение",
    "монстр", "тревога", "panic", "fear", "death", "blood", "prison",
}


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class _ChunkRuntime:
    chunk: DreamChunk
    embedding: list[float]
    symbols: list[str]
    archetypes: list[str]
    dream: Dream


async def get_dream_map(
    db: AsyncSession,
    *,
    user_id: UUID,
    n_neighbors: int = 15,
    min_dist: float = 0.08,
    cluster_method: str = "dbscan",
    force_refresh: bool = False,
) -> DreamMapResponse:
    cache_key = _build_cache_key(
        user_id=user_id,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        cluster_method=cluster_method,
    )
    if not force_refresh:
        cached = await _get_cached_map(cache_key)
        if cached is not None:
            cached.meta.cached = True
            return cached

    runtimes = await _load_chunk_runtimes(db, user_id)
    if len(runtimes) < MIN_CHUNKS_REQUIRED:
        response = DreamMapResponse(
            nodes=[],
            clusters=[],
            meta=DreamMapMetaResponse(
                total_nodes=len(runtimes),
                total_clusters=0,
                cached=False,
                computed_with="umap3d" if umap is not None else "pca3d",
                cluster_method=cluster_method,
                min_chunks_required=MIN_CHUNKS_REQUIRED,
            ),
        )
        await _set_cached_map(cache_key, response)
        return response

    matrix = np.array([runtime.embedding for runtime in runtimes], dtype=float)
    projected_3d = _project_embeddings_3d(
        matrix,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
    )
    xy = _normalize_xy(projected_3d[:, :2])
    z = _normalize_axis(projected_3d[:, 2])
    labels = _cluster_points(xy, method=cluster_method)
    payloads = _build_cluster_payloads(runtimes, xy, z, labels)

    nodes = [
        DreamMapNodeResponse(
            id=str(runtime.chunk.id),
            dream_id=str(runtime.chunk.dream_id),
            x=float(xy[index][0]),
            y=float(xy[index][1]),
            z=float(z[index]),
            cluster_id=payload["cluster_id"],
            cluster_label=payload["label"],
            archetype_color=payload["color"],
            cosine_sim_to_center=_clamp_unit(payload["cosine_to_center"]),
            size_weight=payload["size_weight"],
            text_preview=_preview(runtime.chunk.text),
            date=runtime.dream.created_at.strftime("%Y-%m-%d"),
            emotion_valence=_emotion_valence(runtime.chunk.text),
            tokens=len(runtime.chunk.text.split()),
        )
        for index, (runtime, payload) in enumerate(zip(runtimes, payloads, strict=False))
    ]

    cluster_to_indices: dict[int, list[int]] = defaultdict(list)
    for index, payload in enumerate(payloads):
        cluster_to_indices[payload["cluster_id"]].append(index)

    clusters = [
        DreamMapClusterResponse(
            id=cluster_id,
            label=payloads[indexes[0]]["label"],
            color=payloads[indexes[0]]["color"],
            count=len(indexes),
            center=DreamMapClusterCenter(
                x=float(np.mean([xy[i][0] for i in indexes])),
                y=float(np.mean([xy[i][1] for i in indexes])),
            ),
        )
        for cluster_id, indexes in sorted(cluster_to_indices.items(), key=lambda item: item[0])
    ]

    response = DreamMapResponse(
        nodes=nodes,
        clusters=clusters,
        meta=DreamMapMetaResponse(
            total_nodes=len(nodes),
            total_clusters=len(clusters),
            cached=False,
            computed_with="umap3d" if umap is not None else "pca3d",
            cluster_method=cluster_method,
            min_chunks_required=MIN_CHUNKS_REQUIRED,
        ),
    )
    await _set_cached_map(cache_key, response)
    return response


async def get_map_chunk_detail(
    db: AsyncSession,
    *,
    user_id: UUID,
    chunk_id: UUID,
) -> DreamMapChunkDetailResponse | None:
    runtimes = await _load_chunk_runtimes(db, user_id)
    if not runtimes:
        return None
    runtime_by_id = {runtime.chunk.id: runtime for runtime in runtimes}
    runtime = runtime_by_id.get(chunk_id)
    if runtime is None:
        return None

    projection = await get_dream_map(db, user_id=user_id)
    node = next((item for item in projection.nodes if item.id == str(chunk_id)), None)
    if node is None:
        return None

    neighbors = sorted(
        (
            DreamMapNeighborResponse(
                chunk_id=str(other.chunk.id),
                dream_id=str(other.chunk.dream_id),
                text_preview=_preview(other.chunk.text),
                cosine_similarity=_clamp_unit(
                    cosine_similarity(runtime.embedding, other.embedding)
                ),
                date=other.dream.created_at.strftime("%Y-%m-%d"),
            )
            for other in runtimes
            if other.chunk.id != chunk_id
        ),
        key=lambda item: item.cosine_similarity,
        reverse=True,
    )[:6]

    return DreamMapChunkDetailResponse(
        id=str(runtime.chunk.id),
        dream_id=str(runtime.chunk.dream_id),
        cluster_id=node.cluster_id,
        cluster_label=node.cluster_label,
        archetype_color=node.archetype_color,
        text=runtime.chunk.text,
        date=runtime.dream.created_at.strftime("%Y-%m-%d"),
        emotion_valence=_emotion_valence(runtime.chunk.text),
        tokens=len(runtime.chunk.text.split()),
        z=node.z,
        size_weight=node.size_weight,
        neighbors=neighbors,
    )


async def stream_dream_map(
    db: AsyncSession,
    *,
    user_id: UUID,
    n_neighbors: int = 15,
    min_dist: float = 0.08,
    cluster_method: str = "dbscan",
    force_refresh: bool = False,
    batch_size: int = DEFAULT_STREAM_BATCH_SIZE,
):
    projection = await get_dream_map(
        db,
        user_id=user_id,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        cluster_method=cluster_method,
        force_refresh=force_refresh,
    )
    total = len(projection.nodes)
    if total == 0:
        yield {
            "type": "complete",
            "clusters": [cluster.model_dump() for cluster in projection.clusters],
            "meta": projection.meta.model_dump(),
        }
        return
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield {
            "type": "batch",
            "batch": [node.model_dump() for node in projection.nodes[start:end]],
            "progress": end / total,
            "total": total,
        }
    yield {
        "type": "complete",
        "clusters": [cluster.model_dump() for cluster in projection.clusters],
        "meta": projection.meta.model_dump(),
    }


async def invalidate_user_map_cache(user_id: UUID) -> None:
    client = await _get_redis_client()
    if client is None:
        return
    pattern = f"{_CACHE_PREFIX}:{user_id}:*"
    try:
        keys = [key async for key in client.scan_iter(match=pattern)]
        if keys:
            await client.delete(*keys)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to invalidate dream map cache for %s: %s", user_id, exc)
    finally:
        await _close_redis_client(client)


async def _load_chunk_runtimes(db: AsyncSession, user_id: UUID) -> list[_ChunkRuntime]:
    dreams = list((await db.execute(select(Dream).where(Dream.user_id == user_id))).scalars().all())
    if not dreams:
        return []

    chunks = list((await db.execute(select(DreamChunk).where(DreamChunk.user_id == user_id))).scalars().all())
    known_dream_ids = {chunk.dream_id for chunk in chunks}
    missing = [dream for dream in dreams if dream.content.strip() and dream.id not in known_dream_ids]
    if missing:
        for dream in missing:
            try:
                await rebuild_dream_memory(db, dream, user_id)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to backfill dream memory for map dream %s: %s", dream.id, exc)
        await db.commit()
        chunks = list((await db.execute(select(DreamChunk).where(DreamChunk.user_id == user_id))).scalars().all())

    symbols = list((await db.execute(select(DreamSymbol).where(DreamSymbol.user_id == user_id))).scalars().all())
    archetypes = list((await db.execute(select(DreamArchetype).where(DreamArchetype.user_id == user_id))).scalars().all())

    symbols_by_chunk: dict[UUID, list[str]] = defaultdict(list)
    for row in symbols:
        if row.chunk_id is not None:
            symbols_by_chunk[row.chunk_id].append(row.symbol_name)

    archetypes_by_dream: dict[UUID, list[str]] = defaultdict(list)
    for row in archetypes:
        archetypes_by_dream[row.dream_id].extend([row.archetype_name] * max(1, int(row.delta or 1)))

    dream_by_id = {dream.id: dream for dream in dreams}
    runtimes: list[_ChunkRuntime] = []
    changed = False
    for chunk in chunks:
        dream = dream_by_id.get(chunk.dream_id)
        if dream is None:
            continue
        embedding = deserialize_embedding(chunk.embedding_text)
        if embedding is None:
            try:
                embedding = await request_embedding(chunk.text)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to embed chunk %s for map: %s", chunk.id, exc)
                continue
            chunk.embedding_text = serialize_embedding(embedding)
            changed = True
        if not embedding:
            continue
        runtimes.append(
            _ChunkRuntime(
                chunk=chunk,
                embedding=embedding,
                symbols=symbols_by_chunk.get(chunk.id, []),
                archetypes=archetypes_by_dream.get(chunk.dream_id, []),
                dream=dream,
            )
        )
    if changed:
        await db.commit()
    return runtimes


def _project_embeddings_3d(matrix: np.ndarray, *, n_neighbors: int, min_dist: float) -> np.ndarray:
    if len(matrix) == 1:
        return np.array([[0.0, 0.0, 0.0]], dtype=float)
    if umap is not None and len(matrix) >= 4:
        reducer = umap.UMAP(
            n_components=3,
            metric="cosine",
            n_neighbors=max(2, min(n_neighbors, len(matrix) - 1)),
            min_dist=min_dist,
            random_state=42,
        )
        return reducer.fit_transform(matrix)
    return _pca_project_3d(matrix)


def _pca_project_3d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - np.mean(matrix, axis=0, keepdims=True)
    try:
        u, s, _vh = np.linalg.svd(centered, full_matrices=False)
        projected = u[:, :3] * s[:3]
    except np.linalg.LinAlgError:  # pragma: no cover
        projected = centered[:, :3]
    if projected.shape[1] < 3:
        projected = np.pad(projected, ((0, 0), (0, 3 - projected.shape[1])))
    return projected.astype(float)


def _normalize_xy(points: np.ndarray) -> np.ndarray:
    if len(points) == 0:
        return np.zeros((0, 2), dtype=float)
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    spans = np.where((maxs - mins) < 1e-9, 1.0, (maxs - mins))
    return ((points - mins) / spans).astype(float)


def _normalize_axis(values: np.ndarray) -> np.ndarray:
    if len(values) == 0:
        return np.zeros((0,), dtype=float)
    min_v = float(np.min(values))
    max_v = float(np.max(values))
    if abs(max_v - min_v) < 1e-9:
        return np.zeros_like(values, dtype=float)
    normalized = ((values - min_v) / (max_v - min_v)) * 2 - 1
    return normalized.astype(float)


def _cluster_points(points: np.ndarray, *, method: str) -> list[int]:
    if len(points) < MIN_CHUNKS_REQUIRED:
        return [-1 for _ in range(len(points))]
    if DBSCAN is None or method == "fallback":
        return _fallback_cluster(points)
    distances = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distances.append(float(np.linalg.norm(points[i] - points[j])))
    eps = 0.16
    if distances:
        eps = max(0.08, min(0.32, float(np.percentile(distances, 22))))
    model = DBSCAN(eps=eps, min_samples=max(2, min(5, len(points) // 10 or 2)))
    labels = model.fit_predict(points)
    if set(labels) == {-1}:
        return _fallback_cluster(points)
    return [int(item) for item in labels.tolist()]


def _fallback_cluster(points: np.ndarray) -> list[int]:
    labels: list[int] = []
    for x, y in points.tolist():
        if x < 0.33 and y < 0.5:
            labels.append(0)
        elif x >= 0.33 and x < 0.66:
            labels.append(1)
        elif y >= 0.5:
            labels.append(2)
        else:
            labels.append(3)
    return labels


def _build_cluster_payloads(
    runtimes: list[_ChunkRuntime],
    xy: np.ndarray,
    z_values: np.ndarray,
    labels: list[int],
) -> list[dict[str, Any]]:
    cluster_to_indices: dict[int, list[int]] = defaultdict(list)
    for index, cluster_id in enumerate(labels):
        cluster_to_indices[cluster_id].append(index)

    payloads: list[dict[str, Any]] = [{} for _ in runtimes]
    raw_size_weights: list[float] = [0.0 for _ in runtimes]

    for cluster_id, indexes in cluster_to_indices.items():
        embeddings = [runtimes[index].embedding for index in indexes]
        center_embedding = np.mean(np.array(embeddings, dtype=float), axis=0)
        label = _resolve_cluster_label([runtimes[index] for index in indexes], cluster_id)
        color = _ARCHETYPE_COLORS.get(label, _ARCHETYPE_COLORS["Noise"])
        for index in indexes:
            cosine_to_center = _clamp_unit(
                cosine_similarity(
                    runtimes[index].embedding,
                    center_embedding.tolist(),
                )
            )
            raw_size_weights[index] = cosine_to_center
            payloads[index] = {
                "cluster_id": cluster_id,
                "label": label,
                "color": color,
                "cosine_to_center": cosine_to_center,
            }

    size_array = np.array(raw_size_weights, dtype=float)
    min_size = float(np.min(size_array)) if len(size_array) else 0.0
    max_size = float(np.max(size_array)) if len(size_array) else 1.0
    span = max(1e-9, max_size - min_size)
    for index, payload in enumerate(payloads):
        payload["size_weight"] = float((size_array[index] - min_size) / span)
    return payloads


def _resolve_cluster_label(runtimes: list[_ChunkRuntime], cluster_id: int) -> str:
    if cluster_id == -1:
        return "Noise"
    archetypes = Counter(
        archetype
        for runtime in runtimes
        for archetype in runtime.archetypes
        if archetype.strip()
    )
    if archetypes:
        return archetypes.most_common(1)[0][0]
    hints = Counter(
        _ARCHETYPE_HINTS[symbol]
        for runtime in runtimes
        for symbol in runtime.symbols
        if symbol in _ARCHETYPE_HINTS
    )
    if hints:
        return hints.most_common(1)[0][0]
    return f"Pattern {cluster_id + 1}"


def _emotion_valence(text: str) -> float:
    tokens = [token.strip(".,!?;:()[]{}«»\"'").lower() for token in text.split()]
    score = 0
    for token in tokens:
        if token in _POSITIVE_TOKENS:
            score += 1
        if token in _NEGATIVE_TOKENS:
            score -= 1
    if not tokens:
        return 0.0
    value = score / max(4.0, len(tokens) / 8)
    return max(-1.0, min(1.0, value))


def _preview(text: str, limit: int = _PREVIEW_LIMIT) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _build_cache_key(
    *,
    user_id: UUID,
    n_neighbors: int,
    min_dist: float,
    cluster_method: str,
) -> str:
    params = json.dumps(
        {
            "n_neighbors": n_neighbors,
            "min_dist": min_dist,
            "cluster_method": cluster_method,
        },
        sort_keys=True,
    )
    digest = hashlib.sha1(params.encode("utf-8")).hexdigest()[:12]
    return f"{_CACHE_PREFIX}:{user_id}:{digest}"


async def _get_cached_map(cache_key: str) -> DreamMapResponse | None:
    client = await _get_redis_client()
    if client is None:
        return None
    try:
        raw = await client.get(cache_key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return DreamMapResponse.model_validate_json(raw)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to read dream map cache %s: %s", cache_key, exc)
        return None
    finally:
        await _close_redis_client(client)


async def _set_cached_map(cache_key: str, dream_map: DreamMapResponse) -> None:
    client = await _get_redis_client()
    if client is None:
        return
    try:
        await client.set(
            cache_key,
            dream_map.model_dump_json(),
            ex=settings.map_cache_ttl_seconds,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to write dream map cache %s: %s", cache_key, exc)
    finally:
        await _close_redis_client(client)


async def _get_redis_client():
    try:
        client = redis_asyncio.from_url(settings.redis_url, decode_responses=False)
        await client.ping()
        return client
    except Exception:  # pragma: no cover
        return None


async def _close_redis_client(client) -> None:
    close = getattr(client, "aclose", None) or getattr(client, "close", None)
    if close is None:
        return
    result = close()
    if result is not None:
        await result
