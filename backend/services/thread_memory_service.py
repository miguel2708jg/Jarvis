"""Thread memory persistence for LangGraph state."""
import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import BaseMessage, convert_to_messages, messages_from_dict
from langchain_core.messages.base import messages_to_dict

from backend.storage.factory import create_store
from backend.storage.schemas import THREAD_MEMORY_SCHEMA

_store = create_store("thread_memory", THREAD_MEMORY_SCHEMA)


def _serialize_messages(messages: list[Any]) -> str:
    """Serialize LangChain messages to JSON string."""
    normalized = convert_to_messages(messages)
    return json.dumps(messages_to_dict(normalized))


def _deserialize_messages(messages_str: str) -> list[BaseMessage]:
    """Deserialize JSON string to LangChain messages."""
    raw_messages = json.loads(messages_str)
    if not raw_messages:
        return []

    first_message = raw_messages[0]
    if isinstance(first_message, dict) and "data" in first_message and "type" in first_message:
        return messages_from_dict(raw_messages)

    # Backward compatibility for older rows stored as plain model_dump dicts.
    return convert_to_messages(raw_messages)


def save_thread_memory(
    thread_id: str,
    messages: list,
    user_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """
    Save the current state of a thread's conversation.
    
    Args:
        thread_id: The thread/conversation ID (used as primary key).
        messages: List of LangChain messages.
        user_id: Optional user identifier.
        session_id: Optional session identifier.
    """
    existing = _store.get(thread_id)
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "id": thread_id,  # Use thread_id as the primary key
        "thread_id": thread_id,
        "messages": _serialize_messages(messages),
        "user_id": user_id or "default",
        "session_id": session_id or thread_id,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
    _store.set(thread_id, data)


def get_thread_memory(thread_id: str) -> dict | None:
    """
    Retrieve the saved state of a thread.
    
    Args:
        thread_id: The thread/conversation ID.
        
    Returns:
        Dictionary with messages and metadata, or None if not found.
    """
    row = _store.get(thread_id)
    if row:
        return {
            "id": row["id"],
            "thread_id": row["thread_id"],
            "messages": _deserialize_messages(row["messages"]),
            "user_id": row.get("user_id"),
            "session_id": row.get("session_id"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    return None


def get_thread_messages(thread_id: str) -> list[dict]:
    """
    Get just the messages from a thread's memory.
    
    Args:
        thread_id: The thread/conversation ID.
        
    Returns:
        List of message dicts, empty list if not found.
    """
    memory = get_thread_memory(thread_id)
    return memory["messages"] if memory else []


def delete_thread_memory(thread_id: str) -> bool:
    """
    Delete a thread's memory.
    
    Args:
        thread_id: The thread/conversation ID.
        
    Returns:
        True if deleted, False otherwise.
    """
    return _store.delete(thread_id)


def list_thread_memories(user_id: str | None = None) -> list[dict]:
    """
    List all thread memories, optionally filtered by user.
    
    Args:
        user_id: Optional user identifier to filter by.
        
    Returns:
        List of thread memory summaries (without full messages).
    """
    if user_id:
        rows = _store.query("user_id = ? ORDER BY updated_at DESC", (user_id,))
    else:
        rows = _store.all()
    
    return [
        {
            "id": row["id"],
            "thread_id": row["thread_id"],
            "user_id": row.get("user_id"),
            "session_id": row.get("session_id"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": len(_deserialize_messages(row["messages"])),
        }
        for row in rows
    ]


def update_thread_memory_timestamp(thread_id: str) -> bool:
    """
    Update the timestamp of a thread's memory.
    
    Args:
        thread_id: The thread/conversation ID.
        
    Returns:
        True if updated, False if not found.
    """
    memory = get_thread_memory(thread_id)
    if not memory:
        return False
    
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "id": memory["id"],
        "thread_id": memory["thread_id"],
        "messages": _serialize_messages(memory["messages"]),
        "user_id": memory.get("user_id") or "default",
        "session_id": memory.get("session_id") or thread_id,
        "created_at": memory["created_at"],
        "updated_at": now,
    }
    _store.set(thread_id, data)
    return True
