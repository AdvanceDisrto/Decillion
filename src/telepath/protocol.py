"""Signed Telepath message wire format."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

HELLO = "HELLO"
SESSION_OPEN = "SESSION_OPEN"
SESSION_ACCEPT = "SESSION_ACCEPT"
SESSION_DENY = "SESSION_DENY"
REQUEST_SHARD = "REQUEST_SHARD"
SHARD_DATA = "SHARD_DATA"
SHARD_DENY = "SHARD_DENY"
RAM_BROADCAST = "RAM_BROADCAST"
ACK = "ACK"
ERROR = "ERROR"


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass
class Message:
    type: str
    sender: str
    nonce: str
    ts: float
    payload: dict
    signature: str = ""

    def unsigned(self) -> dict:
        return {
            "type": self.type,
            "sender": self.sender,
            "nonce": self.nonce,
            "ts": self.ts,
            "payload": self.payload,
        }

    def sign(self, key: Ed25519PrivateKey) -> Message:
        self.signature = key.sign(canonical(self.unsigned())).hex()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> Message:
        return cls(
            type=value["type"],
            sender=value["sender"],
            nonce=value["nonce"],
            ts=float(value["ts"]),
            payload=value["payload"],
            signature=value.get("signature", ""),
        )


def make(kind: str, key: Ed25519PrivateKey, payload: dict | None = None) -> Message:
    return Message(
        type=kind,
        sender=key.public_key().public_bytes_raw().hex(),
        nonce=uuid.uuid4().hex,
        ts=time.time(),
        payload=payload or {},
    ).sign(key)


def verify(message: Message, max_skew_s: float = 300.0) -> tuple[bool, str]:
    if abs(time.time() - message.ts) > max_skew_s:
        return False, "timestamp out of window"
    if len(message.nonce) < 16:
        return False, "invalid nonce"
    try:
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(message.sender))
        public.verify(bytes.fromhex(message.signature), canonical(message.unsigned()))
    except (InvalidSignature, ValueError, KeyError, TypeError):
        return False, "bad signature"
    return True, "ok"
