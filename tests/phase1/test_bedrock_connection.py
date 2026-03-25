"""Phase 1: Verify Bedrock LLM connection.

Requires AWS credentials in .env or environment variables.
Run: pytest tests/phase1/test_bedrock_connection.py -m integration -v
"""
import pytest
from langchain_core.messages import HumanMessage


@pytest.mark.integration
def test_bedrock_connection():
    """Ping Bedrock and assert a non-empty response is returned."""
    from backend.llm.bedrock import get_llm
    llm = get_llm()
    response = llm.invoke([HumanMessage(content="Say 'hello' in exactly one word.")])
    assert response.content
    assert isinstance(response.content, str)
    assert len(response.content) > 0


@pytest.mark.integration
def test_bedrock_multi_turn():
    """Verify the LLM can maintain a simple two-turn conversation."""
    from langchain_core.messages import HumanMessage, AIMessage
    from backend.llm.bedrock import get_llm

    llm = get_llm()
    messages = [
        HumanMessage(content="My name is Alex."),
        AIMessage(content="Nice to meet you, Alex!"),
        HumanMessage(content="What is my name?"),
    ]
    response = llm.invoke(messages)
    assert "Alex" in response.content
