"""Chat endpoints: POST /chat (blocking) and WS /ws/chat (streaming)."""
import json
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from backend.api.auth import authenticate_websocket
from backend.api.dependencies import get_jarvis_graph
from backend.api.errors import llm_unavailable_message
from backend.models.chat import ChatAttachmentUploadResponse, ChatRequest, ChatResponse, StreamChunk
from backend.services import knowledge_service, thread_service
from backend.services.message_service import delete_messages_by_thread
from backend.services.thread_memory_service import (
    delete_thread_memory,
    get_thread_memory,
    list_thread_memories,
)

router = APIRouter()


class ChatThreadCreate(BaseModel):
    title: str | None = None


class ChatThreadSummary(BaseModel):
    id: str
    title: str
    user_id: str | None = None
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatThreadMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str | None = None


def _extract_text_content(payload) -> str:
    """Extract plain text from LangChain message/chunk payloads."""
    content = getattr(payload, "content", payload)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts).strip()
    return ""


def _request_user_id(request: Request) -> str:
    return getattr(request.state, "user_email", None) or "default"


def _message_role(message: BaseMessage) -> Literal["user", "assistant"] | None:
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    message_type = getattr(message, "type", "")
    if message_type == "human":
        return "user"
    if message_type == "ai":
        return "assistant"
    return None


def _message_content(message: BaseMessage) -> str:
    return _extract_text_content(message)


def _message_created_at(message: BaseMessage) -> str | None:
    metadata = getattr(message, "response_metadata", None) or {}
    created_at = metadata.get("created_at") if isinstance(metadata, dict) else None
    return str(created_at) if created_at else None


def _message_id(thread_id: str, index: int) -> str:
    return f"{thread_id}-{index}"


def _thread_title_from_messages(messages: list[BaseMessage]) -> str:
    for message in messages:
        if _message_role(message) == "user":
            content = _message_content(message).strip()
            if content:
                return content[:80]
    return "New chat"


def _thread_summary_from_memory(memory: dict) -> ChatThreadSummary:
    messages = memory.get("messages") or []
    return ChatThreadSummary(
        id=memory["thread_id"],
        title=_thread_title_from_messages(messages),
        user_id=memory.get("user_id"),
        created_at=memory["created_at"],
        updated_at=memory["updated_at"],
        message_count=sum(1 for message in messages if _message_role(message)),
    )


def _thread_summary_from_metadata(thread: dict, memory: dict | None = None) -> ChatThreadSummary:
    messages = memory.get("messages") if memory else []
    title = thread.get("title") or _thread_title_from_messages(messages or [])
    return ChatThreadSummary(
        id=thread["id"],
        title=title,
        user_id=thread.get("user_id"),
        created_at=str(thread["created_at"]),
        updated_at=str(memory["updated_at"] if memory else thread["updated_at"]),
        message_count=sum(1 for message in messages if _message_role(message)),
    )


def _ensure_thread(thread_id: str, user_id: str, title: str | None = None) -> None:
    existing = thread_service.get_thread(thread_id)
    memory = get_thread_memory(thread_id)
    owner = (memory or existing or {}).get("user_id")
    if owner and owner != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    if existing:
        if not existing.get("title") and title:
            thread_service.update_thread(thread_id, title=title)
        return
    thread_service.create_thread(title=title, user_id=user_id, thread_id=thread_id)


@router.get("/chat/threads", response_model=list[ChatThreadSummary])
async def list_chat_threads(request: Request):
    """List conversations for the authenticated user."""
    user_id = _request_user_id(request)
    threads_by_id = {thread["id"]: thread for thread in thread_service.list_threads(user_id=user_id)}
    memories = list_thread_memories(user_id=user_id)
    summaries: dict[str, ChatThreadSummary] = {}

    for memory_summary in memories:
        memory = get_thread_memory(memory_summary["thread_id"])
        if memory:
            thread = threads_by_id.get(memory["thread_id"])
            summaries[memory["thread_id"]] = (
                _thread_summary_from_metadata(thread, memory)
                if thread
                else _thread_summary_from_memory(memory)
            )

    for thread_id, thread in threads_by_id.items():
        if thread_id not in summaries:
            summaries[thread_id] = _thread_summary_from_metadata(thread)

    return sorted(summaries.values(), key=lambda item: item.updated_at, reverse=True)


@router.post("/chat/threads", response_model=ChatThreadSummary, status_code=status.HTTP_201_CREATED)
async def create_chat_thread(payload: ChatThreadCreate, request: Request):
    """Create an empty conversation and return its stable ID."""
    thread = thread_service.create_thread(title=payload.title or "New chat", user_id=_request_user_id(request))
    return _thread_summary_from_metadata(thread)


