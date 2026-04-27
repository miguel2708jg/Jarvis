"""Phase 4: End-to-end integration test.

Sends a chat message that triggers a tool call, then verifies the data
appears in the REST API. Requires an Ollama model configured in `.env` or
environment variables.

Run: pytest tests/phase4/test_integration.py -m integration -v
"""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app_with_real_graph(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    import backend.api.dependencies as deps
    import backend.services.notes_service as notes_svc
    import backend.services.todos_service as todos_svc

    notes_svc._store = JsonStore("notes", data_dir=str(tmp_path))
    todos_svc._store = JsonStore("todos", data_dir=str(tmp_path))

    from backend.agent.graph import build_graph, reset_graph
    from backend.tools.registry import ALL_TOOLS

    reset_graph()
    graph = build_graph(tools=ALL_TOOLS)
    deps.get_jarvis_graph = lambda: graph

    from backend.api.main import app

    yield app
    reset_graph()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chat_creates_note_visible_via_rest(app_with_real_graph):
    """Send a chat message asking to create a note; verify it appears in GET /notes."""
    async with AsyncClient(transport=ASGITransport(app=app_with_real_graph), base_url="http://test") as client:
        r = await client.post(
            "/chat",
            json={
                "message": "Please create a note titled 'Integration Test' with content 'E2E verified'",
                "session_id": "e2e-test",
            },
        )
        assert r.status_code == 200

        r = await client.get("/notes")
        assert r.status_code == 200
        notes = r.json()
        titles = [n["title"] for n in notes]
        assert any("Integration" in t for t in titles), f"Expected note not found. Notes: {titles}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chat_creates_todo_visible_via_rest(app_with_real_graph):
    """Send a chat message asking to create a todo; verify it appears in GET /todos."""
    async with AsyncClient(transport=ASGITransport(app=app_with_real_graph), base_url="http://test") as client:
        r = await client.post(
            "/chat",
            json={
                "message": "Add a high priority todo: Complete integration tests",
                "session_id": "e2e-test-2",
            },
        )
        assert r.status_code == 200

        r = await client.get("/todos")
        assert r.status_code == 200
        todos = r.json()
        texts = [t["text"] for t in todos]
        assert any("integration" in t.lower() or "complete" in t.lower() for t in texts), (
            f"Expected todo not found. Todos: {texts}"
        )
