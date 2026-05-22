"""REST endpoints for chat conversations and stored messages."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.message import Message
from backend.models.thread import Thread
from backend.services import message_service, thread_memory_service, thread_service

router = APIRouter()


class ThreadCreate(BaseModel):
    title: str | None = None
    user_id: str = "default"


class ThreadUpdate(BaseModel):
    title: str | None = None


@router.get("", response_model=list[Thread])
def list_threads(user_id: str | None = None):
    return thread_service.list_threads(user_id)


@router.post("", response_model=Thread, status_code=201)
def create_thread(body: ThreadCreate):
    return thread_service.create_thread(body.title or "Nueva conversacion", body.user_id)


@router.get("/{thread_id}", response_model=Thread)
def get_thread(thread_id: str):
    data = thread_service.get_thread(thread_id)
    if not data:
        raise HTTPException(status_code=404, detail="Thread not found")
    return data


@router.put("/{thread_id}", response_model=Thread)
def update_thread(thread_id: str, body: ThreadUpdate):
    data = thread_service.update_thread(thread_id, body.title)
    if not data:
        raise HTTPException(status_code=404, detail="Thread not found")
    return data


@router.delete("/{thread_id}", status_code=204)
def delete_thread(thread_id: str):
    data = thread_service.get_thread(thread_id)
    if not data:
        raise HTTPException(status_code=404, detail="Thread not found")

    message_service.delete_messages_by_thread(thread_id)
    thread_memory_service.delete_thread_memory(thread_id)
    thread_service.delete_thread(thread_id)


@router.get("/{thread_id}/messages", response_model=list[Message])
def list_thread_messages(thread_id: str):
    if not thread_service.get_thread(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    return message_service.list_messages(thread_id)
