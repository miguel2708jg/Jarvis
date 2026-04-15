from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field


class Thread(BaseModel):
    """Model for chat threads/conversations."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    user_id: str = "default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
