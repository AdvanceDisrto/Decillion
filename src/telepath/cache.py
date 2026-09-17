"""Size-bounded LRU plaintext shard cache."""

from __future__ import annotations

from collections import OrderedDict


class ShardCache:
    def __init__(self, max_entries: int = 512, max_bytes: int = 64 * 1024 * 1024):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.entries: OrderedDict[tuple, bytes] = OrderedDict()
        self.bytes_used = 0
        self.hits = self.misses = self.evictions = 0

    def get(self, key: tuple) -> bytes | None:
        value = self.entries.get(key)
        if value is None:
            self.misses += 1
            return None
        self.entries.move_to_end(key)
        self.hits += 1
        return value

    def put(self, key: tuple, value: bytes) -> None:
        if len(value) > self.max_bytes:
            return
        previous = self.entries.pop(key, None)
        if previous is not None:
            self.bytes_used -= len(previous)
        self.entries[key] = value
        self.bytes_used += len(value)
        while len(self.entries) > self.max_entries or self.bytes_used > self.max_bytes:
            _, evicted = self.entries.popitem(last=False)
            self.bytes_used -= len(evicted)
            self.evictions += 1

    def summary(self) -> dict:
        total = self.hits + self.misses
        return {
            "entries": len(self.entries),
            "bytes_used": self.bytes_used,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": self.hits / total if total else 0.0,
        }
