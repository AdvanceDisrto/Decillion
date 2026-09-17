"""Hot/warm/cold/ice classification for observed shards."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum


class Tier(StrEnum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    ICE = "ice"


@dataclass
class TierEntry:
    key: str
    size_bytes: int
    location: str
    last_access: float = field(default_factory=time.time)
    tier: Tier = Tier.HOT


class TierRegistry:
    def __init__(self):
        self.entries: dict[str, TierEntry] = {}

    def touch(self, key: str, size_bytes: int, location: str) -> None:
        self.entries[key] = TierEntry(key, size_bytes, location)

    def reclassify(self, now: float | None = None) -> list[tuple[str, Tier, Tier]]:
        current = time.time() if now is None else now
        moves = []
        for entry in self.entries.values():
            age = current - entry.last_access
            tier = (
                Tier.HOT
                if age < 60
                else Tier.WARM
                if age < 3600
                else Tier.COLD
                if age < 604800
                else Tier.ICE
            )
            if tier != entry.tier:
                moves.append((entry.key, entry.tier, tier))
                entry.tier = tier
        return moves

    def summary(self) -> dict:
        return {
            tier.value: sum(
                entry.size_bytes for entry in self.entries.values() if entry.tier == tier
            )
            for tier in Tier
        }
