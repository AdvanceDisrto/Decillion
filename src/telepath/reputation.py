"""Local peer-transfer observations used for routing hints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PeerRecord:
    successful: int = 0
    denied: int = 0
    failed: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    average_latency_ms: float = 0.0

    def score(self) -> float:
        total = self.successful + self.denied + self.failed
        return (
            0.5
            if total == 0
            else max(0.0, (self.successful - 0.5 * self.denied - self.failed) / total)
        )


class Reputation:
    def __init__(self):
        self.peers: dict[str, PeerRecord] = {}

    def record(
        self, peer: str, outcome: str, size: int = 0, latency_ms: float = 0.0, inbound: bool = True
    ) -> None:
        row = self.peers.setdefault(peer, PeerRecord())
        if outcome == "success":
            row.successful += 1
            row.bytes_in += size if inbound else 0
            row.bytes_out += 0 if inbound else size
            row.average_latency_ms += (latency_ms - row.average_latency_ms) / row.successful
        elif outcome == "denied":
            row.denied += 1
        else:
            row.failed += 1

    def summary(self) -> list[dict]:
        return [
            {"pub": key[:8], "score": round(row.score(), 3), **row.__dict__}
            for key, row in sorted(
                self.peers.items(), key=lambda item: item[1].score(), reverse=True
            )
        ]
