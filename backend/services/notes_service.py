"""Business logic for note management."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.models.note import Note
from backend.storage.json_store import JsonStore
from backend.storage.sqlite_store import SQLiteStore

NOTES_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_store = SQLiteStore("notes", NOTES_SCHEMA)
_legacy_import_checked = False


def _normalize_tags(tags: list[str] | None) -> list[str]:
    """Trim, deduplicate, and normalize tags while preserving order."""
    if not tags:
        return []

    seen: set[str] = set()
    normalized: list[str] = []
    for raw_tag in tags:
        tag = raw_tag.strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    return normalized


def _serialize_tags(tags: list[str]) -> str:
    """Serialize tags list to a comma-separated string."""
    return ",".join(_normalize_tags(tags))


def _deserialize_tags(tags_str: str | None) -> list[str]:
    """Deserialize a comma-separated string to a normalized tag list."""
    if isinstance(tags_str, list):
        return _normalize_tags(tags_str)
    if not isinstance(tags_str, str) or not tags_str:
        return []
    return _normalize_tags(tags_str.split(","))


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


def _import_legacy_notes_if_needed() -> None:
    """One-time import for installations that still have JSON-backed notes."""
    global _legacy_import_checked

    if _legacy_import_checked or not isinstance(_store, SQLiteStore):
        return
    _legacy_import_checked = True

    if _store.all():
        return

    for legacy_dir in _candidate_legacy_dirs():
        legacy_file = legacy_dir / "notes.json"
        if not legacy_file.exists():
            continue

        legacy_store = JsonStore("notes", data_dir=str(legacy_dir))
        for raw_note in legacy_store.all():
            note = Note(**raw_note)
            data = note.model_dump()
            data["tags"] = _serialize_tags(note.tags)
            data["created_at"] = note.created_at.isoformat()
            data["updated_at"] = note.updated_at.isoformat()
            _store.set(note.id, data)
        break


def _row_to_note(row: dict[str, Any]) -> Note:
    """Convert database row to Note model."""
    return Note(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=_deserialize_tags(row.get("tags")),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _note_to_dict(note: Note) -> dict[str, Any]:
    """Serialize note models using JSON-friendly types."""
    return note.model_dump(mode="json")


def create_note(title: str, content: str, tags: list[str] | None = None) -> dict:
    _import_legacy_notes_if_needed()
    note = Note(
        title=title.strip(),
        content=content.strip(),
        tags=_normalize_tags(tags),
    )
    data = note.model_dump()
    data["tags"] = _serialize_tags(note.tags)
    data["created_at"] = note.created_at.isoformat()
    data["updated_at"] = note.updated_at.isoformat()
    _store.set(note.id, data)
    return _note_to_dict(note)


def list_notes(tag: str | None = None) -> list[dict]:
    _import_legacy_notes_if_needed()
    notes = [_row_to_note(row) for row in _all_rows()]
    if tag:
        normalized_tag = tag.strip().lower()
        notes = [
            note
            for note in notes
            if normalized_tag in {note_tag.lower() for note_tag in note.tags}
        ]
    notes.sort(key=lambda note: note.updated_at, reverse=True)
    return [_note_to_dict(note) for note in notes]


def get_note(note_id: str) -> dict | None:
    _import_legacy_notes_if_needed()
    row = _store.get(note_id)
    if row:
        note = _row_to_note(_coerce_row(row))
        return _note_to_dict(note)
    return None


def update_note(note_id: str, title: str | None = None, content: str | None = None, tags: list[str] | None = None) -> dict | None:
    _import_legacy_notes_if_needed()
    row = _store.get(note_id)
    if not row:
        return None
    note = _row_to_note(_coerce_row(row))
    if title is not None:
        note.title = title.strip()
    if content is not None:
        note.content = content.strip()
    if tags is not None:
        note.tags = _normalize_tags(tags)
    note.updated_at = datetime.now(timezone.utc)
    data = note.model_dump()
    data["tags"] = _serialize_tags(note.tags)
    data["created_at"] = note.created_at.isoformat()
    data["updated_at"] = note.updated_at.isoformat()
    _store.set(note.id, data)
    return _note_to_dict(note)


def delete_note(note_id: str) -> str:
    _import_legacy_notes_if_needed()
    deleted = _store.delete(note_id)
    return f"Note {note_id} deleted." if deleted else f"Note {note_id} not found."
