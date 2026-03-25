"""Phase 1: Verify the LangGraph state machine works end-to-end.

Run: pytest tests/phase1/test_graph_basic.py -m integration -v
"""
import pytest
from langchain_core.messages import HumanMessage, AIMessage


@pytest.mark.integration
def test_graph_returns_ai_message():
    """Invoke the graph with a simple message and assert an AIMessage is in state."""
    from backend.agent.graph import build_graph

    graph = build_graph()  # no tools — Phase 1
    result = graph.invoke({"messages": [HumanMessage(content="Hello, Jarvis!")]})

    messages = result["messages"]
    assert len(messages) >= 2  # human + AI
    last = messages[-1]
    assert isinstance(last, AIMessage)
    assert last.content


@pytest.mark.integration
def test_graph_multi_turn():
    """Verify state accumulates across multiple invocations."""
    from backend.agent.graph import build_graph

    graph = build_graph()
    state = {"messages": [HumanMessage(content="My favourite colour is blue.")]}
    state = graph.invoke(state)

    state["messages"].append(HumanMessage(content="What is my favourite colour?"))
    state = graph.invoke(state)

    last_ai = state["messages"][-1]
    assert "blue" in last_ai.content.lower()
