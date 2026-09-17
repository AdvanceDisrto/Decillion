"""Ed25519 access requests, replay protection, ACLs, and Merkle helpers."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class AccessRequest:
    requester_pubkey: str
    model_id: str
    purpose: str
    nonce: str
    timestamp: float
    signature: str

    def to_dict(self) -> dict:
        return asdict(self)

    def unsigned(self) -> dict:
        value = self.to_dict()
        value.pop("signature")
        return value


def sign_request(
    private_key: Ed25519PrivateKey,
    model_id: str,
    purpose: str,
    *,
    nonce: str | None = None,
    timestamp: float | None = None,
) -> AccessRequest:
    public = private_key.public_key().public_bytes_raw().hex()
    body = {
        "requester_pubkey": public,
        "model_id": model_id,
        "purpose": purpose,
        "nonce": nonce or uuid.uuid4().hex,
        "timestamp": timestamp if timestamp is not None else time.time(),
    }
    return AccessRequest(**body, signature=private_key.sign(canonical(body)).hex())


def verify_request(req: AccessRequest, max_skew_s: float = 300.0) -> tuple[bool, str]:
    if not req.model_id or not req.purpose or len(req.nonce) < 16:
        return False, "required field is missing or invalid"
    if abs(time.time() - req.timestamp) > max_skew_s:
        return False, "timestamp out of window"
    try:
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(req.requester_pubkey))
        public.verify(bytes.fromhex(req.signature), canonical(req.unsigned()))
    except (InvalidSignature, ValueError):
        return False, "bad signature"
    return True, "ok"


class NonceCache:
    """Bounded in-memory replay cache for signed requests."""

    def __init__(self, ttl_s: float = 600.0, max_entries: int = 100_000):
        self.ttl_s = ttl_s
        self.max_entries = max_entries
        self._seen: dict[tuple[str, str], float] = {}

    def accept(self, pubkey: str, nonce: str, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        if len(self._seen) >= self.max_entries:
            self._seen = {key: expiry for key, expiry in self._seen.items() if expiry > current}
            if len(self._seen) >= self.max_entries:
                return False
        key = (pubkey, nonce)
        if self._seen.get(key, 0) > current:
            return False
        self._seen[key] = current + self.ttl_s
        return True


class ACL:
    """Atomic allowlist per model ID; ``*`` applies to all models."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rules = json.loads(self.path.read_text()) if self.path.exists() else {}
        if not self.path.exists():
            self.save()

    def allow(self, model_id: str, pubkey_hex: str) -> None:
        if len(bytes.fromhex(pubkey_hex)) != 32:
            raise ValueError("Ed25519 public key must be 32 bytes")
        self.rules[model_id] = sorted(set([*self.rules.get(model_id, []), pubkey_hex]))
        self.save()

    def revoke(self, model_id: str, pubkey_hex: str) -> None:
        self.rules[model_id] = [key for key in self.rules.get(model_id, []) if key != pubkey_hex]
        self.save()

    def is_allowed(self, model_id: str, pubkey_hex: str) -> bool:
        return pubkey_hex in self.rules.get("*", []) or pubkey_hex in self.rules.get(model_id, [])

    def save(self) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.rules, indent=2, sort_keys=True) + "\n")
        temporary.replace(self.path)


def _hash(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return b"\x00" * 32
    current = list(leaves)
    while len(current) > 1:
        if len(current) % 2:
            current.append(current[-1])
        current = [_hash(current[i] + current[i + 1]) for i in range(0, len(current), 2)]
    return current[0]


def merkle_proof(leaves: list[bytes], index: int) -> list[tuple[bytes, str]]:
    if not 0 <= index < len(leaves):
        raise IndexError(index)
    proof: list[tuple[bytes, str]] = []
    current = list(leaves)
    cursor = index
    while len(current) > 1:
        if len(current) % 2:
            current.append(current[-1])
        sibling = cursor ^ 1
        proof.append((current[sibling], "right" if cursor % 2 == 0 else "left"))
        current = [_hash(current[i] + current[i + 1]) for i in range(0, len(current), 2)]
        cursor //= 2
    return proof


def verify_merkle(leaf: bytes, proof: list[tuple[bytes, str]], root: bytes) -> bool:
    current = leaf
    for sibling, side in proof:
        current = _hash(current + sibling) if side == "right" else _hash(sibling + current)
    return current == root
