"""Phase 4: End-to-end integration test.

Sends a chat message that triggers a tool call, then verifies the data
appears in the REST API. Requires Bedrock credentials.

Run: pytest tests/phase4/test_integration.py -m integration -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from langchain_core.messages import HumanMessage


@pytest.fixture
def app_with_real_graph(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    import backend.tools.notes as nm
    import backend.tools.todos as tm
    import backend.tools.calendar as cm
    import backend.api.routers.notes as notes_router
    import backend.api.routers.todos as todos_router
    import backend.api.routers.calendar as cal_router
    import backend.api.dependencies as deps

    store_n = JsonStore("notes", data_dir=str(tmp_path))
    store_t = JsonStore("todos", data_dir=str(tmp_path))
    store_c = JsonStore("calendar", data_dir=str(tmp_path))

    nm._store = store_n
    tm._store = store_t
    cm._store = store_c
    notes_router._store = store_n
    todos_router._store = store_t
    cal_router._store = store_c

    from backend.agent.graph import build_graph, reset_graph
    reset_graph()
    from backend.tools.registry import ALL_TOOLS
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
        # Chat request that should trigger create_note tool
        r = await client.post("/chat", json={
            "message": "Please create a note titled 'Integration Test' with content 'E2E verified'",
            "session_id": "e2e-test",
        })
        assert r.status_code == 200

        # Verify note appears in REST endpoint
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
        r = await client.post("/chat", json={
            "message": "Add a high priority todo: Complete integration tests",
            "session_id": "e2e-test-2",
        })
        assert r.status_code == 200

        r = await client.get("/todos")
        assert r.status_code == 200
        todos = r.json()
        texts = [t["text"] for t in todos]
        assert any("integration" in t.lower() or "complete" in t.lower() for t in texts), (
            f"Expected todo not found. Todos: {texts}"
        )
