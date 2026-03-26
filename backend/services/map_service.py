"""Dream map projection service built around symbol nodes."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import numpy as np
from numpy.linalg import norm as np_norm
from redis import asyncio as redis_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Dream, DreamArchetype, DreamChunk, DreamSymbol, DreamSymbolEntity
from schemas.map import (
    DreamMapClusterCenter,
    DreamMapClusterResponse,
    DreamMapMetaResponse,
    DreamMapNodeResponse,
    DreamMapOccurrenceResponse,
    DreamMapResponse,
    DreamMapSymbolDetailResponse,
)
from services.embedding_service import (
    cosine_similarity,
    deserialize_embedding,
    request_embedding,
    serialize_embedding,
)
from services.rag_service import _normalize_symbol, rebuild_dream_memory

logger = logging.getLogger(__name__)

try:
    import umap  # type: ignore
except Exception:  # pragma: no cover
    umap = None

try:
    from sklearn.cluster import DBSCAN  # type: ignore
except Exception:  # pragma: no cover
    DBSCAN = None

MIN_SYMBOLS_REQUIRED = 5
DEFAULT_STREAM_BATCH_SIZE = 20
_CACHE_PREFIX = "dream-map:v4"
_PREVIEW_LIMIT = 80
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]{2,}", re.UNICODE)
_LABEL_STOPWORDS = {
    "потом",
    "кстати",
    "типа",
    "кто",
    "мне",
    "меня",
    "было",
    "были",
    "такой",
    "такая",
    "вот",
    "это",
    "как",
    "что",
    "где",
    "когда",
    "или",
    "для",
    "ещё",
    "еще",
}
_GENERIC_SYMBOLS = {
    "где",
    "чуть",
    "следующий",
    "следующая",
    "следующее",
    "находит",
    "находить",
    "сон",
    "сны",
    "сна",
    "сне",
    "который",
    "которая",
    "которые",
    "какой",
    "какая",
    "какие",
    "какое",
    "потом",
    "кстати",
    "типа",
    "вроде",
    "такой",
    "такая",
    "такие",
    "единственное",
    "просто",
    "вообще",
    "сразу",
    "человек",
    "люди",
    "место",
    "штука",
    "вещь",
    "трекинг",
    "tracking",
    "gps",
    "людей",
    "люди",
    "человек",
    "компании",
    "компания",
    "каких",
    "какой",
    "какая",
    "какие",
    "возможно",
    "возможный",
    "возможная",
    "возможные",
    "эльфов",
    "эльфы",
    "фей",
    "фея",
    "феи",
}

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


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class _ChunkRuntime:
    chunk: DreamChunk
    embedding: list[float]
    symbols: list[str]
    archetypes: list[str]
    dream: Dream


@dataclass
class _SymbolOccurrence:
    entity: DreamSymbolEntity
    chunk: _ChunkRuntime | None


@dataclass
class _SymbolRuntime:
    id: str
    symbol_name: str
    display_label: str
    embedding: list[float]
    archetypes: list[str]
    occurrences: list[_SymbolOccurrence]
    preview_text: str
    last_seen_at: datetime
    dream_count: int
    occurrence_count: int


async def get_dream_map(
    db: AsyncSession,
    *,
    user_id: UUID,
    n_neighbors: int = 15,
    min_dist: float = 0.02,
    cluster_method: str = "dbscan",
    force_refresh: bool = False,
    dispersion: float = 1.0,
    jitter: float = 0.03,
) -> DreamMapResponse:
    cache_key = _build_cache_key(
        user_id=user_id,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        cluster_method=cluster_method,
        dispersion=dispersion,
        jitter=jitter,
    )
    if not force_refresh:
        cached = await _get_cached_map(cache_key)
        if cached is not None:
            cached.meta.cached = True
            return cached

    runtimes = await _load_symbol_runtimes(db, user_id)
    if len(runtimes) < MIN_SYMBOLS_REQUIRED:
        response = DreamMapResponse(
            nodes=[],
            clusters=[],
            archetype_filters=[],
            meta=DreamMapMetaResponse(
                total_nodes=len(runtimes),
                total_clusters=0,
                cached=False,
                computed_with="umap3d" if umap is not None else "pca3d",
                cluster_method=cluster_method,
                min_nodes_required=MIN_SYMBOLS_REQUIRED,
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
    if jitter > 0:
        xy = _apply_deterministic_jitter(xy, runtimes, user_id, amplitude=jitter)
    z = _normalize_axis(projected_3d[:, 2])
    labels = _cluster_points(xy, method=cluster_method)
    payloads = _build_cluster_payloads(runtimes, labels)

    nodes = [
        DreamMapNodeResponse(
            id=runtime.id,
            symbol_name=runtime.symbol_name,
            display_label=runtime.display_label,
            x=float(xy[index][0]),
            y=float(xy[index][1]),
            z=float(z[index]),
            cluster_id=payload["cluster_id"],
            cluster_label=payload["label"],
            archetype_color=payload["color"],
            cosine_sim_to_center=_clamp_unit(payload["cosine_to_center"]),
            size_weight=payload["size_weight"],
            occurrence_count=runtime.occurrence_count,
            dream_count=runtime.dream_count,
            last_seen_at=runtime.last_seen_at.strftime("%Y-%m-%d"),
            preview_text=runtime.preview_text,
            related_archetypes=_top_values(runtime.archetypes, limit=4),
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
        archetype_filters=sorted(
            {
                archetype
                for node in nodes
                for archetype in node.related_archetypes
                if archetype.strip()
            }
        ),
        meta=DreamMapMetaResponse(
            total_nodes=len(nodes),
            total_clusters=len(clusters),
            cached=False,
            computed_with="umap3d" if umap is not None else "pca3d",
            cluster_method=cluster_method,
            min_nodes_required=MIN_SYMBOLS_REQUIRED,
        ),
    )
    await _set_cached_map(cache_key, response)
    return response


async def get_map_symbol_detail(
    db: AsyncSession,
    *,
    user_id: UUID,
    symbol_id: str,
) -> DreamMapSymbolDetailResponse | None:
    runtimes = await _load_symbol_runtimes(db, user_id)
    runtime_by_id = {runtime.id: runtime for runtime in runtimes}
    runtime = runtime_by_id.get(symbol_id)
    if runtime is None:
        return None

    projection = await get_dream_map(db, user_id=user_id)
    node = next((item for item in projection.nodes if item.id == symbol_id), None)
    if node is None:
        return None

    occurrences_sorted = sorted(
        runtime.occurrences,
        key=lambda item: (
            item.chunk.dream.created_at
            if item.chunk is not None
            else item.entity.created_at
        ),
        reverse=True,
    )
    occurrence_items = [
        DreamMapOccurrenceResponse(
            dream_id=str(item.entity.dream_id),
            date=(
                item.chunk.dream.created_at.strftime("%Y-%m-%d")
                if item.chunk is not None
                else item.entity.created_at.strftime("%Y-%m-%d")
            ),
            text_preview=(
                _preview(item.chunk.chunk.text)
                if item.chunk is not None
                else runtime.display_label
            ),
        )
        for item in occurrences_sorted[:6]
    ]
    if not occurrences_sorted:
        return None

    dream_ids = {item.entity.dream_id for item in occurrences_sorted}
    related_symbols = Counter()
    if dream_ids:
        rows = list(
            (
                await db.execute(
                    select(DreamSymbolEntity).where(
                        DreamSymbolEntity.user_id == user_id,
                        DreamSymbolEntity.dream_id.in_(list(dream_ids)),
                    )
                )
            ).scalars().all()
        )
        for row in rows:
            canonical = _normalize_symbol((row.canonical_name or "").strip().lower())
            if not canonical or canonical == runtime.symbol_name:
                continue
            if not _is_symbol_candidate(canonical):
                continue
            label = _clean_display_label(row.display_label, canonical)
            if len(label.split()) < 2:
                continue
            if label == runtime.display_label:
                continue
            related_symbols[label] += 1

    return DreamMapSymbolDetailResponse(
        id=runtime.id,
        symbol_name=runtime.symbol_name,
        display_label=runtime.display_label,
        primary_dream_id=str(occurrences_sorted[0].entity.dream_id),
        cluster_id=node.cluster_id,
        cluster_label=node.cluster_label,
        archetype_color=node.archetype_color,
        occurrence_count=runtime.occurrence_count,
        dream_count=runtime.dream_count,
        z=node.z,
        size_weight=node.size_weight,
        last_seen_at=runtime.last_seen_at.strftime("%Y-%m-%d"),
        related_archetypes=_top_values(runtime.archetypes, limit=4),
        related_symbols=[name for name, _count in related_symbols.most_common(5)],
        occurrences=occurrence_items,
    )


async def stream_dream_map(
    db: AsyncSession,
    *,
    user_id: UUID,
    n_neighbors: int = 15,
    min_dist: float = 0.02,
    cluster_method: str = "dbscan",
    force_refresh: bool = False,
    batch_size: int = DEFAULT_STREAM_BATCH_SIZE,
    dispersion: float = 1.0,
    jitter: float = 0.03,
):
    projection = await get_dream_map(
        db,
        user_id=user_id,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        cluster_method=cluster_method,
        force_refresh=force_refresh,
        dispersion=dispersion,
        jitter=jitter,
    )
    total = len(projection.nodes)
    if total == 0:
        yield {
            "type": "complete",
            "clusters": [cluster.model_dump() for cluster in projection.clusters],
            "archetype_filters": projection.archetype_filters,
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
        "archetype_filters": projection.archetype_filters,
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


async def _load_symbol_runtimes(db: AsyncSession, user_id: UUID) -> list[_SymbolRuntime]:
    chunk_runtimes = await _load_chunk_runtimes(db, user_id)
    if not chunk_runtimes:
        return []

    entity_rows = list(
        (
            await db.execute(
                select(DreamSymbolEntity).where(DreamSymbolEntity.user_id == user_id)
            )
        ).scalars().all()
    )
    if not entity_rows:
        return []

    chunk_runtime_by_id = {runtime.chunk.id: runtime for runtime in chunk_runtimes}
    dream_to_chunks: dict[UUID, list[_ChunkRuntime]] = defaultdict(list)
    for runtime in chunk_runtimes:
        dream_to_chunks[runtime.chunk.dream_id].append(runtime)

    occurrences_by_symbol: dict[str, list[_SymbolOccurrence]] = defaultdict(list)

    for row in entity_rows:
        symbol_name = _normalize_symbol((row.canonical_name or "").strip().lower())
        if not _is_symbol_candidate(symbol_name):
            continue
        chunk_runtime = None
        if row.chunk_id is not None:
            chunk_runtime = chunk_runtime_by_id.get(row.chunk_id)
        else:
            candidates = dream_to_chunks.get(row.dream_id, [])
            if candidates:
                chunk_runtime = candidates[0]
        occurrences_by_symbol[symbol_name].append(
            _SymbolOccurrence(entity=row, chunk=chunk_runtime)
        )

    runtimes: list[_SymbolRuntime] = []
    for symbol_name, occurrences in occurrences_by_symbol.items():
        if not occurrences:
            continue
        display_labels = Counter()
        vectors: list[list[float]] = []
        previews: list[str] = []
        timestamps: list[datetime] = []
        dream_ids: set[UUID] = set()
        archetypes = [
            archetype
            for item in occurrences
            for archetype in (
                list(item.entity.related_archetypes_json or [])
                + (item.chunk.archetypes if item.chunk is not None else [])
            )
            if archetype.strip()
        ]
        for item in occurrences:
            dream_ids.add(item.entity.dream_id)
            timestamps.append(item.entity.created_at)
            if item.chunk is not None:
                vectors.append(item.chunk.embedding)
                previews.append(item.chunk.chunk.text)
                timestamps.append(item.chunk.dream.created_at)

            label = _clean_display_label(item.entity.display_label, symbol_name)
            if label:
                display_labels[label] += 1

        if display_labels:
            display_label = display_labels.most_common(1)[0][0]
        else:
            display_label = _build_symbol_display_label(symbol_name, occurrences)
        if not display_label:
            display_label = f"мотив {symbol_name}"

        if vectors:
            embedding = np.mean(np.array(vectors, dtype=float), axis=0).tolist()
        else:
            try:
                embedding = await request_embedding(display_label)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to embed symbol entity '%s': %s", symbol_name, exc)
                continue

        preview_text = _preview(previews[0] if previews else display_label)
        last_seen_at = max(timestamps) if timestamps else datetime.utcnow()

        runtimes.append(
            _SymbolRuntime(
                id=_build_symbol_id(user_id, symbol_name),
                symbol_name=symbol_name,
                display_label=display_label,
                embedding=embedding,
                archetypes=archetypes,
                occurrences=sorted(
                    occurrences,
                    key=lambda item: (
                        item.chunk.dream.created_at
                        if item.chunk is not None
                        else item.entity.created_at
                    ),
                    reverse=True,
                ),
                preview_text=preview_text,
                last_seen_at=last_seen_at,
                dream_count=len(dream_ids),
                occurrence_count=len(occurrences),
            )
        )

    runtimes.sort(
        key=lambda item: (item.dream_count, item.occurrence_count, item.last_seen_at),
        reverse=True,
    )
    return runtimes


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
        chunk_symbols = list(dict.fromkeys(symbols_by_chunk.get(chunk.id, [])))
        if not chunk_symbols and isinstance(chunk.metadata_json, dict):
            raw = chunk.metadata_json.get("symbols") or []
            chunk_symbols = [str(item).strip() for item in raw if str(item).strip()]
        runtimes.append(
            _ChunkRuntime(
                chunk=chunk,
                embedding=embedding,
                symbols=chunk_symbols,
                archetypes=archetypes_by_dream.get(chunk.dream_id, []),
                dream=dream,
            )
        )
    if changed:
        await db.commit()
    return runtimes


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalization. Prevents near-zero rows from exploding."""
    norms = np_norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms < 1e-9, 1.0, norms)
    return matrix / norms


