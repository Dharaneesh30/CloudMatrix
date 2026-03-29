from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass
class HashNode:
    key: str
    value: Any


class HashTable:
    """
    Hash table with chaining collision handling.
    Suitable for fast task-id lookups in API hot paths.
    """

    def __init__(self, capacity: int = 2048) -> None:
        self.capacity = max(16, capacity)
        self.buckets: List[List[HashNode]] = [[] for _ in range(self.capacity)]
        self.size = 0

    def _index(self, key: str) -> int:
        return hash(key) % self.capacity

    def _needs_resize(self) -> bool:
        return (self.size / self.capacity) > 0.75

    def _resize(self) -> None:
        old_items = list(self.items())
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        self.size = 0
        for key, value in old_items:
            self.put(key, value)

    def put(self, key: str, value: Any) -> None:
        index = self._index(key)
        chain = self.buckets[index]

        for node in chain:
            if node.key == key:
                node.value = value
                return

        chain.append(HashNode(key=key, value=value))
        self.size += 1

        if self._needs_resize():
            self._resize()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        index = self._index(key)
        for node in self.buckets[index]:
            if node.key == key:
                return node.value
        return default

    def delete(self, key: str) -> bool:
        index = self._index(key)
        chain = self.buckets[index]
        for i, node in enumerate(chain):
            if node.key == key:
                del chain[i]
                self.size -= 1
                return True
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def items(self) -> List[Tuple[str, Any]]:
        result: List[Tuple[str, Any]] = []
        for chain in self.buckets:
            for node in chain:
                result.append((node.key, node.value))
        return result
