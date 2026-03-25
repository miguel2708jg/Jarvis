"""JarvisState extends MessagesState with session metadata."""
from typing import Annotated
from langgraph.graph import MessagesState


class JarvisState(MessagesState):
    """Extends MessagesState with user/session tracking."""
    user_id: str | None = None
    session_id: str | None = None
