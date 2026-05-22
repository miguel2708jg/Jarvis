"""Phase 3: Voice endpoint tests with external services mocked."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_chat_stores(monkeypatch, tmp_path):
    from backend.config import settings
    from backend.storage.sqlite_store import SQLiteStore
    import backend.services.message_service as message_svc
    import backend.services.thread_memory_service as memory_svc
    import backend.services.thread_service as thread_svc

    monkeypatch.setattr(settings, "database_path", str(tmp_path / "jarvis.db"))
    message_svc._store = SQLiteStore("messages", message_svc.MESSAGES_SCHEMA)
    memory_svc._store = SQLiteStore("thread_memory", memory_svc.THREAD_MEMORY_SCHEMA)
    thread_svc._store = SQLiteStore("threads", thread_svc.THREADS_SCHEMA)


def test_convert_to_wav_reports_ffmpeg_failure(monkeypatch):
    from backend.api.routers import voice

    class Result:
        returncode = 1
        stderr = b"bad audio"
        stdout = b""

    monkeypatch.setattr(voice.subprocess, "run", lambda *args, **kwargs: Result())

    with pytest.raises(ValueError, match="Audio conversion failed: bad audio"):
        voice._convert_to_wav(b"not audio", "audio/webm")


@pytest.mark.asyncio
async def test_tts_rejects_empty_text(monkeypatch):
    from backend.api.routers import voice
    from backend.api.main import app

    monkeypatch.setattr(voice, "_synthesize", lambda text: "audio")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/voice/tts", json={"text": "   "})

    assert r.status_code == 400


@pytest.mark.asyncio
async def test_voice_pipeline_returns_transcript_reply_and_audio(monkeypatch):
    from backend.api.routers import voice
    from backend.api.main import app

    async def fake_transcribe(wav_content: bytes) -> str:
        assert wav_content == b"wav"
        return "Create a todo"

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={"messages": [MagicMock(content="Todo created")]})

    monkeypatch.setattr(voice, "_convert_to_wav", lambda content, content_type: b"wav")
    monkeypatch.setattr(voice, "_transcribe", fake_transcribe)
    monkeypatch.setattr(voice, "_synthesize", lambda text: "base64-wav")
    app.dependency_overrides[voice.get_jarvis_graph] = lambda: mock_graph

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/voice",
                data={"session_id": "voice-session", "personality_id": "focus"},
                files={"audio": ("recording.webm", b"abc", "audio/webm")},
            )
    finally:
        app.dependency_overrides.pop(voice.get_jarvis_graph, None)

    assert r.status_code == 200
    assert r.json() == {
        "transcript": "Create a todo",
        "response_text": "Todo created",
        "audio_base64": "base64-wav",
        "session_id": "voice-session",
    }
