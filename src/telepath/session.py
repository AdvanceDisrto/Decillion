"""Peer-bound, model-bound, budgeted shard sessions."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str
    peer_pub: str
    model_id: str
    purpose: str
    budget_shards: int
    used_shards: int = 0
    opened_at: float = field(default_factory=time.time)
    ttl_s: float = 600.0

    def consume(self) -> bool:
        if time.time() > self.opened_at + self.ttl_s or self.used_shards >= self.budget_shards:
            return False
        self.used_shards += 1
        return True


class SessionRegistry:
    def __init__(self, max_sessions: int = 256):
        self.max_sessions = max_sessions
        self.sessions: dict[str, Session] = {}

    def open(
        self, peer_pub: str, model_id: str, purpose: str, budget: int, ttl_s: float
    ) -> Session:
        self._gc()
        if not 1 <= budget <= 1_000_000 or not 1 <= ttl_s <= 86_400:
            raise ValueError("session budget or TTL out of bounds")
        if len(self.sessions) >= self.max_sessions:
            oldest = min(self.sessions.values(), key=lambda item: item.opened_at)
            self.sessions.pop(oldest.session_id)
        session = Session(uuid.uuid4().hex, peer_pub, model_id, purpose, budget, ttl_s=ttl_s)
        self.sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        self._gc()
        return self.sessions.get(session_id)

    def _gc(self) -> None:
        now = time.time()
        for key in [
            key for key, value in self.sessions.items() if now > value.opened_at + value.ttl_s
        ]:
            self.sessions.pop(key, None)

    def summary(self) -> dict:
        self._gc()
        return {
            "open": len(self.sessions),
            "used_shards": sum(s.used_shards for s in self.sessions.values()),
        }
