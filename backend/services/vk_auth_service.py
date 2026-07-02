"""VK ID OAuth 2.0 — state-based polling pattern (same as Yandex)."""

import json
import uuid

import httpx
from redis import asyncio as redis_asyncio

from config import settings

STATE_TTL = 600
KEY_PREFIX = "vk_auth:"
VK_TOKEN_URL = "https://oauth.vk.com/access_token"
VK_AUTH_BASE = "https://oauth.vk.com/authorize"
REDIRECT_URI = "https://app.innercore.art/auth/callback/vk"
VK_API_VERSION = "5.131"


async def _redis():
    return redis_asyncio.from_url(settings.redis_url, decode_responses=True)


def _require_settings():
    if not settings.vk_client_id or not settings.vk_client_secret:
        raise RuntimeError("vk_auth_not_configured")


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
        "client_id": settings.vk_client_id or "",
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email",
        "state": state,
        "v": VK_API_VERSION,
    })
    return f"{VK_AUTH_BASE}?{params}"


async def exchange_code(code: str) -> dict:
    """Exchange authorization code → token. VK returns user_id + optional email in response."""
    _require_settings()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            VK_TOKEN_URL,
            params={
                "client_id": settings.vk_client_id,
                "client_secret": settings.vk_client_secret.get_secret_value(),
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
        )
    if r.status_code != 200:
        raise ValueError(f"vk_token_exchange_failed: {r.status_code}")
    data = r.json()
    if "error" in data:
        raise ValueError(f"vk_error: {data.get('error_description', data['error'])}")
    return data


async def complete_state(state: str, access_token: str, refresh_token: str) -> None:
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
