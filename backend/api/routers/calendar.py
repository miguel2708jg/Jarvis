"""REST endpoints for Calendar Events."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services import calendar_service

router = APIRouter()


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


@router.get("")
def list_events(upcoming_only: bool = Query(True), calendar_id: str = Query("primary")):
    return calendar_service.list_calendar_events(upcoming_only, calendar_id)


@router.post("", status_code=201)
def create_event(body: EventCreate, calendar_id: str = Query("primary")):
    try:
        return calendar_service.create_calendar_event(
            body.title, body.start_datetime, body.end_datetime, body.description, body.location, calendar_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{event_id}")
def get_event(event_id: str, calendar_id: str = Query("primary")):
    data = calendar_service.get_calendar_event(event_id, calendar_id)
    if not data:
        raise HTTPException(status_code=404, detail="Event not found")
    return data


@router.put("/{event_id}")
def update_event(event_id: str, body: EventUpdate, calendar_id: str = Query("primary")):
    try:
        data = calendar_service.update_calendar_event(
            event_id, body.title, body.start_datetime, body.end_datetime, body.description, body.location, calendar_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not data:
        raise HTTPException(status_code=404, detail="Event not found")
    return data


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: str, calendar_id: str = Query("primary")):
    result = calendar_service.delete_calendar_event(event_id, calendar_id)
    if "not found" in result:
        raise HTTPException(status_code=404, detail="Event not found")
