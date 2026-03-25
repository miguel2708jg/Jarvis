"""REST endpoints for Email (Gmail) — read-only list/get/search + send."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _gmail_available() -> bool:
    from backend.config import settings
    return bool(settings.gmail_credentials_file or settings.gmail_token_file)


@router.get("")
def list_emails(label: str = "INBOX", max: int = Query(default=10, ge=1, le=100)):
    if not _gmail_available():
        raise HTTPException(status_code=503, detail="Gmail not configured")
    from backend.tools.email import list_emails as _list
    return _list.invoke({"max_results": max, "label": label})


@router.get("/search")
def search_emails(q: str, max: int = Query(default=10, ge=1, le=100)):
    if not _gmail_available():
        raise HTTPException(status_code=503, detail="Gmail not configured")
    from backend.tools.email import search_emails as _search
    return _search.invoke({"query": q, "max_results": max})


@router.get("/{message_id}")
def get_email(message_id: str):
    if not _gmail_available():
        raise HTTPException(status_code=503, detail="Gmail not configured")
    from backend.tools.email import get_email as _get
    return _get.invoke({"message_id": message_id})


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/send")
def send_email(request: SendEmailRequest):
    if not _gmail_available():
        raise HTTPException(status_code=503, detail="Gmail not configured")
    from backend.tools.email import send_email as _send
    return {"result": _send.invoke({"to": request.to, "subject": request.subject, "body": request.body})}
