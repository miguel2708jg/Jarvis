"""Google Workspace OAuth client behavior."""

import json

import pytest


def test_google_workspace_oauth_missing_token_fails_without_interactive_flow(monkeypatch, tmp_path):
    from backend.services import google_workspace_client

    credentials_file = tmp_path / "credentials.json"
    token_file = tmp_path / "token.json"
    credentials_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        google_workspace_client.settings,
        "google_credentials_file",
        str(credentials_file),
        raising=False,
    )
    monkeypatch.setattr(
        google_workspace_client.settings,
        "google_token_file",
        str(token_file),
        raising=False,
    )
    monkeypatch.setattr(google_workspace_client.settings, "gmail_credentials_file", None, raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "gmail_token_file", None, raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "gcal_token_file", None, raising=False)
    monkeypatch.setattr(
        google_workspace_client.settings,
        "google_allow_interactive_oauth",
        False,
        raising=False,
    )

    with pytest.raises(google_workspace_client.GoogleWorkspaceConfigurationError) as exc:
        google_workspace_client.get_credentials()

    message = str(exc.value)
    assert "authorized token file" in message
    assert "GOOGLE_ALLOW_INTERACTIVE_OAUTH=true" in message


def test_google_workspace_refresh_uses_google_request_without_constructor_timeout(monkeypatch, tmp_path):
    from backend.services import google_workspace_client
    import google.auth.transport.requests as request_module
    import google.oauth2.credentials as credentials_module

    token_file = tmp_path / "token.json"
    token_file.write_text(
        json.dumps(
            {
                "token": "old-token",
                "refresh_token": "refresh-token",
                "client_id": "id",
                "client_secret": "secret",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": google_workspace_client.GOOGLE_WORKSPACE_SCOPES,
            }
        ),
        encoding="utf-8",
    )
    calls = {}

    class FakeRequest:
        def __init__(self):
            calls["request_created"] = True

    class FakeCredentials:
        valid = False
        expired = True
        refresh_token = "refresh-token"
        token = "old-token"

        def has_scopes(self, scopes):
            return True

        def refresh(self, request):
            calls["request"] = request
            self.valid = True
            self.token = "new-token"

        def to_json(self):
            return '{"token":"new-token"}'

    monkeypatch.setattr(request_module, "Request", FakeRequest)
    monkeypatch.setattr(
        credentials_module.Credentials,
        "from_authorized_user_file",
        lambda path, scopes: FakeCredentials(),
    )
    monkeypatch.setattr(google_workspace_client.settings, "google_credentials_file", None, raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "google_token_file", str(token_file), raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "gmail_credentials_file", None, raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "gmail_token_file", None, raising=False)
    monkeypatch.setattr(google_workspace_client.settings, "gcal_token_file", None, raising=False)

    creds = google_workspace_client.get_credentials()

    assert creds.token == "new-token"
    assert calls["request_created"] is True
    assert isinstance(calls["request"], FakeRequest)
