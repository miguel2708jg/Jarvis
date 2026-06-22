"""Storage backend selection."""
from __future__ import annotations

from backend.config import settings
from backend.storage.postgres_store import PostgresStore
from backend.storage.sqlite_store import SQLiteStore


def should_use_postgres(database_url: str | None = None) -> bool:
    url = database_url if database_url is not None else settings.database_url
    if not url:
        return False
    return url.startswith(("postgresql://", "postgres://"))


def create_store(table_name: str, schema: str):
    if should_use_postgres():
        return PostgresStore(table_name, schema)
    if not settings.allow_sqlite_fallback:
        raise RuntimeError(
            "DATABASE_URL is required for Jarvis runtime storage. "
            "Set ALLOW_SQLITE_FALLBACK=true only for tests, local recovery, or manual SQLite backup work."
        )
    return SQLiteStore(table_name, schema)
