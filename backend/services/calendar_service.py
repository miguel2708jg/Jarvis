"""Business logic for local calendar event management."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from backend.models.calendar_event import CalendarEvent
from backend.storage.sqlite_store import SQLiteStore

CALENDAR_SCHEMA = """
CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    start_datetime TEXT NOT NULL,
    end_datetime TEXT NOT NULL,
    description TEXT,
    location TEXT,
    created_at TEXT NOT NULL
)
"""

_store = SQLiteStore("calendar_events", CALENDAR_SCHEMA)


def _parse_event_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid calendar datetime: {value}") from exc


def _sortable_datetime(value: datetime) -> float:
    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.timestamp()


def _coerce_row(row: Any) -> dict[str, Any]:
    return dict(row)


def _row_to_event(row: dict[str, Any]) -> CalendarEvent:
    return CalendarEvent(
        id=row["id"],
        title=row["title"],
        start_datetime=_parse_event_datetime(row["start_datetime"]),
        end_datetime=_parse_event_datetime(row["end_datetime"]),
        description=row.get("description") or "",
        location=row.get("location") or "",
        created_at=_parse_event_datetime(row["created_at"]),
    )


def _event_to_row(event: CalendarEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "title": event.title,
        "start_datetime": event.start_datetime.isoformat(),
        "end_datetime": event.end_datetime.isoformat(),
        "description": event.description,
        "location": event.location,
        "created_at": event.created_at.isoformat(),
    }


def _event_to_dict(event: CalendarEvent) -> dict[str, Any]:
    return event.model_dump(mode="json")


def _validate_event(event: CalendarEvent) -> None:
    if _sortable_datetime(event.end_datetime) <= _sortable_datetime(event.start_datetime):
        raise ValueError("Calendar event end_datetime must be after start_datetime.")


def _build_event(
    *,
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    event_id: str | None = None,
    created_at: datetime | None = None,
) -> CalendarEvent:
    data: dict[str, Any] = {
        "title": title.strip(),
        "start_datetime": _parse_event_datetime(start_datetime),
        "end_datetime": _parse_event_datetime(end_datetime),
        "description": description.strip(),
        "location": location.strip(),
        "created_at": created_at or datetime.now(timezone.utc),
    }
    if event_id is not None:
        data["id"] = event_id

    try:
        event = CalendarEvent(**data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    _validate_event(event)
    return event


def create_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
) -> dict:
    _ = calendar_id
    event = _build_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
    )
    _store.set(event.id, _event_to_row(event))
    return _event_to_dict(event)


def list_calendar_events(
    upcoming_only: bool = True, calendar_id: str = "primary", max_results: int = 50
) -> list[dict]:
    _ = calendar_id
    now_ts = datetime.now(timezone.utc).timestamp()
    events = [_row_to_event(_coerce_row(row)) for row in _store.all()]
    if upcoming_only:
        events = [
            event
            for event in events
            if _sortable_datetime(event.end_datetime) >= now_ts
        ]
    events.sort(key=lambda event: _sortable_datetime(event.start_datetime))
    return [_event_to_dict(event) for event in events[:max_results]]


def get_calendar_event(event_id: str, calendar_id: str = "primary") -> dict | None:
    _ = calendar_id
    row = _store.get(event_id)
    if not row:
        return None
    return _event_to_dict(_row_to_event(_coerce_row(row)))


def update_calendar_event(
    event_id: str,
    title: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str = "primary",
) -> dict | None:
    _ = calendar_id
    row = _store.get(event_id)
    if not row:
        return None

    current = _row_to_event(_coerce_row(row))
    event = _build_event(
        event_id=current.id,
        title=title if title is not None else current.title,
        start_datetime=start_datetime if start_datetime is not None else current.start_datetime.isoformat(),
        end_datetime=end_datetime if end_datetime is not None else current.end_datetime.isoformat(),
        description=description if description is not None else current.description,
        location=location if location is not None else current.location,
        created_at=current.created_at,
    )
    _store.set(event.id, _event_to_row(event))
    return _event_to_dict(event)


def delete_calendar_event(event_id: str, calendar_id: str = "primary") -> str:
    _ = calendar_id
    deleted = _store.delete(event_id)
    return f"Event {event_id} deleted." if deleted else f"Event {event_id} not found."
