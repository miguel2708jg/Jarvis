"""Shared OAuth client helpers for Google Workspace APIs."""
from __future__ import annotations

import os
import json

from backend.config import settings

GOOGLE_WORKSPACE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


class GoogleWorkspaceConfigurationError(RuntimeError):
    """Raised when Google Workspace OAuth configuration is missing."""


def credentials_file() -> str | None:
    return settings.google_credentials_file or settings.gmail_credentials_file


def token_file() -> str | None:
    return settings.google_token_file or settings.gmail_token_file or settings.gcal_token_file


def is_configured() -> bool:
    return bool(credentials_file() or token_file())


def _authorization_required_message(configured_token_file: str | None) -> str:
    target = configured_token_file or "token.json"
    return (
        "Google Workspace OAuth needs an authorized token file before Jarvis can use "
        f"Gmail, Calendar, or Drive. Configure GOOGLE_TOKEN_FILE or GMAIL_TOKEN_FILE "
        f"and create {target}. The backend will not start interactive OAuth during a "
        "chat request. Temporarily set GOOGLE_ALLOW_INTERACTIVE_OAUTH=true only while "
        "running a local authorization command."
    )


def _token_has_scopes(configured_token_file: str, required_scopes: list[str]) -> bool:
    try:
        with open(configured_token_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    token_scopes = set(token_data.get("scopes") or [])
    return set(required_scopes).issubset(token_scopes)


def get_credentials(scopes: list[str] | None = None):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    required_scopes = scopes or GOOGLE_WORKSPACE_SCOPES
    configured_token_file = token_file()
    configured_credentials_file = credentials_file()
    creds = None
    token_exists_with_required_scopes = False

    if (
        configured_token_file
        and os.path.exists(configured_token_file)
        and _token_has_scopes(configured_token_file, required_scopes)
    ):
        token_exists_with_required_scopes = True
        creds = Credentials.from_authorized_user_file(configured_token_file, required_scopes)
        if not creds.has_scopes(required_scopes):
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:
                raise GoogleWorkspaceConfigurationError(
                    f"Google OAuth token refresh failed: {exc}"
                ) from exc
        elif configured_credentials_file and os.path.exists(configured_credentials_file):
            if not settings.google_allow_interactive_oauth or not configured_token_file:
                raise GoogleWorkspaceConfigurationError(
                    _authorization_required_message(configured_token_file)
                )
            flow = InstalledAppFlow.from_client_secrets_file(configured_credentials_file, required_scopes)
            creds = flow.run_local_server(port=0)
        else:
            if configured_token_file and not token_exists_with_required_scopes:
                raise GoogleWorkspaceConfigurationError(
                    _authorization_required_message(configured_token_file)
                )
            raise GoogleWorkspaceConfigurationError(
                "Google Workspace OAuth is not configured. Set GOOGLE_CREDENTIALS_FILE and GOOGLE_TOKEN_FILE."
            )

        if configured_token_file:
            token_dir = os.path.dirname(configured_token_file)
            if token_dir:
                os.makedirs(token_dir, exist_ok=True)
            with open(configured_token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

    if not creds.token:
        raise GoogleWorkspaceConfigurationError("Google OAuth did not return an access token.")

    return creds


def build_service(api_name: str, api_version: str):
    from googleapiclient.discovery import build

    return build(api_name, api_version, credentials=get_credentials(), cache_discovery=False)
