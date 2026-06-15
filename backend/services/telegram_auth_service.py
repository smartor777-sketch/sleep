"""Telegram bot deep-link auth: short-lived tokens in Redis + user create/find."""

import json
import logging
import secrets
from datetime import datetime

from redis import asyncio as redis_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import OAuthIdentity, User

logger = logging.getLogger(__name__)

PROVIDER = "telegram"
KEY_PREFIX = "tg_auth:"
TOKEN_TTL_SECONDS = 600  # 10 minutes


async def _redis():
    return redis_asyncio.from_url(settings.redis_url, decode_responses=True)


def new_auth_token() -> str:
    # URL-safe, ~32 chars
    return secrets.token_urlsafe(24)


async def create_pending_token() -> str:
    token = new_auth_token()
    client = await _redis()
    try:
        await client.set(KEY_PREFIX + token, "pending", ex=TOKEN_TTL_SECONDS)
    finally:
        await client.close()
    return token


async def get_token_state(token: str) -> dict | None:
    """Return None if expired/not found, else {"status": "pending"} or
    {"status": "completed", "access_token": ..., "refresh_token": ...}."""
    client = await _redis()
    try:
        raw = await client.get(KEY_PREFIX + token)
        if raw is None:
            return None
        if raw == "pending":
            return {"status": "pending"}
        try:
            data = json.loads(raw)
            data["status"] = "completed"
            # one-shot read: delete so the same token can't be redeemed twice
            await client.delete(KEY_PREFIX + token)
            return data
        except json.JSONDecodeError:
            logger.warning("Corrupted tg_auth payload for token %s", token)
            await client.delete(KEY_PREFIX + token)
            return None
    finally:
        await client.close()


async def complete_token(token: str, access_token: str, refresh_token: str) -> bool:
    """Replace pending value with completed payload, keeping the same TTL window.
    Returns False if token doesn't exist."""
    client = await _redis()
    try:
        if not await client.exists(KEY_PREFIX + token):
            return False
        payload = json.dumps({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        })
        await client.set(KEY_PREFIX + token, payload, ex=TOKEN_TTL_SECONDS)
        return True
    finally:
        await client.close()


async def get_or_create_telegram_user(
    db: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    """Find existing User by telegram OAuth identity or create a fresh one."""
    sub = str(telegram_id)
    q = (
        select(OAuthIdentity)
        .where(OAuthIdentity.provider == PROVIDER, OAuthIdentity.provider_subject == sub)
    )
    existing = (await db.execute(q)).scalar_one_or_none()
    if existing:
        user = await db.get(User, existing.user_id)
        if user is None:
            # identity row pointing at deleted user — repair
            await db.delete(existing)
            await db.flush()
        else:
            user.last_login_at = datetime.utcnow()
            await db.commit()
            return user

    # Create new non-anonymous user
    user = User(
        is_anonymous=False,
        first_name=first_name,
        last_name=last_name,
        last_login_at=datetime.utcnow(),
    )
    from services.billing_service import start_trial
    start_trial(user)
    db.add(user)
    await db.flush()  # need user.id for OAuthIdentity

    identity = OAuthIdentity(
        user_id=user.id,
        provider=PROVIDER,
        provider_subject=sub,
        email=None,
    )
    db.add(identity)
    await db.commit()
    await db.refresh(user)
    logger.info("Created TG user id=%s telegram_id=%s username=%s", user.id, telegram_id, username)
    return user
