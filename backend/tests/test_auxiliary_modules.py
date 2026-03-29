from types import SimpleNamespace
from uuid import uuid4

import pytest

import main
from services import archetype_service, message_task_service
from prompts import get_chat_system_prompt

from tests.helpers import FakeDb, FakeResult


@pytest.mark.asyncio
async def test_apply_archetypes_delta_adds_and_updates():
    user_id = uuid4()
    existing = SimpleNamespace(count=2)
    db = FakeDb(execute_results=[FakeResult(scalar=None), FakeResult(scalar=existing)])

    await archetype_service.apply_archetypes_delta(db, user_id, {"shadow": 3, "anima": 2, "": 1, "zero": 0})

    assert any(getattr(item, "name", None) == "shadow" for item in db.added)
    assert existing.count == 4


def test_get_message_task_status_paths(monkeypatch):
    class FakeAsyncResult:
        def __init__(self, task_id, app):
            self.task_id = task_id
            self.app = app
            self.status = "SUCCESS" if task_id == "ok" else "FAILURE"
            self.result = "done"
            self.info = RuntimeError("boom")

        def ready(self):
            return True

        def successful(self):
            return self.task_id == "ok"

        def failed(self):
            return self.task_id != "ok"

    monkeypatch.setattr(message_task_service, "AsyncResult", FakeAsyncResult)

    assert message_task_service.get_message_task_status("ok")["result"] == "done"
    assert message_task_service.get_message_task_status("bad")["error"] == "boom"


@pytest.mark.asyncio
async def test_main_endpoints_and_lifespan(monkeypatch):
    calls = {"init": 0, "close": 0}

    async def fake_init_db():
        calls["init"] += 1

    async def fake_close_db():
        calls["close"] += 1

    monkeypatch.setattr(main, "init_db", fake_init_db)
    monkeypatch.setattr(main, "close_db", fake_close_db)

    assert await main.root() == {"service": "InnerCore Backend API", "version": "1.0.0", "status": "running"}
    assert await main.health_check() == {"status": "ok", "service": "backend", "version": "1.0.0"}
    async with main.lifespan(main.app):
        pass
    assert calls == {"init": 1, "close": 1}


def test_prompt_includes_user_context():
    prompt = get_chat_system_prompt("likes symbolism")
    assert "USER CONTEXT: likes symbolism" in prompt
    assert "CRITICAL LANGUAGE REQUIREMENT" in prompt
