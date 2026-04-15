"""Business logic for to-do management."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from typing import Literal

from backend.config import settings
from backend.models.todo import Todo
from backend.storage.json_store import JsonStore
from backend.storage.sqlite_store import SQLiteStore

TODOS_SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'medium',
    due_date TEXT,
    created_at TEXT NOT NULL
)
"""

_store = SQLiteStore("todos", TODOS_SCHEMA)
_UNSET = object()
_legacy_import_checked = False


def _coerce_row(row: Any) -> dict[str, Any]:
    """Ensure rows coming from different storage backends are plain dictionaries."""
    return dict(row)


def _all_rows() -> list[dict[str, Any]]:
    return [_coerce_row(row) for row in _store.all()]


def _candidate_legacy_dirs() -> list[Path]:
    primary = Path(settings.data_dir)
    candidates = [primary, primary.parent / "data", primary.parent / "Data"]
    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)
    return unique_candidates


def _import_legacy_todos_if_needed() -> None:
    """One-time import for installations that still have JSON-backed todos."""
    global _legacy_import_checked

    if _legacy_import_checked or not isinstance(_store, SQLiteStore):
        return
    _legacy_import_checked = True

    if _store.all():
        return

    for legacy_dir in _candidate_legacy_dirs():
        legacy_file = legacy_dir / "todos.json"
        if not legacy_file.exists():
            continue

        legacy_store = JsonStore("todos", data_dir=str(legacy_dir))
        for raw_todo in legacy_store.all():
            todo = Todo(**raw_todo)
            data = todo.model_dump()
            data["completed"] = 1 if todo.completed else 0
            data["due_date"] = todo.due_date.isoformat() if todo.due_date else None
            data["created_at"] = todo.created_at.isoformat()
            _store.set(todo.id, data)
        break


def _parse_due_date(due_date: str | None) -> datetime | None:
    """Parse an ISO datetime or date string into a datetime object."""
    if due_date is None:
        return None

    value = due_date.strip()
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sortable_datetime(value: datetime) -> float:
    """Return a comparable timestamp for naive or aware datetimes."""
    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.timestamp()


def _row_to_todo(row: dict) -> Todo:
    """Convert database row to Todo model."""
    return Todo(
        id=row["id"],
        text=row["text"],
        completed=bool(row["completed"]),
        priority=row["priority"],
        due_date=_parse_due_date(row.get("due_date")),
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
    )


def _todo_to_dict(todo: Todo) -> dict[str, Any]:
    """Serialize todo models using JSON-friendly types."""
    return todo.model_dump(mode="json")


def create_todo(text: str, priority: Literal["low", "medium", "high"] = "medium", due_date: str | None = None) -> dict:
    _import_legacy_todos_if_needed()
    todo = Todo(
        text=text.strip(),
        priority=priority,
        due_date=_parse_due_date(due_date),
    )
    data = todo.model_dump()
    data["completed"] = 1 if todo.completed else 0
    data["due_date"] = todo.due_date.isoformat() if todo.due_date else None
    data["created_at"] = todo.created_at.isoformat()
    _store.set(todo.id, data)
    return _todo_to_dict(todo)


def list_todos(show_completed: bool = False) -> list[dict]:
    _import_legacy_todos_if_needed()
    todos = [_row_to_todo(row) for row in _all_rows()]
    if not show_completed:
        todos = [todo for todo in todos if not todo.completed]
    todos.sort(
        key=lambda todo: (
            todo.completed,
            todo.due_date is None,
            _sortable_datetime(todo.due_date or todo.created_at),
        )
    )
    return [_todo_to_dict(todo) for todo in todos]


def get_todo(todo_id: str) -> dict | None:
    _import_legacy_todos_if_needed()
    row = _store.get(todo_id)
    if row:
        todo = _row_to_todo(_coerce_row(row))
        return _todo_to_dict(todo)
    return None


def update_todo(
    todo_id: str,
    text: str | None = None,
    priority: Literal["low", "medium", "high"] | None = None,
    due_date: str | None | object = _UNSET,
    completed: bool | None = None,
) -> dict | None:
    _import_legacy_todos_if_needed()
    row = _store.get(todo_id)
    if not row:
        return None

    todo = _row_to_todo(_coerce_row(row))
    if text is not None:
        todo.text = text.strip()
    if priority is not None:
        todo.priority = priority
    if due_date is not _UNSET:
        todo.due_date = _parse_due_date(due_date)
    if completed is not None:
        todo.completed = completed

    data = todo.model_dump()
    data["completed"] = 1 if todo.completed else 0
    data["due_date"] = todo.due_date.isoformat() if todo.due_date else None
    data["created_at"] = todo.created_at.isoformat()
    _store.set(todo.id, data)
    return _todo_to_dict(todo)


def complete_todo(todo_id: str) -> dict | None:
    return update_todo(todo_id, completed=True)


def delete_todo(todo_id: str) -> str:
    _import_legacy_todos_if_needed()
    deleted = _store.delete(todo_id)
    return f"Todo {todo_id} deleted." if deleted else f"Todo {todo_id} not found."
