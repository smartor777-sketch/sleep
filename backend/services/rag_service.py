"""Rule-based RAG memory pipeline for dream chunks and symbols."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Dream, DreamArchetype, DreamChunk, DreamSymbol
from services.embedding_service import (
    EMBEDDING_MODEL_NAME,
    cosine_similarity,
    deserialize_embedding,
    request_embedding,
    serialize_embedding,
)

_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+|\n{2,}")
_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё]{3,}", re.UNICODE)
_STOPWORDS = {
    "это", "как", "что", "когда", "потом", "после", "меня", "мне", "было", "были",
    "очень", "будто", "снова", "там", "здесь", "этот", "эта", "эти", "the", "and",
    "with", "from", "into", "that", "this", "have", "then", "they", "them", "was",
    "were", "about", "because", "while", "where", "который", "которая", "свой",
    "свои", "только", "через", "между", "вокруг", "себя", "него", "неё", "если",
    "или", "для", "над", "под", "без", "она", "они", "оно", "его", "её", "уже",
}
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
            parts.append("Relevant past chunks:")
            for item in self.related_chunks:
                parts.append(
                    f"- score {item['score']:.2f}; dream {item['dream_date']}; chunk {item['chunk_index'] + 1}; "
                    f"symbols={', '.join(item['symbol_overlap']) or 'none'}; text={item['text']}"
                )
        return "\n".join(parts)


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


async def rebuild_dream_memory(
    db: AsyncSession,
    dream: Dream,
    user_id: UUID,
    archetypes_delta: dict[str, int] | None = None,
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
            )
        )
    db.add_all(chunk_rows)
    await db.flush()

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
    scored: list[dict] = []
    for chunk in chunk_rows:
        chunk_vec = deserialize_embedding(chunk.embedding_text)
        if chunk_vec is None:
            continue
        embedding_score = max((cosine_similarity(query_vec, chunk_vec) for query_vec in query_vecs), default=0.0)
        symbol_overlap = sorted(current_symbol_set & symbols_by_chunk.get(chunk.id, set()))
        archetype_overlap = sorted(current_archetypes & archetypes_by_dream.get(chunk.dream_id, set()))
        hybrid_score = embedding_score + (0.18 * len(symbol_overlap)) + (0.12 * len(archetype_overlap))
        if hybrid_score <= 0:
            continue
        scored.append(
            {
                "dream_id": chunk.dream_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "score": hybrid_score,
                "symbol_overlap": symbol_overlap,
                "archetype_overlap": archetype_overlap,
                "dream_date": dream.created_at.strftime("%d.%m.%Y"),
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
