"""Provider for Gonka Proxy (OpenAI-compatible API)."""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GonkaProxyProvider:
    """Provider for chat completions via Gonka Proxy."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://proxy.gonka.gg/v1",
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def analyze_dream(
        self,
        dream_text: str,
        system_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """Single-turn analysis call with system + user messages."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": dream_text},
        ]
        return await self.chat_completion(messages=messages, temperature=temperature)

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn chat completion."""
        normalized_messages = [self._normalize_message(m) for m in messages]
        payload = {
            "model": self.model,
            "messages": normalized_messages,
            "temperature": temperature,
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Requesting Gonka Proxy: model=%s, messages=%s, temperature=%s",
            self.model,
            len(normalized_messages),
            temperature,
        )

        _retryable = {502, 503, 504}
        _max_retries = 3
        _retry_delay = 5.0

        last_exc: Exception | None = None
        for attempt in range(1, _max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    break
            except httpx.HTTPStatusError as e:
                last_exc = e
                if e.response.status_code in _retryable and attempt < _max_retries:
                    logger.warning(
                        "Gonka Proxy %s on attempt %s/%s, retrying in %.0fs...",
                        e.response.status_code, attempt, _max_retries, _retry_delay,
                    )
                    await asyncio.sleep(_retry_delay)
                    continue
                logger.error(
                    "Gonka Proxy HTTP error: status=%s body=%s",
                    e.response.status_code,
                    e.response.text[:200],
                )
                raise
            except Exception as e:
                last_exc = e
                if attempt < _max_retries:
                    logger.warning(
                        "Gonka Proxy request failed on attempt %s/%s: %s, retrying...",
                        attempt, _max_retries, e,
                    )
                    await asyncio.sleep(_retry_delay)
                    continue
                logger.error("Gonka Proxy request failed: %s", e)
                raise
        else:
            raise last_exc

        content = self._extract_content(data)
        if not content:
            logger.error("Empty response content from Gonka Proxy")
            raise ValueError("Empty response from Gonka Proxy")

        return content

    async def health_check(self) -> bool:
        url = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _normalize_message(message: dict[str, Any]) -> dict[str, str]:
        role = str(message.get("role", "user"))
        content = message.get("content")
        if content is None:
            content = message.get("text", "")
        return {"role": role, "content": str(content)}

    @staticmethod
    def _extract_content(payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts).strip()
        return ""
