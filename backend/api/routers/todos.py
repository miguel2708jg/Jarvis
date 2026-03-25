"""REST endpoints for Todos."""
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.todo import Todo
from backend.storage.json_store import JsonStore

router = APIRouter()
_store = JsonStore("todos")


class TodoCreate(BaseModel):
    text: str
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: str | None = None


@router.get("", response_model=list[Todo])
def list_todos(show_completed: bool = False):
    todos = [Todo(**t) for t in _store.all()]
    if not show_completed:
        todos = [t for t in todos if not t.completed]
    return todos


@router.post("", response_model=Todo, status_code=201)
def create_todo(body: TodoCreate):
    from datetime import datetime
    todo = Todo(
        text=body.text,
        priority=body.priority,
        due_date=datetime.fromisoformat(body.due_date) if body.due_date else None,
    )
    _store.set(todo.id, todo.model_dump())
    return todo


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: str):
    data = _store.get(todo_id)
    if not data:
        raise HTTPException(status_code=404, detail="Todo not found")
    return Todo(**data)


@router.patch("/{todo_id}/complete", response_model=Todo)
def complete_todo(todo_id: str):
    data = _store.get(todo_id)
    if not data:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo = Todo(**data)
    todo.completed = True
    _store.set(todo.id, todo.model_dump())
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: str):
    if not _store.delete(todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
