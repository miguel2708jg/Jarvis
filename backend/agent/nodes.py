"""LangGraph nodes for the Jarvis agent."""
import json

from langchain_core.messages import BaseMessage, SystemMessage, convert_to_messages, message_to_dict

from backend.agent.state import JarvisState
from backend.agent.prompts import build_system_prompt
from backend.llm.bedrock import get_llm
from backend.services.thread_memory_service import (
    get_thread_messages,
    save_thread_memory,
)


def _thread_id_from_state(state: JarvisState) -> str | None:
    return state.get("thread_id") or state.get("session_id")


def _normalize_messages(messages: list | None) -> list[BaseMessage]:
    return list(convert_to_messages(messages or []))


def _message_fingerprint(message: BaseMessage) -> str:
    return json.dumps(message_to_dict(message), sort_keys=True, default=str)


def _merge_message_history(
    existing_messages: list[BaseMessage],
    current_messages: list[BaseMessage],
) -> list[BaseMessage]:
    """Merge stored history with current state, preserving repeated user turns."""
    if not existing_messages:
        return current_messages
    if not current_messages:
        return existing_messages

    existing_fingerprints = [_message_fingerprint(message) for message in existing_messages]
    current_fingerprints = [_message_fingerprint(message) for message in current_messages]

    overlap = 0
    max_overlap = min(len(existing_fingerprints), len(current_fingerprints))
    for size in range(max_overlap, 0, -1):
        if existing_fingerprints[-size:] == current_fingerprints[:size]:
            overlap = size
            break

    return existing_messages + current_messages[overlap:]


def _load_memory_if_needed(state: JarvisState) -> dict:
    """Load thread memory if not already loaded."""
    if state.get("memory_loaded", False):
        return {}

    current_messages = _normalize_messages(state.get("messages", []))
    thread_id = _thread_id_from_state(state)
    if not thread_id:
        return {"messages": current_messages, "memory_loaded": True}

    existing_messages = get_thread_messages(thread_id)
    return {
        "messages": _merge_message_history(existing_messages, current_messages),
        "memory_loaded": True,
    }


def _save_memory_if_needed(
    state: JarvisState,
    thread_id: str | None,
    response: BaseMessage,
) -> None:
    """Save current state to thread memory."""
    if not thread_id:
        return

    updated_messages = _normalize_messages(state.get("messages", [])) + [response]
    save_thread_memory(
        thread_id=thread_id,
        messages=updated_messages,
        user_id=state.get("user_id"),
        session_id=state.get("session_id") or thread_id,
    )


def call_model(state: JarvisState) -> dict:
    """Invoke the LLM with the current message history."""
    memory_update = _load_memory_if_needed(state)
    state = {**state, **memory_update}

    thread_id = _thread_id_from_state(state)
    llm = get_llm()
    messages = [SystemMessage(content=build_system_prompt())] + state["messages"]
    response = llm.invoke(messages)
    _save_memory_if_needed(state, thread_id, response)
    return {"messages": [response], "memory_loaded": True}


def call_model_with_tools(state: JarvisState, llm_with_tools) -> dict:
    """Invoke the LLM (with bound tools) with the current message history."""
    memory_update = _load_memory_if_needed(state)
    state = {**state, **memory_update}

    thread_id = _thread_id_from_state(state)
    messages = [SystemMessage(content=build_system_prompt())] + state["messages"]
    response = llm_with_tools.invoke(messages)
    _save_memory_if_needed(state, thread_id, response)
    return {"messages": [response], "memory_loaded": True}
