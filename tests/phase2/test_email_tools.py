"""Phase 2: Gmail MCP tool tests.

These tests require real Gmail credentials and are skipped by default.
Run: pytest tests/phase2/test_email_tools.py -m requires_credentials -v
"""
import pytest


@pytest.mark.requires_credentials
def test_list_emails():
    from backend.tools.email import search_email_threads
    emails = search_email_threads.invoke({"query": "in:inbox", "max_results": 5})
    assert isinstance(emails, list)
    for email in emails:
        assert "message_id" in email
        assert "thread_id" in email
        assert "subject" in email


@pytest.mark.requires_credentials
def test_search_emails():
    from backend.tools.email import search_email_threads
    results = search_email_threads.invoke({"query": "is:unread", "max_results": 3})
    assert isinstance(results, list)


@pytest.mark.requires_credentials
def test_get_email():
    from backend.tools.email import search_email_threads, get_email_thread
    emails = search_email_threads.invoke({"query": "in:inbox", "max_results": 1})
    if not emails:
        pytest.skip("No emails in inbox")
    thread = get_email_thread.invoke({"thread_id": emails[0]["thread_id"]})
    assert "messages" in thread
