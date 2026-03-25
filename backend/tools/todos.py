"""LangChain tools for to-do management."""
from typing import Literal
from langchain_core.tools import tool

from backend.models.todo import Todo
from backend.storage.json_store import JsonStore

_store = JsonStore("todos")


@tool
def create_todo(text: str, priority: Literal["low", "medium", "high"] = "medium", due_date: str | None = None) -> dict:
    """Create a new to-do item. due_date should be ISO format string (e.g. 2024-12-31T10:00:00)."""
    from datetime import datetime
    todo = Todo(
        text=text,
        priority=priority,
        due_date=datetime.fromisoformat(due_date) if due_date else None,
    )
    _store.set(todo.id, todo.model_dump())
    return todo.model_dump()


@tool
def list_todos(show_completed: bool = False) -> list[dict]:
    """List to-do items. By default only shows incomplete items."""
    todos = [Todo(**t) for t in _store.all()]
    if not show_completed:
        todos = [t for t in todos if not t.completed]
    return [t.model_dump() for t in todos]


@tool
def complete_todo(todo_id: str) -> dict | None:
    """Mark a to-do item as completed."""
    data = _store.get(todo_id)
    if not data:
        return None
    todo = Todo(**data)
    todo.completed = True
    _store.set(todo.id, todo.model_dump())
    return todo.model_dump()


@tool
def delete_todo(todo_id: str) -> str:
    """Delete a to-do item by its ID."""
    deleted = _store.delete(todo_id)
    return f"Todo {todo_id} deleted." if deleted else f"Todo {todo_id} not found."
