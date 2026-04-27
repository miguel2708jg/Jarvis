"""Phase 1: Verify Ollama LLM connection.

Requires an Ollama model configured in `.env` or environment variables.
Run: pytest tests/phase1/test_ollama_connection.py -m integration -v
"""
import pytest
from langchain_core.messages import HumanMessage


def test_ollama_base_url_normalization():
    """Trim a trailing API path so cloud and local hosts work with ChatOllama."""
    from backend.llm.ollama import _normalize_base_url

    assert _normalize_base_url("http://localhost:11434") == "http://localhost:11434"
    assert _normalize_base_url("http://localhost:11434/api") == "http://localhost:11434"
    assert _normalize_base_url("https://ollama.com/api/") == "https://ollama.com"


@pytest.mark.integration
def test_ollama_connection():
    """Ping Ollama and assert a non-empty response is returned."""
    from backend.llm import get_llm

    llm = get_llm()
    response = llm.invoke([HumanMessage(content="Say 'hello' in exactly one word.")])
    assert response.content
    assert isinstance(response.content, str)
    assert len(response.content) > 0


@pytest.mark.integration
def test_ollama_multi_turn():
    """Verify the LLM can maintain a simple two-turn conversation."""
    from langchain_core.messages import AIMessage, HumanMessage

    from backend.llm import get_llm

    llm = get_llm()
    messages = [
        HumanMessage(content="My name is Alex."),
        AIMessage(content="Nice to meet you, Alex!"),
        HumanMessage(content="What is my name?"),
    ]
    response = llm.invoke(messages)
    assert "Alex" in response.content
