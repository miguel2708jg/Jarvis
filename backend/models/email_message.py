from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    snippet: str
    date: str
    labels: list[str] = Field(default_factory=list)
    is_read: bool = True


class EmailThread(BaseModel):
    thread_id: str
    messages: list[EmailMessage] = Field(default_factory=list)
