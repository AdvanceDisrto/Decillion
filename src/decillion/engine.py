"""Encrypted storage orchestration."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .errors import AuthorizationError, IntegrityError
from .keys import KeyProvider
from .objects import ObjectStore
from .receipts import Receipt, ReceiptSigner, verify_receipt

MAGIC = b"DECILLION\x01"


@dataclass(frozen=True)
class StoredObject:
    receipt: Receipt


class SovereignStorage:
    def __init__(self, store: ObjectStore, keys: KeyProvider, signer: ReceiptSigner):
        self.store = store
        self.keys = keys
        self.signer = signer

    @staticmethod
    def _context(owner: str, filename: str) -> bytes:
        return (
            b"decillion:v1\x00"
            + owner.encode()
            + b"\x00"
            + hashlib.sha256(filename.encode()).digest()
        )

    def upload(self, owner: str, filename: str, plaintext: bytes) -> StoredObject:
        if not owner or len(owner) > 512:
            raise ValueError("owner is required and must be at most 512 characters")
        if not filename or len(filename) > 1024:
            raise ValueError("filename is required and must be at most 1024 characters")
        context = self._context(owner, filename)
        data_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        ciphertext = AESGCM(data_key).encrypt(nonce, plaintext, context)
        payload = MAGIC + nonce + ciphertext
        object_id = hashlib.sha256(payload).hexdigest()
        wrapped = self.keys.wrap(data_key, context)
        self.store.put(object_id, payload)
        receipt = Receipt.create(
            object_id=object_id,
            owner=owner,
            filename=filename,
            plaintext_size=len(plaintext),
            ciphertext_size=len(payload),
            wrapped_key=wrapped,
        )
        return StoredObject(self.signer.sign(receipt))

    def download(
        self,
        receipt: Receipt,
        *,
        owner: str,
        filename: str,
        attestation: str | None = None,
    ) -> bytes:
        verify_receipt(receipt, self.signer.public_key)
        if receipt.owner != owner:
            raise AuthorizationError("receipt owner does not match caller")
        expected_name_hash = hashlib.sha256(filename.encode()).hexdigest()
        if receipt.original_name_hash != expected_name_hash:
            raise AuthorizationError("filename binding does not match receipt")
        payload = self.store.get(receipt.object_id)
        if hashlib.sha256(payload).hexdigest() != receipt.object_id:
            raise IntegrityError("stored ciphertext digest does not match receipt")
        if not payload.startswith(MAGIC) or len(payload) < len(MAGIC) + 28:
            raise IntegrityError("invalid encrypted-object envelope")
        context = self._context(owner, filename)
        wrapped = base64.urlsafe_b64decode(receipt.wrapped_key)
        data_key = self.keys.unwrap(wrapped, context, attestation)
        offset = len(MAGIC)
        try:
            return AESGCM(data_key).decrypt(
                payload[offset : offset + 12], payload[offset + 12 :], context
            )
        except InvalidTag as exc:
            raise IntegrityError("ciphertext authentication failed") from exc
