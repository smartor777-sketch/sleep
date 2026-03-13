from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api import auth as auth_api
from schemas import (
    AnonymousAuthRequest,
    ForgotPasswordRequest,
    LinkRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
)

from tests.helpers import FakeDb


@pytest.mark.asyncio
async def test_register_paths(monkeypatch):
    async def existing_user(_db, _email):
        return SimpleNamespace()

    monkeypatch.setattr(auth_api, "get_user_by_email", existing_user)
    with pytest.raises(HTTPException, match="Email already registered"):
        await auth_api.register(RegisterRequest(email="user@example.com", password="password123"), FakeDb())

    async def fake_get_user_by_email(_db, _email):
        return None

    async def fake_create_user(_db, data):
        return SimpleNamespace(id=uuid4(), email=data.email)

    async def fake_create_email_verification_token(_db, _user_id):
        return "verify-token"

    monkeypatch.setattr(auth_api, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_api, "create_user", fake_create_user)
    monkeypatch.setattr(auth_api, "create_email_verification_token", fake_create_email_verification_token)
    monkeypatch.setattr(auth_api.email_service, "send_verification_email", lambda email, token: (_ for _ in ()).throw(RuntimeError("smtp")))
    monkeypatch.setattr(auth_api, "create_access_token", lambda data: "access")
    monkeypatch.setattr(auth_api, "create_refresh_token", lambda data: "refresh")

    response = await auth_api.register(RegisterRequest(email="user@example.com", password="password123"), FakeDb())

    assert response["access_token"] == "access"
    assert response["refresh_token"] == "refresh"


