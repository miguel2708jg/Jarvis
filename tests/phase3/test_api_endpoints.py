"""Phase 3: API endpoint tests using httpx AsyncClient (no real server needed).

Run: pytest tests/phase3/test_api_endpoints.py -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def isolated_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    import backend.api.routers.notes as notes_router
    import backend.api.routers.todos as todos_router
    import backend.api.routers.calendar as cal_router
    notes_router._store = JsonStore("notes", data_dir=str(tmp_path))
    todos_router._store = JsonStore("todos", data_dir=str(tmp_path))
    cal_router._store = JsonStore("calendar", data_dir=str(tmp_path))


@pytest.fixture
def app():
    # Patch get_jarvis_graph so tests don't need Bedrock
    from unittest.mock import MagicMock, AsyncMock
    from backend.api import main as main_mod
    import backend.api.dependencies as deps

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={
        "messages": [MagicMock(content="Hello from Jarvis!")]
    })
    deps.get_jarvis_graph = lambda: mock_graph

    from backend.api.main import app
    return app


@pytest.mark.asyncio
async def test_health(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_list_notes(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/notes", json={"title": "Hello", "content": "World"})
        assert r.status_code == 201
        note_id = r.json()["id"]

        r = await client.get("/notes")
        assert r.status_code == 200
        ids = [n["id"] for n in r.json()]
        assert note_id in ids


@pytest.mark.asyncio
async def test_get_note_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/notes/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_and_complete_todo(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/todos", json={"text": "Write tests", "priority": "high"})
        assert r.status_code == 201
        todo_id = r.json()["id"]

        r = await client.patch(f"/todos/{todo_id}/complete")
        assert r.status_code == 200
        assert r.json()["completed"] is True


@pytest.mark.asyncio
async def test_create_calendar_event(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/calendar", json={
            "title": "Team standup",
            "start_datetime": "2024-12-01T09:00:00",
            "end_datetime": "2024-12-01T09:30:00",
        })
    assert r.status_code == 201
    assert r.json()["title"] == "Team standup"


@pytest.mark.asyncio
async def test_delete_note(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/notes", json={"title": "Delete me", "content": "..."})
        note_id = r.json()["id"]
        r = await client.delete(f"/notes/{note_id}")
        assert r.status_code == 204
        r = await client.get(f"/notes/{note_id}")
        assert r.status_code == 404
