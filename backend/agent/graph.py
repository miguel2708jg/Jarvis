"""Assembles and compiles the Jarvis LangGraph StateGraph."""
from functools import partial

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from backend.agent.state import JarvisState
from backend.agent.nodes import call_model, call_model_with_tools
from backend.llm.bedrock import get_llm


def build_graph(tools: list | None = None):
    """
    Build the Jarvis StateGraph.

    - Phase 1 (no tools):  START → agent → END
    - Phase 2+ (tools):    START → agent ↔ tools → END
    """
    builder = StateGraph(JarvisState)

    if tools:
        llm_with_tools = get_llm().bind_tools(tools)
        agent_node = partial(call_model_with_tools, llm_with_tools=llm_with_tools)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", ToolNode(tools))
        builder.add_edge(START, "agent")
        builder.add_conditional_edges("agent", tools_condition)
        builder.add_edge("tools", "agent")
    else:
        builder.add_node("agent", call_model)
        builder.add_edge(START, "agent")
        builder.add_edge("agent", END)

    return builder.compile()


# Module-level compiled graph (no tools — Phase 1 default)
# Phase 2+: call build_graph(tools=ALL_TOOLS) explicitly
_graph = None


def get_graph(tools: list | None = None):
    """Return a singleton compiled graph, building it on first call."""
    global _graph
    if _graph is None:
        _graph = build_graph(tools=tools)
    return _graph


def reset_graph():
    """Reset the singleton (useful for tests)."""
    global _graph
    _graph = None


def get_graph_with_memory(tools: list | None = None):
    """
    Get graph with thread memory persistence enabled.
    
    The graph will automatically load and save conversation history
    from/to SQLite based on the thread_id in the state.
    """
    return get_graph(tools=tools)
