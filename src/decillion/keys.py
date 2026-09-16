"""Envelope-encryption key providers."""

from __future__ import annotations

import base64
import os
from abc import ABC, abstractmethod

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import AttestationError


class KeyProvider(ABC):
    @abstractmethod
    def wrap(self, data_key: bytes, context: bytes) -> bytes: ...

    @abstractmethod
    def unwrap(
        self, wrapped_key: bytes, context: bytes, attestation: str | None = None
    ) -> bytes: ...


class LocalKeyProvider(KeyProvider):
    """AES-GCM envelope provider backed by a 256-bit environment key."""

    def __init__(self, master_key: bytes, require_attestation: bool = False):
        if len(master_key) != 32:
            raise ValueError("master key must be exactly 32 bytes")
        self._master_key = master_key
        self.require_attestation = require_attestation

    @classmethod
    def from_env(cls) -> LocalKeyProvider:
        encoded = os.getenv("DECILLION_MASTER_KEY")
        if not encoded:
            raise RuntimeError("DECILLION_MASTER_KEY is required")
        try:
            key = base64.urlsafe_b64decode(encoded.encode("ascii"))
        except Exception as exc:
            raise ValueError("DECILLION_MASTER_KEY must be URL-safe base64") from exc
        require = os.getenv("DECILLION_REQUIRE_ATTESTATION", "false").lower() == "true"
        return cls(key, require_attestation=require)

    def wrap(self, data_key: bytes, context: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + AESGCM(self._master_key).encrypt(nonce, data_key, context)

    def unwrap(self, wrapped_key: bytes, context: bytes, attestation: str | None = None) -> bytes:
        if self.require_attestation and not attestation:
            raise AttestationError("valid attestation is required before key release")
        if len(wrapped_key) < 29:
            raise ValueError("wrapped key is truncated")
        return AESGCM(self._master_key).decrypt(wrapped_key[:12], wrapped_key[12:], context)


def generate_master_key() -> str:
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")
