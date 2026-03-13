from types import SimpleNamespace

import httpx
import pytest

from llm_client import LLMClient, LLMPermanentError, LLMTransientError


class FakeAsyncClient:
    def __init__(self, error=None, response=None, capture_json=None):
        self._error = error
        self._response = response
        self._capture_json = capture_json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        if self._capture_json is not None:
            self._capture_json.append(kwargs.get("json"))
        if self._error is not None:
            raise self._error
        return self._response


@pytest.mark.asyncio
async def test_analyze_dream_raises_transient_for_503(monkeypatch):
    request = httpx.Request("POST", "http://llm.test/analyze")
    response = httpx.Response(503, request=request, text="service unavailable")
    error = httpx.HTTPStatusError("boom", request=request, response=response)
    monkeypatch.setattr("llm_client.httpx.AsyncClient", lambda timeout: FakeAsyncClient(error))

    client = LLMClient(base_url="http://llm.test")

    with pytest.raises(LLMTransientError):
        await client.analyze_dream("dream text long enough")


@pytest.mark.asyncio
async def test_analyze_dream_raises_permanent_for_400(monkeypatch):
    request = httpx.Request("POST", "http://llm.test/analyze")
    response = httpx.Response(400, request=request, text="bad request")
    error = httpx.HTTPStatusError("boom", request=request, response=response)
    monkeypatch.setattr("llm_client.httpx.AsyncClient", lambda timeout: FakeAsyncClient(error))

    client = LLMClient(base_url="http://llm.test")

    with pytest.raises(LLMPermanentError):
        await client.analyze_dream("dream text long enough")


@pytest.mark.asyncio
async def test_analyze_dream_truncates_user_description(monkeypatch):
    captured = []
    request = httpx.Request("POST", "http://llm.test/analyze")
    response = httpx.Response(200, request=request, json={"analysis_text": "ok"})
    monkeypatch.setattr(
        "llm_client.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(response=response, capture_json=captured),
    )

    client = LLMClient(base_url="http://llm.test")
    long_description = "x" * 1400

    result = await client.analyze_dream_structured(
        "dream text long enough",
        user_description=long_description,
    )

    assert result.analysis_text == "ok"
    assert captured[0]["user_description"] == "x" * 1000


@pytest.mark.asyncio
async def test_analyze_dream_structured_parses_symbol_entities(monkeypatch):
    request = httpx.Request("POST", "http://llm.test/analyze")
    response = httpx.Response(
        200,
        request=request,
        json={
            "analysis_text": "ok",
            "symbol_entities": [
                {
                    "canonical_name": "лес",
                    "display_label": "темный лес",
                    "entity_type": "place",
                    "weight": 0.9,
                    "source_chunk_indexes": [0, 2],
                    "related_archetypes": ["Тень"],
                }
            ],
        },
    )
    monkeypatch.setattr(
        "llm_client.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(response=response),
    )

    client = LLMClient(base_url="http://llm.test")
    result = await client.analyze_dream_structured("dream text long enough")

    assert len(result.symbol_entities) == 1
    assert result.symbol_entities[0].display_label == "темный лес"
