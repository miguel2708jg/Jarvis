"""Shared API error helpers."""


def llm_unavailable_message(exc: Exception) -> str:
    raw = str(exc)
    lower = raw.lower()
    if "unauthorized" in lower or "status code: 401" in lower:
        return (
            "Ollama authentication failed. Check OLLAMA_API_KEY for Ollama Cloud, "
            "or use local Ollama with OLLAMA_BASE_URL=http://localhost:11434."
        )
    return f"Jarvis model backend unavailable: {raw}"
