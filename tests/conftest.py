"""Test-wide storage defaults."""

import pytest


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m"):
        return
    skip_credentials = pytest.mark.skip(reason="requires real Google OAuth credentials")
    for item in items:
        if "requires_credentials" in item.keywords:
            item.add_marker(skip_credentials)


@pytest.fixture(autouse=True)
def disable_external_database_by_default(monkeypatch):
    """Keep tests from connecting to a real DATABASE_URL in the local .env."""
    from backend.config import settings

    monkeypatch.setattr(settings, "database_url", None, raising=False)
    monkeypatch.setattr(settings, "allow_sqlite_fallback", True, raising=False)