@pytest.mark.asyncio
async def test_login_paths(monkeypatch):
    async def fake_authenticate_user(_db, email, password):
        if email == "missing@example.com":
            return None
        if email == "inactive@example.com":
            return SimpleNamespace(is_active=False, email=email)
        return SimpleNamespace(is_active=True, email=email, id=uuid4())

    monkeypatch.setattr(auth_api, "authenticate_user", fake_authenticate_user)
    monkeypatch.setattr(auth_api, "create_access_token", lambda data: "access")
    monkeypatch.setattr(auth_api, "create_refresh_token", lambda data: "refresh")

    with pytest.raises(HTTPException, match="Incorrect email or password"):
        await auth_api.login(LoginRequest(email="missing@example.com", password="password123"), FakeDb())
    with pytest.raises(HTTPException, match="User is inactive"):
        await auth_api.login(LoginRequest(email="inactive@example.com", password="password123"), FakeDb())

    response = await auth_api.login(LoginRequest(email="ok@example.com", password="password123"), FakeDb())
    assert response["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_anonymous_auth_paths(monkeypatch):
    with pytest.raises(HTTPException, match="invalid device_id"):
        await auth_api.anonymous_auth(SimpleNamespace(device_id="short"), FakeDb())

    async def fake_get_or_create_anonymous_user(_db, _device_id):
        return SimpleNamespace(id=uuid4(), is_anonymous=True, email=None, last_login_at=None), True

    monkeypatch.setattr(auth_api, "get_or_create_anonymous_user", fake_get_or_create_anonymous_user)
    monkeypatch.setattr(auth_api, "create_access_token", lambda data: "access")
    monkeypatch.setattr(auth_api, "create_refresh_token", lambda data: "refresh")
    db = FakeDb()

    response = await auth_api.anonymous_auth(AnonymousAuthRequest(device_id="device-12345678"), db)

    assert response.access_token == "access"
    assert db.commits == 1


@pytest.mark.asyncio
async def test_link_provider_paths(monkeypatch):
    current_user = SimpleNamespace(id=uuid4(), is_anonymous=True, email=None)
    db = FakeDb()

    with pytest.raises(HTTPException, match="invalid_provider"):
        await auth_api.link_provider(LinkRequest(provider="x", id_token="1234567890"), current_user, db)

    async def bad_google(_token):
        raise ValueError("bad_token")

    monkeypatch.setattr(auth_api, "verify_google_id_token", bad_google)
    with pytest.raises(HTTPException, match="bad_token"):
        await auth_api.link_provider(LinkRequest(provider="google", id_token="1234567890"), current_user, db)

    async def good_google(_token):
        return {"sub": "sub1", "email": "user@example.com"}

    async def foreign_identity(_db, _provider, _subject):
        return SimpleNamespace(user_id=uuid4())

    monkeypatch.setattr(auth_api, "verify_google_id_token", good_google)
    monkeypatch.setattr(auth_api, "get_identity", foreign_identity)
    with pytest.raises(HTTPException, match="identity_already_linked"):
        await auth_api.link_provider(LinkRequest(provider="google", id_token="1234567890"), current_user, db)

    async def no_identity(_db, _provider, _subject):
        return None

    async def existing_user_identities(_db, _user):
        return [SimpleNamespace(provider="google")]

    monkeypatch.setattr(auth_api, "get_identity", no_identity)
    monkeypatch.setattr(auth_api, "get_user_identities", existing_user_identities)
    with pytest.raises(HTTPException, match="user_already_has_identity"):
        await auth_api.link_provider(LinkRequest(provider="google", id_token="1234567890"), current_user, db)

    async def empty_user_identities(_db, _user):
        return []

    async def fake_create_identity(_db, _user, provider, subject, email):
        return SimpleNamespace(provider=provider, provider_subject=subject, email=email)

    monkeypatch.setattr(auth_api, "get_user_identities", empty_user_identities)
    monkeypatch.setattr(auth_api, "create_identity", fake_create_identity)

    response = await auth_api.link_provider(LinkRequest(provider="google", id_token="1234567890"), current_user, db)

    assert response.linked is True
    assert current_user.is_anonymous is False
    assert current_user.email == "user@example.com"
    assert db.commits == 1


@pytest.mark.asyncio
async def test_refresh_and_verify_email_paths(monkeypatch):
    monkeypatch.setattr(auth_api, "verify_token", lambda token, token_type: {"sub": "user-1"})
    monkeypatch.setattr(auth_api, "create_access_token", lambda data: "access")
    monkeypatch.setattr(auth_api, "create_refresh_token", lambda data: "refresh")

    response = await auth_api.refresh_token_endpoint(RefreshTokenRequest(refresh_token="r"), FakeDb())
    assert response["access_token"] == "access"

    monkeypatch.setattr(auth_api, "verify_token", lambda token, token_type: {})
    with pytest.raises(HTTPException, match="Invalid refresh token"):
        await auth_api.refresh_token_endpoint(RefreshTokenRequest(refresh_token="r"), FakeDb())

    async def no_verified_user(_db, _token):
        return None

    monkeypatch.setattr(auth_api, "verify_email_token", no_verified_user)
    with pytest.raises(HTTPException, match="Invalid or expired verification token"):
        await auth_api.verify_email(FakeDb(), "missing")

    async def verified_user(_db, _token):
        return SimpleNamespace(email="user@example.com")

    monkeypatch.setattr(auth_api, "verify_email_token", verified_user)
    response = await auth_api.verify_email(FakeDb(), "ok")
    assert response["message"] == "Email successfully verified"


@pytest.mark.asyncio
async def test_verification_and_password_reset_endpoints(monkeypatch):
    async def fake_get_user_by_email(_db, email):
        if email == "missing@example.com":
            return None
        if email == "verified@example.com":
            return SimpleNamespace(id=uuid4(), email=email, email_verified=True, password_hash="hash")
        if email == "oauth@example.com":
            return SimpleNamespace(id=uuid4(), email=email, email_verified=False, password_hash=None)
        return SimpleNamespace(id=uuid4(), email=email, email_verified=False, password_hash="hash")

    monkeypatch.setattr(auth_api, "get_user_by_email", fake_get_user_by_email)
    async def fake_create_email_token(_db, _user_id):
        return "verify-token"

    async def fake_create_reset_token(_db, _user_id):
        return "reset-token"

    monkeypatch.setattr(auth_api, "create_email_verification_token", fake_create_email_token)
    monkeypatch.setattr(auth_api, "create_password_reset_token", fake_create_reset_token)
    monkeypatch.setattr(auth_api.email_service, "send_verification_email", lambda email, token: None)
    monkeypatch.setattr(auth_api.email_service, "send_password_reset_email", lambda email, token: None)

    response = await auth_api.resend_verification(ResendVerificationRequest(email="missing@example.com"), FakeDb())
    assert response["message"].startswith("If the email exists")

    with pytest.raises(HTTPException, match="Email already verified"):
        await auth_api.resend_verification(ResendVerificationRequest(email="verified@example.com"), FakeDb())

    response = await auth_api.resend_verification(ResendVerificationRequest(email="pending@example.com"), FakeDb())
    assert response["message"] == "Verification email has been sent"

    response = await auth_api.forgot_password(ForgotPasswordRequest(email="missing@example.com"), FakeDb())
    assert response["message"].startswith("If the email exists")

    with pytest.raises(HTTPException, match="Cannot reset password for OAuth2 accounts"):
        await auth_api.forgot_password(ForgotPasswordRequest(email="oauth@example.com"), FakeDb())

    response = await auth_api.forgot_password(ForgotPasswordRequest(email="pending@example.com"), FakeDb())
    assert response["message"] == "Password reset email has been sent"


@pytest.mark.asyncio
async def test_reset_delete_and_logout(monkeypatch):
    async def bad_reset(_db, _token, _password):
        return None

    monkeypatch.setattr(auth_api, "reset_password", bad_reset)
    with pytest.raises(HTTPException, match="Invalid or expired reset token"):
        await auth_api.reset_password_endpoint(
            ResetPasswordRequest(token="bad", new_password="password123"),
            FakeDb(),
        )

    async def good_reset(_db, _token, _password):
        return SimpleNamespace(email="user@example.com")

    monkeypatch.setattr(auth_api, "reset_password", good_reset)
    response = await auth_api.reset_password_endpoint(
        ResetPasswordRequest(token="ok", new_password="password123"),
        FakeDb(),
    )
    assert response["message"] == "Password successfully reset"

    current_user = SimpleNamespace(email="user@example.com")
    db = FakeDb()
    response = await auth_api.delete_account(current_user, db)
    assert response["message"] == "Account successfully deleted"
    assert db.deleted == [current_user]

    response = await auth_api.logout()
    assert response["message"] == "Successfully logged out"
