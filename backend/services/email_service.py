"""App-facing Gmail adapter backed by Google's remote Gmail MCP server."""
from __future__ import annotations

from typing import Any

from backend.services import gmail_api_client, gmail_mcp_client, knowledge_service


class EmailValidationError(ValueError):
    """Raised when a local email request is invalid."""


class EmailAuthorizationError(PermissionError):
    """Raised when Gmail credentials exist but do not authorize mail access."""


GMAIL_AUTHORIZATION_MESSAGE = (
    "Gmail access is configured but not authorized for inbox access. "
    "Delete the configured GMAIL_TOKEN_FILE, restart the backend, and approve the "
    "https://www.googleapis.com/auth/gmail.modify scope during OAuth. "
    "Also confirm the Gmail API is enabled for the Google Cloud project."
)


def gmail_available() -> bool:
    return gmail_mcp_client.is_configured()


def _is_gmail_permission_error(exc: Exception) -> bool:
    message = str(exc).lower()
    provider_markers = (
        "caller does not have permission",
        "permission denied",
        "insufficient authentication scopes",
        "insufficient permissions",
        "access not configured",
        "api has not been used",
        "forbidden",
    )
    return (
        gmail_mcp_client.is_permission_error(exc)
        or any(marker in message for marker in provider_markers)
    )


def _authorization_error() -> EmailAuthorizationError:
    return EmailAuthorizationError(GMAIL_AUTHORIZATION_MESSAGE)


def _call_mcp_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return gmail_mcp_client.call_tool(name, arguments or {})
    except gmail_mcp_client.GmailMCPError as exc:
        if _is_gmail_permission_error(exc):
            raise _authorization_error() from exc
        raise


def _require_non_empty(value: str | None, field: str) -> str:
    if not value or not value.strip():
        raise EmailValidationError(f"{field} is required")
    return value.strip()


def _normalize_string_list(values: list[str] | None, field: str) -> list[str]:
    normalized = [value.strip() for value in (values or []) if value and value.strip()]
    if values is not None and not normalized:
        raise EmailValidationError(f"{field} must contain at least one value")
    return normalized


def _require_send_confirmation(user_confirmed: bool) -> None:
    if not user_confirmed:
        raise EmailValidationError("Sending email requires explicit user confirmation.")


def _attachments_from_source_ids(source_ids: list[str] | None) -> list[dict[str, Any]]:
    normalized = _normalize_string_list(source_ids, "attachment_source_ids") if source_ids is not None else []
    try:
        return [
            knowledge_service.get_source_attachment(source_id)
            for source_id in normalized
        ]
    except FileNotFoundError as exc:
        raise EmailValidationError(f"Attachment source not found: {exc}") from exc


def _label_to_query(label: str | None) -> str:
    normalized = (label or "INBOX").strip()
    upper = normalized.upper()
    if upper == "INBOX":
        return "in:inbox"
    if upper == "UNREAD":
        return "is:unread"
    if not normalized:
        return "in:inbox"
    return f"label:{normalized}"


def _latest_message(thread: dict[str, Any]) -> dict[str, Any]:
    messages = thread.get("messages") or []
    if not messages:
        return {}
    return messages[-1]


def _message_to_email(message: dict[str, Any], thread_id: str) -> dict[str, Any]:
    labels = message.get("labelIds") or []
    recipients = message.get("toRecipients") or []
    body = message.get("plaintextBody") or message.get("htmlBody") or ""
    return {
        "message_id": message.get("id", ""),
        "thread_id": thread_id,
        "sender": message.get("sender", ""),
        "recipient": ", ".join(recipients),
        "subject": message.get("subject", ""),
        "body": body,
        "snippet": message.get("snippet", ""),
        "date": message.get("date", ""),
        "labels": labels,
        "is_read": "UNREAD" not in labels,
    }


def _thread_to_summary(thread: dict[str, Any]) -> dict[str, Any] | None:
    message = _latest_message(thread)
    if not message:
        return None
    return _message_to_email(message, thread.get("id", ""))


def _search_threads(query: str, max_results: int = 10) -> dict[str, Any]:
    if max_results < 1:
        raise EmailValidationError("max_results must be at least 1")
    try:
        return gmail_mcp_client.call_tool(
            "search_threads",
            {"query": query, "pageSize": min(max_results, 100)},
        )
    except gmail_mcp_client.GmailMCPError as exc:
        if _is_gmail_permission_error(exc):
            try:
                return gmail_api_client.search_threads(query, max_results=max_results)
            except Exception as fallback_exc:
                if _is_gmail_permission_error(fallback_exc):
                    raise _authorization_error() from fallback_exc
                raise
        raise


def list_emails(max_results: int = 10, label: str = "INBOX") -> list[dict[str, Any]]:
    return search_emails(_label_to_query(label), max_results=max_results)


