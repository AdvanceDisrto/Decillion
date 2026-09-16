#!/usr/bin/env python3
"""Prevent secrets, ciphertext, and model weights from entering Git."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

BLOCKED_SUFFIXES = {
    ".safetensors",
    ".gguf",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".parquet",
    ".arrow",
}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"DECILLION_MASTER_KEY\s*=\s*[\"']?[A-Za-z0-9_-]{40,}={0,2}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    files = subprocess.check_output(
        [  # noqa: S607 - fixed executable in developer tooling
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=root,
        text=True,
    ).splitlines()
    violations: list[str] = []
    for name in files:
        path = root / name
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            violations.append(f"model/data artifact is tracked: {name}")
        if path.is_file() and path.stat().st_size > 5_000_000:
            violations.append(f"tracked file exceeds 5 MB: {name}")
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                violations.append(f"possible secret in {name}: {pattern.pattern}")
    if violations:
        raise SystemExit("\n".join(violations))
    print(f"REPOSITORY_POLICY_PASS tracked_files={len(files)}")


if __name__ == "__main__":
    main()
