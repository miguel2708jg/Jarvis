"""Unit tests for the Google Calendar service adapter."""
from backend.services import calendar_service


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeEvents:
    def __init__(self):
        self.calls = []
        self.event = {
            "id": "event-1",
            "summary": "Standup",
            "start": {"dateTime": "2035-12-01T09:00:00+00:00"},
            "end": {"dateTime": "2035-12-01T09:30:00+00:00"},
            "description": "Daily sync",
            "location": "Room 1",
            "created": "2035-12-01T00:00:00Z",
        }

    def insert(self, **kwargs):
        self.calls.append(("insert", kwargs))
        return FakeRequest(self.event)

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return FakeRequest({"items": [self.event]})

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return FakeRequest(self.event)

    def patch(self, **kwargs):
        self.calls.append(("patch", kwargs))
        patched = {**self.event, "summary": kwargs["body"]["summary"]}
        return FakeRequest(patched)

    def delete(self, **kwargs):
        self.calls.append(("delete", kwargs))
        return FakeRequest({})


class FakeCalendarService:
    def __init__(self):
        self.events_resource = FakeEvents()

    def events(self):
        return self.events_resource


def test_calendar_create_maps_google_event(monkeypatch):
    fake = FakeCalendarService()
    monkeypatch.setattr(calendar_service, "_service", lambda: fake)

    event = calendar_service.create_calendar_event(
        "Standup",
        "2035-12-01T09:00:00Z",
        "2035-12-01T09:30:00Z",
        "Daily sync",
        "Room 1",
    )

    assert event["id"] == "event-1"
    assert event["title"] == "Standup"
    call_name, call = fake.events_resource.calls[0]
    assert call_name == "insert"
    assert call["calendarId"] == "primary"
    assert call["body"]["summary"] == "Standup"
    assert call["body"]["start"]["dateTime"] == "2035-12-01T09:00:00+00:00"


def test_calendar_list_get_update_delete(monkeypatch):
    fake = FakeCalendarService()
    monkeypatch.setattr(calendar_service, "_service", lambda: fake)

    assert calendar_service.list_calendar_events()[0]["title"] == "Standup"
    assert calendar_service.get_calendar_event("event-1")["id"] == "event-1"
    assert calendar_service.update_calendar_event("event-1", title="Updated")["title"] == "Updated"
    assert calendar_service.delete_calendar_event("event-1") == "Event event-1 deleted."

    call_names = [name for name, _ in fake.events_resource.calls]
    assert call_names == ["list", "get", "get", "patch", "delete"]


def test_calendar_tool_returns_error_payload_when_service_fails(monkeypatch):
    from backend.tools import calendar as calendar_tools

    def fail_create(*args, **kwargs):
        raise calendar_service.CalendarServiceError("Google Calendar request failed")

    monkeypatch.setattr(calendar_tools.calendar_service, "create_calendar_event", fail_create)

    result = calendar_tools.create_calendar_event.invoke(
        {
            "title": "Standup",
            "start_datetime": "2035-12-01T09:00:00Z",
            "end_datetime": "2035-12-01T09:30:00Z",
        }
    )

    assert result["status"] == "calendar_unavailable"
    assert "Google Calendar request failed" in result["error"]
