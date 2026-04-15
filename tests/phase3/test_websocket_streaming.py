"""Phase 3: WebSocket streaming tests.

Run: pytest tests/phase3/test_websocket_streaming.py -v
"""
import json
import pytest
from unittest.mock import MagicMock

from fastapi import WebSocketDisconnect


@pytest.fixture
def mock_graph():
    async def mock_astream_events(state, version="v2"):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Hello")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content=" Jarvis")}}

    graph = MagicMock()
    graph.astream_events = mock_astream_events
    return graph


class FakeWebSocket:
    def __init__(self, incoming_messages: list[str]):
        self._incoming_messages = list(incoming_messages)
        self.sent_messages: list[str] = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def receive_text(self) -> str:
        if self._incoming_messages:
            return self._incoming_messages.pop(0)
        raise WebSocketDisconnect()

    async def send_text(self, message: str):
        self.sent_messages.append(message)


@pytest.mark.asyncio
async def test_websocket_receives_tokens_and_done(mock_graph):
    from backend.api.routers.chat import ws_chat

    websocket = FakeWebSocket(
        [json.dumps({"message": "Hello", "session_id": "test-session"})]
    )

    await ws_chat(websocket, graph=mock_graph)

    frames = [json.loads(message) for message in websocket.sent_messages]

    types = [f["type"] for f in frames]
    assert websocket.accepted is True
    assert "token" in types, f"Expected 'token' frame, got: {types}"
    assert "done" in types, f"Expected 'done' frame, got: {types}"


@pytest.mark.asyncio
async def test_websocket_uses_final_model_output_when_no_stream_tokens():
    from backend.api.routers.chat import ws_chat

    class FinalOnlyGraph:
        async def astream_events(self, state, version="v2"):
            yield {"event": "on_chat_model_start", "data": {"input": state}}
            yield {
                "event": "on_tool_start",
                "name": "create_note",
                "data": {"input": {"title": "Código de teléfono", "content": "12345"}},
            }
            yield {
                "event": "on_tool_end",
                "name": "create_note",
                "data": {"output": {"id": "note-1", "title": "Código de teléfono", "content": "12345"}},
            }
            yield {"event": "on_chat_model_start", "data": {"input": state}}
            yield {
                "event": "on_chat_model_end",
                "data": {"output": MagicMock(content="He creado la nota con el código de teléfono 12345.")},
            }

    websocket = FakeWebSocket(
        [json.dumps({"message": "Crea una nota, código de teléfono 12345", "session_id": "test-session"})]
    )

    await ws_chat(websocket, graph=FinalOnlyGraph())

    frames = [json.loads(message) for message in websocket.sent_messages]
    tokens = [frame["content"] for frame in frames if frame["type"] == "token"]

    assert any("código de teléfono 12345" in token.lower() for token in tokens), frames
    assert frames[-1]["type"] == "done", frames


@pytest.mark.asyncio
async def test_websocket_sends_error_without_crashing_connection():
    from backend.api.routers.chat import ws_chat

    class FailingGraph:
        async def astream_events(self, state, version="v2"):
            if state["messages"][0].content == "first":
                raise ValueError("broken model id")
            yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="ok")}}

    websocket = FakeWebSocket(
        [
            json.dumps({"message": "first", "session_id": "test-session"}),
            json.dumps({"message": "second", "session_id": "test-session"}),
        ]
    )

    await ws_chat(websocket, graph=FailingGraph())

    frames = [json.loads(message) for message in websocket.sent_messages]
    types = [frame["type"] for frame in frames]

    assert "error" in types, f"Expected 'error' frame, got: {types}"
    assert types.count("done") == 1, f"Expected one successful 'done' frame, got: {types}"
