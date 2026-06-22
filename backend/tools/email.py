"""LangChain tools for Gmail via Google's remote Gmail MCP server."""
from langchain_core.tools import tool

from backend.services import email_service


@tool
def search_email_threads(query: str, max_results: int = 10) -> list[dict]:
    """Search Gmail threads using Gmail search syntax and return message summaries."""
    return email_service.search_emails(query, max_results)


@tool
def get_email_thread(thread_id: str) -> dict:
    """Get the full content of a Gmail thread by thread ID."""
    return email_service.get_thread(thread_id)


@tool
def create_email_draft(
    to: list[str],
    subject: str = "",
    body: str = "",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    html_body: str | None = None,
    reply_to_message_id: str | None = None,
    attachment_source_ids: list[str] | None = None,
) -> dict:
    """Create a Gmail draft. This does not send email. Use attachment_source_ids for uploaded chat files."""
    return email_service.create_draft(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        html_body=html_body,
        reply_to_message_id=reply_to_message_id,
        attachment_source_ids=attachment_source_ids,
    )


@tool
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
) -> dict:
    """Send a Gmail email only after the user explicitly confirms sending."""
    return email_service.send_email(
        to=to,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        html_body=html_body,
        reply_to_message_id=reply_to_message_id,
        attachment_source_ids=attachment_source_ids,
        user_confirmed=user_confirmed,
    )


@tool
def send_email_draft(draft_id: str, user_confirmed: bool = False) -> dict:
    """Send an existing Gmail draft only after the user explicitly confirms sending."""
    return email_service.send_draft(draft_id=draft_id, user_confirmed=user_confirmed)


@tool
def list_email_drafts(query: str | None = None, page_size: int = 20) -> dict:
    """List Gmail drafts, optionally filtered with Gmail search syntax."""
    return email_service.list_drafts(query=query, page_size=page_size)


@tool
def list_email_labels(page_size: int = 100) -> dict:
    """List Gmail labels."""
    return email_service.list_labels(page_size=page_size)


@tool
def create_email_label(display_name: str) -> dict:
    """Create a Gmail label."""
    return email_service.create_label(display_name)


@tool
def update_email_label(label_id: str, display_name: str) -> dict:
    """Rename a Gmail label."""
    return email_service.update_label(label_id, display_name=display_name)


@tool
def apply_email_labels_to_thread(thread_id: str, label_ids: list[str]) -> dict:
    """Apply Gmail labels to a thread after the user explicitly asks."""
    return email_service.apply_labels_to_thread(thread_id, label_ids)


@tool
def remove_email_labels_from_thread(thread_id: str, label_ids: list[str]) -> dict:
    """Remove Gmail labels from a thread after the user explicitly asks."""
    return email_service.remove_labels_from_thread(thread_id, label_ids)


@tool
def apply_email_labels_to_message(message_id: str, label_ids: list[str]) -> dict:
    """Apply Gmail labels to a message after the user explicitly asks."""
    return email_service.apply_labels_to_message(message_id, label_ids)


@tool
def remove_email_labels_from_message(message_id: str, label_ids: list[str]) -> dict:
    """Remove Gmail labels from a message after the user explicitly asks."""
    return email_service.remove_labels_from_message(message_id, label_ids)
