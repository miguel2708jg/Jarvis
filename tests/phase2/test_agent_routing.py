"""Phase 2: Integration tests - verify the agent routes to the correct tool.

Requires an Ollama model configured in `.env` or environment variables.
Run: pytest tests/phase2/test_agent_routing.py -m integration -v
"""
import pytest
from langchain_core.messages import HumanMessage, ToolMessage


@pytest.fixture
def graph_with_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from backend.agent.graph import build_graph, reset_graph

    reset_graph()
    # Re-point stores to tmp_path
    from backend.storage.json_store import JsonStore
    import backend.tools.notes as nm
    import backend.tools.todos as tm

    nm._store = JsonStore("notes", data_dir=str(tmp_path))
    tm._store = JsonStore("todos", data_dir=str(tmp_path))

    from backend.tools.registry import ALL_TOOLS

    yield build_graph(tools=ALL_TOOLS)
    reset_graph()


@pytest.mark.integration
def test_agent_creates_note(graph_with_tools):
    """Agent should call create_note when asked to save a note."""
    result = graph_with_tools.invoke(
        {"messages": [HumanMessage(content="Save a note titled 'Meeting' with content 'Discuss Q4 goals'")]}
    )
    messages = result["messages"]
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert any("Meeting" in str(m.content) for m in tool_messages), (
        "Expected create_note tool to be called with 'Meeting'"
    )


@pytest.mark.integration
def test_agent_creates_todo(graph_with_tools):
    """Agent should call create_todo when asked to add a task."""
    result = graph_with_tools.invoke(
        {"messages": [HumanMessage(content="Add a high-priority todo: finish the presentation")]}
    )
    messages = result["messages"]
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert any("presentation" in str(m.content).lower() for m in tool_messages)
