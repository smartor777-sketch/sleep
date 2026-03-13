from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from schemas import DreamCreate, DreamUpdate
from services import dream_service
from services.embedding_service import serialize_embedding

from tests.helpers import FakeDb, FakeResult


@pytest.mark.asyncio
async def test_get_user_timezone_falls_back_to_utc():
    user = SimpleNamespace(id=uuid4(), timezone="Bad/Zone")
    tz = await dream_service.get_user_timezone(user)
    assert str(tz) == "UTC"


@pytest.mark.asyncio
async def test_create_dream_checks_limit_and_builds_embedding(monkeypatch):
    async def fake_check_dreams_limit(_db, _user):
        return True

    calls = {"embed": 0, "rag": 0}

    async def fake_recalculate(_db, dream):
        calls["embed"] += 1
        dream.embedding_text = "[]"

    async def fake_rebuild(_db, dream, user_id):
        calls["rag"] += 1
        assert dream.user_id == user_id

    monkeypatch.setattr(dream_service, "check_dreams_limit", fake_check_dreams_limit)
    monkeypatch.setattr(dream_service, "recalculate_dream_embedding", fake_recalculate)
    monkeypatch.setattr(dream_service, "rebuild_dream_memory", fake_rebuild)
    db = FakeDb()
    user = SimpleNamespace(id=uuid4())

    dream = await dream_service.create_dream(
        db,
        user,
        DreamCreate(content="  A very long dream text for title generation  ", comment="note"),
    )

    assert dream.user_id == user.id
    assert dream.title == "A very long dream text for title generation"
    assert calls == {"embed": 1, "rag": 1}
    assert db.commits == 2
    assert db.refreshes == [dream, dream]


@pytest.mark.asyncio
async def test_create_dream_rejects_when_daily_limit_exceeded(monkeypatch):
    async def fake_check_dreams_limit(_db, _user):
        return False

    monkeypatch.setattr(dream_service, "check_dreams_limit", fake_check_dreams_limit)

    with pytest.raises(ValueError, match="Daily limit"):
        await dream_service.create_dream(FakeDb(), SimpleNamespace(id=uuid4()), DreamCreate(content="long enough dream content"))


@pytest.mark.asyncio
async def test_update_dream_validates_future_date_and_rebuilds(monkeypatch):
    dream = SimpleNamespace(id=uuid4(), user_id=uuid4(), title="Old", content="Body", comment="note")
    db = FakeDb()

    with pytest.raises(ValueError, match="future"):
        await dream_service.update_dream(
            db,
            dream,
            DreamUpdate(created_at=datetime.now(timezone.utc) + timedelta(days=1)),
        )

    calls = {"embed": 0, "rag": 0}

    async def fake_recalculate(_db, _dream):
        calls["embed"] += 1

    async def fake_rebuild(_db, _dream, _user_id):
        calls["rag"] += 1

    monkeypatch.setattr(dream_service, "recalculate_dream_embedding", fake_recalculate)
    monkeypatch.setattr(dream_service, "rebuild_dream_memory", fake_rebuild)

    updated = await dream_service.update_dream(
        db,
        dream,
        DreamUpdate(title="New", created_at=datetime(2025, 1, 2, 3, 4, 5)),
    )

    assert updated.title == "New"
    assert updated.created_at.tzinfo is not None
    assert updated.recorded_at == updated.created_at
    assert calls == {"embed": 1, "rag": 1}
    assert db.commits == 1
    assert db.refreshes == [dream]


@pytest.mark.asyncio
async def test_search_dreams_scores_matches():
    q = "wolf"
    dreams = [
        SimpleNamespace(title="Wolf chase", content="nothing", comment="", recorded_at=datetime.now(timezone.utc)),
        SimpleNamespace(title="Other", content="A wolf appeared", comment="wolf note", recorded_at=datetime.now(timezone.utc)),
    ]
    db = FakeDb(execute_results=[FakeResult(scalars=dreams)])
    user = SimpleNamespace(id=uuid4())

    results = await dream_service.search_dreams(db, user, q)

    assert len(results) == 2
    assert results[0][1] == 0.6
    assert results[1][1] == 0.6


@pytest.mark.asyncio
async def test_search_dreams_semantic_backfills_missing_embeddings(monkeypatch):
    async def fake_request_embedding(text):
        assert text == "forest"
        return [1.0, 0.0]

    async def fake_recalculate(_db, dream):
        dream.embedding_text = serialize_embedding([0.5, 0.5])

    monkeypatch.setattr(dream_service, "request_embedding", fake_request_embedding)
    monkeypatch.setattr(dream_service, "recalculate_dream_embedding", fake_recalculate)

    dream_a = SimpleNamespace(
        id=uuid4(),
        embedding_text=serialize_embedding([1.0, 0.0]),
        recorded_at=datetime.now(timezone.utc),
    )
    dream_b = SimpleNamespace(
        id=uuid4(),
        embedding_text=None,
        recorded_at=datetime.now(timezone.utc),
    )
    db = FakeDb(execute_results=[FakeResult(scalars=[dream_a, dream_b])])
    user = SimpleNamespace(id=uuid4())

    results = await dream_service.search_dreams_semantic(db, user, "forest", limit=10)

    assert [item[0] for item in results] == [dream_a, dream_b]
    assert db.commits == 1


@pytest.mark.asyncio
async def test_delete_dream_commits():
    dream = SimpleNamespace(id=uuid4())
    db = FakeDb()

    await dream_service.delete_dream(db, dream)

    assert db.deleted == [dream]
    assert db.commits == 1
