"""LangChain tools for knowledge vault workflows."""
from langchain_core.tools import tool

from backend.services import knowledge_service


@tool
def search_knowledge_pages(query: str, page_type: str | None = None, limit: int = 5) -> list[dict]:
    """Search knowledge pages lexically by title/summary/tags/aliases."""
    return [page.model_dump(by_alias=True) for page in knowledge_service.search_pages(query, page_type, limit)]


@tool
def get_knowledge_page(path: str) -> dict:
    """Fetch a knowledge page by relative wiki path."""
    return knowledge_service.get_page(path).model_dump(by_alias=True)


@tool
def ingest_note_to_knowledge(note_id: str) -> dict:
    """Snapshot a note into immutable raw sources and update the knowledge wiki."""
    return knowledge_service.ingest_note(note_id).model_dump(by_alias=True)


@tool
def lint_knowledge_base() -> dict:
    """Run explicit knowledge-base lint/maintenance and apply wiki fixes."""
    return knowledge_service.lint_knowledge_base().model_dump(by_alias=True)
