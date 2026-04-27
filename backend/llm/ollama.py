"""Factory for the Ollama LLM; returns a provider-agnostic BaseChatModel."""
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from backend.config import settings


def _normalize_base_url(base_url: str) -> str:
    """Normalize host values because the Ollama client appends `/api` internally."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/api"):
        return normalized[:-4]
    return normalized


def get_llm() -> BaseChatModel:
    """Return a ChatOllama instance configured from settings."""
    kwargs: dict = {
        "model": settings.ollama_model_id,
        "base_url": _normalize_base_url(settings.ollama_base_url),
        "temperature": settings.ollama_temperature,
        # Tool-calling models are more reliable when streaming is bypassed for tool steps.
        "disable_streaming": "tool_calling",
    }
    if settings.ollama_api_key:
        kwargs["client_kwargs"] = {
            "headers": {"Authorization": f"Bearer {settings.ollama_api_key}"}
        }

    return ChatOllama(**kwargs)
