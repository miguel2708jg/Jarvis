"""Phase 2: Unit tests for Notes and Todos tools (no Ollama required).

Run: pytest tests/phase2/test_tools.py -v
"""
import os
import pytest
import tempfile


@pytest.fixture(autouse=True)
def isolated_store(monkeypatch, tmp_path):
    """Redirect all JSON stores to a temp directory per test."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.storage.json_store import JsonStore
    import backend.services.notes_service as notes_svc
    import backend.services.todos_service as todos_svc

    notes_svc._store = JsonStore("notes", data_dir=str(tmp_path))
    todos_svc._store = JsonStore("todos", data_dir=str(tmp_path))
    yield


# --- Notes ---

def test_create_and_get_note():
    from backend.tools.notes import create_note, get_note
    note = create_note.invoke({"title": "Test", "content": "Hello"})
    assert note["title"] == "Test"
    fetched = get_note.invoke({"note_id": note["id"]})
    assert fetched["content"] == "Hello"


def test_list_notes_empty():
    from backend.tools.notes import list_notes
    assert list_notes.invoke({}) == []


def test_list_notes_with_tag_filter():
    from backend.tools.notes import create_note, list_notes
    create_note.invoke({"title": "A", "content": "x", "tags": ["work"]})
    create_note.invoke({"title": "B", "content": "y", "tags": ["personal"]})
    work_notes = list_notes.invoke({"tag": "work"})
    assert len(work_notes) == 1
    assert work_notes[0]["title"] == "A"


def test_delete_note():
    from backend.tools.notes import create_note, delete_note, get_note
    note = create_note.invoke({"title": "To delete", "content": "bye"})
    result = delete_note.invoke({"note_id": note["id"]})
    assert "deleted" in result
    assert get_note.invoke({"note_id": note["id"]}) is None


def test_update_note():
    from backend.tools.notes import create_note, update_note
    note = create_note.invoke({"title": "Old title", "content": "old content"})
    updated = update_note.invoke({"note_id": note["id"], "title": "New title"})
    assert updated["title"] == "New title"
    assert updated["content"] == "old content"


# --- Todos ---

def test_create_and_list_todo():
    from backend.tools.todos import create_todo, list_todos
    todo = create_todo.invoke({"text": "Buy milk", "priority": "low"})
    assert todo["text"] == "Buy milk"
    todos = list_todos.invoke({})
    assert len(todos) == 1


def test_complete_todo():
    from backend.tools.todos import create_todo, complete_todo
    todo = create_todo.invoke({"text": "Finish report"})
    completed = complete_todo.invoke({"todo_id": todo["id"]})
    assert completed["completed"] is True


def test_update_todo():
    from backend.tools.todos import create_todo, update_todo
    todo = create_todo.invoke({"text": "Draft spec", "priority": "low"})
    updated = update_todo.invoke({
        "todo_id": todo["id"],
        "text": "Draft product spec",
        "priority": "high",
        "due_date": "2026-05-01",
    })
    assert updated["text"] == "Draft product spec"
    assert updated["priority"] == "high"
    assert updated["due_date"].startswith("2026-05-01")


def test_mcp_todo_crud_surface():
    from backend import mcp_server

    todo = mcp_server.create_todo("MCP task", "low")
    fetched = mcp_server.get_todo(todo["id"])
    assert fetched["text"] == "MCP task"

    updated = mcp_server.update_todo(todo["id"], text="Updated MCP task", priority="high")
    assert updated["text"] == "Updated MCP task"
    assert updated["priority"] == "high"


def test_list_todos_hides_completed_by_default():
    from backend.tools.todos import create_todo, complete_todo, list_todos
    todo = create_todo.invoke({"text": "Done task"})
    complete_todo.invoke({"todo_id": todo["id"]})
    assert list_todos.invoke({}) == []
    assert len(list_todos.invoke({"show_completed": True})) == 1


def test_delete_todo():
    from backend.tools.todos import create_todo, delete_todo
    todo = create_todo.invoke({"text": "To delete"})
    result = delete_todo.invoke({"todo_id": todo["id"]})
    assert "deleted" in result
