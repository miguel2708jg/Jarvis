"""Business logic for thread management."""
from datetime import datetime, timezone

from backend.models.thread import Thread
from backend.storage.sqlite_store import SQLiteStore

THREADS_SCHEMA = """
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    title TEXT,
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_store = SQLiteStore("threads", THREADS_SCHEMA)


def _row_to_thread(row: dict) -> Thread:
    """Convert database row to Thread model."""
    return Thread(
        id=row["id"],
        title=row.get("title"),
        user_id=row["user_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _thread_to_data(thread: Thread) -> dict:
    """Convert Thread model to database dict."""
    return {
        "id": thread.id,
        "title": thread.title,
        "user_id": thread.user_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
    }


def create_thread(title: str | None = None, user_id: str = "default") -> dict:
    """Create a new thread."""
    thread = Thread(title=title, user_id=user_id)
    data = _thread_to_data(thread)
    _store.set(thread.id, data)
    return thread.model_dump()


def list_threads(user_id: str | None = None) -> list[dict]:
    """List all threads, optionally filtered by user_id."""
    if user_id:
        rows = _store.query("user_id = ? ORDER BY updated_at DESC", (user_id,))
    else:
        rows = _store.all()
    threads = [_row_to_thread(row) for row in rows]
    return [t.model_dump() for t in threads]


def get_thread(thread_id: str) -> dict | None:
    """Get a thread by ID."""
    row = _store.get(thread_id)
    if row:
        thread = _row_to_thread(row)
        return thread.model_dump()
    return None


def update_thread(thread_id: str, title: str | None = None) -> dict | None:
    """Update a thread's title."""
    row = _store.get(thread_id)
    if not row:
        return None
    thread = _row_to_thread(row)
    if title is not None:
        thread.title = title
    thread.updated_at = datetime.now(timezone.utc)
    data = _thread_to_data(thread)
    _store.set(thread.id, data)
    return thread.model_dump()


def delete_thread(thread_id: str) -> str:
    """Delete a thread by ID."""
    deleted = _store.delete(thread_id)
    return f"Thread {thread_id} deleted." if deleted else f"Thread {thread_id} not found."
