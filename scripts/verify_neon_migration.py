"""Read-only verification that local SQLite rows are present in Neon/Postgres.

Usage:
    python scripts/verify_neon_migration.py --source Data/jarvis.db
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
from scripts.migrate_sqlite_to_postgres import TABLE_ORDER, _load_psycopg


def _sqlite_connect_readonly(source: Path) -> sqlite3.Connection:
    if not source.exists():
        raise FileNotFoundError(f"SQLite source not found: {source}")
    conn = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _postgres_table_exists(conn: Any, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        ) AS exists
        """,
        (table_name,),
    ).fetchone()
    return bool(row["exists"] if isinstance(row, dict) else row[0])


def _count(conn: Any, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"] if isinstance(row, dict) else row[0])


def _ids(conn: Any, table_name: str) -> set[str]:
    return {str(row["id"]) for row in conn.execute(f"SELECT id FROM {table_name}").fetchall()}


def verify(source: Path, database_url: str) -> int:
    psycopg, dict_row = _load_psycopg()
    failures = 0

    with _sqlite_connect_readonly(source) as sqlite_conn:
        with psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=15,
            options="-c default_transaction_read_only=on",
        ) as pg_conn:
            for table_name in TABLE_ORDER:
                sqlite_exists = _sqlite_table_exists(sqlite_conn, table_name)
                postgres_exists = _postgres_table_exists(pg_conn, table_name)

                if not postgres_exists:
                    print(f"{table_name}: FAIL neon_table_missing")
                    failures += 1
                    continue

                neon_count = _count(pg_conn, table_name)
                if not sqlite_exists:
                    print(f"{table_name}: OK sqlite_missing neon={neon_count}")
                    continue

                sqlite_count = _count(sqlite_conn, table_name)
                sqlite_ids = _ids(sqlite_conn, table_name)
                neon_ids = _ids(pg_conn, table_name)
                missing_in_neon = sorted(sqlite_ids - neon_ids)
                extra_in_neon = sorted(neon_ids - sqlite_ids)

                status = "OK" if not missing_in_neon else "FAIL"
                print(
                    f"{table_name}: {status} sqlite={sqlite_count} neon={neon_count} "
                    f"missing_in_neon={len(missing_in_neon)} extra_in_neon={len(extra_in_neon)}"
                )
                if missing_in_neon:
                    failures += 1
                    print(f"  missing_sample={', '.join(missing_in_neon[:5])}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SQLite rows are present in Neon/Postgres.")
    parser.add_argument("--source", default="Data/jarvis.db", help="SQLite source path.")
    parser.add_argument("--database-url", default=None, help="PostgreSQL/Neon connection URL.")
    args = parser.parse_args()

    database_url = args.database_url or settings.database_url
    if not database_url:
        raise SystemExit("DATABASE_URL is required. Set it in .env or pass --database-url.")

    failures = verify(Path(args.source), database_url)
    if failures:
        print(f"Verification failed: {failures} table(s) have missing Neon data.")
        return 1

    print("Verification passed: Neon contains all rows from the SQLite source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
