"""REST endpoints for Gmail via Google's remote Gmail MCP server."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.models.email_message import EmailMessage, EmailThread
from backend.services import email_service, gmail_mcp_client
from backend.services.email_service import EmailAuthorizationError, EmailValidationError

router = APIRouter()


def _translate_email_error(exc: Exception) -> HTTPException:
    if isinstance(exc, EmailValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, EmailAuthorizationError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, gmail_mcp_client.GmailMCPConfigurationError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, gmail_mcp_client.GmailMCPError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=503, detail=f"Gmail MCP unavailable: {exc}")


def _ensure_gmail_available() -> None:
    if not email_service.gmail_available():
        raise HTTPException(status_code=503, detail="Gmail MCP not configured")


@router.get("", response_model=list[EmailMessage])
def list_emails(label: str = "INBOX", max: int = Query(default=10, ge=1, le=100)):
    _ensure_gmail_available()
    try:
        return email_service.list_emails(max_results=max, label=label)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.get("/search", response_model=list[EmailMessage])
def search_emails(q: str, max: int = Query(default=10, ge=1, le=100)):
    _ensure_gmail_available()
    try:
        return email_service.search_emails(query=q, max_results=max)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.get("/threads/{thread_id}", response_model=EmailThread)
def get_thread(thread_id: str):
    _ensure_gmail_available()
    try:
        return email_service.get_thread(thread_id)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


class CreateDraftRequest(BaseModel):
    to: list[str]
    subject: str = ""
    body: str = ""
    cc: list[str] | None = None
    bcc: list[str] | None = None
    html_body: str | None = Field(default=None, alias="htmlBody")
    reply_to_message_id: str | None = Field(default=None, alias="replyToMessageId")
    attachment_source_ids: list[str] | None = Field(default=None, alias="attachmentSourceIds")

    model_config = {"populate_by_name": True}


class SendEmailRequest(CreateDraftRequest):
    user_confirmed: bool = Field(default=False, alias="userConfirmed")


class SendDraftRequest(BaseModel):
    user_confirmed: bool = Field(default=False, alias="userConfirmed")

    model_config = {"populate_by_name": True}


@router.post("/drafts")
def create_draft(request: CreateDraftRequest):
    _ensure_gmail_available()
    try:
        return email_service.create_draft(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            html_body=request.html_body,
            reply_to_message_id=request.reply_to_message_id,
            attachment_source_ids=request.attachment_source_ids,
        )
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/send")
def send_email(request: SendEmailRequest):
    _ensure_gmail_available()
    try:
        return email_service.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            html_body=request.html_body,
            reply_to_message_id=request.reply_to_message_id,
            attachment_source_ids=request.attachment_source_ids,
            user_confirmed=request.user_confirmed,
        )
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/drafts/{draft_id}/send")
def send_draft(draft_id: str, request: SendDraftRequest):
    _ensure_gmail_available()
    try:
        return email_service.send_draft(draft_id=draft_id, user_confirmed=request.user_confirmed)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.get("/drafts")
def list_drafts(q: str | None = None, max: int = Query(default=20, ge=1, le=50)):
    _ensure_gmail_available()
    try:
        return email_service.list_drafts(query=q, page_size=max)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


class LabelRequest(BaseModel):
    display_name: str = Field(alias="displayName")
    color: dict[str, str] | None = None

    model_config = {"populate_by_name": True}


class LabelUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, alias="displayName")
    color: dict[str, str] | None = None

    model_config = {"populate_by_name": True}


class LabelMutationRequest(BaseModel):
    label_ids: list[str] = Field(alias="labelIds")

    model_config = {"populate_by_name": True}


@router.get("/labels")
def list_labels(max: int = Query(default=100, ge=1, le=100)):
    _ensure_gmail_available()
    try:
        return email_service.list_labels(page_size=max)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/labels")
def create_label(request: LabelRequest):
    _ensure_gmail_available()
    try:
        return email_service.create_label(request.display_name, color=request.color)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.put("/labels/{label_id}")
def update_label(label_id: str, request: LabelUpdateRequest):
    _ensure_gmail_available()
    try:
        return email_service.update_label(
            label_id,
            display_name=request.display_name,
            color=request.color,
        )
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/threads/{thread_id}/labels")
def apply_thread_labels(thread_id: str, request: LabelMutationRequest):
    _ensure_gmail_available()
    try:
        return email_service.apply_labels_to_thread(thread_id, request.label_ids)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/threads/{thread_id}/labels/remove")
def remove_thread_labels(thread_id: str, request: LabelMutationRequest):
    _ensure_gmail_available()
    try:
        return email_service.remove_labels_from_thread(thread_id, request.label_ids)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/messages/{message_id}/labels")
def apply_message_labels(message_id: str, request: LabelMutationRequest):
    _ensure_gmail_available()
    try:
        return email_service.apply_labels_to_message(message_id, request.label_ids)
    except Exception as exc:
        raise _translate_email_error(exc) from exc


@router.post("/messages/{message_id}/labels/remove")
def remove_message_labels(message_id: str, request: LabelMutationRequest):
    _ensure_gmail_available()
    try:
        return email_service.remove_labels_from_message(message_id, request.label_ids)
    except Exception as exc:
        raise _translate_email_error(exc) from exc
