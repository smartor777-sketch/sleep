"""Google Gemini provider (free tier) with model fallback chain.

Calls the native Generative Language REST API. If the primary model is
rate-limited (429) or fails transiently, we walk down an ordered chain of
fallback models (e.g. gemini-3.6-flash -> gemini-3.5-flash ->
gemini-3.5-flash-lite) to maximise availability on the free tier.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GeminiProvider:
    """Provider for chat/analysis completions via Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.6-flash",
        fallback_models: list[str] | None = None,
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout: float = 180.0,
        max_output_tokens: int = 12000,
    ):
        self.api_key = api_key
        self.model = model
        self.fallback_models = fallback_models or []
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens

    async def analyze_dream(
        self,
        dream_text: str,
        system_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """Single-turn analysis with system + user message."""
        contents = [{"role": "user", "parts": [{"text": dream_text}]}]
        return await self._generate(
            system_prompt=system_prompt,
            contents=contents,
            temperature=temperature,
        )

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn chat. Extracts the system message into systemInstruction
        and maps assistant -> model (Gemini's term) for the rest."""
        contents: list[dict] = []
        system_prompt: str | None = None
        for message in messages:
            role = str(message.get("role", "user"))
            content = message.get("content") or message.get("text") or ""
            if role == "system":
                system_prompt = (system_prompt or "") + ("\n" if system_prompt else "") + str(content)
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": str(content)}]})
        if not contents:
            contents = [{"role": "user", "parts": [{"text": ""}]}]
        return await self._generate(
            system_prompt=system_prompt,
            contents=contents,
            temperature=temperature,
        )

    async def health_check(self) -> bool:
        return bool(self.api_key)

    def _require_key(self) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        return self.api_key

    async def _generate(
        self,
        system_prompt: str | None,
        contents: list[dict],
        temperature: float,
    ) -> str:
        models = [self.model, *self.fallback_models]
        last_exc: Exception | None = None
        for model in models:
            try:
                return await self._generate_once(
                    model=model,
                    system_prompt=system_prompt,
                    contents=contents,
                    temperature=temperature,
                )
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("Gemini model %s failed (%s); %sfallbacks left",
                               model, exc, "trying " if models[-1] != model else "no ")
        raise RuntimeError(f"All Gemini models failed: {last_exc}") from last_exc

    async def _generate_once(
        self,
        model: str,
        system_prompt: str | None,
        contents: list[dict],
        temperature: float,
    ) -> str:
        url = f"{self.base_url}/v1beta/models/{model}:generateContent"
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        key = self._require_key()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, 3):  # retry transient statuses per model
                response = await client.post(url, json=payload, params={"key": key})
                if response.status_code in _RETRYABLE_STATUS and attempt < 2:
                    await asyncio.sleep(5.0 * attempt)
                    continue
                response.raise_for_status()
                break

        data = response.json()
        text = self._extract_text(data)
        if not text:
            logger.error("Empty Gemini response for %s: %s", model, str(data)[:300])
            raise ValueError(f"Empty response from Gemini ({model})")
        return text

    @staticmethod
    def _extract_text(payload: dict) -> str:
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return ""
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        if isinstance(parts, list):
            return "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        return ""