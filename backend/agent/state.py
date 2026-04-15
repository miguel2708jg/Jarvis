"""JarvisState extends MessagesState with session metadata."""
from typing import Annotated, Any
from langgraph.graph import MessagesState


class JarvisState(MessagesState):
    """
    Extends MessagesState with user/session tracking and thread memory.
    
    Attributes:
        user_id: User identifier for multi-user support.
        session_id: Session identifier (defaults to thread_id).
        thread_id: Thread/conversation ID for persistent memory.
        memory_loaded: Flag indicating if memory was loaded from DB.
    """
    user_id: str | None = None
    session_id: str | None = None
    thread_id: str | None = None
    memory_loaded: bool = False
