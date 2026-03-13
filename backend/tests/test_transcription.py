from io import BytesIO
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException, UploadFile

from api import audio as audio_api
from services import transcription_service


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        if self._error is not None:
            raise self._error
        return self._response


@pytest.mark.asyncio
async def test_transcribe_audio_returns_text(monkeypatch):
    request = httpx.Request("POST", "https://api.cometapi.com/v1/audio/transcriptions")
    response = httpx.Response(200, request=request, json={"text": "dream transcription"})
    monkeypatch.setattr(
        transcription_service,
        "settings",
        SimpleNamespace(
            transcriptions_base_url="https://api.cometapi.com",
            transcriptions_model="whisper-1",
            transcriptions_api_key=SimpleNamespace(get_secret_value=lambda: "key-1"),
            embeddings_api_key=None,
        ),
    )
    monkeypatch.setattr(
        transcription_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(response=response),
    )

    result = await transcription_service.transcribe_audio(
        filename="recording.m4a",
        content=b"audio",
        content_type="audio/mp4",
        language="ru",
    )

    assert result == "dream transcription"


@pytest.mark.asyncio
async def test_transcribe_audio_raises_transient_for_503(monkeypatch):
    request = httpx.Request("POST", "https://api.cometapi.com/v1/audio/transcriptions")
    response = httpx.Response(503, request=request, text="unavailable")
    error = httpx.HTTPStatusError("boom", request=request, response=response)
    monkeypatch.setattr(
        transcription_service,
        "settings",
        SimpleNamespace(
            transcriptions_base_url="https://api.cometapi.com",
            transcriptions_model="whisper-1",
            transcriptions_api_key=SimpleNamespace(get_secret_value=lambda: "key-1"),
            embeddings_api_key=None,
        ),
    )
    monkeypatch.setattr(
        transcription_service.httpx,
        "AsyncClient",
        lambda timeout: FakeAsyncClient(error=error),
    )

    with pytest.raises(transcription_service.TranscriptionTransientError):
        await transcription_service.transcribe_audio(filename="recording.m4a", content=b"audio")


@pytest.mark.asyncio
async def test_create_transcription_endpoint_returns_schema(monkeypatch):
    async def fake_transcribe_audio(**kwargs):
        assert kwargs["filename"] == "recording.m4a"
        assert kwargs["language"] == "ru"
        return "transcribed text"

    monkeypatch.setattr(audio_api, "transcribe_audio", fake_transcribe_audio)

    upload = UploadFile(
        filename="recording.m4a",
        file=BytesIO(b"audio-bytes"),
        headers={"content-type": "audio/mp4"},
    )

    response = await audio_api.create_transcription(
        current_user=SimpleNamespace(id="user-1"),
        file=upload,
        language="ru",
        prompt=None,
    )

    assert response.text == "transcribed text"


@pytest.mark.asyncio
async def test_create_transcription_endpoint_maps_provider_errors(monkeypatch):
    async def fake_transcribe_audio(**kwargs):
        raise transcription_service.TranscriptionPermanentError("bad audio")

    monkeypatch.setattr(audio_api, "transcribe_audio", fake_transcribe_audio)

    upload = UploadFile(
        filename="recording.m4a",
        file=BytesIO(b"audio-bytes"),
        headers={"content-type": "audio/mp4"},
    )

    with pytest.raises(HTTPException, match="bad audio") as exc:
        await audio_api.create_transcription(
            current_user=SimpleNamespace(id="user-1"),
            file=upload,
            language=None,
            prompt=None,
        )

    assert exc.value.status_code == 400
