"""Phase 3: API endpoint tests using httpx AsyncClient (no real server needed).

Run: pytest tests/phase3/test_api_endpoints.py -v
"""
import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage, HumanMessage

AUTH_HEADERS = {
    "x-jarvis-internal-auth": "test-internal-token",
    "x-jarvis-user-email": "majg2708@gmail.com",
}


@pytest.fixture(autouse=True)
def isolated_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    from backend.storage.sqlite_store import SQLiteStore
    from backend.config import settings
    import backend.services.notes_service as notes_svc
    import backend.services.todos_service as todos_svc
    import backend.services.thread_service as thread_svc
    import backend.services.thread_memory_service as memory_svc
    import backend.services.message_service as message_svc

    monkeypatch.setattr(settings, "database_path", str(tmp_path / "jarvis.db"))
    monkeypatch.setattr(settings, "auth_allowed_emails", "majg2708@gmail.com")
    monkeypatch.setattr(settings, "backend_internal_auth_token", "test-internal-token")
    monkeypatch.setattr(settings, "backend_auth_token_secret", "test-ws-secret")
    notes_svc._store = JsonStore("notes", data_dir=str(tmp_path))
    todos_svc._store = JsonStore("todos", data_dir=str(tmp_path))
    thread_svc._store = SQLiteStore("threads", thread_svc.THREADS_SCHEMA)
    memory_svc._store = SQLiteStore("thread_memory", memory_svc.THREAD_MEMORY_SCHEMA)
    message_svc._store = SQLiteStore("messages", message_svc.MESSAGES_SCHEMA)


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
async def test_chat_endpoint_normalizes_structured_model_content(app):
    from unittest.mock import AsyncMock, MagicMock

    import backend.api.routers.chat as chat_router

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [MagicMock(content=[{"text": "Hello from structured content"}])]}
    )
    app.dependency_overrides[chat_router.get_jarvis_graph] = lambda: mock_graph

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
            r = await client.post("/chat", json={"message": "Hello", "session_id": "structured-content"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["content"] == "Hello from structured content"


@pytest.mark.asyncio
async def test_email_list_route(app, monkeypatch):
    import backend.services.email_service as email_svc

    monkeypatch.setattr(email_svc, "gmail_available", lambda: True)
    monkeypatch.setattr(
        email_svc,
        "list_emails",
        lambda max_results, label: [
            {
                "message_id": "msg-1",
                "thread_id": "thread-1",
                "sender": "sender@example.com",
                "recipient": "me@example.com",
                "subject": "Hello",
                "body": "",
                "snippet": "Preview",
                "date": "2026-06-10",
                "labels": ["INBOX", "UNREAD"],
                "is_read": False,
            }
        ],
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.get("/emails")
    assert r.status_code == 200
    assert r.json()[0]["thread_id"] == "thread-1"
    assert r.json()[0]["is_read"] is False


@pytest.mark.asyncio
async def test_email_routes_return_503_when_unconfigured(app, monkeypatch):
    import backend.services.email_service as email_svc

    monkeypatch.setattr(email_svc, "gmail_available", lambda: False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.get("/emails")
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_email_routes_return_403_when_gmail_is_not_authorized(app, monkeypatch):
    import backend.services.email_service as email_svc

    monkeypatch.setattr(email_svc, "gmail_available", lambda: True)
    monkeypatch.setattr(
        email_svc,
        "list_emails",
        lambda max_results, label: (_ for _ in ()).throw(
            email_svc.EmailAuthorizationError("Gmail access is configured but not authorized")
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.get("/emails")

    assert r.status_code == 403
    assert "not authorized" in r.json()["detail"]


@pytest.mark.asyncio
async def test_chat_threads_list_messages_and_delete(app):
    import backend.services.thread_memory_service as memory_svc

    memory_svc.save_thread_memory(
        "thread-1",
        [HumanMessage(content="Remember my color is blue"), AIMessage(content="I will remember.")],
        user_id="majg2708@gmail.com",
        session_id="thread-1",
    )
    memory_svc.save_thread_memory(
        "other-thread",
        [HumanMessage(content="Private")],
        user_id="other@example.com",
        session_id="other-thread",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        listed = await client.get("/chat/threads")
        messages = await client.get("/chat/threads/thread-1/messages")
        other_messages = await client.get("/chat/threads/other-thread/messages")
        deleted = await client.delete("/chat/threads/thread-1")
        deleted_messages = await client.get("/chat/threads/thread-1/messages")

    assert listed.status_code == 200
    thread_ids = [thread["id"] for thread in listed.json()]
    assert "thread-1" in thread_ids
    assert "other-thread" not in thread_ids
    assert listed.json()[0]["title"] == "Remember my color is blue"
    assert messages.status_code == 200
    assert [message["role"] for message in messages.json()] == ["user", "assistant"]
    assert messages.json()[0]["content"] == "Remember my color is blue"
    assert other_messages.status_code == 404
    assert deleted.status_code == 204
    assert deleted_messages.status_code == 404


@pytest.mark.asyncio
async def test_chat_attachment_upload_returns_source(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        files = {"file": ("memo.txt", b"hello from chat", "text/plain")}
        response = await client.post("/chat/attachments", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["source"]["original_filename"] == "memo.txt"
    assert body["source"]["source_id"].startswith("file-")
    assert "hello from chat" in body["extracted_preview"]


@pytest.mark.asyncio
async def test_email_search_thread_draft_and_labels(app, monkeypatch):
    import backend.services.email_service as email_svc

    monkeypatch.setattr(email_svc, "gmail_available", lambda: True)
    monkeypatch.setattr(email_svc, "search_emails", lambda query, max_results: [])
    monkeypatch.setattr(email_svc, "get_thread", lambda thread_id: {"thread_id": thread_id, "messages": []})
    monkeypatch.setattr(
        email_svc,
        "create_draft",
        lambda **kwargs: {"id": "draft-1", "subject": kwargs["subject"]},
    )
    monkeypatch.setattr(email_svc, "send_email", lambda **kwargs: {"id": "sent-1", "subject": kwargs["subject"]})
    monkeypatch.setattr(email_svc, "send_draft", lambda draft_id, user_confirmed: {"id": "sent-draft", "draft": draft_id})
    monkeypatch.setattr(email_svc, "list_labels", lambda page_size: {"labels": []})
    monkeypatch.setattr(email_svc, "create_label", lambda display_name, color=None: {"labelId": "Label_1", "name": display_name})
    monkeypatch.setattr(email_svc, "update_label", lambda label_id, display_name=None, color=None: {"labelId": label_id, "name": display_name})
    monkeypatch.setattr(email_svc, "apply_labels_to_thread", lambda thread_id, label_ids: {})
    monkeypatch.setattr(email_svc, "remove_labels_from_message", lambda message_id, label_ids: {})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        assert (await client.get("/emails/search", params={"q": "is:unread"})).status_code == 200
        thread = await client.get("/emails/threads/thread-1")
        draft = await client.post("/emails/drafts", json={"to": ["a@example.com"], "subject": "Hi"})
        sent = await client.post("/emails/send", json={"to": ["a@example.com"], "subject": "Hi", "userConfirmed": True})
        sent_draft = await client.post("/emails/drafts/draft-1/send", json={"userConfirmed": True})
        labels = await client.get("/emails/labels")
        created = await client.post("/emails/labels", json={"displayName": "Jarvis"})
        updated = await client.put("/emails/labels/Label_1", json={"displayName": "Jarvis Updated"})
        applied = await client.post("/emails/threads/thread-1/labels", json={"labelIds": ["Label_1"]})
        removed = await client.post("/emails/messages/msg-1/labels/remove", json={"labelIds": ["Label_1"]})

    assert thread.json()["thread_id"] == "thread-1"
    assert draft.json()["id"] == "draft-1"
    assert sent.json()["id"] == "sent-1"
    assert sent_draft.json()["id"] == "sent-draft"
    assert labels.json()["labels"] == []
    assert created.json()["name"] == "Jarvis"
    assert updated.json()["name"] == "Jarvis Updated"
    assert applied.status_code == 200
    assert removed.status_code == 200


def test_safe_email_tools_are_registered():
    from backend.tools.registry import ALL_TOOLS

    tool_names = {tool.name for tool in ALL_TOOLS}

    assert "send_email" in tool_names
    assert "send_email_draft" in tool_names
    assert "delete_email_label" not in tool_names
    assert "search_email_threads" in tool_names
    assert "get_email_thread" in tool_names
    assert "create_email_draft" in tool_names
    assert "list_email_labels" in tool_names
    assert "search_drive_files" in tool_names
    assert "get_drive_file" in tool_names
    assert "create_drive_text_file" in tool_names
    assert "create_drive_folder" in tool_names
    assert "delete_drive_file" not in tool_names
    assert "move_drive_file" not in tool_names
    assert "rename_drive_file" not in tool_names


@pytest.mark.asyncio
async def test_protected_routes_require_internal_auth(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/notes")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_routes_reject_non_whitelisted_email(app):
    headers = {
        "x-jarvis-internal-auth": "test-internal-token",
        "x-jarvis-user-email": "other@example.com",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as client:
        r = await client.get("/notes")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_and_list_notes(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.post("/notes", json={"title": "Hello", "content": "World"})
        assert r.status_code == 201
        note_id = r.json()["id"]

        r = await client.get("/notes")
        assert r.status_code == 200
        ids = [n["id"] for n in r.json()]
        assert note_id in ids


@pytest.mark.asyncio
async def test_get_note_not_found(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.get("/notes/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_and_complete_todo(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.post("/todos", json={"text": "Write tests", "priority": "high"})
        assert r.status_code == 201
        todo_id = r.json()["id"]

        r = await client.patch(f"/todos/{todo_id}/complete")
        assert r.status_code == 200
        assert r.json()["completed"] is True


@pytest.mark.asyncio
async def test_update_todo(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
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
async def test_calendar_crud(app, monkeypatch):
    import backend.services.calendar_service as calendar_svc

    events = {}

    def fake_create(title, start_datetime, end_datetime, description="", location="", calendar_id="primary"):
        event = {
            "id": "event-1",
            "title": title,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "description": description,
            "location": location,
            "created_at": "2035-12-01T00:00:00Z",
        }
        events[event["id"]] = event
        return event

    def fake_update(event_id, title=None, start_datetime=None, end_datetime=None, description=None, location=None, calendar_id="primary"):
        event = events.get(event_id)
        if not event:
            return None
        if title is not None:
            event["title"] = title
        if start_datetime is not None:
            event["start_datetime"] = start_datetime
        if end_datetime is not None:
            event["end_datetime"] = end_datetime
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location
        return event

    monkeypatch.setattr(calendar_svc, "create_calendar_event", fake_create)
    monkeypatch.setattr(calendar_svc, "list_calendar_events", lambda upcoming_only=True, calendar_id="primary": list(events.values()))
    monkeypatch.setattr(calendar_svc, "get_calendar_event", lambda event_id, calendar_id="primary": events.get(event_id))
    monkeypatch.setattr(calendar_svc, "update_calendar_event", fake_update)
    monkeypatch.setattr(
        calendar_svc,
        "delete_calendar_event",
        lambda event_id, calendar_id="primary": f"Event {event_id} deleted." if events.pop(event_id, None) else f"Event {event_id} not found.",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
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
async def test_calendar_rejects_invalid_dates(app, monkeypatch):
    import backend.services.calendar_service as calendar_svc

    def fake_create(title, start_datetime, end_datetime, description="", location="", calendar_id="primary"):
        if start_datetime == "not-a-date":
            raise ValueError("Invalid calendar datetime: not-a-date")
        raise ValueError("Calendar event end_datetime must be after start_datetime.")

    monkeypatch.setattr(calendar_svc, "create_calendar_event", fake_create)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
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
async def test_calendar_upcoming_filter(app, monkeypatch):
    import backend.services.calendar_service as calendar_svc

    all_events = [
        {
            "id": "past",
            "title": "Past event",
            "start_datetime": "2000-01-01T09:00:00",
            "end_datetime": "2000-01-01T10:00:00",
            "description": "",
            "location": "",
            "created_at": "2000-01-01T00:00:00Z",
        },
        {
            "id": "future",
            "title": "Future event",
            "start_datetime": "2035-01-01T09:00:00",
            "end_datetime": "2035-01-01T10:00:00",
            "description": "",
            "location": "",
            "created_at": "2035-01-01T00:00:00Z",
        },
    ]

    def fake_create(title, start_datetime, end_datetime, description="", location="", calendar_id="primary"):
        return next(event for event in all_events if event["title"] == title)

    def fake_list(upcoming_only=True, calendar_id="primary"):
        return [event for event in all_events if not upcoming_only or event["id"] == "future"]

    monkeypatch.setattr(calendar_svc, "create_calendar_event", fake_create)
    monkeypatch.setattr(calendar_svc, "list_calendar_events", fake_list)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=AUTH_HEADERS) as client:
        r = await client.post("/notes", json={"title": "Delete me", "content": "..."})
        note_id = r.json()["id"]
        r = await client.delete(f"/notes/{note_id}")
        assert r.status_code == 204
        r = await client.get(f"/notes/{note_id}")
        assert r.status_code == 404