def _project_embeddings_3d(matrix: np.ndarray, *, n_neighbors: int, min_dist: float) -> np.ndarray:
    if len(matrix) == 1:
        return np.array([[0.0, 0.0, 0.0]], dtype=float)
    normed = _l2_normalize(matrix)
    if umap is not None and len(normed) >= 4:
        reducer = umap.UMAP(
            n_components=3,
            metric="cosine",
            n_neighbors=max(2, min(n_neighbors, len(normed) - 1)),
            min_dist=min_dist,
            random_state=42,
        )
        return reducer.fit_transform(normed)
    return _pca_project_3d(normed)


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


def _apply_deterministic_jitter(
    xy: np.ndarray,
    runtimes: list[_SymbolRuntime],
    user_id: UUID,
    amplitude: float = 0.03,
) -> np.ndarray:
    """Deterministic jitter seeded by md5(user_id:symbol_name), amplitude ~3%."""
    result = xy.copy()
    for i, runtime in enumerate(runtimes):
        seed_str = f"{user_id}:{runtime.symbol_name}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        dx = (rng.random() * 2 - 1) * amplitude
        dy = (rng.random() * 2 - 1) * amplitude
        result[i][0] = np.clip(result[i][0] + dx, 0.0, 1.0)
        result[i][1] = np.clip(result[i][1] + dy, 0.0, 1.0)
    return result


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
    if len(points) < MIN_SYMBOLS_REQUIRED:
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
    runtimes: list[_SymbolRuntime],
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
            prominence = (
                (runtimes[index].dream_count * 0.7) +
                (runtimes[index].occurrence_count * 0.3)
            )
            raw_size_weights[index] = prominence + cosine_to_center
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


