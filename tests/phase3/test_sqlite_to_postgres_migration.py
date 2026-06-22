"""SQLite to PostgreSQL migration behavior without a real PostgreSQL server."""

import sqlite3


class FakeCursor:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class FakePostgresConnection:
    def __init__(self):
        self.rows = {}
        self.schemas = []

    def execute(self, sql, params=None):
        sql = sql.strip()
        if sql.startswith("CREATE TABLE"):
            self.schemas.append(sql)
            return FakeCursor({"count": 0})

        if sql.startswith("INSERT INTO"):
            table = sql.split()[2]
            self.rows.setdefault(table, {})
            self.rows[table][params[0]] = tuple(params)
            return FakeCursor({"count": len(self.rows[table])})

        if sql.startswith("SELECT COUNT(*) AS count FROM"):
            table = sql.split()[-1]
            return FakeCursor({"count": len(self.rows.get(table, {}))})

        raise AssertionError(f"Unexpected SQL: {sql}")


def test_migrate_table_upserts_rows_idempotently(tmp_path):
    from scripts.migrate_sqlite_to_postgres import migrate_table

    db_path = tmp_path / "jarvis.db"
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute(
        """
        CREATE TABLE todos (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'medium',
            due_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    sqlite_conn.execute(
        "INSERT INTO todos (id, text, completed, priority, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("todo-1", "Ship migration", 0, "high", None, "2026-04-29T00:00:00+00:00"),
    )
    sqlite_conn.commit()

    pg_conn = FakePostgresConnection()

    first = migrate_table(sqlite_conn, pg_conn, "todos")
    second = migrate_table(sqlite_conn, pg_conn, "todos")

    assert first == {"source": 1, "migrated": 1, "destination": 1}
    assert second == {"source": 1, "migrated": 1, "destination": 1}
    assert len(pg_conn.rows["todos"]) == 1


def test_migrate_knowledge_pages_table(tmp_path):
    from scripts.migrate_sqlite_to_postgres import migrate_table
    from backend.storage.schemas import KNOWLEDGE_PAGES_SCHEMA

    db_path = tmp_path / "jarvis.db"
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute(KNOWLEDGE_PAGES_SCHEMA)
    sqlite_conn.execute(
        """
        INSERT INTO knowledge_pages (
            id, path, type, title, summary, body, updated_at,
            source_ids, tags, aliases, metadata, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "concepts/db-brain.md",
            "concepts/db-brain.md",
            "concept",
            "DB Brain",
            "Structured wiki page",
            "Body",
            "2026-04-15T00:00:00+00:00",
            "[]",
            '["db"]',
            "[]",
            "{}",
            "2026-04-15T00:00:00+00:00",
        ),
    )
    sqlite_conn.commit()

    pg_conn = FakePostgresConnection()

    result = migrate_table(sqlite_conn, pg_conn, "knowledge_pages")

    assert result == {"source": 1, "migrated": 1, "destination": 1}
    assert len(pg_conn.rows["knowledge_pages"]) == 1
