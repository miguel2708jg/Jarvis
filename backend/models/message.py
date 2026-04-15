from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Model for chat messages within a thread."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    thread_id: str
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
