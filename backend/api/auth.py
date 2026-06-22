"""Authentication helpers for Jarvis HTTP and WebSocket requests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, Request, WebSocket, status
from fastapi.responses import JSONResponse

from backend.config import settings


def allowed_emails() -> set[str]:
    return {
        email.strip().lower()
        for email in settings.auth_allowed_emails.split(",")
        if email.strip()
    }


def is_allowed_email(email: str | None) -> bool:
    return bool(email and email.strip().lower() in allowed_emails())


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign_payload(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_ws_token(token: str | None) -> str:
    if not settings.backend_auth_token_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Backend auth is not configured")
    if not token or "." not in token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")

    payload_b64, signature = token.split(".", 1)
    expected = _sign_payload(payload_b64, settings.backend_auth_token_secret)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")

    try:
        payload: dict[str, Any] = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token") from exc

    email = str(payload.get("email") or "").strip().lower()
    exp = int(payload.get("exp") or 0)
    if exp < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired auth token")
    if not is_allowed_email(email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not allowed")
    return email


def authenticate_internal_request(request: Request) -> str:
    configured_token = settings.backend_internal_auth_token
    if not configured_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Backend auth is not configured")

    supplied_token = request.headers.get("x-jarvis-internal-auth")
    email = request.headers.get("x-jarvis-user-email")
    if not supplied_token or not hmac.compare_digest(supplied_token, configured_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid backend auth token")
    if not is_allowed_email(email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not allowed")
    return email.strip().lower()


async def auth_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    try:
        email = authenticate_internal_request(request)
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    request.state.user_email = email
    return await call_next(request)


async def authenticate_websocket(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    return verify_ws_token(token)
