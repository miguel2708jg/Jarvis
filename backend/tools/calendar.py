"""LangChain tools for calendar event management."""
from langchain_core.tools import tool

from backend.models.calendar_event import CalendarEvent
from backend.storage.json_store import JsonStore

_store = JsonStore("calendar")


@tool
def create_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
) -> dict:
    """Create a calendar event. Datetimes must be ISO format (e.g. 2024-12-31T10:00:00)."""
    from datetime import datetime
    event = CalendarEvent(
        title=title,
        start_datetime=datetime.fromisoformat(start_datetime),
        end_datetime=datetime.fromisoformat(end_datetime),
        description=description,
        location=location,
    )
    _store.set(event.id, event.model_dump())
    return event.model_dump()


@tool
def list_calendar_events() -> list[dict]:
    """List all upcoming calendar events, sorted by start time."""
    events = [CalendarEvent(**e) for e in _store.all()]
    events.sort(key=lambda e: e.start_datetime)
    return [e.model_dump() for e in events]


@tool
def get_calendar_event(event_id: str) -> dict | None:
    """Get a calendar event by its ID."""
    return _store.get(event_id)


@tool
def delete_calendar_event(event_id: str) -> str:
    """Delete a calendar event by its ID."""
    deleted = _store.delete(event_id)
    return f"Event {event_id} deleted." if deleted else f"Event {event_id} not found."
