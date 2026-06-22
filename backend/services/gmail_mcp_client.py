"""Client for Google's remote Gmail MCP server."""
from __future__ import annotations

import json
from typing import Any

import anyio

from backend.config import settings
from backend.services import google_workspace_client


GMAIL_MCP_SCOPES = google_workspace_client.GOOGLE_WORKSPACE_SCOPES


class GmailMCPConfigurationError(RuntimeError):
    """Raised when Gmail OAuth configuration is missing."""


class GmailMCPError(RuntimeError):
    """Raised when Gmail MCP returns an error or cannot be reached."""


def is_configured() -> bool:
    return google_workspace_client.is_configured()


def get_credentials():
    try:
        return google_workspace_client.get_credentials(GMAIL_MCP_SCOPES)
    except google_workspace_client.GoogleWorkspaceConfigurationError as exc:
        raise GmailMCPConfigurationError(str(exc)) from exc


def _get_access_token() -> str:
    creds = get_credentials()
    if not creds.token:
        raise GmailMCPConfigurationError("Gmail OAuth did not return an access token.")
    return creds.token


def is_permission_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "caller does not have permission" in message or "permission denied" in message


def _extract_text_content(result: Any) -> str:
    parts: list[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            parts.append(text)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts).strip()


def _extract_structured_content(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if structured is None and hasattr(result, "model_dump"):
        structured = result.model_dump().get("structuredContent")
    if isinstance(structured, dict):
        return structured

    text = _extract_text_content(result)
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"content": text}
        if isinstance(parsed, dict):
            return parsed
        return {"content": parsed}

    return {}


async def _call_tool_async(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    headers = {"Authorization": f"Bearer {_get_access_token()}"}

    try:
        async with streamablehttp_client(
            settings.gmail_mcp_endpoint,
            headers=headers,
            timeout=settings.gmail_mcp_timeout_seconds,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
    except GmailMCPConfigurationError:
        raise
    except Exception as exc:
        raise GmailMCPError(f"Gmail MCP request failed: {exc}") from exc

    if getattr(result, "isError", False):
        message = _extract_text_content(result) or f"Gmail MCP tool {name} failed."
        raise GmailMCPError(message)

    return _extract_structured_content(result)


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return anyio.run(_call_tool_async, name, arguments or {})