def _resolve_cluster_label(runtimes: list[_SymbolRuntime], cluster_id: int) -> str:
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
        _ARCHETYPE_HINTS[runtime.symbol_name]
        for runtime in runtimes
        if runtime.symbol_name in _ARCHETYPE_HINTS
    )
    if hints:
        return hints.most_common(1)[0][0]
    return f"Pattern {cluster_id + 1}"


def _build_symbol_display_label(
    symbol_name: str,
    occurrences: list[_SymbolOccurrence],
) -> str:
    phrases = Counter()
    for occurrence in occurrences:
        if occurrence.chunk is None:
            continue
        words = [match.group(0).lower() for match in _WORD_RE.finditer(occurrence.chunk.chunk.text)]
        normalized = [_normalize_symbol(word) for word in words]
        for index, token in enumerate(normalized):
            if token != symbol_name:
                continue
            left = words[index - 1] if index > 0 else ""
            current = words[index]
            right = words[index + 1] if index + 1 < len(words) else ""
            parts = [
                part
                for part in [left, current, right]
                if part and part not in _LABEL_STOPWORDS
            ]
            if len(parts) >= 2:
                phrases[" ".join(parts[:3])] += 1
            elif current:
                phrases[current] += 1
    if phrases:
        label = sorted(
            phrases.items(),
            key=lambda item: (item[1], len(item[0].split()), len(item[0])),
            reverse=True,
        )[0][0]
        normalized = " ".join(label.strip().split()[:3])
        if len(normalized.split()) >= 2:
            return normalized

    contexts = Counter()
    for occurrence in occurrences:
        if occurrence.chunk is None:
            continue
        for word in _WORD_RE.findall(occurrence.chunk.chunk.text.lower()):
            normalized = _normalize_symbol(word)
            if normalized == symbol_name or normalized in _LABEL_STOPWORDS:
                continue
            contexts[normalized] += 1
    if contexts:
        other, _count = contexts.most_common(1)[0]
        label = f"{other} {symbol_name}".strip()
        if len(label.split()) >= 2:
            return label
    return f"мотив {symbol_name}"


