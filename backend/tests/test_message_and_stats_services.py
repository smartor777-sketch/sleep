from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytz

from models import MessageRole
from services import message_service, stats_service

from tests.helpers import FakeDb, FakeResult


@pytest.mark.asyncio
async def test_create_message_and_get_messages_for_dream():
    db = FakeDb(execute_results=[FakeResult(scalar=2), FakeResult(scalars=[SimpleNamespace(id=1), SimpleNamespace(id=2)])])
    message_db = FakeDb()
    user_id = uuid4()
    dream_id = uuid4()

    msg = await message_service.create_message(message_db, user_id, dream_id, MessageRole.USER.value, "hello")
    messages, total = await message_service.get_messages_for_dream(db, user_id, dream_id, limit=2, offset=0)

    assert msg.content == "hello"
    assert message_db.commits == 1
    assert message_db.refreshes == [msg]
    assert len(messages) == 2
    assert total == 2


@pytest.mark.asyncio
async def test_build_llm_context_builds_anchor_and_follow_up(monkeypatch):
    monkeypatch.setattr(message_service, "MAX_RECENT_MESSAGES", 2)
    async def fake_build_retrieval_context(*args, **kwargs):
        return SimpleNamespace(to_prompt_block=lambda: "RAG BLOCK")

    monkeypatch.setattr(message_service, "build_retrieval_context", fake_build_retrieval_context)

    user_id = uuid4()
    old_dream_id = uuid4()
    current_dream_id = uuid4()
    old_dream = SimpleNamespace(id=old_dream_id, created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    current_dream = SimpleNamespace(id=current_dream_id, created_at=datetime(2024, 1, 2, tzinfo=timezone.utc))

    def msg(role, content):
        return SimpleNamespace(role=role, content=content, created_at=datetime.now(timezone.utc))

    db = FakeDb(
        execute_results=[
            FakeResult(scalar=current_dream),
            FakeResult(scalars=[old_dream, current_dream]),
            FakeResult(scalar=msg(MessageRole.USER.value, "old user")),
            FakeResult(scalar=msg(MessageRole.ASSISTANT.value, "old assistant")),
            FakeResult(scalar=msg(MessageRole.USER.value, "current user")),
            FakeResult(scalar=msg(MessageRole.ASSISTANT.value, "current assistant")),
            FakeResult(
                scalars=[
                    msg(MessageRole.USER.value, "current user"),
                    msg(MessageRole.ASSISTANT.value, "current assistant"),
                    msg(MessageRole.USER.value, "follow 1"),
                    msg(MessageRole.ASSISTANT.value, "follow 2"),
                    msg(MessageRole.USER.value, "follow 3"),
                ]
            ),
        ]
    )

    messages = await message_service.build_llm_context(db, user_id, current_dream_id, "SYSTEM")

    assert messages[0] == {"role": "system", "text": "SYSTEM"}
    assert messages[1] == {"role": "system", "text": "RAG BLOCK"}
    assert any(m["text"].startswith("[Сон от 01.01.2024]") for m in messages)
    assert any(m["text"].startswith("[Текущий сон от 02.01.2024]") for m in messages)
    assert messages[-2:] == [
        {"role": MessageRole.ASSISTANT.value, "text": "follow 2"},
        {"role": MessageRole.USER.value, "text": "follow 3"},
    ]


@pytest.mark.asyncio
async def test_build_llm_context_can_skip_retrieval(monkeypatch):
    async def fail_build_retrieval_context(*args, **kwargs):
        raise AssertionError("retrieval should not run")

    monkeypatch.setattr(message_service, "build_retrieval_context", fail_build_retrieval_context)

    user_id = uuid4()
    current_dream_id = uuid4()
    current_dream = SimpleNamespace(id=current_dream_id, created_at=datetime(2024, 1, 2, tzinfo=timezone.utc))

    def msg(role, content):
        return SimpleNamespace(role=role, content=content, created_at=datetime.now(timezone.utc))

    db = FakeDb(
        execute_results=[
            FakeResult(scalars=[current_dream]),
            FakeResult(scalar=msg(MessageRole.USER.value, "current user")),
            FakeResult(scalar=msg(MessageRole.ASSISTANT.value, "current assistant")),
            FakeResult(
                scalars=[
                    msg(MessageRole.USER.value, "current user"),
                    msg(MessageRole.ASSISTANT.value, "current assistant"),
                ]
            ),
        ]
    )

    messages = await message_service.build_llm_context(
        db,
        user_id,
        current_dream_id,
        "SYSTEM",
        include_retrieval=False,
    )

    assert messages[0] == {"role": "system", "text": "SYSTEM"}
    assert all(message["text"] != "RAG BLOCK" for message in messages[1:])


@pytest.mark.asyncio
async def test_get_user_stats_aggregates_counts(monkeypatch):
    tz = pytz.UTC
    async def fake_get_user_timezone(_user):
        return tz

    monkeypatch.setattr(stats_service, "get_user_timezone", fake_get_user_timezone)

    now = datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0)
    rows = [
        now,
        now - timedelta(days=1),
        now - timedelta(days=3),
    ]
    archetypes = [SimpleNamespace(name="shadow", count=3), SimpleNamespace(name="anima", count=1)]
    db = FakeDb(execute_results=[FakeResult(scalar=3), FakeResult(scalars=rows), FakeResult(scalars=archetypes)])
    user = SimpleNamespace(id=uuid4())

    stats = await stats_service.get_user_stats(db, user)

    assert stats["total_dreams"] == 3
    assert stats["streak_days"] == 2
    assert stats["avg_time_of_day"] == "06:00"
    assert len(stats["dreams_last_14_days"]) == 14
    assert stats["archetypes_top"] == [{"name": "shadow", "count": 3}, {"name": "anima", "count": 1}]
