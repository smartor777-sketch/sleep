from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest

from services import embedding_service

from tests.helpers import FakeDb


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, headers):
        self.calls.append((url, json, headers))
        if self.error:
            raise self.error
        return self.response


def test_serialize_deserialize_and_cosine_similarity():
    raw = embedding_service.serialize_embedding([1, 2.5, 3])
    assert embedding_service.deserialize_embedding(raw) == [1.0, 2.5, 3.0]
    assert embedding_service.deserialize_embedding(None) is None
    assert embedding_service.deserialize_embedding("{bad") is None
    assert embedding_service.deserialize_embedding('{"a":1}') is None
    assert embedding_service.deserialize_embedding('["x"]') is None
    assert embedding_service.cosine_similarity([1, 0], [1, 0]) == 1.0
    assert embedding_service.cosine_similarity([0, 0], [1, 1]) == 0.0
    assert embedding_service.cosine_similarity([1], [1, 2]) == 0.0


def test_build_dream_embedding_text():
    dream = SimpleNamespace(title="Title", content="Body", comment="Note")
    assert embedding_service.build_dream_embedding_text(dream) == "Title Body Note"


@pytest.mark.asyncio
async def test_request_embedding_success(monkeypatch):
    request = httpx.Request("POST", "https://api.cometapi.com/v1/embeddings")
    response = httpx.Response(200, request=request, json={"data": [{"embedding": [1, 2, 3]}]})
    fake_client = FakeAsyncClient(response=response)
    monkeypatch.setattr(embedding_service.httpx, "AsyncClient", lambda timeout: fake_client)
    monkeypatch.setattr(embedding_service.settings, "embeddings_api_key", SimpleNamespace(get_secret_value=lambda: "secret"))
    monkeypatch.setattr(embedding_service.settings, "embeddings_base_url", "https://api.cometapi.com")
    monkeypatch.setattr(embedding_service.settings, "embeddings_model", "text-embedding-3-small")

    vec = await embedding_service.request_embedding("hello world")

    assert vec == [1.0, 2.0, 3.0]
    assert fake_client.calls[0][0] == "https://api.cometapi.com/v1/embeddings"


@pytest.mark.asyncio
async def test_request_embedding_error_paths(monkeypatch):
    monkeypatch.setattr(embedding_service.settings, "embeddings_api_key", None)
    with pytest.raises(RuntimeError, match="EMBEDDINGS_API_KEY"):
        await embedding_service.request_embedding("hello")

    monkeypatch.setattr(embedding_service.settings, "embeddings_api_key", SimpleNamespace(get_secret_value=lambda: "secret"))
    request = httpx.Request("POST", "https://api.cometapi.com/v1/embeddings")
    http_error = httpx.HTTPStatusError(
        "bad",
        request=request,
        response=httpx.Response(429, request=request, text="too many"),
    )
    monkeypatch.setattr(embedding_service.httpx, "AsyncClient", lambda timeout: FakeAsyncClient(error=http_error))
    with pytest.raises(RuntimeError, match="embedding_http_429"):
        await embedding_service.request_embedding("hello")

    req_error = httpx.RequestError("boom", request=request)
    monkeypatch.setattr(embedding_service.httpx, "AsyncClient", lambda timeout: FakeAsyncClient(error=req_error))
    with pytest.raises(RuntimeError, match="embedding_request_failed"):
        await embedding_service.request_embedding("hello")

    monkeypatch.setattr(
        embedding_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(response=httpx.Response(200, request=request, json={"data": []})),
    )
    with pytest.raises(RuntimeError, match="embedding_missing_data"):
        await embedding_service.request_embedding("hello")

    monkeypatch.setattr(
        embedding_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(response=httpx.Response(200, request=request, json={"data": [{"embedding": "bad"}]})),
    )
    with pytest.raises(RuntimeError, match="embedding_missing_vector"):
        await embedding_service.request_embedding("hello")

    monkeypatch.setattr(
        embedding_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(response=httpx.Response(200, request=request, json={"data": [{"embedding": [1, "x"]}]})),
    )
    with pytest.raises(RuntimeError, match="embedding_invalid_vector"):
        await embedding_service.request_embedding("hello")

    assert await embedding_service.request_embedding("   ") == []


@pytest.mark.asyncio
async def test_recalculate_dream_embedding_sets_fields(monkeypatch):
    async def fake_request_embedding(text):
        assert text == "Title Body Note"
        return [0.1, 0.2]

    monkeypatch.setattr(embedding_service, "request_embedding", fake_request_embedding)
    monkeypatch.setattr(embedding_service.settings, "embeddings_model", "text-embedding-3-small")

    dream = SimpleNamespace(title="Title", content="Body", comment="Note", embedding_text=None, embedding_model=None, embedding_updated_at=None)
    db = FakeDb()

    await embedding_service.recalculate_dream_embedding(db, dream)

    assert embedding_service.deserialize_embedding(dream.embedding_text) == [0.1, 0.2]
    assert dream.embedding_model == "text-embedding-3-small"
    assert isinstance(dream.embedding_updated_at, datetime)
    assert dream in db.added
