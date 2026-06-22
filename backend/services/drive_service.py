"""Google Drive read/create helpers for the Jarvis agent."""
from __future__ import annotations

import io
from typing import Any

from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload

from backend.services import google_workspace_client

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
TEXT_MIME_TYPE = "text/plain"
EXPORT_MIME_TYPE = "text/plain"


class DriveValidationError(ValueError):
    """Raised when a Drive request is invalid."""


class DriveAuthorizationError(PermissionError):
    """Raised when Google credentials do not authorize Drive access."""


class DriveServiceError(RuntimeError):
    """Raised when Google Drive cannot complete a request."""


def _service():
    return google_workspace_client.build_service("drive", "v3")


def _require_non_empty(value: str | None, field: str) -> str:
    if not value or not value.strip():
        raise DriveValidationError(f"{field} is required")
    return value.strip()


def _translate_error(exc: Exception) -> Exception:
    message = str(exc).lower()
    if "insufficient authentication scopes" in message or "permission" in message or "forbidden" in message:
        return DriveAuthorizationError(
            "Google Drive access is configured but not authorized. Delete GOOGLE_TOKEN_FILE, restart the backend, "
            "and approve the drive.readonly and drive.file scopes during OAuth."
        )
    return DriveServiceError(f"Google Drive request failed: {exc}")


def _file_to_dict(file: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": file.get("id", ""),
        "name": file.get("name", ""),
        "mime_type": file.get("mimeType", ""),
        "web_view_link": file.get("webViewLink", ""),
        "created_time": file.get("createdTime", ""),
        "modified_time": file.get("modifiedTime", ""),
        "parents": file.get("parents") or [],
    }


def _download_request(file_id: str, mime_type: str):
    service = _service()
    if mime_type.startswith("application/vnd.google-apps."):
        return service.files().export_media(fileId=file_id, mimeType=EXPORT_MIME_TYPE)
    return service.files().get_media(fileId=file_id)


def _download_text(file_id: str, mime_type: str) -> str:
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, _download_request(file_id, mime_type))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue().decode("utf-8", errors="replace")


def search_drive_files(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    query = _require_non_empty(query, "query")
    max_results = min(max(max_results, 1), 50)
    escaped = query.replace("'", "\\'")
    drive_query = (
        f"name contains '{escaped}' and trashed = false"
        if " " not in query or "=" not in query
        else f"({query}) and trashed = false"
    )
    try:
        result = (
            _service()
            .files()
            .list(
                q=drive_query,
                pageSize=max_results,
                fields="files(id,name,mimeType,webViewLink,createdTime,modifiedTime,parents)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return [_file_to_dict(file) for file in result.get("files") or []]


def get_drive_file(file_id: str, include_content: bool = True) -> dict[str, Any]:
    file_id = _require_non_empty(file_id, "file_id")
    try:
        file = (
            _service()
            .files()
            .get(fileId=file_id, fields="id,name,mimeType,webViewLink,createdTime,modifiedTime,parents")
            .execute()
        )
        data = _file_to_dict(file)
        if include_content:
            data["content"] = _download_text(file_id, data["mime_type"])
        return data
    except Exception as exc:
        raise _translate_error(exc) from exc


def create_drive_text_file(
    name: str,
    content: str,
    parent_id: str | None = None,
    mime_type: str = TEXT_MIME_TYPE,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "name": _require_non_empty(name, "name"),
        "mimeType": mime_type or TEXT_MIME_TYPE,
    }
    if parent_id:
        metadata["parents"] = [_require_non_empty(parent_id, "parent_id")]
    media = MediaInMemoryUpload((content or "").encode("utf-8"), mimetype=TEXT_MIME_TYPE, resumable=False)
    try:
        file = (
            _service()
            .files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,mimeType,webViewLink,createdTime,modifiedTime,parents",
            )
            .execute()
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _file_to_dict(file)


def create_drive_folder(name: str, parent_id: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "name": _require_non_empty(name, "name"),
        "mimeType": FOLDER_MIME_TYPE,
    }
    if parent_id:
        metadata["parents"] = [_require_non_empty(parent_id, "parent_id")]
    try:
        folder = (
            _service()
            .files()
            .create(body=metadata, fields="id,name,mimeType,webViewLink,createdTime,modifiedTime,parents")
            .execute()
        )
    except Exception as exc:
        raise _translate_error(exc) from exc
    return _file_to_dict(folder)
