from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional

try:
    from .hash_table import HashTable
except ImportError:
    from core.hash_table import HashTable


class TaskCache:
    """Small in-memory cache for frequent task lookup by id."""

    def __init__(self, capacity: int = 4096) -> None:
        self._lock = Lock()
        self._table = HashTable(capacity=capacity)

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._table.get(task_id)

    def put(self, task_id: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._table.put(task_id, payload)

    def clear(self) -> None:
        with self._lock:
            self._table = HashTable(capacity=4096)


task_cache = TaskCache()
