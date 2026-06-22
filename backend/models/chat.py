from typing import Literal, Any
from pydantic import BaseModel, Field
import uuid

from backend.models.knowledge import KnowledgeSource


class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    personality_id: str | None = None


class ChatResponse(BaseModel):
    content: str
    session_id: str


class ChatAttachmentUploadResponse(BaseModel):
    source: KnowledgeSource
    extracted_preview: str = ""


class StreamChunk(BaseModel):
    type: Literal["token", "tool_start", "tool_end", "done", "error"]
    content: str = ""
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: Any | None = None