@router.get("/chat/threads/{thread_id}/messages", response_model=list[ChatThreadMessage])
async def get_chat_thread_messages(thread_id: str, request: Request):
    """Return saved user/assistant messages for a conversation."""
    memory = get_thread_memory(thread_id)
    thread = thread_service.get_thread(thread_id)
    user_id = _request_user_id(request)
    owner = (memory or thread or {}).get("user_id")
    if owner and owner != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    if not memory:
        if thread:
            return []
        raise HTTPException(status_code=404, detail="Thread not found")

    messages: list[ChatThreadMessage] = []
    for index, message in enumerate(memory["messages"]):
        role = _message_role(message)
        content = _message_content(message)
        if not role or not content:
            continue
        messages.append(
            ChatThreadMessage(
                id=_message_id(thread_id, index),
                role=role,
                content=content,
                created_at=_message_created_at(message),
            )
        )
    return messages


@router.delete("/chat/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_thread(thread_id: str, request: Request):
    """Delete a conversation's metadata, stored memory, and flat messages."""
    memory = get_thread_memory(thread_id)
    thread = thread_service.get_thread(thread_id)
    user_id = _request_user_id(request)
    owner = (memory or thread or {}).get("user_id")
    if owner and owner != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")
    if not memory and not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    delete_thread_memory(thread_id)
    delete_messages_by_thread(thread_id)
    thread_service.delete_thread(thread_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/chat/attachments", response_model=ChatAttachmentUploadResponse)
async def upload_chat_attachment(
    file: UploadFile = File(...),
    filename: str | None = Form(default=None),
):
    try:
        data = await file.read()
        source_name = filename or file.filename or "upload.txt"
        source, extracted_text = knowledge_service.ingest_file_bytes(source_name, data)
        return ChatAttachmentUploadResponse(source=source, extracted_preview=extracted_text[:4000])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, graph=Depends(get_jarvis_graph)):
    """Blocking chat endpoint. Invokes the graph and returns the final AI response."""
    user_id = _request_user_id(http_request)
    _ensure_thread(request.session_id, user_id, title=request.message[:80])
    try:
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "user_id": user_id,
                "session_id": request.session_id,
                "personality_id": request.personality_id,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=llm_unavailable_message(exc)) from exc
    ai_message = state["messages"][-1]
    content = _extract_text_content(ai_message)
    if not content:
        content = str(getattr(ai_message, "content", "") or "")
    return ChatResponse(content=content, session_id=request.session_id)


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket, graph=Depends(get_jarvis_graph)):
    """
    WebSocket streaming chat.

    Client → Server:  { "message": str, "session_id": str }
    Server → Client:  { "type": "token"|"tool_start"|"tool_end"|"done"|"error", ... }
    """
    try:
        user_email = await authenticate_websocket(websocket)
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                message = data.get("message", "")
                session_id = data.get("session_id", "default")
                personality_id = data.get("personality_id")
                model_streamed_text = False
                _ensure_thread(session_id, user_email, title=message[:80])

                async for event in graph.astream_events(
                    {
                        "messages": [HumanMessage(content=message)],
                        "user_id": user_email,
                        "session_id": session_id,
                        "personality_id": personality_id,
                    },
                    version="v2",
                ):
                    kind = event["event"]

                    if kind == "on_chat_model_start":
                        model_streamed_text = False

                    elif kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        token = _extract_text_content(chunk)
                        if token:
                            model_streamed_text = True
                            await websocket.send_text(
                                StreamChunk(type="token", content=token).model_dump_json()
                            )

                    elif kind == "on_chat_model_end":
                        output = event["data"].get("output")
                        token = _extract_text_content(output)
                        if token and not model_streamed_text:
                            await websocket.send_text(
                                StreamChunk(type="token", content=token).model_dump_json()
                            )

                    elif kind == "on_tool_start":
                        await websocket.send_text(
                            StreamChunk(
                                type="tool_start",
                                tool_name=event.get("name"),
                                tool_input=event["data"].get("input"),
                            ).model_dump_json()
                        )

                    elif kind == "on_tool_end":
                        await websocket.send_text(
                            StreamChunk(
                                type="tool_end",
                                tool_name=event.get("name"),
                                tool_output=event["data"].get("output"),
                            ).model_dump_json()
                        )

                await websocket.send_text(StreamChunk(type="done").model_dump_json())
            except Exception as exc:
                await websocket.send_text(
                    StreamChunk(type="error", content=llm_unavailable_message(exc)).model_dump_json()
                )

    except WebSocketDisconnect:
        pass
