"""REST endpoints for Notes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.note import Note
from backend.storage.json_store import JsonStore

router = APIRouter()
_store = JsonStore("notes")


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


@router.get("", response_model=list[Note])
def list_notes(tag: str | None = None):
    notes = [Note(**n) for n in _store.all()]
    if tag:
        notes = [n for n in notes if tag in n.tags]
    return notes


@router.post("", response_model=Note, status_code=201)
def create_note(body: NoteCreate):
    note = Note(**body.model_dump())
    _store.set(note.id, note.model_dump())
    return note


@router.get("/{note_id}", response_model=Note)
def get_note(note_id: str):
    data = _store.get(note_id)
    if not data:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(**data)


@router.put("/{note_id}", response_model=Note)
def update_note(note_id: str, body: NoteUpdate):
    from datetime import datetime, timezone
    data = _store.get(note_id)
    if not data:
        raise HTTPException(status_code=404, detail="Note not found")
    note = Note(**data)
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    if body.tags is not None:
        note.tags = body.tags
    note.updated_at = datetime.now(timezone.utc)
    _store.set(note.id, note.model_dump())
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: str):
    if not _store.delete(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
