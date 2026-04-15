"""LangChain tools for to-do management."""
from typing import Literal
from langchain_core.tools import tool

from backend.services import todos_service


@tool
def create_todo(text: str, priority: Literal["low", "medium", "high"] = "medium", due_date: str | None = None) -> dict:
    """Create a new to-do item. due_date should be ISO format string (e.g. 2024-12-31T10:00:00)."""
    return todos_service.create_todo(text, priority, due_date)


@tool
def list_todos(show_completed: bool = False) -> list[dict]:
    """List to-do items. By default only shows incomplete items."""
    return todos_service.list_todos(show_completed)


@tool
def get_todo(todo_id: str) -> dict | None:
    """Get a specific to-do item by its ID."""
    return todos_service.get_todo(todo_id)


@tool
def update_todo(
    todo_id: str,
    text: str | None = None,
    priority: Literal["low", "medium", "high"] | None = None,
    due_date: str | None = None,
    completed: bool | None = None,
    clear_due_date: bool = False,
) -> dict | None:
    """Update a to-do item's text, priority, due date, or completed status."""
    resolved_due_date: str | None | object = todos_service._UNSET
    if due_date is not None:
        resolved_due_date = due_date
    elif clear_due_date:
        resolved_due_date = None

    return todos_service.update_todo(
        todo_id,
        text=text,
        priority=priority,
        due_date=resolved_due_date,
        completed=completed,
    )


@tool
def complete_todo(todo_id: str) -> dict | None:
    """Mark a to-do item as completed."""
    return todos_service.complete_todo(todo_id)


@tool
def delete_todo(todo_id: str) -> str:
    """Delete a to-do item by its ID."""
    return todos_service.delete_todo(todo_id)
