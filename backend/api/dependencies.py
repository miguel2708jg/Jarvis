"""FastAPI dependency: provides a singleton compiled graph with all tools."""
from backend.agent.graph import get_graph
from backend.tools.registry import ALL_TOOLS


def get_jarvis_graph():
    """Return the singleton Jarvis graph, built with all registered tools."""
    return get_graph(tools=ALL_TOOLS)
