"""PostgreSQL storage backend for Neon and compatible providers."""
from __future__ import annotations

import re
from typing import Any, Callable, Optional

from backend.config import settings

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str) -> str:
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return value


def _postgres_placeholders(sql: str) -> str:
    """Convert the local SQLite-style placeholder convention to psycopg."""
    return sql.replace("?", "%s")


class PostgresStore:
    """Generic PostgreSQL store for CRUD operations."""

    def __init__(
        self,
        table_name: str,
        schema: str,
        database_url: str | None = None,
        connect: Callable[..., Any] | None = None,
    ):
        self.table_name = _validate_identifier(table_name)
        self.database_url = database_url or settings.database_url
        if not self.database_url:
            raise ValueError("DATABASE_URL is required for PostgresStore")
        self._connect = connect
        self._connection = None
        self._schema = schema
        self._initialized = False

    def _get_connection(self):
        if self._connection is not None and not getattr(self._connection, "closed", False):
            return self._connection

        if self._connect is not None:
            self._connection = self._connect(self.database_url)
            return self._connection

        import psycopg
        from psycopg.rows import dict_row

        self._connection = psycopg.connect(
            self.database_url,
            row_factory=dict_row,
            connect_timeout=15,
        )
        return self._connection

    @staticmethod
    def _is_connection_error(exc: Exception) -> bool:
        import psycopg

        return isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError))

    def _reset_connection(self) -> None:
        conn = self._connection
        self._connection = None
        close = getattr(conn, "close", None)
        if close is None:
            return
        try:
            close()
        except Exception:
            pass

    def _run_with_reconnect(self, operation: Callable[[Any], Any]) -> Any:
        for attempt in range(2):
            try:
                conn = self._get_connection()
                return operation(conn)
            except Exception as exc:
                if attempt == 0 and self._is_connection_error(exc):
                    self._reset_connection()
                    continue
                raise
        raise RuntimeError("Postgres operation retry exhausted")

    def _commit(self, conn) -> None:
        commit = getattr(conn, "commit", None)
        if commit is not None:
            commit()

    def _ensure_initialized(self, conn) -> None:
        if self._initialized:
            return
        conn.execute(self._schema)
        self._commit(conn)
        self._initialized = True

    def set(self, key: str, data: dict[str, Any]) -> None:
        _ = key
        columns = list(data.keys())
        for column in columns:
            _validate_identifier(column)

        cols = ", ".join(columns)
        placeholders = ", ".join(["%s" for _ in columns])
        updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != "id"])
        if not updates:
            updates = "id = EXCLUDED.id"

        sql = (
            f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT (id) DO UPDATE SET {updates}"
        )

        def operation(conn):
            self._ensure_initialized(conn)
            conn.execute(sql, list(data.values()))
            self._commit(conn)

        self._run_with_reconnect(operation)

    def get(self, key: str) -> Optional[dict[str, Any]]:
        def operation(conn):
            self._ensure_initialized(conn)
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = %s", (key,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

        return self._run_with_reconnect(operation)

    def all(self) -> list[dict[str, Any]]:
        def operation(conn):
            self._ensure_initialized(conn)
            cursor = conn.execute(f"SELECT * FROM {self.table_name}")
            return [dict(row) for row in cursor.fetchall()]

        return self._run_with_reconnect(operation)

    def delete(self, key: str) -> bool:
        def operation(conn):
            self._ensure_initialized(conn)
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = %s", (key,)
            )
            self._commit(conn)
            return cursor.rowcount > 0

        return self._run_with_reconnect(operation)

    def delete_where(self, where_clause: str, params: tuple = ()) -> int:
        def operation(conn):
            self._ensure_initialized(conn)
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE {_postgres_placeholders(where_clause)}",
                params,
            )
            self._commit(conn)
            return cursor.rowcount

        return self._run_with_reconnect(operation)

    def query(self, where_clause: str, params: tuple = ()) -> list[dict[str, Any]]:
        def operation(conn):
            self._ensure_initialized(conn)
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {_postgres_placeholders(where_clause)}",
                params,
            )
            return [dict(row) for row in cursor.fetchall()]

        return self._run_with_reconnect(operation)
