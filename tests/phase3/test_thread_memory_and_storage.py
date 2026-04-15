"""Phase 3: Coverage for thread memory and SQLite compatibility."""

from langchain_core.messages import AIMessage, HumanMessage


def _make_sqlite_store(monkeypatch, tmp_path, table_name: str, schema: str, db_name: str):
    import backend.storage.sqlite_store as sqlite_store_mod

    db_path = tmp_path / db_name
    monkeypatch.setattr(sqlite_store_mod.settings, "database_path", str(db_path), raising=False)
    monkeypatch.setattr(sqlite_store_mod.settings, "data_dir", str(tmp_path / "ignored"), raising=False)
    return sqlite_store_mod.SQLiteStore(table_name, schema)


def test_sqlite_store_uses_database_path(monkeypatch, tmp_path):
    schema = """
    CREATE TABLE IF NOT EXISTS samples (
        id TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """
    store = _make_sqlite_store(monkeypatch, tmp_path, "samples", schema, "nested/custom.db")

    store.set("sample-1", {"id": "sample-1", "value": "stored"})

    assert store.db_path == tmp_path / "nested" / "custom.db"
    assert store.get("sample-1")["value"] == "stored"


def test_load_memory_merges_saved_history_with_current_turn(monkeypatch, tmp_path):
    import backend.agent.nodes as nodes
    import backend.services.thread_memory_service as memory_svc

    monkeypatch.setattr(
        memory_svc,
        "_store",
        _make_sqlite_store(monkeypatch, tmp_path, "thread_memory", memory_svc.THREAD_MEMORY_SCHEMA, "memory.db"),
    )

    memory_svc.save_thread_memory(
        "thread-1",
        [HumanMessage(content="Remember this"), AIMessage(content="Stored reply")],
    )

    update = nodes._load_memory_if_needed(
        {
            "messages": [HumanMessage(content="New question")],
            "session_id": "thread-1",
        }
    )

    assert update["memory_loaded"] is True
    assert [message.content for message in update["messages"]] == [
        "Remember this",
        "Stored reply",
        "New question",
    ]


def test_load_memory_marks_new_threads_as_loaded(monkeypatch, tmp_path):
    import backend.agent.nodes as nodes
    import backend.services.thread_memory_service as memory_svc

    monkeypatch.setattr(
        memory_svc,
        "_store",
        _make_sqlite_store(monkeypatch, tmp_path, "thread_memory", memory_svc.THREAD_MEMORY_SCHEMA, "fresh.db"),
    )

    update = nodes._load_memory_if_needed(
        {
            "messages": [HumanMessage(content="Fresh chat")],
            "session_id": "fresh-thread",
        }
    )

    assert update["memory_loaded"] is True
    assert [message.content for message in update["messages"]] == ["Fresh chat"]


def test_notes_service_imports_legacy_json(monkeypatch, tmp_path):
    import backend.services.notes_service as notes_svc
    from backend.models.note import Note
    from backend.storage.json_store import JsonStore

    legacy_dir = tmp_path / "data"
    legacy_store = JsonStore("notes", data_dir=str(legacy_dir))
    note = Note(title="Legacy note", content="Imported content", tags=["Work", "work"])
    legacy_store.set(note.id, note.model_dump())

    monkeypatch.setattr(
        notes_svc,
        "_store",
        _make_sqlite_store(monkeypatch, tmp_path, "notes", notes_svc.NOTES_SCHEMA, "notes.db"),
    )
    monkeypatch.setattr(notes_svc.settings, "data_dir", str(legacy_dir), raising=False)
    monkeypatch.setattr(notes_svc, "_legacy_import_checked", False)

    imported_notes = notes_svc.list_notes()

    assert len(imported_notes) == 1
    assert imported_notes[0]["title"] == "Legacy note"
    assert imported_notes[0]["tags"] == ["Work"]


def test_todos_service_imports_legacy_json(monkeypatch, tmp_path):
    import backend.services.todos_service as todos_svc
    from backend.models.todo import Todo
    from backend.storage.json_store import JsonStore

    legacy_dir = tmp_path / "data"
    legacy_store = JsonStore("todos", data_dir=str(legacy_dir))
    todo = Todo(text="Legacy task", priority="high")
    legacy_store.set(todo.id, todo.model_dump())

    monkeypatch.setattr(
        todos_svc,
        "_store",
        _make_sqlite_store(monkeypatch, tmp_path, "todos", todos_svc.TODOS_SCHEMA, "todos.db"),
    )
    monkeypatch.setattr(todos_svc.settings, "data_dir", str(legacy_dir), raising=False)
    monkeypatch.setattr(todos_svc, "_legacy_import_checked", False)

    imported_todos = todos_svc.list_todos(show_completed=True)

    assert len(imported_todos) == 1
    assert imported_todos[0]["text"] == "Legacy task"
    assert imported_todos[0]["priority"] == "high"
