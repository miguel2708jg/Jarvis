"""Migrate Jarvis relational data from SQLite to PostgreSQL.

Usage:
    python scripts/migrate_sqlite_to_postgres.py --source Data/jarvis.db
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings
from backend.storage.schemas import TABLE_SCHEMAS

TABLE_ORDER = [
    "todos",
    "notes",
    "threads",
    "messages",
    "thread_memory",
    "calendar_events",
    "knowledge_pages",
    "knowledge_sources",
    "knowledge_links",
    "knowledge_log",
]


def _load_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise SystemExit(
            "psycopg is required. Install dependencies with `pip install -r requirements.txt`."
        ) from exc
    return psycopg, dict_row


def _sqlite_connect_readonly(source: Path) -> sqlite3.Connection:
    if not source.exists():
        raise FileNotFoundError(f"SQLite source not found: {source}")
    conn = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(sqlite_conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = sqlite_conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row["name"] for row in rows]


def _table_exists(sqlite_conn: sqlite3.Connection, table_name: str) -> bool:
    row = sqlite_conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _upsert_sql(table_name: str, columns: list[str]) -> str:
    cols = ", ".join(columns)
    placeholders = ", ".join(["%s" for _ in columns])
    updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "id"])
    if not updates:
        updates = "id = EXCLUDED.id"
    return (
        f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {updates}"
    )


def migrate_table(sqlite_conn: sqlite3.Connection, pg_conn: Any, table_name: str) -> dict[str, int]:
    pg_conn.execute(TABLE_SCHEMAS[table_name])

    if not _table_exists(sqlite_conn, table_name):
        return {"source": 0, "migrated": 0, "destination": _count_destination(pg_conn, table_name)}

    columns = _table_columns(sqlite_conn, table_name)
    if not columns:
        return {"source": 0, "migrated": 0, "destination": _count_destination(pg_conn, table_name)}

    rows = sqlite_conn.execute(f"SELECT * FROM {table_name}").fetchall()
    upsert = _upsert_sql(table_name, columns)
    migrated = 0
    for row in rows:
        pg_conn.execute(upsert, [row[column] for column in columns])
        migrated += 1

    return {
        "source": len(rows),
        "migrated": migrated,
        "destination": _count_destination(pg_conn, table_name),
    }


def _count_destination(pg_conn: Any, table_name: str) -> int:
    row = pg_conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    if isinstance(row, dict):
        return int(row["count"])
    return int(row[0])


def migrate(source: Path, database_url: str) -> dict[str, dict[str, int]]:
    psycopg, dict_row = _load_psycopg()
    results: dict[str, dict[str, int]] = {}
    with _sqlite_connect_readonly(source) as sqlite_conn:
        with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=15) as pg_conn:
            for table_name in TABLE_ORDER:
                with pg_conn.transaction():
                    results[table_name] = migrate_table(sqlite_conn, pg_conn, table_name)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate Jarvis SQLite data to PostgreSQL.")
    parser.add_argument("--source", default="Data/jarvis.db", help="SQLite database path.")
    parser.add_argument("--database-url", default=None, help="PostgreSQL connection URL.")
    args = parser.parse_args()

    database_url = args.database_url or settings.database_url
    if not database_url:
        raise SystemExit("DATABASE_URL is required. Set it in .env or pass --database-url.")

    results = migrate(Path(args.source), database_url)
    for table_name, counts in results.items():
        print(
            f"{table_name}: source={counts['source']} "
            f"migrated={counts['migrated']} destination={counts['destination']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
