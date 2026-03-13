from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from api import dreams as dreams_api
from models import AnalysisStatus
from schemas import DreamCreate


def _dream_with_analysis(status=None, error_message=None):
    return SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        title="A dream title",
        content="This is a long enough dream text for validation.",
        emoji="",
        comment="",
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        gradient_color_1=None,
        gradient_color_2=None,
        analysis=None if status is None else SimpleNamespace(status=status, error_message=error_message),
    )


def test_map_analysis_status_variants():
    assert dreams_api._map_analysis_status(_dream_with_analysis()) == (False, "saved", None)
    assert dreams_api._map_analysis_status(_dream_with_analysis(AnalysisStatus.PENDING.value)) == (
        False,
        "analyzing",
        None,
    )
    assert dreams_api._map_analysis_status(_dream_with_analysis(AnalysisStatus.COMPLETED.value)) == (
        True,
        "analyzed",
        None,
    )
    assert dreams_api._map_analysis_status(
        _dream_with_analysis(AnalysisStatus.FAILED.value, "llm failed")
    ) == (False, "analysis_failed", "llm failed")


@pytest.mark.asyncio
async def test_create_dream_endpoint_auto_starts_analysis(monkeypatch):
    dream = _dream_with_analysis()
    current_user = SimpleNamespace(id=uuid4())

    async def fake_create_dream(_db, _user, _dream_data):
        return dream

    async def fake_create_analysis(_db, _dream, _user, allow_retry=False):
        assert allow_retry is False
        _dream.analysis = SimpleNamespace(status=AnalysisStatus.PENDING.value, error_message=None)
        return _dream.analysis, "task-123"

    async def fake_refresh(_dream):
        return None

    monkeypatch.setattr(dreams_api, "create_dream", fake_create_dream)
    monkeypatch.setattr(dreams_api, "create_analysis", fake_create_analysis)

    response = await dreams_api.create_dream_endpoint(
        DreamCreate(content="This is a long enough dream text for validation."),
        current_user,
        db=SimpleNamespace(refresh=fake_refresh),
    )

    assert response.analysis_status == "analyzing"
    assert response.has_analysis is False
    assert response.analysis_error_message is None
