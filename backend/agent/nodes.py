"""LangGraph nodes for the Jarvis agent."""
from langchain_core.messages import SystemMessage

from backend.agent.state import JarvisState
from backend.agent.prompts import SYSTEM_PROMPT
from backend.llm.bedrock import get_llm


def call_model(state: JarvisState) -> dict:
    """Invoke the LLM with the current message history."""
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def call_model_with_tools(state: JarvisState, llm_with_tools) -> dict:
    """Invoke the LLM (with bound tools) with the current message history."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
