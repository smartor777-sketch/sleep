from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from models import User
from schemas import UserCreate
from services import auth_service

from tests.helpers import FakeDb, FakeResult


@pytest.mark.asyncio
async def test_create_user_hashes_password_and_persists():
    db = FakeDb()
    payload = UserCreate(email="user@example.com", password="password123", first_name="A", last_name="B")

    user = await auth_service.create_user(db, payload)

    assert isinstance(user, User)
    assert user.email == "user@example.com"
    assert user.password_hash != "password123"
    assert auth_service.verify_password("password123", user.password_hash)
    assert db.commits == 1
    assert db.refreshes == [user]


@pytest.mark.asyncio
async def test_get_or_create_anonymous_user_returns_existing(monkeypatch):
    existing = SimpleNamespace(id=uuid4(), device_id="device-12345678")

    async def fake_get_user_by_device_id(_db, _device_id):
        return existing

    monkeypatch.setattr(auth_service, "get_user_by_device_id", fake_get_user_by_device_id)

    user, is_new = await auth_service.get_or_create_anonymous_user(FakeDb(), "device-12345678")

    assert user is existing
    assert is_new is False


@pytest.mark.asyncio
async def test_get_or_create_anonymous_user_creates_new(monkeypatch):
    async def fake_get_user_by_device_id(_db, _device_id):
        return None

    monkeypatch.setattr(auth_service, "get_user_by_device_id", fake_get_user_by_device_id)
    db = FakeDb()

    user, is_new = await auth_service.get_or_create_anonymous_user(db, "device-12345678")

    assert is_new is True
    assert user.is_anonymous is True
    assert user.device_id == "device-12345678"
    assert db.commits == 1
    assert db.refreshes == [user]


@pytest.mark.asyncio
async def test_authenticate_user_branches(monkeypatch):
    async def fake_get_user_by_email(_db, email):
        if email == "missing@example.com":
            return None
        if email == "oauth@example.com":
            return SimpleNamespace(password_hash=None)
        if email == "bad@example.com":
            return SimpleNamespace(password_hash=auth_service.get_password_hash("secret"))
        return SimpleNamespace(password_hash=auth_service.get_password_hash("secret"))

    monkeypatch.setattr(auth_service, "get_user_by_email", fake_get_user_by_email)

    assert await auth_service.authenticate_user(FakeDb(), "missing@example.com", "secret") is None
    assert await auth_service.authenticate_user(FakeDb(), "oauth@example.com", "secret") is None
    assert await auth_service.authenticate_user(FakeDb(), "bad@example.com", "wrong") is None
    assert await auth_service.authenticate_user(FakeDb(), "ok@example.com", "secret") is not None


@pytest.mark.asyncio
async def test_create_and_verify_email_token_paths():
    user_id = uuid4()
    db = FakeDb()

    token = await auth_service.create_email_verification_token(db, user_id, expires_hours=2)

    assert token
    verification = db.added[0]
    assert verification.user_id == user_id
    assert db.commits == 1

    expired = SimpleNamespace(user_id=user_id, token="expired", expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    expired_db = FakeDb(execute_results=[FakeResult(scalar=expired)])
    assert await auth_service.verify_email_token(expired_db, "expired") is None
    assert expired_db.deleted == [expired]
    assert expired_db.commits == 1

    user = SimpleNamespace(id=user_id, email_verified=False)
    valid = SimpleNamespace(user_id=user_id, token="valid", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    valid_db = FakeDb(execute_results=[FakeResult(scalar=valid), FakeResult(scalar=user)])
    verified_user = await auth_service.verify_email_token(valid_db, "valid")

    assert verified_user is user
    assert user.email_verified is True
    assert valid_db.deleted == [valid]
    assert valid_db.commits == 1
    assert valid_db.refreshes == [user]


@pytest.mark.asyncio
async def test_verify_email_token_missing_returns_none():
    db = FakeDb(execute_results=[FakeResult(scalar=None)])
    assert await auth_service.verify_email_token(db, "missing") is None


@pytest.mark.asyncio
async def test_create_and_reset_password_paths():
    user_id = uuid4()
    db = FakeDb()

    token = await auth_service.create_password_reset_token(db, user_id, expires_hours=2)
    assert token
    assert db.added[0].user_id == user_id

    missing_db = FakeDb(execute_results=[FakeResult(scalar=None)])
    assert await auth_service.reset_password(missing_db, "missing", "new-password123") is None

    expired = SimpleNamespace(user_id=user_id, used=False, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    expired_db = FakeDb(execute_results=[FakeResult(scalar=expired)])
    assert await auth_service.reset_password(expired_db, "expired", "new-password123") is None
    assert expired_db.deleted == [expired]

    user = SimpleNamespace(id=user_id, password_hash=None)
    reset = SimpleNamespace(user_id=user_id, used=False, expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    valid_db = FakeDb(execute_results=[FakeResult(scalar=reset), FakeResult(scalar=user)])
    updated_user = await auth_service.reset_password(valid_db, "valid", "new-password123")

    assert updated_user is user
    assert reset.used is True
    assert auth_service.verify_password("new-password123", user.password_hash)
    assert valid_db.commits == 1
    assert valid_db.refreshes == [user]
