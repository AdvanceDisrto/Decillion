"""License-gated Hugging Face discovery and mirroring."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .errors import LicensePolicyError

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


def mirror(model_id: str, expected_license: str, destination: Path, include_weights: bool) -> dict:
    api, snapshot_download = _hub()
    info = api.model_info(model_id, files_metadata=False)
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
        destination = destination.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        local = snapshot_download(
            repo_id=model_id, revision=info.sha, local_dir=destination / model_id
        )
        record.update(downloaded_weights=True, destination=local)
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
    args = parser.parse_args()
    if args.command == "discover":
        values = [asdict(item) for item in discover(args.license, max(1, min(args.limit, 1000)))]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(values, indent=2) + "\n")
        print(json.dumps({"models": len(values), "output": str(args.output)}))
    else:
        result = mirror(args.model_id, args.license, args.destination, args.include_weights)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
