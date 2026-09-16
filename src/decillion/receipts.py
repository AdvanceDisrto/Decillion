"""Canonical signed receipts and Merkle aggregation."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat


def canonical_json(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


@dataclass(frozen=True)
class Receipt:
    version: int
    object_id: str
    owner: str
    original_name_hash: str
    plaintext_size: int
    ciphertext_size: int
    created_at: str
    wrapped_key: str
    signature: str = ""

    def unsigned(self) -> dict:
        value = asdict(self)
        value.pop("signature")
        return value

    def digest(self) -> bytes:
        return hashlib.sha256(canonical_json(self.unsigned())).digest()

    @classmethod
    def create(
        cls,
        *,
        object_id: str,
        owner: str,
        filename: str,
        plaintext_size: int,
        ciphertext_size: int,
        wrapped_key: bytes,
    ) -> Receipt:
        return cls(
            version=1,
            object_id=object_id,
            owner=owner,
            original_name_hash=hashlib.sha256(filename.encode()).hexdigest(),
            plaintext_size=plaintext_size,
            ciphertext_size=ciphertext_size,
            created_at=datetime.now(UTC).isoformat(),
            wrapped_key=base64.urlsafe_b64encode(wrapped_key).decode(),
        )


class ReceiptSigner:
    def __init__(self, private_key: Ed25519PrivateKey):
        self.private_key = private_key

    @classmethod
    def generate(cls) -> ReceiptSigner:
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def load_or_create(cls, path: str | Path) -> ReceiptSigner:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if target.exists():
            return cls(Ed25519PrivateKey.from_private_bytes(target.read_bytes()))
        private_key = Ed25519PrivateKey.generate()
        encoded = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        fd, temp_name = tempfile.mkstemp(prefix=".signing-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            try:
                os.link(temp_name, target)
            except FileExistsError:
                return cls(Ed25519PrivateKey.from_private_bytes(target.read_bytes()))
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return cls(private_key)

    def sign(self, receipt: Receipt) -> Receipt:
        signature = base64.urlsafe_b64encode(self.private_key.sign(receipt.digest())).decode()
        return Receipt(**receipt.unsigned(), signature=signature)

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()


def verify_receipt(receipt: Receipt, public_key: Ed25519PublicKey) -> None:
    public_key.verify(base64.urlsafe_b64decode(receipt.signature), receipt.digest())


def merkle_root(receipts: Iterable[Receipt]) -> str:
    leaves = [hashlib.sha256(canonical_json(asdict(item))).digest() for item in receipts]
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    while len(leaves) > 1:
        if len(leaves) % 2:
            leaves.append(leaves[-1])
        leaves = [
            hashlib.sha256(leaves[i] + leaves[i + 1]).digest() for i in range(0, len(leaves), 2)
        ]
    return leaves[0].hex()
