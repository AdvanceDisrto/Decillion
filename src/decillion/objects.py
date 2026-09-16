"""Content-addressed object backends."""

from __future__ import annotations

import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path


class ObjectStore(ABC):
    @abstractmethod
    def put(self, object_id: str, payload: bytes) -> None: ...

    @abstractmethod
    def get(self, object_id: str) -> bytes: ...

    @abstractmethod
    def exists(self, object_id: str) -> bool: ...


class FileObjectStore(ObjectStore):
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _path(self, object_id: str) -> Path:
        if len(object_id) != 64 or any(c not in "0123456789abcdef" for c in object_id):
            raise ValueError("object_id must be a lowercase SHA-256 digest")
        return self.root / object_id[:2] / object_id[2:4] / object_id

    def put(self, object_id: str, payload: bytes) -> None:
        target = self._path(object_id)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temp_name = tempfile.mkstemp(prefix=".upload-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def get(self, object_id: str) -> bytes:
        return self._path(object_id).read_bytes()

    def exists(self, object_id: str) -> bool:
        return self._path(object_id).is_file()
