"""Token verification for Google/Apple ID tokens."""

import time
from typing import Any

import httpx
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from config import settings

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"

_JWKS_CACHE: dict[str, dict[str, Any]] = {}
_JWKS_CACHE_TS: dict[str, float] = {}
_JWKS_TTL_SECONDS = 3600


async def _get_jwks(url: str) -> dict[str, Any]:
    now = time.time()
    cached = _JWKS_CACHE.get(url)
    cached_ts = _JWKS_CACHE_TS.get(url, 0)
    if cached and (now - cached_ts) < _JWKS_TTL_SECONDS:
        return cached

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    _JWKS_CACHE[url] = data
    _JWKS_CACHE_TS[url] = now
    return data


def _pick_key(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


async def verify_google_id_token(id_token: str) -> dict[str, Any]:
    if not settings.google_client_id:
        raise ValueError("google_client_id_not_configured")

    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise ValueError("invalid_token")

    jwks = await _get_jwks(GOOGLE_JWKS_URL)
    key = _pick_key(jwks, header.get("kid"))
    if not key:
        raise ValueError("invalid_token")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.google_client_id,
            issuer=None,
            options={"verify_aud": True, "verify_exp": True, "verify_iss": False},
        )
    except ExpiredSignatureError:
        raise ValueError("token_expired")
    except JWTClaimsError:
        raise ValueError("audience_mismatch")
    except JWTError:
        raise ValueError("invalid_token")

    issuer = claims.get("iss")
    if issuer not in ("https://accounts.google.com", "accounts.google.com"):
        raise ValueError("invalid_token")

    if not claims.get("sub"):
        raise ValueError("invalid_token")

    return claims


async def verify_apple_id_token(id_token: str) -> dict[str, Any]:
    if not settings.apple_client_id:
        raise ValueError("apple_client_id_not_configured")

    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError:
        raise ValueError("invalid_token")

    jwks = await _get_jwks(APPLE_JWKS_URL)
    key = _pick_key(jwks, header.get("kid"))
    if not key:
        raise ValueError("invalid_token")

    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=[header.get("alg", "RS256")],
            audience=settings.apple_client_id,
            issuer="https://appleid.apple.com",
            options={"verify_aud": True, "verify_exp": True, "verify_iss": True},
        )
    except ExpiredSignatureError:
        raise ValueError("token_expired")
    except JWTClaimsError:
        raise ValueError("audience_mismatch")
    except JWTError:
        raise ValueError("invalid_token")

    if not claims.get("sub"):
        raise ValueError("invalid_token")

    return claims
