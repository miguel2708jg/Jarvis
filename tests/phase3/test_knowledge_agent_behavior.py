"""Phase 3: Agent-facing behavior checks for knowledge tools and prompt policy."""


def test_prompt_includes_knowledge_read_then_write_policy():
    from backend.agent.prompts import build_system_prompt

    prompt = build_system_prompt()
    assert "knowledge questions" in prompt.lower()
    assert "search the knowledge index" in prompt.lower()
    assert "only run knowledge write operations" in prompt.lower()


def test_registry_contains_knowledge_tools():
    from backend.tools.registry import ALL_TOOLS

    names = {tool.name for tool in ALL_TOOLS}
    assert "search_knowledge_pages" in names
    assert "get_knowledge_page" in names
    assert "ingest_note_to_knowledge" in names
    assert "lint_knowledge_base" in names
