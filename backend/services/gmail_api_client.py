"""Direct Gmail REST API fallback for read operations."""
from __future__ import annotations

import base64
import re
from email.message import EmailMessage
from html import unescape
from typing import Any

from googleapiclient.discovery import build

from backend.services import gmail_mcp_client


class GmailAPIError(RuntimeError):
    """Raised when the direct Gmail API fallback cannot complete a request."""


def _service():
    return build("gmail", "v1", credentials=gmail_mcp_client.get_credentials(), cache_discovery=False)


def _header(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _decode_body(data: str | None) -> str:
    if not data:
        return ""
    padding = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8", errors="replace")
    except Exception:
        return ""


def _walk_parts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [payload]
    for part in payload.get("parts") or []:
        parts.extend(_walk_parts(part))
    return parts


def _plain_text_from_payload(payload: dict[str, Any]) -> str:
    html = ""
    for part in _walk_parts(payload):
        mime_type = part.get("mimeType")
        body = _decode_body((part.get("body") or {}).get("data"))
        if not body:
            continue
        if mime_type == "text/plain":
            return body.strip()
        if mime_type == "text/html" and not html:
            html = body
    if not html:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _message_to_mcp_shape(message: dict[str, Any]) -> dict[str, Any]:
    payload = message.get("payload") or {}
    headers = payload.get("headers") or []
    to_recipients = [value.strip() for value in _header(headers, "To").split(",") if value.strip()]
    return {
        "id": message.get("id", ""),
        "sender": _header(headers, "From"),
        "toRecipients": to_recipients,
        "subject": _header(headers, "Subject"),
        "plaintextBody": _plain_text_from_payload(payload),
        "snippet": message.get("snippet", ""),
        "date": _header(headers, "Date"),
        "labelIds": message.get("labelIds") or [],
    }


def get_thread(thread_id: str, message_format: str = "FULL_CONTENT") -> dict[str, Any]:
    try:
        result = (
            _service()
            .users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
    except Exception as exc:
        raise GmailAPIError(f"Gmail API request failed: {exc}") from exc

    return {
        "id": result.get("id", thread_id),
        "messages": [_message_to_mcp_shape(message) for message in result.get("messages") or []],
    }


def search_threads(query: str, max_results: int = 10) -> dict[str, Any]:
    try:
        result = (
            _service()
            .users()
            .threads()
            .list(userId="me", q=query, maxResults=min(max_results, 100))
            .execute()
        )
    except Exception as exc:
        raise GmailAPIError(f"Gmail API request failed: {exc}") from exc

    threads = [get_thread(thread["id"]) for thread in result.get("threads") or [] if thread.get("id")]
    return {"threads": threads}


def _build_message(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    if subject:
        message["Subject"] = subject
    if reply_to_message_id:
        message["In-Reply-To"] = reply_to_message_id
        message["References"] = reply_to_message_id

    message.set_content(body or "")
    if html_body:
        message.add_alternative(html_body, subtype="html")

    for attachment in attachments or []:
        mime_type = str(attachment.get("mime_type") or "application/octet-stream")
        maintype, _, subtype = mime_type.partition("/")
        if not maintype or not subtype:
            maintype, subtype = "application", "octet-stream"
        content = attachment.get("content") or b""
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif not isinstance(content, bytes):
            content = bytes(content)
        message.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=str(attachment.get("filename") or "attachment"),
        )
    return message


def _raw_message_payload(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")


def create_draft(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message = _build_message(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        html_body=html_body,
        reply_to_message_id=reply_to_message_id,
        attachments=attachments,
    )

    try:
        return (
            _service()
            .users()
            .drafts()
            .create(userId="me", body={"message": {"raw": _raw_message_payload(message)}})
            .execute()
        )
    except Exception as exc:
        raise GmailAPIError(f"Gmail API request failed: {exc}") from exc


def send_email(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message = _build_message(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        html_body=html_body,
        reply_to_message_id=reply_to_message_id,
        attachments=attachments,
    )

    try:
        return (
            _service()
            .users()
            .messages()
            .send(userId="me", body={"raw": _raw_message_payload(message)})
            .execute()
        )
    except Exception as exc:
        raise GmailAPIError(f"Gmail API request failed: {exc}") from exc


def send_draft(draft_id: str) -> dict[str, Any]:
    try:
        return (
            _service()
            .users()
            .drafts()
            .send(userId="me", body={"id": draft_id})
            .execute()
        )
    except Exception as exc:
        raise GmailAPIError(f"Gmail API request failed: {exc}") from exc
