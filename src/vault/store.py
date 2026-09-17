"""Encrypted, content-addressed, sharded model store for an external drive."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .access import canonical, merkle_root
from .manifest import ModelManifest, Shard

SHARD_SIZE = 1024 * 1024
ALLOWED_SUFFIXES = {".bin", ".pt", ".safetensors"}


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class VaultStore:
    """A vault whose ciphertext, manifests, keys, and receipts live under ``root``."""

    def __init__(self, root: str | Path, shard_size: int = SHARD_SIZE):
        if shard_size <= 0:
            raise ValueError("shard_size must be positive")
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.shard_dir = self.root / "shards"
        self.manifest_dir = self.root / "manifests"
        self.keys_dir = self.root / "keys"
        for directory in (self.shard_dir, self.manifest_dir, self.keys_dir):
            directory.mkdir(exist_ok=True, mode=0o700)
        self.shard_size = shard_size
        self.config_path = self.root / "vault.json"
        self._ensure_config()

    def _ensure_config(self) -> None:
        if self.config_path.exists():
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
            if config.get("format_version") != 1 or len(bytes.fromhex(config["kdf_salt"])) != 16:
                raise RuntimeError("unsupported or corrupt vault configuration")
            return
        config = {
            "format_version": 1,
            "vault_id": str(uuid.uuid4()),
            "kdf": "scrypt-n32768-r8-p1",
            "kdf_salt": os.urandom(16).hex(),
            "shard_size": self.shard_size,
        }
        self._atomic_bytes(self.config_path, json.dumps(config, indent=2).encode() + b"\n")

    @staticmethod
    def _atomic_bytes(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _master_key(self) -> bytes:
        passphrase = os.environ.get("IZETTA_VAULT_PASSPHRASE")
        if not passphrase:
            raise RuntimeError("set IZETTA_VAULT_PASSPHRASE")
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        return Scrypt(salt=bytes.fromhex(config["kdf_salt"]), length=32, n=2**15, r=8, p=1).derive(
            passphrase.encode()
        )

    def receipt_key(self) -> bytes:
        return HKDF(
            algorithm=hashes.SHA256(), length=32, salt=None, info=b"decillion-vault-receipts-v1"
        ).derive(self._master_key())

    def _manifest_path(self, model_id: str) -> Path:
        return self.manifest_dir / f"{_sha(model_id.encode())}.json"

    def _shard_path(self, ciphertext_hash: str) -> Path:
        return (
            self.shard_dir / ciphertext_hash[:2] / ciphertext_hash[2:4] / f"{ciphertext_hash}.bin"
        )

    @staticmethod
    def _aad(model_id: str, index: int, plaintext_hash: str) -> bytes:
        return canonical({"model_id": model_id, "index": index, "plaintext_hash": plaintext_hash})

    def _write_shard(self, blob: bytes, ciphertext_hash: str) -> None:
        destination = self._shard_path(ciphertext_hash)
        if destination.exists():
            if destination.read_bytes() != blob:
                raise RuntimeError("ciphertext hash collision")
            return
        self._atomic_bytes(destination, blob)

    def _wrap_key(self, key_id: str, data_key: bytes) -> None:
        nonce = os.urandom(12)
        wrapped = AESGCM(self._master_key()).encrypt(nonce, data_key, key_id.encode())
        self._atomic_bytes(self.keys_dir / f"{key_id}.bin", nonce + wrapped)

    def unwrap_key(self, key_id: str) -> bytes:
        blob = (self.keys_dir / f"{key_id}.bin").read_bytes()
        if len(blob) < 29:
            raise RuntimeError("wrapped key is truncated")
        return AESGCM(self._master_key()).decrypt(blob[:12], blob[12:], key_id.encode())

    def add_file(
        self,
        path: str | Path,
        model_id: str,
        source: str,
        license: str,
        metadata: dict | None = None,
    ) -> ModelManifest:
        """Encrypt and publish a supported weight file without returning its DEK."""
        source_path = Path(path)
        if source_path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("weight file must end in .safetensors, .pt, or .bin")
        if not source_path.is_file() or source_path.is_symlink():
            raise ValueError("weight file must be a regular, non-symlink file")
        if not model_id or len(model_id) > 512:
            raise ValueError("model_id is required and must be at most 512 characters")
        if self._manifest_path(model_id).exists():
            raise FileExistsError(f"model already exists: {model_id}")

        data_key = AESGCM.generate_key(bit_length=256)
        cipher = AESGCM(data_key)
        shards: list[Shard] = []
        leaves: list[bytes] = []
        total = 0
        file_digest = hashlib.sha256()
        with source_path.open("rb") as handle:
            for index, chunk in enumerate(iter(lambda: handle.read(self.shard_size), b"")):
                file_digest.update(chunk)
                plaintext_hash = _sha(chunk)
                nonce = os.urandom(12)
                ciphertext = cipher.encrypt(
                    nonce, chunk, self._aad(model_id, index, plaintext_hash)
                )
                blob = nonce + ciphertext
                ciphertext_hash = _sha(blob)
                self._write_shard(blob, ciphertext_hash)
                shards.append(
                    Shard(
                        index=index,
                        plaintext_hash=plaintext_hash,
                        ciphertext_hash=ciphertext_hash,
                        plaintext_bytes=len(chunk),
                        ciphertext_bytes=len(blob),
                        nonce_hex=nonce.hex(),
                    )
                )
                leaves.append(bytes.fromhex(ciphertext_hash))
                total += len(chunk)
        if not shards:
            raise ValueError("weight file is empty")

        key_id = "k_" + uuid.uuid4().hex
        manifest = ModelManifest(
            model_id=model_id,
            source=source,
            license=license,
            size_bytes=total,
            n_shards=len(shards),
            merkle_root=merkle_root(leaves).hex(),
            key_id=key_id,
            shards=shards,
            metadata={**(metadata or {}), "file_sha256": file_digest.hexdigest()},
        )
        self._wrap_key(key_id, data_key)
        self._atomic_bytes(self._manifest_path(model_id), manifest.to_json().encode())
        return manifest

    def _decrypt_shard(self, manifest: ModelManifest, shard: Shard, key: bytes) -> bytes:
        blob = self._shard_path(shard.ciphertext_hash).read_bytes()
        if _sha(blob) != shard.ciphertext_hash or len(blob) != shard.ciphertext_bytes:
            raise RuntimeError(f"shard {shard.index} ciphertext integrity failure")
        if blob[:12].hex() != shard.nonce_hex:
            raise RuntimeError(f"shard {shard.index} nonce mismatch")
        plaintext = AESGCM(key).decrypt(
            blob[:12],
            blob[12:],
            self._aad(manifest.model_id, shard.index, shard.plaintext_hash),
        )
        if _sha(plaintext) != shard.plaintext_hash or len(plaintext) != shard.plaintext_bytes:
            raise RuntimeError(f"shard {shard.index} plaintext integrity failure")
        return plaintext

    def stream_plaintext(self, manifest: ModelManifest) -> Iterator[bytes]:
        key = self.unwrap_key(manifest.key_id)
        for shard in sorted(manifest.shards, key=lambda item: item.index):
            yield self._decrypt_shard(manifest, shard, key)

    def read_shard_plaintext(self, manifest: ModelManifest, index: int) -> bytes:
        if not 0 <= index < manifest.n_shards:
            raise IndexError(index)
        shard = next((item for item in manifest.shards if item.index == index), None)
        if shard is None:
            raise IndexError(index)
        return self._decrypt_shard(manifest, shard, self.unwrap_key(manifest.key_id))

    def list_manifests(self) -> list[ModelManifest]:
        return [ModelManifest.load(path) for path in sorted(self.manifest_dir.glob("*.json"))]

    def get_manifest(self, model_id: str) -> ModelManifest | None:
        path = self._manifest_path(model_id)
        if not path.exists():
            return None
        manifest = ModelManifest.load(path)
        return manifest if manifest.model_id == model_id else None

    def verify(self, manifest: ModelManifest) -> tuple[bool, list[str]]:
        errors: list[str] = []
        leaves: list[bytes] = []
        expected_indices = list(range(manifest.n_shards))
        actual_indices = [
            shard.index for shard in sorted(manifest.shards, key=lambda item: item.index)
        ]
        if actual_indices != expected_indices:
            errors.append("shard indexes are not contiguous")
        for shard in sorted(manifest.shards, key=lambda item: item.index):
            path = self._shard_path(shard.ciphertext_hash)
            if not path.is_file():
                errors.append(f"shard {shard.index}: missing")
                continue
            blob = path.read_bytes()
            actual_hash = _sha(blob)
            if actual_hash != shard.ciphertext_hash:
                errors.append(f"shard {shard.index}: ciphertext hash mismatch")
            else:
                leaves.append(bytes.fromhex(actual_hash))
            if len(blob) != shard.ciphertext_bytes:
                errors.append(f"shard {shard.index}: size mismatch")
            if len(blob) < 12 or blob[:12].hex() != shard.nonce_hex:
                errors.append(f"shard {shard.index}: nonce mismatch")
        computed = merkle_root(leaves).hex()
        if computed != manifest.merkle_root:
            errors.append(f"merkle root mismatch: {computed} != {manifest.merkle_root}")
        return not errors, errors

    def stats(self) -> dict:
        manifests = self.list_manifests()
        unique = sum(1 for _ in self.shard_dir.rglob("*.bin"))
        return {
            "models": len(manifests),
            "total_plaintext_bytes": sum(item.size_bytes for item in manifests),
            "total_shards": sum(item.n_shards for item in manifests),
            "unique_shard_files": unique,
            "exact_ciphertext_reuse": max(0, sum(item.n_shards for item in manifests) - unique),
        }
