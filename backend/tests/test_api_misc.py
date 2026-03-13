from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api import analyses as analyses_api
from api import messages as messages_api
from api import stats as stats_api
from models import AnalysisMessage, AnalysisStatus, MessageRole
from schemas import AnalysisCreate, MessageSend

from tests.helpers import FakeDb


@pytest.mark.asyncio
async def test_analyses_api_endpoints(monkeypatch):
    user = SimpleNamespace(id=uuid4())
    dream = SimpleNamespace(id=uuid4())
    analysis = SimpleNamespace(
        id=uuid4(),
        dream_id=dream.id,
        user_id=user.id,
        result="result",
        status=AnalysisStatus.PENDING.value,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
    )

    async def missing_dream(_db, _dream_id, _current_user):
        return None

    monkeypatch.setattr(analyses_api, "get_dream_by_id", missing_dream)
    with pytest.raises(HTTPException, match="Dream not found"):
        await analyses_api.create_analysis_endpoint(AnalysisCreate(dream_id=uuid4()), user, FakeDb())

    async def found_dream(_db, _dream_id, _current_user):
        return dream

    async def conflict_create_analysis(_db, _dream, _user, allow_retry=True):
        raise ValueError("analysis_already_exists")

    monkeypatch.setattr(analyses_api, "get_dream_by_id", found_dream)
    monkeypatch.setattr(analyses_api, "create_analysis", conflict_create_analysis)
    with pytest.raises(HTTPException, match="analysis_already_exists"):
        await analyses_api.create_analysis_endpoint(AnalysisCreate(dream_id=dream.id), user, FakeDb())

    async def ok_create_analysis(_db, _dream, _user, allow_retry=True):
        return analysis, "task-1"

    monkeypatch.setattr(analyses_api, "create_analysis", ok_create_analysis)
    response = await analyses_api.create_analysis_endpoint(AnalysisCreate(dream_id=dream.id), user, FakeDb())
    assert response["task_id"] == "task-1"

    async def fake_task_status(_task_id):
        return {"status": "SUCCESS", "result": "done", "progress": 100}

    monkeypatch.setattr(analyses_api, "get_task_status", fake_task_status)
    task_status = await analyses_api.get_task_status_endpoint("task-1", user)
    assert task_status["result"] == "done"

    async def no_analysis(_db, _dream_id, _current_user):
        return None

    monkeypatch.setattr(analyses_api, "get_analysis_by_dream_id", no_analysis)
    with pytest.raises(HTTPException, match="Analysis not found for this dream"):
        await analyses_api.get_analysis_by_dream_endpoint(dream.id, user, FakeDb())

    async def analysis_by_dream(_db, _dream_id, _current_user):
        return analysis

    monkeypatch.setattr(analyses_api, "get_analysis_by_dream_id", analysis_by_dream)
    assert (await analyses_api.get_analysis_by_dream_endpoint(dream.id, user, FakeDb())).id == analysis.id

    async def no_analysis_by_id(_db, _analysis_id, _current_user):
        return None

    monkeypatch.setattr(analyses_api, "get_analysis_by_id", no_analysis_by_id)
    with pytest.raises(HTTPException, match="Analysis not found"):
        await analyses_api.get_analysis_endpoint(analysis.id, user, FakeDb())

    async def yes_analysis_by_id(_db, _analysis_id, _current_user):
        return analysis

    monkeypatch.setattr(analyses_api, "get_analysis_by_id", yes_analysis_by_id)
    assert (await analyses_api.get_analysis_endpoint(analysis.id, user, FakeDb())).id == analysis.id

    async def fake_get_user_analyses(_db, _current_user, limit=100):
        return [analysis]

    monkeypatch.setattr(analyses_api, "get_user_analyses", fake_get_user_analyses)
    listing = await analyses_api.get_analyses_endpoint(user, FakeDb())
    assert listing["total"] == 1


@pytest.mark.asyncio
async def test_messages_and_stats_api_endpoints(monkeypatch):
    user = SimpleNamespace(id=uuid4())
    dream = SimpleNamespace(id=uuid4())
    msg = AnalysisMessage(
        id=uuid4(),
        user_id=user.id,
        dream_id=dream.id,
        role=MessageRole.USER.value,
        content="hello",
        created_at=datetime.now(timezone.utc),
    )

    async def missing_dream(_db, _dream_id, _current_user):
        return None

    monkeypatch.setattr(messages_api, "get_dream_by_id", missing_dream)
    with pytest.raises(HTTPException, match="Dream not found"):
        await messages_api.send_message(MessageSend(dream_id=dream.id, content="hello"), user, FakeDb())

    async def found_dream(_db, _dream_id, _current_user):
        return dream

    async def fake_create_message(_db, user_id=None, dream_id=None, role=None, content=None):
        return msg

    monkeypatch.setattr(messages_api, "get_dream_by_id", found_dream)
    monkeypatch.setattr(messages_api, "create_message", fake_create_message)

    class FakeTask:
        id = "task-123"

    class FakeDelay:
        @staticmethod
        def delay(user_id, dream_id):
            return FakeTask()

    import tasks

    monkeypatch.setattr(tasks, "reply_to_dream_chat_task", FakeDelay)
    response = await messages_api.send_message(MessageSend(dream_id=dream.id, content="hello"), user, FakeDb())
    assert response.task_id == "task-123"

    async def fake_get_messages_for_dream(_db, user_id=None, dream_id=None, limit=50, offset=0):
        return [msg], 1

    monkeypatch.setattr(messages_api, "get_messages_for_dream", fake_get_messages_for_dream)
    listing = await messages_api.get_dream_messages(dream.id, user, FakeDb(), limit=50, offset=0)
    assert listing.total == 1

    monkeypatch.setattr(messages_api, "get_message_task_status", lambda task_id: {"task_id": task_id, "status": "SUCCESS"})
    assert (await messages_api.get_message_task("task-123", user))["status"] == "SUCCESS"

    async def fake_get_user_stats(_db, _current_user):
        return {"total_dreams": 1, "streak_days": 0, "dreams_by_weekday": {}, "dreams_last_14_days": [], "archetypes_top": [], "avg_time_of_day": None}

    monkeypatch.setattr(stats_api, "get_user_stats", fake_get_user_stats)
    stats = await stats_api.get_stats(user, FakeDb())
    assert stats["total_dreams"] == 1
