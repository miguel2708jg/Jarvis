"""Unit tests for the Gmail MCP-backed email adapter."""
import pytest

from backend.services import email_service


def test_list_emails_maps_label_to_query_and_thread_summary(monkeypatch):
    calls = []

    def fake_call_tool(name, arguments):
        calls.append((name, arguments))
        return {
            "threads": [
                {
                    "id": "thread-1",
                    "messages": [
                        {
                            "id": "msg-1",
                            "sender": "boss@example.com",
                            "toRecipients": ["me@example.com"],
                            "subject": "Status",
                            "snippet": "Please review",
                            "date": "2026-06-10",
                            "labelIds": ["INBOX", "UNREAD"],
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr(email_service.gmail_mcp_client, "call_tool", fake_call_tool)

    emails = email_service.list_emails(max_results=5, label="UNREAD")

    assert calls == [("search_threads", {"query": "is:unread", "pageSize": 5})]
    assert emails[0]["message_id"] == "msg-1"
    assert emails[0]["thread_id"] == "thread-1"
    assert emails[0]["recipient"] == "me@example.com"
    assert emails[0]["is_read"] is False


def test_list_emails_falls_back_to_gmail_api_when_mcp_denies_permission(monkeypatch):
    calls = []

    def fake_call_tool(name, arguments):
        calls.append((name, arguments))
        raise email_service.gmail_mcp_client.GmailMCPError("The caller does not have permission")

    monkeypatch.setattr(email_service.gmail_mcp_client, "call_tool", fake_call_tool)
    monkeypatch.setattr(
        email_service.gmail_api_client,
        "search_threads",
        lambda query, max_results: {
            "threads": [
                {
                    "id": "thread-api",
                    "messages": [
                        {
                            "id": "msg-api",
                            "sender": "sender@example.com",
                            "toRecipients": ["me@example.com"],
                            "subject": "Fallback",
                            "snippet": "Loaded through Gmail API",
                            "date": "2026-06-11",
                            "labelIds": ["INBOX"],
                        }
                    ],
                }
            ]
        },
    )

    emails = email_service.list_emails(max_results=3, label="INBOX")

    assert calls == [("search_threads", {"query": "in:inbox", "pageSize": 3})]
    assert emails[0]["thread_id"] == "thread-api"
    assert emails[0]["message_id"] == "msg-api"
    assert emails[0]["is_read"] is True


def test_list_emails_reports_authorization_error_when_fallback_is_denied(monkeypatch):
    def fake_call_tool(name, arguments):
        raise email_service.gmail_mcp_client.GmailMCPError("The caller does not have permission")

    def fake_search_threads(query, max_results):
        raise email_service.gmail_api_client.GmailAPIError(
            "Gmail API request failed: 403 insufficient authentication scopes"
        )

    monkeypatch.setattr(email_service.gmail_mcp_client, "call_tool", fake_call_tool)
    monkeypatch.setattr(email_service.gmail_api_client, "search_threads", fake_search_threads)

    with pytest.raises(email_service.EmailAuthorizationError) as exc:
        email_service.list_emails(max_results=3, label="INBOX")

    assert "GMAIL_TOKEN_FILE" in str(exc.value)


def test_search_emails_rejects_empty_query():
    with pytest.raises(email_service.EmailValidationError):
        email_service.search_emails(" ")


def test_get_thread_maps_full_messages(monkeypatch):
    monkeypatch.setattr(
        email_service.gmail_mcp_client,
        "call_tool",
        lambda name, arguments: {
            "id": arguments["threadId"],
            "messages": [
                {
                    "id": "msg-1",
                    "sender": "a@example.com",
                    "toRecipients": ["me@example.com"],
                    "subject": "Hi",
                    "plaintextBody": "Full text",
                    "snippet": "Full",
                    "date": "2026-06-10",
                    "labelIds": ["INBOX"],
                }
            ],
        },
    )

    thread = email_service.get_thread("thread-1")

    assert thread["thread_id"] == "thread-1"
    assert thread["messages"][0]["body"] == "Full text"
    assert thread["messages"][0]["is_read"] is True


def test_get_thread_falls_back_to_gmail_api_when_mcp_denies_permission(monkeypatch):
    monkeypatch.setattr(
        email_service.gmail_mcp_client,
        "call_tool",
        lambda name, arguments: (_ for _ in ()).throw(
            email_service.gmail_mcp_client.GmailMCPError("The caller does not have permission")
        ),
    )
    monkeypatch.setattr(
        email_service.gmail_api_client,
        "get_thread",
        lambda thread_id, message_format="FULL_CONTENT": {
            "id": thread_id,
            "messages": [
                {
                    "id": "msg-api",
                    "sender": "a@example.com",
                    "toRecipients": ["me@example.com"],
                    "subject": "Hi",
                    "plaintextBody": "Direct API body",
                    "snippet": "Direct",
                    "date": "2026-06-11",
                    "labelIds": ["UNREAD"],
                }
            ],
        },
    )

    thread = email_service.get_thread("thread-api")

    assert thread["thread_id"] == "thread-api"
    assert thread["messages"][0]["body"] == "Direct API body"
    assert thread["messages"][0]["is_read"] is False


def test_create_draft_validates_recipients(monkeypatch):
    called = {}

    def fake_call_tool(name, arguments):
        called["name"] = name
        called["arguments"] = arguments
        return {"id": "draft-1"}

    monkeypatch.setattr(email_service.gmail_mcp_client, "call_tool", fake_call_tool)

    draft = email_service.create_draft(
        to=["user@example.com"],
        subject="Draft",
        body="Body",
        cc=["copy@example.com"],
        reply_to_message_id="msg-1",
    )

    assert draft["id"] == "draft-1"
    assert called["name"] == "create_draft"
    assert called["arguments"]["to"] == ["user@example.com"]
    assert called["arguments"]["replyToMessageId"] == "msg-1"

    with pytest.raises(email_service.EmailValidationError):
        email_service.create_draft(to=[], subject="Nope")


def test_create_draft_with_attachment_uses_gmail_api(monkeypatch):
    calls = {}

    def fake_get_source_attachment(source_id):
        calls["source_id"] = source_id
        return {
            "filename": "memo.txt",
            "content": b"hello",
            "mime_type": "text/plain",
        }

    def fake_create_draft(**kwargs):
        calls["draft"] = kwargs
        return {"id": "draft-api"}

    monkeypatch.setattr(email_service.knowledge_service, "get_source_attachment", fake_get_source_attachment)
    monkeypatch.setattr(email_service.gmail_api_client, "create_draft", fake_create_draft)
    monkeypatch.setattr(
        email_service.gmail_mcp_client,
        "call_tool",
        lambda name, arguments: (_ for _ in ()).throw(AssertionError("MCP should not handle attachments")),
    )

    draft = email_service.create_draft(
        to=["user@example.com"],
        subject="Attached",
        body="See attached.",
        attachment_source_ids=["file-1"],
    )

    assert draft["id"] == "draft-api"
    assert calls["source_id"] == "file-1"
    assert calls["draft"]["attachments"][0]["filename"] == "memo.txt"


def test_send_email_requires_confirmation():
    with pytest.raises(email_service.EmailValidationError):
        email_service.send_email(to=["user@example.com"], subject="Hi", user_confirmed=False)


def test_send_email_with_attachment_uses_gmail_api_when_confirmed(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        email_service.knowledge_service,
        "get_source_attachment",
        lambda source_id: {
            "filename": "memo.txt",
            "content": b"hello",
            "mime_type": "text/plain",
        },
    )
    def fake_send_email(**kwargs):
        calls["send"] = kwargs
        return {"id": "sent-1"}

    monkeypatch.setattr(email_service.gmail_api_client, "send_email", fake_send_email)

    result = email_service.send_email(
        to=["user@example.com"],
        subject="Attached",
        body="See attached.",
        attachment_source_ids=["file-1"],
        user_confirmed=True,
    )

    assert result["id"] == "sent-1"
    assert calls["send"]["attachments"][0]["filename"] == "memo.txt"


def test_send_draft_requires_confirmation_and_sends_when_confirmed(monkeypatch):
    with pytest.raises(email_service.EmailValidationError):
        email_service.send_draft("draft-1", user_confirmed=False)

    monkeypatch.setattr(email_service.gmail_api_client, "send_draft", lambda draft_id: {"id": "sent-draft", "draft": draft_id})

    result = email_service.send_draft("draft-1", user_confirmed=True)

    assert result == {"id": "sent-draft", "draft": "draft-1"}


def test_label_mutations_validate_input(monkeypatch):
    calls = []
    monkeypatch.setattr(
        email_service.gmail_mcp_client,
        "call_tool",
        lambda name, arguments: calls.append((name, arguments)) or {},
    )

    email_service.apply_labels_to_thread("thread-1", ["Label_1"])
    email_service.remove_labels_from_message("msg-1", ["Label_1"])

    assert calls[0] == ("label_thread", {"threadId": "thread-1", "labelIds": ["Label_1"]})
    assert calls[1] == ("unlabel_message", {"messageId": "msg-1", "labelIds": ["Label_1"]})

    with pytest.raises(email_service.EmailValidationError):
        email_service.apply_labels_to_thread("thread-1", [])
