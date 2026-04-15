"""Chat endpoints: POST /chat (blocking) and WS /ws/chat (streaming)."""
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from backend.api.dependencies import get_jarvis_graph
from backend.models.chat import ChatRequest, ChatResponse, StreamChunk

router = APIRouter()


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
    state = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "session_id": request.session_id,
        }
    )
    ai_message = state["messages"][-1]
    return ChatResponse(content=ai_message.content, session_id=request.session_id)


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
                model_streamed_text = False

                async for event in graph.astream_events(
                    {
                        "messages": [HumanMessage(content=message)],
                        "session_id": session_id,
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
                    StreamChunk(type="error", content=str(exc)).model_dump_json()
                )

    except WebSocketDisconnect:
        pass
