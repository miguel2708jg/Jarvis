"""Phase 3: WebSocket streaming tests.

Run: pytest tests/phase3/test_websocket_streaming.py -v
"""
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def app_with_mock_graph():
    import backend.api.dependencies as deps

    async def mock_astream_events(state, version="v2"):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Hello")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content=" Jarvis")}}

    mock_graph = MagicMock()
    mock_graph.astream_events = mock_astream_events
    deps.get_jarvis_graph = lambda: mock_graph

    from backend.api.main import app
    return app


@pytest.mark.asyncio
async def test_websocket_receives_tokens_and_done(app_with_mock_graph):
    from httpx_ws import aconnect_ws
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app_with_mock_graph), base_url="http://test") as client:
        async with aconnect_ws("/ws/chat", client) as ws:
            await ws.send_text(json.dumps({"message": "Hello", "session_id": "test-session"}))

            frames = []
            for _ in range(10):
                try:
                    msg = await ws.receive_text()
                    frame = json.loads(msg)
                    frames.append(frame)
                    if frame["type"] == "done":
                        break
                except Exception:
                    break

    types = [f["type"] for f in frames]
    assert "token" in types, f"Expected 'token' frame, got: {types}"
    assert "done" in types, f"Expected 'done' frame, got: {types}"
