"""External model-weight vault with atomic imports and integrity inventories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .errors import IntegrityError

MARKER = ".decillion-vault.json"
MANIFEST = "decillion-manifest.json"
FORMAT_VERSION = 1
_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class VaultError(RuntimeError):
    """The external vault is missing, unsafe, full, locked, or malformed."""


@dataclass(frozen=True)
class VaultStatus:
    root: str
    vault_id: str
    quota_bytes: int
    reserve_bytes: int
    used_bytes: int
    free_bytes: int
    model_snapshots: int


class WeightVault:
    def __init__(self, root: str | Path, config: dict):
        self.root = Path(root).expanduser().resolve()
        self.config = config
        if config.get("format_version") != FORMAT_VERSION:
            raise VaultError("unsupported or missing vault format version")

    @classmethod
    def initialize(
        cls,
        root: str | Path,
        *,
        quota_bytes: int = 0,
        reserve_bytes: int = 10 * 1024**3,
    ) -> WeightVault:
        destination = Path(root).expanduser().resolve()
        if quota_bytes < 0 or reserve_bytes < 0:
            raise VaultError("quota and reserve must be non-negative")
        cls._reject_repository_path(destination)
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        marker = destination / MARKER
        if marker.exists():
            return cls.open(destination)
        config = {
            "format_version": FORMAT_VERSION,
            "vault_id": str(uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "quota_bytes": quota_bytes,
            "reserve_bytes": reserve_bytes,
        }
        cls._atomic_json(marker, config)
        (destination / "models").mkdir(mode=0o700)
        (destination / ".staging").mkdir(mode=0o700)
        (destination / ".locks").mkdir(mode=0o700)
        return cls(destination, config)

    @classmethod
    def open(cls, root: str | Path) -> WeightVault:
        destination = Path(root).expanduser().resolve()
        marker = destination / MARKER
        if not marker.is_file():
            raise VaultError(f"vault is not initialized: {destination}")
        try:
            config = json.loads(marker.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise VaultError("vault marker is unreadable") from exc
        return cls(destination, config)

    @staticmethod
    def _reject_repository_path(destination: Path) -> None:
        for parent in (destination, *destination.parents):
            if (parent / ".git").exists():
                raise VaultError("model vault must be outside every Git working tree")

    @staticmethod
    def _atomic_json(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".json-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    @staticmethod
    def _safe_component(value: str) -> str:
        if not _COMPONENT.fullmatch(value):
            raise VaultError(f"unsafe model path component: {value!r}")
        return value

    def snapshot_path(self, model_id: str, revision: str) -> Path:
        parts = model_id.split("/")
        if len(parts) != 2:
            raise VaultError("model ID must use organization/name form")
        organization, name = (self._safe_component(part) for part in parts)
        revision = self._safe_component(revision)
        return self.root / "models" / organization / name / revision

    def status(self) -> VaultStatus:
        disk = shutil.disk_usage(self.root)
        used = sum(
            path.stat().st_size for path in (self.root / "models").rglob("*") if path.is_file()
        )
        snapshots = sum(1 for _ in (self.root / "models").rglob(MANIFEST))
        return VaultStatus(
            root=str(self.root),
            vault_id=str(self.config["vault_id"]),
            quota_bytes=int(self.config.get("quota_bytes", 0)),
            reserve_bytes=int(self.config.get("reserve_bytes", 0)),
            used_bytes=used,
            free_bytes=disk.free,
            model_snapshots=snapshots,
        )

    def require_capacity(self, expected_bytes: int) -> None:
        if expected_bytes < 0:
            raise VaultError("expected size must be non-negative")
        status = self.status()
        quota = status.quota_bytes
        if quota and status.used_bytes + expected_bytes > quota:
            raise VaultError("download would exceed vault quota")
        if expected_bytes + status.reserve_bytes > status.free_bytes:
            raise VaultError("download would violate free-space reserve")

    @contextmanager
    def download_slot(self, model_id: str, revision: str) -> Iterator[Path]:
        key = hashlib.sha256(f"{model_id}@{revision}".encode()).hexdigest()
        lock = self.root / ".locks" / f"{key}.lock"
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise VaultError("this model revision is already being downloaded") from exc
        os.close(descriptor)
        staging = Path(tempfile.mkdtemp(prefix=f"{key[:12]}-", dir=self.root / ".staging"))
        try:
            yield staging
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            lock.unlink(missing_ok=True)

    @staticmethod
    def _inventory(directory: Path) -> tuple[list[dict], int]:
        files: list[dict] = []
        total = 0
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise VaultError(f"symbolic links are not allowed in snapshots: {path}")
            if not path.is_file() or path.name == MANIFEST:
                continue
            relative = path.relative_to(directory).as_posix()
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(8 * 1024**2), b""):
                    digest.update(block)
            size = path.stat().st_size
            total += size
            files.append({"path": relative, "size": size, "sha256": digest.hexdigest()})
        return files, total

    def commit_snapshot(
        self,
        staging: Path,
        *,
        model_id: str,
        revision: str,
        license_name: str,
    ) -> dict:
        target = self.snapshot_path(model_id, revision)
        if target.exists():
            return self.verify(model_id, revision)
        files, total = self._inventory(staging)
        if not files:
            raise VaultError("refusing to commit an empty model snapshot")
        self.require_capacity(total)
        manifest = {
            "format_version": FORMAT_VERSION,
            "model_id": model_id,
            "revision": revision,
            "license": license_name,
            "created_at": datetime.now(UTC).isoformat(),
            "total_bytes": total,
            "files": files,
        }
        self._atomic_json(staging / MANIFEST, manifest)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.replace(staging, target)
        return manifest

    def verify(self, model_id: str, revision: str) -> dict:
        target = self.snapshot_path(model_id, revision)
        manifest_path = target / MANIFEST
        if not manifest_path.is_file():
            raise IntegrityError("model manifest is missing")
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise IntegrityError("model manifest is unreadable") from exc
        actual_files, actual_total = self._inventory(target)
        if actual_files != manifest.get("files") or actual_total != manifest.get("total_bytes"):
            raise IntegrityError("model snapshot failed SHA-256 inventory verification")
        if manifest.get("model_id") != model_id or manifest.get("revision") != revision:
            raise IntegrityError("model manifest identity does not match its path")
        return manifest