def _clean_display_label(raw: str, symbol_name: str) -> str:
    words = []
    for word in _WORD_RE.findall((raw or "").lower()):
        normalized = _normalize_symbol(word)
        if not normalized:
            continue
        if normalized in _LABEL_STOPWORDS or normalized in _GENERIC_SYMBOLS:
            continue
        words.append(normalized)
    if not words:
        return ""
    words = words[:3]
    if len(words) == 1:
        if words[0] == symbol_name:
            return f"мотив {symbol_name}"
        return f"{words[0]} {symbol_name}"[:32].strip()
    return " ".join(words)


def _is_symbol_candidate(symbol_name: str) -> bool:
    normalized = _normalize_symbol((symbol_name or "").strip().lower())
    if not normalized or len(normalized) < 3:
        return False
    if normalized in _GENERIC_SYMBOLS or normalized in _LABEL_STOPWORDS:
        return False
    if normalized.isdigit():
        return False
    return True


def _preview(text: str, limit: int = _PREVIEW_LIMIT) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _build_symbol_id(user_id: UUID, symbol_name: str) -> str:
    digest = hashlib.sha1(f"{user_id}:{symbol_name}".encode("utf-8")).hexdigest()
    return digest[:24]


def _top_values(values: list[str], *, limit: int) -> list[str]:
    counts = Counter(value for value in values if value.strip())
    return [name for name, _count in counts.most_common(limit)]


def _build_cache_key(
    *,
    user_id: UUID,
    n_neighbors: int,
    min_dist: float,
    cluster_method: str,
    dispersion: float = 1.0,
    jitter: float = 0.03,
) -> str:
    params = json.dumps(
        {
            "n_neighbors": n_neighbors,
            "min_dist": min_dist,
            "cluster_method": cluster_method,
            "dispersion": dispersion,
            "jitter": jitter,
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
    if client is None:
        return
    try:
        await client.close()
    except Exception:  # pragma: no cover
        pass
