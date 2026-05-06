"""SQLite storage backend for notes and todos."""
import sqlite3
from pathlib import Path
from typing import Any, Optional

from backend.config import settings


class SQLiteStore:
    """Generic SQLite store for CRUD operations."""

    def __init__(self, table_name: str, schema: str):
        """
        Initialize SQLite store.

        Args:
            table_name: Name of the table to use.
            schema: SQL schema for creating the table (CREATE TABLE IF NOT EXISTS ...).
        """
        self.table_name = table_name
        self.db_path = (
            Path(settings.database_path)
            if settings.database_path
            else Path(settings.data_dir) / "jarvis.db"
        )
        self._init_db(schema)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self, schema: str) -> None:
        """Initialize the database with the provided schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(schema)
            conn.commit()

    def set(self, key: str, data: dict[str, Any]) -> None:
        """
        Insert or update a record by ID.

        Args:
            key: The record ID.
            data: Dictionary of column values.
        """
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        update_placeholders = ", ".join([f"{col} = ?" for col in columns])

        with self._get_connection() as conn:
            # Try update first
            values = list(data.values()) + [key]
            cursor = conn.execute(
                f"UPDATE {self.table_name} SET {update_placeholders} WHERE id = ?",
                values,
            )
            if cursor.rowcount == 0:
                # If no rows updated, insert
                cols = ", ".join(columns)
                conn.execute(
                    f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders})",
                    list(data.values()),
                )

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """
        Get a record by ID.

        Args:
            key: The record ID.

        Returns:
            Dictionary of column values or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?", (key,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def all(self) -> list[dict[str, Any]]:
        """
        Get all records.

        Returns:
            List of dictionaries containing all records.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {self.table_name}")
            return [dict(row) for row in cursor.fetchall()]

    def delete(self, key: str) -> bool:
        """
        Delete a record by ID.

        Args:
            key: The record ID.

        Returns:
            True if deleted, False otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?", (key,)
            )
            return cursor.rowcount > 0

    def delete_where(self, where_clause: str, params: tuple = ()) -> int:
        """Delete records matching a custom WHERE clause."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE {where_clause}", params
            )
            conn.commit()
            return cursor.rowcount

    def query(self, where_clause: str, params: tuple = ()) -> list[dict[str, Any]]:
        """
        Query records with a custom WHERE clause.

        Args:
            where_clause: SQL WHERE clause (without WHERE keyword).
            params: Parameters for the query.

        Returns:
            List of matching records.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE {where_clause}", params
            )
            return [dict(row) for row in cursor.fetchall()]
