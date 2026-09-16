#!/usr/bin/env python3
import tempfile
from pathlib import Path

from decillion.vault import WeightVault


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        vault = WeightVault.initialize(Path(temp) / "external-vault", reserve_bytes=0)
        with vault.download_slot("smoke/model", "revision-001") as staging:
            (staging / "config.json").write_text('{"architecture":"smoke"}\n')
            (staging / "model.safetensors").write_bytes(b"verified-smoke-weights")
            manifest = vault.commit_snapshot(
                staging,
                model_id="smoke/model",
                revision="revision-001",
                license_name="mit",
            )
        verified = vault.verify("smoke/model", "revision-001")
        assert verified == manifest
        status = vault.status()
        assert status.model_snapshots == 1
        print(
            "WEIGHT_VAULT_SMOKE_PASS "
            f"vault_id={status.vault_id} files={len(manifest['files'])} "
            f"bytes={manifest['total_bytes']}"
        )


if __name__ == "__main__":
    main()
