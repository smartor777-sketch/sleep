"""Yandex OAuth 2.0 auth service — state-based polling pattern (like Telegram)."""

import json
import uuid

import httpx
from redis import asyncio as redis_asyncio

from config import settings

STATE_TTL = 600  # 10 min
KEY_PREFIX = "yandex_auth:"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_URL = "https://login.yandex.ru/info?format=json"
YANDEX_AUTH_BASE = "https://oauth.yandex.ru/authorize"
REDIRECT_URI = "https://app.innercore.art/auth/callback/yandex"


async def _redis():
    return redis_asyncio.from_url(settings.redis_url, decode_responses=True)


def _require_settings():
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        raise RuntimeError("yandex_auth_not_configured")


async def create_state() -> str:
    _require_settings()
    state = uuid.uuid4().hex
    client = await _redis()
    try:
        await client.setex(KEY_PREFIX + state, STATE_TTL, "pending")
    finally:
        await client.aclose()
    return state


def build_auth_url(state: str) -> str:
    from urllib.parse import urlencode
    params = urlencode({
        "response_type": "code",
        "client_id": settings.yandex_client_id or "",
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "force_confirm": "no",
    })
    return f"{YANDEX_AUTH_BASE}?{params}"


async def exchange_code(code: str) -> dict:
    _require_settings()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            YANDEX_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.yandex_client_id,
                "client_secret": settings.yandex_client_secret.get_secret_value(),
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code != 200:
        raise ValueError(f"yandex_token_exchange_failed: {r.status_code}")
    return r.json()


async def get_user_info(yandex_token: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            YANDEX_USER_URL,
            headers={"Authorization": f"OAuth {yandex_token}"},
        )
    if r.status_code != 200:
        raise ValueError("yandex_userinfo_failed")
    return r.json()


async def complete_state(state: str, access_token: str, refresh_token: str) -> bool:
    client = await _redis()
    try:
        val = json.dumps({
            "status": "completed",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        })
        await client.setex(KEY_PREFIX + state, STATE_TTL, val)
    finally:
        await client.aclose()
    return True


async def get_state_data(state: str) -> dict | None:
    client = await _redis()
    try:
        raw = await client.get(KEY_PREFIX + state)
    finally:
        await client.aclose()
    if raw is None:
        return None
    if raw == "pending":
        return {"status": "pending"}
    try:
        return json.loads(raw)
    except Exception:
        return {"status": "pending"}
