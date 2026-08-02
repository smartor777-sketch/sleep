"""Provider for Mistral AI (OpenAI-compatible fallback).

Call pattern mirrors the Mistral integration used in durable-object-starter
(src/services/ai-service.js): POST https://api.mistral.ai/v1/chat/completions
with an Authorization: Bearer header and an OpenAI-style message payload.
"""

import logging

from providers.gonka_proxy import GonkaProxyProvider

logger = logging.getLogger(__name__)


class MistralProvider:
    """Fallback provider via Mistral AI (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str,
        model: str = "mistral-large-latest",
        base_url: str = "https://api.mistral.ai/v1",
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
        """Multi-turn chat completion (no internal retries)."""
        normalized_messages = [GonkaProxyProvider._normalize_message(m) for m in messages]
        payload = {
            "model": self.model,
            "messages": normalized_messages,
            "temperature": temperature,
            "max_tokens": 12000,
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Requesting Mistral: model=%s, messages=%s, temperature=%s",
            self.model,
            len(normalized_messages),
            temperature,
        )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = GonkaProxyProvider._extract_content(data)
        if not content:
            logger.error("Empty response content from Mistral")
            raise ValueError("Empty response from Mistral")

        return content
