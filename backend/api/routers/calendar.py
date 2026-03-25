"""REST endpoints for Calendar Events."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.calendar_event import CalendarEvent
from backend.storage.json_store import JsonStore

router = APIRouter()
_store = JsonStore("calendar")


class EventCreate(BaseModel):
    title: str
    start_datetime: str
    end_datetime: str
    description: str = ""
    location: str = ""


class EventUpdate(BaseModel):
    title: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    description: str | None = None
    location: str | None = None


@router.get("", response_model=list[CalendarEvent])
def list_events():
    events = [CalendarEvent(**e) for e in _store.all()]
    events.sort(key=lambda e: e.start_datetime)
    return events


@router.post("", response_model=CalendarEvent, status_code=201)
def create_event(body: EventCreate):
    from datetime import datetime
    event = CalendarEvent(
        title=body.title,
        start_datetime=datetime.fromisoformat(body.start_datetime),
        end_datetime=datetime.fromisoformat(body.end_datetime),
        description=body.description,
        location=body.location,
    )
    _store.set(event.id, event.model_dump())
    return event


@router.get("/{event_id}", response_model=CalendarEvent)
def get_event(event_id: str):
    data = _store.get(event_id)
    if not data:
        raise HTTPException(status_code=404, detail="Event not found")
    return CalendarEvent(**data)


@router.put("/{event_id}", response_model=CalendarEvent)
def update_event(event_id: str, body: EventUpdate):
    from datetime import datetime
    data = _store.get(event_id)
    if not data:
        raise HTTPException(status_code=404, detail="Event not found")
    event = CalendarEvent(**data)
    if body.title is not None:
        event.title = body.title
    if body.start_datetime is not None:
        event.start_datetime = datetime.fromisoformat(body.start_datetime)
    if body.end_datetime is not None:
        event.end_datetime = datetime.fromisoformat(body.end_datetime)
    if body.description is not None:
        event.description = body.description
    if body.location is not None:
        event.location = body.location
    _store.set(event.id, event.model_dump())
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str):
    if not _store.delete(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
