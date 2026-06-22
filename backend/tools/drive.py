"""LangChain tools for Google Drive."""
from langchain_core.tools import tool

from backend.services import drive_service


@tool
def search_drive_files(query: str, max_results: int = 10) -> list[dict]:
    """Search Google Drive files by name or Drive query syntax. Returns file metadata."""
    return drive_service.search_drive_files(query, max_results)


@tool
def get_drive_file(file_id: str, include_content: bool = True) -> dict:
    """Get Google Drive file metadata and, by default, exported text content when available."""
    return drive_service.get_drive_file(file_id, include_content)


@tool
def create_drive_text_file(
    name: str,
    content: str,
    parent_id: str | None = None,
    mime_type: str = "text/plain",
) -> dict:
    """Create a text file in Google Drive. Does not overwrite or delete existing files."""
    return drive_service.create_drive_text_file(name, content, parent_id, mime_type)


@tool
def create_drive_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a folder in Google Drive. Does not move, rename, or delete files."""
    return drive_service.create_drive_folder(name, parent_id)
