"""Rule-based RAG memory pipeline for dream chunks and symbols."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Dream, DreamArchetype, DreamChunk, DreamSymbol, DreamSymbolEntity
from services.embedding_service import (
    EMBEDDING_MODEL_NAME,
    cosine_similarity,
    deserialize_embedding,
    request_embedding,
    serialize_embedding,
)

_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+|\n{2,}")
_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё]{3,}", re.UNICODE)
_ENTITY_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]{3,}", re.UNICODE)
_STOPWORDS = {
    "это", "как", "что", "когда", "потом", "после", "меня", "мне", "было", "были",
    "очень", "будто", "снова", "там", "здесь", "этот", "эта", "эти", "the", "and",
    "with", "from", "into", "that", "this", "have", "then", "they", "them", "was",
    "were", "about", "because", "while", "where", "который", "которая", "свой",
    "свои", "только", "через", "между", "вокруг", "себя", "него", "неё", "если",
    "или", "для", "над", "под", "без", "она", "они", "оно", "его", "её", "уже",
}
_ENTITY_STOPWORDS = _STOPWORDS | {
    "того", "где", "чуть", "есть", "находит", "находить", "следующий", "следующая",
    "следующее", "типа", "кстати", "потом", "вроде", "сон", "сны", "сна", "сне",
    "людей", "люди", "человек", "компании", "компания", "каких", "какой", "какая",
    "какие", "возможно", "возможный", "возможная", "возможные", "эльфов", "эльфы",
    "фей", "фея", "феи",
}
_ALLOWED_ENTITY_TYPES = {"symbol", "place", "figure", "object", "motif", "event"}
_SYMBOL_ALIASES = {
    "дома": "дом",
    "доме": "дом",
    "дому": "дом",
    "домой": "дом",
    "лесу": "лес",
    "леса": "лес",
    "воде": "вода",
    "воды": "вода",
    "моря": "море",
    "реки": "река",
    "машины": "машина",
    "машине": "машина",
    "машину": "машина",
    "зеркала": "зеркало",
    "лестнице": "лестница",
    "двери": "дверь",
    "тени": "тень",
    "children": "child",
    "houses": "house",
    "doors": "door",
    "stairs": "stair",
    "forest": "лес",
    "water": "вода",
    "house": "дом",
    "shadow": "тень",
    "door": "дверь",
    "mirror": "зеркало",
    "mother": "мать",
}


@dataclass
class ChunkCandidate:
    index: int
    text: str


@dataclass
class RetrievalContext:
    current_chunks: list[ChunkCandidate]
    current_symbols: list[str]
    related_chunks: list[dict]
    related_symbols: list[str]
    related_archetypes: list[str]

    def to_prompt_block(self) -> str:
        parts = [
            "SEMANTIC MEMORY CONTEXT",
            "Current dream chunks:",
        ]
        for chunk in self.current_chunks:
            parts.append(f"- chunk {chunk.index + 1}: {chunk.text}")
        if self.current_symbols:
            parts.append(f"Current symbols: {', '.join(self.current_symbols)}")
        if self.related_symbols:
            parts.append(f"Recurring symbols from memory: {', '.join(self.related_symbols)}")
        if self.related_archetypes:
            parts.append(f"Related archetypes from memory: {', '.join(self.related_archetypes)}")
        if self.related_chunks:
            # Sort by datetime for temporal ordering (oldest first)
            sorted_chunks = sorted(
                self.related_chunks,
                key=lambda item: item.get("dream_datetime", ""),
            )
            parts.append("Relevant past chunks (chronological order, oldest → newest):")
            for item in sorted_chunks:
                dt = item.get("dream_datetime") or item["dream_date"]
                parts.append(
                    f"- [{dt}] score {item['score']:.2f}; chunk {item['chunk_index'] + 1}; "
                    f"symbols={', '.join(item['symbol_overlap']) or 'none'}; text={item['text']}"
                )
        return "\n".join(parts)


@dataclass
class SymbolEntityCandidate:
    canonical_name: str
    display_label: str
    entity_type: str
    weight: float
    source_chunk_indexes: list[int]
    related_archetypes: list[str]


def chunk_dream_text(text: str, max_chunk_chars: int = 320) -> list[ChunkCandidate]:
    raw_parts = [part.strip() for part in _SENTENCE_RE.split(text or "") if part.strip()]
    if not raw_parts:
        return []

    chunks: list[str] = []
    current = ""
    for part in raw_parts:
        part = " ".join(part.split())
        if not current:
            current = part
            continue
        combined = f"{current} {part}"
        if len(combined) <= max_chunk_chars:
            current = combined
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)

    if not chunks:
        chunks = [" ".join(text.split())[:max_chunk_chars]]

    return [ChunkCandidate(index=i, text=chunk) for i, chunk in enumerate(chunks)]


def extract_symbols(text: str, limit: int = 8) -> list[str]:
    tokens = [_normalize_symbol(match.group(0)) for match in _TOKEN_RE.finditer(text or "")]
    filtered = [token for token in tokens if token and token not in _STOPWORDS]
    counts = Counter(filtered)
    return [name for name, _count in counts.most_common(limit)]


def _normalize_symbol(token: str) -> str:
    base = token.lower().strip()
    if not base:
        return ""
    return _SYMBOL_ALIASES.get(base, base)


def _sanitize_symbol_entities(
    raw_entities: list[dict[str, Any]] | None,
    *,
    dream_text: str,
    chunks: list[ChunkCandidate],
    archetypes_delta: dict[str, int],
    limit: int = 20,
) -> list[SymbolEntityCandidate]:
    if not raw_entities:
        return []

    chunk_indexes = {chunk.index for chunk in chunks}
    by_key: dict[tuple[str, str], SymbolEntityCandidate] = {}

    for item in raw_entities[:limit]:
        if not isinstance(item, dict):
            continue
        canonical = _normalize_symbol(str(item.get("canonical_name") or "").strip())
        if not _is_entity_token_allowed(canonical):
            continue

        display_label = _normalize_display_label(str(item.get("display_label") or ""))
        if not display_label:
            display_label = f"образ {canonical}"
        if len(display_label.split()) < 2:
            display_label = f"образ {canonical}"
        if len(display_label.split()) > 3:
            display_label = " ".join(display_label.split()[:3])
        if len(display_label.split()) < 1:
            continue

        entity_type = str(item.get("entity_type") or "symbol").strip().lower()
        if entity_type not in _ALLOWED_ENTITY_TYPES:
            entity_type = "symbol"

        try:
            weight = float(item.get("weight", 1.0))
        except Exception:
            weight = 1.0
        weight = max(0.05, min(1.0, weight))

        source_indexes_raw = item.get("source_chunk_indexes") or []
        source_indexes: list[int] = []
        if isinstance(source_indexes_raw, list):
            for idx in source_indexes_raw:
                try:
                    iv = int(idx)
                except Exception:
                    continue
                if iv in chunk_indexes:
                    source_indexes.append(iv)
        source_indexes = sorted(set(source_indexes))

        related_raw = item.get("related_archetypes") or []
        related_archetypes: list[str] = []
        if isinstance(related_raw, list):
            for value in related_raw:
                name = str(value or "").strip()
                if name:
                    related_archetypes.append(name)
        if not related_archetypes:
            inferred: list[str] = []
            for name, delta in archetypes_delta.items():
                key = str(name or "").strip()
                if not key:
                    continue
                try:
                    iv = int(delta or 0)
                except Exception:
                    continue
                if iv > 0:
                    inferred.append(key)
            related_archetypes = inferred[:4]

        key = (canonical, display_label)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = SymbolEntityCandidate(
                canonical_name=canonical,
                display_label=display_label,
                entity_type=entity_type,
                weight=weight,
                source_chunk_indexes=source_indexes,
                related_archetypes=related_archetypes[:4],
            )
            continue

        existing.weight = max(existing.weight, weight)
        existing.source_chunk_indexes = sorted(
            set(existing.source_chunk_indexes) | set(source_indexes)
        )
        existing.related_archetypes = list(
            dict.fromkeys(existing.related_archetypes + related_archetypes)
        )[:4]

    return sorted(by_key.values(), key=lambda item: item.weight, reverse=True)[:limit]


def _fallback_symbol_entities(
    chunks: list[ChunkCandidate],
    limit: int = 20,
) -> list[SymbolEntityCandidate]:
    candidate_chunks: dict[str, list[int]] = defaultdict(list)
    scores = Counter()
    for chunk in chunks:
        for symbol in extract_symbols(chunk.text, limit=6):
            canonical = _normalize_symbol(symbol)
            if not _is_entity_token_allowed(canonical):
                continue
            candidate_chunks[canonical].append(chunk.index)
            scores[canonical] += 1

    entities: list[SymbolEntityCandidate] = []
    for canonical, count in scores.most_common(limit):
        display_label = f"образ {canonical}"
        entities.append(
            SymbolEntityCandidate(
                canonical_name=canonical,
                display_label=display_label,
                entity_type="symbol",
                weight=max(0.1, min(1.0, count / 5)),
                source_chunk_indexes=sorted(set(candidate_chunks.get(canonical, []))),
                related_archetypes=[],
            )
        )
    return entities


def _normalize_display_label(value: str) -> str:
    words = []
    for token in _ENTITY_WORD_RE.findall((value or "").lower()):
        normalized = _normalize_symbol(token)
        if not _is_entity_token_allowed(normalized):
            continue
        words.append(normalized)
    if not words:
        return ""
    return " ".join(words[:3])


def _is_entity_token_allowed(token: str) -> bool:
    value = _normalize_symbol((token or "").strip().lower())
    if len(value) < 3:
        return False
    if value in _ENTITY_STOPWORDS:
        return False
    if value.isdigit():
        return False
    return True


async def rebuild_dream_memory(
    db: AsyncSession,
    dream: Dream,
    user_id: UUID,
    archetypes_delta: dict[str, int] | None = None,
    symbol_entities: list[dict[str, Any]] | None = None,
) -> RetrievalContext:
    current_chunks = chunk_dream_text(dream.content)
    current_symbols = extract_symbols(dream.content)
    retrieval = await build_retrieval_context(
        db,
        user_id=user_id,
        dream=dream,
        current_chunks=current_chunks,
        current_symbols=current_symbols,
        archetypes_delta=archetypes_delta or {},
    )

    await db.execute(delete(DreamSymbolEntity).where(DreamSymbolEntity.dream_id == dream.id))
    await db.execute(delete(DreamSymbol).where(DreamSymbol.dream_id == dream.id))
    await db.execute(delete(DreamChunk).where(DreamChunk.dream_id == dream.id))
    await db.execute(delete(DreamArchetype).where(DreamArchetype.dream_id == dream.id))

    chunk_rows: list[DreamChunk] = []
    for chunk in current_chunks:
        chunk_embedding = await request_embedding(chunk.text)
        chunk_rows.append(
            DreamChunk(
                dream_id=dream.id,
                user_id=user_id,
                chunk_index=chunk.index,
                text=chunk.text,
                embedding_text=serialize_embedding(chunk_embedding),
                embedding_model=EMBEDDING_MODEL_NAME,
                metadata_json={"symbols": extract_symbols(chunk.text, limit=5)},
                source_recorded_at=dream.recorded_at,
                source_created_at=dream.created_at,
                source_order=chunk.index,
            )
        )
    db.add_all(chunk_rows)
    await db.flush()
    chunk_by_index = {chunk.chunk_index: chunk for chunk in chunk_rows}

    symbols_by_chunk: dict[int, list[str]] = {
        chunk.index: extract_symbols(chunk.text, limit=5)
        for chunk in current_chunks
    }
    seen_symbols: set[tuple[str, int | None]] = set()
    for chunk in chunk_rows:
        for symbol in symbols_by_chunk.get(chunk.chunk_index, []):
            key = (symbol, chunk.chunk_index)
            if key in seen_symbols:
                continue
            seen_symbols.add(key)
            db.add(
                DreamSymbol(
                    user_id=user_id,
                    dream_id=dream.id,
                    chunk_id=chunk.id,
                    symbol_name=symbol,
                    weight=1,
                )
            )

    for symbol in current_symbols:
        key = (symbol, None)
        if key in seen_symbols:
            continue
        seen_symbols.add(key)
        db.add(
            DreamSymbol(
                user_id=user_id,
                dream_id=dream.id,
                chunk_id=None,
                symbol_name=symbol,
                weight=1,
            )
        )

    entities = _sanitize_symbol_entities(
        symbol_entities,
        dream_text=dream.content,
        chunks=current_chunks,
        archetypes_delta=archetypes_delta or {},
    )
    if not entities:
        entities = _fallback_symbol_entities(current_chunks)

    for entity in entities:
        linked = {
            chunk_by_index[idx].id
            for idx in entity.source_chunk_indexes
            if idx in chunk_by_index
        }
        if not linked:
            inferred_chunk_indexes = [
                idx
                for idx, symbols in symbols_by_chunk.items()
                if entity.canonical_name in symbols
            ]
            linked = {
                chunk_by_index[idx].id
                for idx in inferred_chunk_indexes
                if idx in chunk_by_index
            }
        if not linked:
            db.add(
                DreamSymbolEntity(
                    user_id=user_id,
                    dream_id=dream.id,
                    chunk_id=None,
                    canonical_name=entity.canonical_name,
                    display_label=entity.display_label,
                    entity_type=entity.entity_type,
                    weight=entity.weight,
                    related_archetypes_json=entity.related_archetypes,
                )
            )
            continue

        for chunk_id in linked:
            db.add(
                DreamSymbolEntity(
                    user_id=user_id,
                    dream_id=dream.id,
                    chunk_id=chunk_id,
                    canonical_name=entity.canonical_name,
                    display_label=entity.display_label,
                    entity_type=entity.entity_type,
                    weight=entity.weight,
                    related_archetypes_json=entity.related_archetypes,
                )
            )

    for name, delta in (archetypes_delta or {}).items():
        try:
            value = int(delta)
        except Exception:
            continue
        if value <= 0:
            continue
        db.add(
            DreamArchetype(
                user_id=user_id,
                dream_id=dream.id,
                archetype_name=name.strip(),
                delta=value,
            )
        )

    return retrieval


async def build_retrieval_context(
    db: AsyncSession,
    user_id: UUID,
    dream: Dream,
    current_chunks: list[ChunkCandidate] | None = None,
    current_symbols: list[str] | None = None,
    archetypes_delta: dict[str, int] | None = None,
    limit: int = 6,
) -> RetrievalContext:
    current_chunks = current_chunks or chunk_dream_text(dream.content)
    current_symbols = current_symbols or extract_symbols(dream.content)
    current_symbol_set = set(current_symbols)
    current_archetypes = {
        (name or "").strip()
        for name, delta in (archetypes_delta or {}).items()
        if (name or "").strip() and int(delta or 0) > 0
    }

    chunk_rows = list(
        (
            await db.execute(
                select(DreamChunk)
                .where(
                    DreamChunk.user_id == user_id,
                    DreamChunk.dream_id != dream.id,
                )
            )
        ).scalars().all()
    )

    symbol_rows = list(
        (
            await db.execute(
                select(DreamSymbol)
                .where(
                    DreamSymbol.user_id == user_id,
                    DreamSymbol.dream_id != dream.id,
                )
            )
        ).scalars().all()
    )
    symbols_by_chunk: dict[UUID | None, set[str]] = defaultdict(set)
    all_past_symbols: Counter[str] = Counter()
    for row in symbol_rows:
        symbols_by_chunk[row.chunk_id].add(row.symbol_name)
        all_past_symbols[row.symbol_name] += 1

    archetype_rows = list(
        (
            await db.execute(
                select(DreamArchetype)
                .where(
                    DreamArchetype.user_id == user_id,
                    DreamArchetype.dream_id != dream.id,
                )
            )
        ).scalars().all()
    )
    archetypes_by_dream: dict[UUID, set[str]] = defaultdict(set)
    for row in archetype_rows:
        archetypes_by_dream[row.dream_id].add(row.archetype_name)

    query_vecs: list[list[float]] = []
    for chunk in current_chunks:
        query_vecs.append(await request_embedding(chunk.text))
    now = datetime.now(timezone.utc)
    scored: list[dict] = []
    for chunk in chunk_rows:
        chunk_vec = deserialize_embedding(chunk.embedding_text)
        if chunk_vec is None:
            continue
        embedding_score = max((cosine_similarity(query_vec, chunk_vec) for query_vec in query_vecs), default=0.0)
        symbol_overlap = sorted(current_symbol_set & symbols_by_chunk.get(chunk.id, set()))
        archetype_overlap = sorted(current_archetypes & archetypes_by_dream.get(chunk.dream_id, set()))

        # Temporal recency bonus: 0.1 * exp(-days_ago / 30), half-life ~30 days
        chunk_date = getattr(chunk, "source_recorded_at", None) or chunk.created_at
        if chunk_date.tzinfo is None:
            days_ago = (now.replace(tzinfo=None) - chunk_date).total_seconds() / 86400
        else:
            days_ago = (now - chunk_date).total_seconds() / 86400
        recency_bonus = 0.1 * math.exp(-max(days_ago, 0) / 30)

        hybrid_score = embedding_score + (0.18 * len(symbol_overlap)) + (0.12 * len(archetype_overlap)) + recency_bonus
        if hybrid_score <= 0:
            continue

        # Store temporal info for prompt block
        chunk_datetime = chunk_date.strftime("%Y-%m-%d %H:%M") if chunk_date else ""
        scored.append(
            {
                "dream_id": chunk.dream_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "score": hybrid_score,
                "symbol_overlap": symbol_overlap,
                "archetype_overlap": archetype_overlap,
                "dream_date": dream.created_at.strftime("%d.%m.%Y"),
                "dream_datetime": chunk_datetime,
            }
        )

    dream_dates = {
        row.id: row.created_at.strftime("%d.%m.%Y")
        for row in (
            await db.execute(select(Dream).where(Dream.user_id == user_id))
        ).scalars().all()
    }
    for item in scored:
        item["dream_date"] = dream_dates.get(item["dream_id"], item["dream_date"])

    scored.sort(key=lambda item: item["score"], reverse=True)

    recurring_symbols = [
        symbol
        for symbol, _count in all_past_symbols.most_common(10)
        if symbol in current_symbol_set
    ]
    related_archetypes = sorted(
        {
            name
            for item in scored[:limit]
            for name in item["archetype_overlap"]
        }
    )

    return RetrievalContext(
        current_chunks=current_chunks,
        current_symbols=current_symbols,
        related_chunks=scored[:limit],
        related_symbols=recurring_symbols[:6],
        related_archetypes=related_archetypes[:6],
    )
