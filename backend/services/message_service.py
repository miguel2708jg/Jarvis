"""Business logic for message management."""
from datetime import datetime, timezone

from backend.models.message import Message
from backend.storage.factory import create_store
from backend.storage.schemas import MESSAGES_SCHEMA

_store = create_store("messages", MESSAGES_SCHEMA)


def _row_to_message(row: dict) -> Message:
    """Convert database row to Message model."""
    return Message(
        id=row["id"],
        thread_id=row["thread_id"],
        role=row["role"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _message_to_data(message: Message) -> dict:
    """Convert Message model to database dict."""
    return {
        "id": message.id,
        "thread_id": message.thread_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def create_message(thread_id: str, content: str, role: str = "user") -> dict:
    """Create a new message in a thread."""
    message = Message(thread_id=thread_id, content=content, role=role)
    data = _message_to_data(message)
    _store.set(message.id, data)
    return message.model_dump()


def list_messages(thread_id: str) -> list[dict]:
    """List all messages in a thread ordered by creation time."""
    rows = _store.query("thread_id = ? ORDER BY created_at ASC", (thread_id,))
    messages = [_row_to_message(row) for row in rows]
    return [m.model_dump() for m in messages]


def get_message(message_id: str) -> dict | None:
    """Get a message by ID."""
    row = _store.get(message_id)
    if row:
        message = _row_to_message(row)
        return message.model_dump()
    return None


def delete_message(message_id: str) -> str:
    """Delete a message by ID."""
    deleted = _store.delete(message_id)
    return f"Message {message_id} deleted." if deleted else f"Message {message_id} not found."


def delete_messages_by_thread(thread_id: str) -> int:
    """Delete all messages in a thread."""
    return _store.delete_where("thread_id = ?", (thread_id,))
