"""Auth helper tests for protected backend access."""
import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi import HTTPException

from backend.api import auth
from backend.config import settings


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _token(payload: dict, secret: str = "test-ws-secret") -> str:
    payload_b64 = _b64url(json.dumps(payload).encode("utf-8"))
    signature = _b64url(hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest())
    return f"{payload_b64}.{signature}"


@pytest.fixture(autouse=True)
def auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "auth_allowed_emails", "majg2708@gmail.com")
    monkeypatch.setattr(settings, "backend_internal_auth_token", "test-internal-token")
    monkeypatch.setattr(settings, "backend_auth_token_secret", "test-ws-secret")


def test_verify_ws_token_accepts_allowed_email():
    token = _token({"email": "majg2708@gmail.com", "exp": int(time.time()) + 60})

    assert auth.verify_ws_token(token) == "majg2708@gmail.com"


@pytest.mark.parametrize(
    "payload,expected_status",
    [
        ({"email": "other@example.com", "exp": int(time.time()) + 60}, 403),
        ({"email": "majg2708@gmail.com", "exp": int(time.time()) - 1}, 401),
    ],
)
def test_verify_ws_token_rejects_invalid_payloads(payload, expected_status):
    with pytest.raises(HTTPException) as exc_info:
        auth.verify_ws_token(_token(payload))

    assert exc_info.value.status_code == expected_status


def test_verify_ws_token_rejects_bad_signature():
    token = _token({"email": "majg2708@gmail.com", "exp": int(time.time()) + 60})

    with pytest.raises(HTTPException) as exc_info:
        auth.verify_ws_token(f"{token}bad")

    assert exc_info.value.status_code == 401