def search_emails(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    query = _require_non_empty(query, "query")
    result = _search_threads(query, max_results=max_results)
    emails: list[dict[str, Any]] = []
    for thread in result.get("threads") or []:
        summary = _thread_to_summary(thread)
        if summary:
            emails.append(summary)
    return emails


def get_thread(thread_id: str, message_format: str = "FULL_CONTENT") -> dict[str, Any]:
    thread_id = _require_non_empty(thread_id, "thread_id")
    try:
        result = gmail_mcp_client.call_tool(
            "get_thread",
            {"threadId": thread_id, "messageFormat": message_format},
        )
    except gmail_mcp_client.GmailMCPError as exc:
        if _is_gmail_permission_error(exc):
            try:
                result = gmail_api_client.get_thread(thread_id, message_format=message_format)
            except Exception as fallback_exc:
                if _is_gmail_permission_error(fallback_exc):
                    raise _authorization_error() from fallback_exc
                raise
        else:
            raise
    messages = [
        _message_to_email(message, result.get("id", thread_id))
        for message in result.get("messages") or []
    ]
    return {"thread_id": result.get("id", thread_id), "messages": messages}


def get_email(message_id: str) -> dict[str, Any]:
    raise EmailValidationError("Fetching by message_id is not supported by Gmail MCP. Use get_thread.")


def create_draft(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachment_source_ids: list[str] | None = None,
) -> dict[str, Any]:
    recipients = _normalize_string_list(to, "to")
    if not recipients:
        raise EmailValidationError("to is required")
    normalized_cc = _normalize_string_list(cc, "cc") if cc else None
    normalized_bcc = _normalize_string_list(bcc, "bcc") if bcc else None
    normalized_attachment_source_ids = (
        _normalize_string_list(attachment_source_ids, "attachment_source_ids")
        if attachment_source_ids is not None
        else []
    )

    if normalized_attachment_source_ids:
        try:
            attachments = _attachments_from_source_ids(normalized_attachment_source_ids)
            return gmail_api_client.create_draft(
                to=recipients,
                subject=subject or "",
                body=body or "",
                cc=normalized_cc,
                bcc=normalized_bcc,
                html_body=html_body,
                reply_to_message_id=reply_to_message_id,
                attachments=attachments,
            )
        except Exception as exc:
            if _is_gmail_permission_error(exc):
                raise _authorization_error() from exc
            raise

    payload: dict[str, Any] = {
        "to": recipients,
        "subject": subject or "",
        "body": body or "",
    }
    if normalized_cc:
        payload["cc"] = normalized_cc
    if normalized_bcc:
        payload["bcc"] = normalized_bcc
    if html_body:
        payload["htmlBody"] = html_body
    if reply_to_message_id:
        payload["replyToMessageId"] = reply_to_message_id

    return _call_mcp_tool("create_draft", payload)


def send_email(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachment_source_ids: list[str] | None = None,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    _require_send_confirmation(user_confirmed)
    recipients = _normalize_string_list(to, "to")
    if not recipients:
        raise EmailValidationError("to is required")

    try:
        return gmail_api_client.send_email(
            to=recipients,
            subject=subject or "",
            body=body or "",
            cc=_normalize_string_list(cc, "cc") if cc else None,
            bcc=_normalize_string_list(bcc, "bcc") if bcc else None,
            html_body=html_body,
            reply_to_message_id=reply_to_message_id,
            attachments=_attachments_from_source_ids(attachment_source_ids),
        )
    except EmailValidationError:
        raise
    except Exception as exc:
        if _is_gmail_permission_error(exc):
            raise _authorization_error() from exc
        raise


def send_draft(draft_id: str, user_confirmed: bool = False) -> dict[str, Any]:
    _require_send_confirmation(user_confirmed)
    draft_id = _require_non_empty(draft_id, "draft_id")
    try:
        return gmail_api_client.send_draft(draft_id)
    except Exception as exc:
        if _is_gmail_permission_error(exc):
            raise _authorization_error() from exc
        raise


def list_drafts(query: str | None = None, page_size: int = 20) -> dict[str, Any]:
    payload: dict[str, Any] = {"pageSize": min(max(page_size, 1), 50)}
    if query:
        payload["query"] = query
    return _call_mcp_tool("list_drafts", payload)


def list_labels(page_size: int = 100) -> dict[str, Any]:
    return _call_mcp_tool("list_labels", {"pageSize": min(max(page_size, 1), 100)})


def create_label(display_name: str, color: dict[str, str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"displayName": _require_non_empty(display_name, "display_name")}
    if color:
        payload["color"] = color
    return _call_mcp_tool("create_label", payload)


def update_label(
    label_id: str,
    display_name: str | None = None,
    color: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"labelId": _require_non_empty(label_id, "label_id")}
    if display_name:
        payload["displayName"] = display_name
    if color:
        payload["color"] = color
    if len(payload) == 1:
        raise EmailValidationError("display_name or color is required")
    return _call_mcp_tool("update_label", payload)


def apply_labels_to_thread(thread_id: str, label_ids: list[str]) -> dict[str, Any]:
    return _call_mcp_tool(
        "label_thread",
        {
            "threadId": _require_non_empty(thread_id, "thread_id"),
            "labelIds": _normalize_string_list(label_ids, "label_ids"),
        },
    )


def remove_labels_from_thread(thread_id: str, label_ids: list[str]) -> dict[str, Any]:
    return _call_mcp_tool(
        "unlabel_thread",
        {
            "threadId": _require_non_empty(thread_id, "thread_id"),
            "labelIds": _normalize_string_list(label_ids, "label_ids"),
        },
    )


def apply_labels_to_message(message_id: str, label_ids: list[str]) -> dict[str, Any]:
    return _call_mcp_tool(
        "label_message",
        {
            "messageId": _require_non_empty(message_id, "message_id"),
            "labelIds": _normalize_string_list(label_ids, "label_ids"),
        },
    )


def remove_labels_from_message(message_id: str, label_ids: list[str]) -> dict[str, Any]:
    return _call_mcp_tool(
        "unlabel_message",
        {
            "messageId": _require_non_empty(message_id, "message_id"),
            "labelIds": _normalize_string_list(label_ids, "label_ids"),
        },
    )
