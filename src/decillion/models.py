"""License-gated Hugging Face discovery and mirroring."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .errors import LicensePolicyError
from .vault import WeightVault

LICENSE_ALIASES = {
    "mit": "mit",
    "apache-2.0": "apache-2.0",
    "apache 2.0": "apache-2.0",
}


def normalize_license(value: str | None) -> str:
    raw = (value or "unknown").strip().lower()
    return LICENSE_ALIASES.get(raw, raw)


def require_license(actual: str | None, expected: str) -> str:
    normalized_actual = normalize_license(actual)
    normalized_expected = normalize_license(expected)
    if normalized_actual != normalized_expected:
        raise LicensePolicyError(
            f"model license {normalized_actual!r} does not match required {normalized_expected!r}"
        )
    return normalized_actual


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    revision: str | None
    license: str
    downloads: int
    discovered_at: str


def _hub():
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError as exc:
        raise SystemExit("Install model support with: pip install -e '.[models]'") from exc
    return HfApi(), snapshot_download


def discover(license_name: str, limit: int) -> list[ModelRecord]:
    api, _ = _hub()
    records = []
    models = api.list_models(
        filter=f"license:{license_name}", sort="downloads", limit=limit, full=True
    )
    for model in models:
        card = getattr(model, "card_data", None) or {}
        actual = card.get("license") if isinstance(card, dict) else getattr(card, "license", None)
        verified = require_license(actual, license_name)
        records.append(
            ModelRecord(
                model_id=model.id,
                revision=getattr(model, "sha", None),
                license=verified,
                downloads=int(getattr(model, "downloads", 0) or 0),
                discovered_at=datetime.now(UTC).isoformat(),
            )
        )
    return records


def _expected_size(info) -> int:
    total = 0
    for sibling in getattr(info, "siblings", None) or []:
        size = getattr(sibling, "size", None)
        lfs = getattr(sibling, "lfs", None)
        if size is None and isinstance(lfs, dict):
            size = lfs.get("size")
        total += int(size or 0)
    return total


def mirror(
    model_id: str,
    expected_license: str,
    destination: Path,
    include_weights: bool,
    allow_patterns: list[str] | None = None,
) -> dict:
    api, snapshot_download = _hub()
    info = api.model_info(model_id, files_metadata=include_weights)
    card = getattr(info, "card_data", None) or {}
    actual = card.get("license") if isinstance(card, dict) else getattr(card, "license", None)
    verified = require_license(actual, expected_license)
    record = {
        "model_id": model_id,
        "revision": info.sha,
        "license": verified,
        "downloaded_weights": False,
    }
    if include_weights:
        vault = WeightVault.open(destination)
        expected_bytes = _expected_size(info)
        vault.require_capacity(expected_bytes)
        target = vault.snapshot_path(model_id, info.sha)
        if target.exists():
            manifest = vault.verify(model_id, info.sha)
        else:
            with vault.download_slot(model_id, info.sha) as staging:
                snapshot_download(
                    repo_id=model_id,
                    revision=info.sha,
                    local_dir=staging,
                    allow_patterns=allow_patterns,
                )
                manifest = vault.commit_snapshot(
                    staging,
                    model_id=model_id,
                    revision=info.sha,
                    license_name=verified,
                )
        record.update(
            downloaded_weights=True,
            destination=str(target),
            expected_bytes=expected_bytes,
            verified_bytes=manifest["total_bytes"],
            verified_files=len(manifest["files"]),
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(prog="decillion-models")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("discover")
    scan.add_argument("--license", default="mit")
    scan.add_argument("--limit", type=int, default=100)
    scan.add_argument("--output", type=Path, required=True)
    copy = sub.add_parser("mirror")
    copy.add_argument("model_id")
    copy.add_argument("--license", required=True)
    copy.add_argument("--destination", type=Path, required=True)
    copy.add_argument("--include-weights", action="store_true")
    copy.add_argument("--allow-pattern", action="append", dest="allow_patterns")
    initialize = sub.add_parser("vault-init")
    initialize.add_argument("--destination", type=Path, required=True)
    initialize.add_argument("--quota-bytes", type=int, default=0)
    initialize.add_argument("--reserve-bytes", type=int, default=10 * 1024**3)
    status = sub.add_parser("vault-status")
    status.add_argument("--destination", type=Path, required=True)
    verify = sub.add_parser("vault-verify")
    verify.add_argument("model_id")
    verify.add_argument("revision")
    verify.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "discover":
        values = [asdict(item) for item in discover(args.license, max(1, min(args.limit, 1000)))]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(values, indent=2) + "\n")
        print(json.dumps({"models": len(values), "output": str(args.output)}))
    elif args.command == "mirror":
        result = mirror(
            args.model_id,
            args.license,
            args.destination,
            args.include_weights,
            args.allow_patterns,
        )
        print(json.dumps(result, indent=2))
    elif args.command == "vault-init":
        vault = WeightVault.initialize(
            args.destination,
            quota_bytes=args.quota_bytes,
            reserve_bytes=args.reserve_bytes,
        )
        print(json.dumps(asdict(vault.status()), indent=2))
    elif args.command == "vault-status":
        print(json.dumps(asdict(WeightVault.open(args.destination).status()), indent=2))
    else:
        manifest = WeightVault.open(args.destination).verify(args.model_id, args.revision)
        print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
