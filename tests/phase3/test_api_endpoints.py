"""Phase 3: API endpoint tests using httpx AsyncClient (no real server needed).

Run: pytest tests/phase3/test_api_endpoints.py -v
"""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    from backend.storage.sqlite_store import SQLiteStore
    from backend.config import settings
    import backend.services.calendar_service as calendar_svc
    import backend.services.message_service as message_svc
    import backend.services.notes_service as notes_svc
    import backend.services.thread_memory_service as memory_svc
    import backend.services.thread_service as thread_svc
    import backend.services.todos_service as todos_svc

    monkeypatch.setattr(settings, "database_path", str(tmp_path / "jarvis.db"))
    calendar_svc._store = SQLiteStore("calendar_events", calendar_svc.CALENDAR_SCHEMA)
    message_svc._store = SQLiteStore("messages", message_svc.MESSAGES_SCHEMA)
    notes_svc._store = JsonStore("notes", data_dir=str(tmp_path))
    memory_svc._store = SQLiteStore("thread_memory", memory_svc.THREAD_MEMORY_SCHEMA)
    thread_svc._store = SQLiteStore("threads", thread_svc.THREADS_SCHEMA)
    todos_svc._store = JsonStore("todos", data_dir=str(tmp_path))


@pytest.fixture
def app():
    # Patch get_jarvis_graph so tests don't need a real Ollama backend
    from unittest.mock import AsyncMock, MagicMock
    import backend.api.dependencies as deps

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={"messages": [MagicMock(content="Hello from Jarvis!")]})
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
async def test_email_routes_are_not_mounted(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/emails")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_threads_crud_and_messages(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/threads", json={"title": "Planning"})
        assert r.status_code == 201
        thread_id = r.json()["id"]

        r = await client.put(f"/threads/{thread_id}", json={"title": "Updated planning"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated planning"

        r = await client.post("/chat", json={"message": "Hello", "session_id": thread_id})
        assert r.status_code == 200

        r = await client.get(f"/threads/{thread_id}/messages")
        assert r.status_code == 200
        messages = r.json()
        assert [message["role"] for message in messages] == ["user", "assistant"]
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hello from Jarvis!"

        r = await client.delete(f"/threads/{thread_id}")
        assert r.status_code == 204
        r = await client.get(f"/threads/{thread_id}")
        assert r.status_code == 404


def test_email_tools_are_not_registered():
    from backend.tools.registry import ALL_TOOLS

    tool_names = {tool.name for tool in ALL_TOOLS}

    assert "list_emails" not in tool_names
    assert "get_email" not in tool_names
    assert "send_email" not in tool_names
    assert "search_emails" not in tool_names


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
async def test_update_todo(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/todos", json={"text": "Original task", "priority": "low"})
        assert r.status_code == 201
        todo_id = r.json()["id"]

        r = await client.put(
            f"/todos/{todo_id}",
            json={"text": "Updated task", "priority": "high", "due_date": "2026-05-05"},
        )
        assert r.status_code == 200
        assert r.json()["text"] == "Updated task"
        assert r.json()["priority"] == "high"
        assert r.json()["due_date"].startswith("2026-05-05")


@pytest.mark.asyncio
async def test_calendar_crud(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/calendar",
            json={
                "title": "Team standup",
                "start_datetime": "2035-12-01T09:00:00",
                "end_datetime": "2035-12-01T09:30:00",
                "description": "Daily sync",
                "location": "Room 1",
            },
        )
        assert r.status_code == 201
        event = r.json()
        event_id = event["id"]
        assert event["title"] == "Team standup"
        assert event["description"] == "Daily sync"
        assert event["location"] == "Room 1"

        r = await client.get("/calendar")
        assert r.status_code == 200
        assert event_id in [item["id"] for item in r.json()]

        r = await client.get(f"/calendar/{event_id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Team standup"

        r = await client.put(
            f"/calendar/{event_id}",
            json={
                "title": "Updated standup",
                "start_datetime": "2035-12-01T10:00:00",
                "end_datetime": "2035-12-01T10:45:00",
                "description": "Updated sync",
                "location": "Room 2",
            },
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated standup"
        assert r.json()["start_datetime"].startswith("2035-12-01T10:00:00")
        assert r.json()["end_datetime"].startswith("2035-12-01T10:45:00")
        assert r.json()["description"] == "Updated sync"
        assert r.json()["location"] == "Room 2"

        r = await client.delete(f"/calendar/{event_id}")
        assert r.status_code == 204

        r = await client.get(f"/calendar/{event_id}")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_calendar_rejects_invalid_dates(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/calendar",
            json={
                "title": "Bad date",
                "start_datetime": "not-a-date",
                "end_datetime": "2035-12-01T09:30:00",
            },
        )
        assert r.status_code == 400

        r = await client.post(
            "/calendar",
            json={
                "title": "Backwards event",
                "start_datetime": "2035-12-01T09:30:00",
                "end_datetime": "2035-12-01T09:00:00",
            },
        )
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_calendar_upcoming_filter(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        past = await client.post(
            "/calendar",
            json={
                "title": "Past event",
                "start_datetime": "2000-01-01T09:00:00",
                "end_datetime": "2000-01-01T10:00:00",
            },
        )
        future = await client.post(
            "/calendar",
            json={
                "title": "Future event",
                "start_datetime": "2035-01-01T09:00:00",
                "end_datetime": "2035-01-01T10:00:00",
            },
        )
        assert past.status_code == 201
        assert future.status_code == 201

        r = await client.get("/calendar")
        assert r.status_code == 200
        titles = [event["title"] for event in r.json()]
        assert "Future event" in titles
        assert "Past event" not in titles

        r = await client.get("/calendar", params={"upcoming_only": False})
        assert r.status_code == 200
        titles = [event["title"] for event in r.json()]
        assert "Past event" in titles
        assert "Future event" in titles


@pytest.mark.asyncio
async def test_delete_note(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/notes", json={"title": "Delete me", "content": "..."})
        note_id = r.json()["id"]
        r = await client.delete(f"/notes/{note_id}")
        assert r.status_code == 204
        r = await client.get(f"/notes/{note_id}")
        assert r.status_code == 404
