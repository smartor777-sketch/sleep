from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from models import AnalysisStatus
from services import analysis_service


class FakeDb:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, _obj):
        return None


@pytest.mark.asyncio
async def test_create_analysis_creates_new_pending_task(monkeypatch):
    db = FakeDb()
    dream = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4())
    captured = {}

    async def fake_get_analysis_by_dream_id(_db, _dream_id, _user):
        return None

    def fake_delay(analysis_id):
        captured["analysis_id"] = analysis_id
        return SimpleNamespace(id="task-123")

    monkeypatch.setattr(analysis_service, "get_analysis_by_dream_id", fake_get_analysis_by_dream_id)
    monkeypatch.setattr("tasks.analyze_dream_task.delay", fake_delay)

    analysis, task_id = await analysis_service.create_analysis(db, dream, user)

    assert analysis.status == AnalysisStatus.PENDING.value
    assert analysis.dream_id == dream.id
    assert analysis.user_id == user.id
    assert analysis.celery_task_id == "task-123"
    assert task_id == "task-123"
    assert captured["analysis_id"] == str(analysis.id)


@pytest.mark.asyncio
async def test_create_analysis_allows_retry_only_for_failed(monkeypatch):
    db = FakeDb()
    dream = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4())
    failed = SimpleNamespace(
        id=uuid4(),
        dream_id=dream.id,
        user_id=user.id,
        status=AnalysisStatus.FAILED.value,
        error_message="upstream failure",
        completed_at=datetime.now(timezone.utc),
        celery_task_id=None,
    )

    async def fake_get_analysis_by_dream_id(_db, _dream_id, _user):
        return failed

    monkeypatch.setattr(analysis_service, "get_analysis_by_dream_id", fake_get_analysis_by_dream_id)
    monkeypatch.setattr("tasks.analyze_dream_task.delay", lambda _analysis_id: SimpleNamespace(id="task-retry"))

    analysis, task_id = await analysis_service.create_analysis(db, dream, user, allow_retry=True)

    assert analysis is failed
    assert analysis.status == AnalysisStatus.PENDING.value
    assert analysis.error_message is None
    assert analysis.completed_at is None
    assert analysis.celery_task_id == "task-retry"
    assert task_id == "task-retry"


@pytest.mark.asyncio
async def test_create_analysis_rejects_completed_or_inflight(monkeypatch):
    db = FakeDb()
    dream = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4())

    async def fake_get_analysis_by_dream_id(_db, _dream_id, _user):
        return SimpleNamespace(status=AnalysisStatus.COMPLETED.value)

    monkeypatch.setattr(analysis_service, "get_analysis_by_dream_id", fake_get_analysis_by_dream_id)

    with pytest.raises(ValueError, match="analysis_already_exists"):
        await analysis_service.create_analysis(db, dream, user)
