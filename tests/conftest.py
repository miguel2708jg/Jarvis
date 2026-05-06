"""Test-wide storage defaults."""

import pytest


@pytest.fixture(autouse=True)
def disable_external_database_by_default(monkeypatch):
    """Keep tests from connecting to a real DATABASE_URL in the local .env."""
    from backend.config import settings

    monkeypatch.setattr(settings, "database_url", None, raising=False)
