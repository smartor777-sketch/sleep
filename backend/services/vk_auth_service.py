"""VK ID OAuth 2.1 (id.vk.ru) with PKCE — state-based polling pattern (same as Yandex).

VK ID is VK's current-generation auth platform (distinct from the legacy
oauth.vk.com flow). It requires PKCE: a code_verifier is generated at
/init time, hashed into a code_challenge sent to the authorize URL, and
the raw verifier is sent back during token exchange. Email/phone are not
in the token response — they're claims inside the `id_token` JWT.
"""

import base64
import hashlib
import json
import secrets
import uuid

import httpx
from redis import asyncio as redis_asyncio

from config import settings

STATE_TTL = 600
KEY_PREFIX = "vk_auth:"
VK_AUTH_BASE = "https://id.vk.ru/authorize"
VK_TOKEN_URL = "https://id.vk.ru/oauth2/auth"
VK_USERS_URL = "https://api.vk.com/method/users.get"
VK_API_VERSION = "5.199"
REDIRECT_URI = "https://app.innercore.art/auth/callback/vk"


async def _redis():
    return redis_asyncio.from_url(settings.redis_url, decode_responses=True)


def _require_settings():
    if not settings.vk_client_id or not settings.vk_client_secret:
        raise RuntimeError("vk_auth_not_configured")


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(64))[:128]
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def _decode_id_token_claim(id_token: str, claim: str) -> str | None:
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get(claim)
    except Exception:
        return None


async def create_state() -> tuple[str, str]:
    """Create a state + PKCE pair. Returns (state, code_challenge)."""
    _require_settings()
    state = uuid.uuid4().hex
    verifier, challenge = _generate_pkce_pair()
    client = await _redis()
    try:
        val = json.dumps({"status": "pending", "code_verifier": verifier})
        await client.setex(KEY_PREFIX + state, STATE_TTL, val)
    finally:
        await client.aclose()
    return state, challenge


def build_auth_url(state: str, code_challenge: str) -> str:
    from urllib.parse import urlencode
    params = urlencode({
        "client_id": settings.vk_client_id or "",
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    return f"{VK_AUTH_BASE}?{params}"


async def exchange_code(code: str, state: str, device_id: str | None) -> dict:
    """Exchange authorization code -> token using the PKCE verifier stored at /init time.

    Returns a dict with at least `access_token`, `user_id` (numeric VK id,
    resolved via api.vk.com/method/users.get if not present in the token
    response), and optionally `email`/`first_name`/`last_name`.
    """
    _require_settings()

    client = await _redis()
    try:
        raw = await client.get(KEY_PREFIX + state)
    finally:
        await client.aclose()
    if raw is None:
        raise ValueError("vk_state_expired")
    try:
        state_data = json.loads(raw) if raw != "pending" else {}
    except Exception:
        state_data = {}
    code_verifier = state_data.get("code_verifier")
    if not code_verifier:
        raise ValueError("vk_pkce_verifier_missing")

    form = {
        "grant_type": "authorization_code",
        "client_id": settings.vk_client_id,
        "client_secret": settings.vk_client_secret.get_secret_value(),
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": code_verifier,
    }
    if device_id:
        form["device_id"] = device_id

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(VK_TOKEN_URL, data=form, headers={"Accept": "application/json"})
    try:
        data = r.json()
    except Exception:
        raise ValueError(f"vk_token_exchange_failed: {r.status_code}")
    if r.status_code != 200 or "error" in data:
        raise ValueError(f"vk_error: {data.get('error_description', data.get('error', r.status_code))}")

    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("vk_no_access_token")

    result = {"access_token": access_token}

    id_token = data.get("id_token")
    if id_token:
        result["email"] = _decode_id_token_claim(id_token, "email")
        result["phone"] = _decode_id_token_claim(id_token, "phone")

    user_id = data.get("user_id")
    if not user_id:
        async with httpx.AsyncClient(timeout=15) as client:
            ur = await client.get(VK_USERS_URL, params={
                "access_token": access_token,
                "fields": "first_name,last_name",
                "v": VK_API_VERSION,
            })
        try:
            udata = ur.json()
            user = (udata.get("response") or [None])[0]
        except Exception:
            user = None
        if user:
            user_id = user.get("id")
            result["first_name"] = user.get("first_name")
            result["last_name"] = user.get("last_name")

    if not user_id:
        raise ValueError("vk_no_user_id")
    result["user_id"] = user_id

    return result


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
        data = json.loads(raw)
    except Exception:
        return {"status": "pending"}
    if data.get("status") != "completed":
        return {"status": "pending"}
    return data
