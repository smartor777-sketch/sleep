from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services import rag_service
from services.embedding_service import serialize_embedding

from tests.helpers import FakeDb, FakeResult


def test_chunk_extract_and_prompt_block():
    chunks = rag_service.chunk_dream_text("I entered the house. Then I saw water.\n\nA mirror appeared.", max_chunk_chars=25)
    assert len(chunks) >= 2
    symbols = rag_service.extract_symbols("В доме была вода и зеркало. The house had water too.")
    assert "дом" in symbols
    assert "вода" in symbols

    context = rag_service.RetrievalContext(
        current_chunks=chunks[:1],
        current_symbols=["дом"],
        related_chunks=[{"score": 0.9, "dream_date": "01.01.2025", "chunk_index": 0, "symbol_overlap": ["дом"], "text": "old chunk"}],
        related_symbols=["дом"],
        related_archetypes=["shadow"],
    )
    block = context.to_prompt_block()
    assert "SEMANTIC MEMORY CONTEXT" in block
    assert "Recurring symbols from memory: дом" in block
    assert "Related archetypes from memory: shadow" in block


@pytest.mark.asyncio
async def test_build_retrieval_context_scores_related_chunks(monkeypatch):
    async def fake_request_embedding(text):
        if "house" in text.lower():
            return [1.0, 0.0]
        return [0.0, 1.0]

    monkeypatch.setattr(rag_service, "request_embedding", fake_request_embedding)

    user_id = uuid4()
    other_dream_id = uuid4()
    current_dream = SimpleNamespace(
        id=uuid4(),
        content="House by the water",
        created_at=datetime(2025, 1, 3, tzinfo=timezone.utc),
    )
    stored_chunk = SimpleNamespace(
        id=uuid4(),
        dream_id=other_dream_id,
        user_id=user_id,
        chunk_index=0,
        text="House and door",
        embedding_text=serialize_embedding([1.0, 0.0]),
    )
    symbol_row = SimpleNamespace(chunk_id=stored_chunk.id, dream_id=other_dream_id, user_id=user_id, symbol_name="дом")
    archetype_row = SimpleNamespace(dream_id=other_dream_id, user_id=user_id, archetype_name="shadow")
    past_dream = SimpleNamespace(id=other_dream_id, created_at=datetime(2024, 12, 31, tzinfo=timezone.utc))
    db = FakeDb(
        execute_results=[
            FakeResult(scalars=[stored_chunk]),
            FakeResult(scalars=[symbol_row]),
            FakeResult(scalars=[archetype_row]),
            FakeResult(scalars=[past_dream, current_dream]),
        ]
    )

    retrieval = await rag_service.build_retrieval_context(
        db,
        user_id=user_id,
        dream=current_dream,
        current_symbols=["дом", "вода"],
        archetypes_delta={"shadow": 2},
    )

    assert retrieval.related_chunks
    assert retrieval.related_chunks[0]["dream_date"] == "31.12.2024"
    assert retrieval.related_symbols == ["дом"]
    assert retrieval.related_archetypes == ["shadow"]


@pytest.mark.asyncio
async def test_rebuild_dream_memory_persists_chunks_symbols_and_archetypes(monkeypatch):
    retrieval = rag_service.RetrievalContext([], [], [], [], [])

    async def fake_build_retrieval_context(*args, **kwargs):
        return retrieval

    async def fake_request_embedding(_text):
        return [0.1, 0.2]

    monkeypatch.setattr(rag_service, "build_retrieval_context", fake_build_retrieval_context)
    monkeypatch.setattr(rag_service, "request_embedding", fake_request_embedding)

    user_id = uuid4()
    dream = SimpleNamespace(id=uuid4(), content="Дом и вода. В зеркале тень.")
    db = FakeDb(execute_results=[FakeResult(), FakeResult(), FakeResult(), FakeResult()])

    result = await rag_service.rebuild_dream_memory(
        db,
        dream,
        user_id,
        archetypes_delta={"shadow": 2, "": 1, "anima": 0},
    )

    assert result is retrieval
    assert db.flushes == 1
    assert any(type(item).__name__ == "DreamChunk" for item in db.added)
    assert any(type(item).__name__ == "DreamSymbol" for item in db.added)
    assert any(type(item).__name__ == "DreamSymbolEntity" for item in db.added)
    assert any(type(item).__name__ == "DreamArchetype" for item in db.added)
