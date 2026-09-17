"""Immutable schemas for encrypted model shards."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Shard:
    index: int
    plaintext_hash: str
    ciphertext_hash: str
    plaintext_bytes: int
    ciphertext_bytes: int
    nonce_hex: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ModelManifest:
    model_id: str
    source: str
    license: str
    size_bytes: int
    n_shards: int
    merkle_root: str
    key_id: str
    shards: list[Shard] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    format_version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> ModelManifest:
        data = json.loads(text)
        data["shards"] = [Shard(**shard) for shard in data.get("shards", [])]
        return cls(**data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ModelManifest:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))
