"""Simple JSON file-based persistence layer."""
import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

from backend.config import settings


class JsonStore:
    """Thread-safe key-value store backed by a JSON file per collection."""

    def __init__(self, collection: str, data_dir: str | None = None):
        self._dir = Path(data_dir or settings.data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"{collection}.json"
        self._lock = Lock()
        if not self._path.exists():
            self._path.write_text("{}")

    def _read(self) -> dict[str, Any]:
        return json.loads(self._path.read_text())

    def _write(self, data: dict[str, Any]) -> None:
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._read().get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def delete(self, key: str) -> bool:
        with self._lock:
            data = self._read()
            if key not in data:
                return False
            del data[key]
            self._write(data)
            return True

    def all(self) -> list[Any]:
        with self._lock:
            return list(self._read().values())

    def clear(self) -> None:
        with self._lock:
            self._write({})
