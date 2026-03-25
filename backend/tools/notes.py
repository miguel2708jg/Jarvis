"""LangChain tools for note management."""
from datetime import datetime, timezone
from langchain_core.tools import tool

from backend.models.note import Note
from backend.storage.json_store import JsonStore

_store = JsonStore("notes")


@tool
def create_note(title: str, content: str, tags: list[str] | None = None) -> dict:
    """Create a new note with a title, content, and optional tags. Returns the created note."""
    note = Note(title=title, content=content, tags=tags or [])
    _store.set(note.id, note.model_dump())
    return note.model_dump()


@tool
def list_notes(tag: str | None = None) -> list[dict]:
    """List all notes, optionally filtered by tag."""
    notes = [Note(**n) for n in _store.all()]
    if tag:
        notes = [n for n in notes if tag in n.tags]
    return [n.model_dump() for n in notes]


@tool
def get_note(note_id: str) -> dict | None:
    """Get a specific note by its ID."""
    data = _store.get(note_id)
    return data


@tool
def update_note(note_id: str, title: str | None = None, content: str | None = None, tags: list[str] | None = None) -> dict | None:
    """Update an existing note's title, content, or tags."""
    data = _store.get(note_id)
    if not data:
        return None
    note = Note(**data)
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if tags is not None:
        note.tags = tags
    note.updated_at = datetime.now(timezone.utc)
    _store.set(note.id, note.model_dump())
    return note.model_dump()


@tool
def delete_note(note_id: str) -> str:
    """Delete a note by its ID. Returns a confirmation message."""
    deleted = _store.delete(note_id)
    return f"Note {note_id} deleted." if deleted else f"Note {note_id} not found."
