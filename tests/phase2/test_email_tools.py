"""Phase 2: Email tool tests.

These tests require real Gmail credentials and are skipped by default.
Run: pytest tests/phase2/test_email_tools.py -m requires_credentials -v
"""
import pytest


@pytest.mark.requires_credentials
def test_list_emails():
    from backend.tools.email import list_emails
    emails = list_emails.invoke({"max_results": 5})
    assert isinstance(emails, list)
    for email in emails:
        assert "message_id" in email
        assert "subject" in email


@pytest.mark.requires_credentials
def test_search_emails():
    from backend.tools.email import search_emails
    results = search_emails.invoke({"query": "is:unread", "max_results": 3})
    assert isinstance(results, list)


@pytest.mark.requires_credentials
def test_get_email():
    from backend.tools.email import list_emails, get_email
    emails = list_emails.invoke({"max_results": 1})
    if not emails:
        pytest.skip("No emails in inbox")
    msg = get_email.invoke({"message_id": emails[0]["message_id"]})
    assert "body" in msg
    assert "sender" in msg
