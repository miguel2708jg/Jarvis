"""Phase 3: Prompt context and node prompt injection tests."""

from datetime import datetime, timezone

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


def test_build_system_prompt_includes_current_datetime_context(monkeypatch):
    import backend.agent.prompts as prompts

    monkeypatch.setattr(prompts.settings, "assistant_timezone", "UTC", raising=False)

    prompt = prompts.build_system_prompt(
        datetime(2026, 4, 8, 17, 45, 30, tzinfo=timezone.utc)
    )

    assert "Current date: 2026-04-08" in prompt
    assert "Current time: 17:45:30" in prompt
    assert "Current weekday: Wednesday" in prompt
    assert "Current timezone: UTC" in prompt
    assert "Current datetime: 2026-04-08T17:45:30+00:00" in prompt


@pytest.mark.parametrize("with_tools", [False, True])
def test_model_nodes_inject_dynamic_system_prompt(monkeypatch, with_tools):
    import backend.agent.nodes as nodes

    captured: dict[str, list] = {}

    class FakeLLM:
        def invoke(self, messages):
            captured["messages"] = messages
            return AIMessage(content="ok")

    monkeypatch.setattr(
        nodes,
        "_load_memory_if_needed",
        lambda state: {"messages": state["messages"], "memory_loaded": True},
    )
    monkeypatch.setattr(nodes, "_save_memory_if_needed", lambda state, thread_id, response: None)
    monkeypatch.setattr(
        nodes,
        "build_system_prompt",
        lambda **kwargs: "Current date: 2026-04-08",
    )

    state = {"messages": [HumanMessage(content="Hola")], "personality_id": "focus"}
    if with_tools:
        nodes.call_model_with_tools(state, FakeLLM())
    else:
        monkeypatch.setattr(nodes, "get_llm", lambda: FakeLLM())
        nodes.call_model(state)

    assert isinstance(captured["messages"][0], SystemMessage)
    assert captured["messages"][0].content == "Current date: 2026-04-08"
    assert captured["messages"][1].content == "Hola"


def test_build_system_prompt_defaults_to_normal_personality():
    from backend.agent.prompts import build_system_prompt

    prompt = build_system_prompt()

    assert "Active personality: Jarvis normal" in prompt
    assert "emails" not in prompt.lower()


def test_build_system_prompt_includes_active_personality():
    from backend.agent.prompts import build_system_prompt

    prompt = build_system_prompt(personality_id="mentor")

    assert "Active personality: Mentor (mentor)" in prompt
    assert "Role: Strategic guide for important decisions and personal growth." in prompt
    assert "Tone:" in prompt
    assert "Rules:" in prompt


def test_build_system_prompt_includes_coach_clarity_frame():
    from backend.agent.prompts import build_system_prompt

    prompt = build_system_prompt(personality_id="coach")

    assert "Objetivo" in prompt
    assert "Relevancia" in prompt
    assert "Expectativas" in prompt
    assert "Indicadores" in prompt


def test_build_system_prompt_ignores_unknown_personality():
    from backend.agent.prompts import build_system_prompt

    prompt = build_system_prompt(personality_id="unknown")

    assert "Active personality: Jarvis normal" in prompt
