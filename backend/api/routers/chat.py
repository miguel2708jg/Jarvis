"""Chat endpoints: POST /chat (blocking) and WS /ws/chat (streaming)."""
import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from backend.api.dependencies import get_jarvis_graph
from backend.api.errors import llm_unavailable_message
from backend.models.chat import ChatRequest, ChatResponse, StreamChunk
from backend.services import message_service, thread_service

router = APIRouter()


DEFAULT_THREAD_TITLE = "Nueva conversacion"


def _title_from_message(message: str) -> str:
    """Build a compact conversation title from the first user message."""
    compact = " ".join(message.strip().split())
    if not compact:
        return DEFAULT_THREAD_TITLE
    return compact[:57] + "..." if len(compact) > 60 else compact


def _ensure_visible_thread(thread_id: str, user_message: str, user_id: str = "default") -> None:
    """Ensure the user-facing thread row exists and has a useful initial title."""
    title = _title_from_message(user_message)
    thread = thread_service.ensure_thread(thread_id, title=title, user_id=user_id)
    if not thread.get("title") or thread.get("title") == DEFAULT_THREAD_TITLE:
        thread_service.update_thread(thread_id, title)


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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, graph=Depends(get_jarvis_graph)):
    """Blocking chat endpoint. Invokes the graph and returns the final AI response."""
    _ensure_visible_thread(request.session_id, request.message, user_id=request.user_id)
    message_service.create_message(request.session_id, request.message, role="user")
    try:
        state = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "user_id": request.user_id,
                "session_id": request.session_id,
                "personality_id": request.personality_id,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=llm_unavailable_message(exc)) from exc
    ai_message = state["messages"][-1]
    ai_content = _extract_text_content(ai_message) or str(ai_message.content)
    message_service.create_message(request.session_id, ai_content, role="assistant")
    thread_service.touch_thread(request.session_id)
    return ChatResponse(content=ai_content, session_id=request.session_id)


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket, graph=Depends(get_jarvis_graph)):
    """
    WebSocket streaming chat.

    Client → Server:  { "message": str, "session_id": str }
    Server → Client:  { "type": "token"|"tool_start"|"tool_end"|"done"|"error", ... }
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                message = data.get("message", "")
                session_id = data.get("session_id", "default")
                user_id = data.get("user_id", "default")
                personality_id = data.get("personality_id")
                model_streamed_text = False
                assistant_parts: list[str] = []

                _ensure_visible_thread(session_id, message, user_id=user_id)
                message_service.create_message(session_id, message, role="user")

                async for event in graph.astream_events(
                    {
                        "messages": [HumanMessage(content=message)],
                        "user_id": user_id,
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
                            assistant_parts.append(token)
                            await websocket.send_text(
                                StreamChunk(type="token", content=token).model_dump_json()
                            )

                    elif kind == "on_chat_model_end":
                        output = event["data"].get("output")
                        token = _extract_text_content(output)
                        if token and not model_streamed_text:
                            assistant_parts.append(token)
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

                assistant_text = "".join(assistant_parts)
                if assistant_text:
                    message_service.create_message(session_id, assistant_text, role="assistant")
                    thread_service.touch_thread(session_id)
                await websocket.send_text(StreamChunk(type="done").model_dump_json())
            except Exception as exc:
                await websocket.send_text(
                    StreamChunk(type="error", content=llm_unavailable_message(exc)).model_dump_json()
                )

    except WebSocketDisconnect:
        pass
