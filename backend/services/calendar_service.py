"""Business logic for Google Calendar event management."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services import google_workspace_client


class CalendarAuthorizationError(PermissionError):
    """Raised when Google credentials do not authorize calendar access."""


class CalendarServiceError(RuntimeError):
    """Raised when Google Calendar cannot complete a request."""


def _service():
    return google_workspace_client.build_service("calendar", "v3")


def _parse_event_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid calendar datetime: {value}") from exc


def _rfc3339(value: str) -> str:
    parsed = _parse_event_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _sortable_datetime(value: str | None) -> float:
    if not value:
        return 0
    normalized = _parse_event_datetime(value)
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    return normalized.timestamp()


def _translate_error(exc: Exception) -> Exception:
    message = str(exc).lower()
    if "insufficient authentication scopes" in message or "permission" in message or "forbidden" in message:
        return CalendarAuthorizationError(
            "Google Calendar access is configured but not authorized. Delete GOOGLE_TOKEN_FILE, restart the backend, "
            "and approve the calendar.events scope during OAuth."
        )
    return CalendarServiceError(f"Google Calendar request failed: {exc}")


def _event_datetime(event: dict[str, Any], key: str) -> str:
    value = event.get(key) or {}
    return value.get("dateTime") or value.get("date") or ""


def _event_to_dict(event: dict[str, Any]) -> dict[str, Any]:
    created = event.get("created") or datetime.now(timezone.utc).isoformat()
    return {
        "id": event.get("id", ""),
        "title": event.get("summary", ""),
        "start_datetime": _event_datetime(event, "start"),
        "end_datetime": _event_datetime(event, "end"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "created_at": created,
    }


def _build_event_body(
    *,
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
) -> dict[str, Any]:
    start = _rfc3339(start_datetime)
    end = _rfc3339(end_datetime)
    if _sortable_datetime(end) <= _sortable_datetime(start):
        raise ValueError("Calendar event end_datetime must be after start_datetime.")

    return {
        "summary": title.strip(),
        "start": {"dateTime": start},
        "end": {"dateTime": end},
        "description": description.strip(),
        "location": location.strip(),
    }


def create_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
) -> dict:
    body = _build_event_body(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
    )
    try:
        event = _service().events().insert(calendarId=calendar_id, body=body).execute()
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _event_to_dict(event)


def list_calendar_events(
    upcoming_only: bool = True, calendar_id: str = "primary", max_results: int = 50
) -> list[dict]:
    params: dict[str, Any] = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if upcoming_only:
        params["timeMin"] = datetime.now(timezone.utc).isoformat()
    try:
        result = _service().events().list(**params).execute()
    except Exception as exc:
        raise _translate_error(exc) from exc
    return [_event_to_dict(event) for event in result.get("items") or []]


def get_calendar_event(event_id: str, calendar_id: str = "primary") -> dict | None:
    try:
        event = _service().events().get(calendarId=calendar_id, eventId=event_id).execute()
    except Exception as exc:
        if "not found" in str(exc).lower() or "404" in str(exc):
            return None
        raise _translate_error(exc) from exc
    return _event_to_dict(event)


def update_calendar_event(
    event_id: str,
    title: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str = "primary",
) -> dict | None:
    current = get_calendar_event(event_id, calendar_id)
    if not current:
        return None

    body = _build_event_body(
        title=title if title is not None else current["title"],
        start_datetime=start_datetime if start_datetime is not None else current["start_datetime"],
        end_datetime=end_datetime if end_datetime is not None else current["end_datetime"],
        description=description if description is not None else current["description"],
        location=location if location is not None else current["location"],
    )
    try:
        event = _service().events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
    except Exception as exc:
        if "not found" in str(exc).lower() or "404" in str(exc):
            return None
        raise _translate_error(exc) from exc
    return _event_to_dict(event)


def delete_calendar_event(event_id: str, calendar_id: str = "primary") -> str:
    try:
        _service().events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except Exception as exc:
        if "not found" in str(exc).lower() or "404" in str(exc):
            return f"Event {event_id} not found."
        raise _translate_error(exc) from exc
    return f"Event {event_id} deleted."
