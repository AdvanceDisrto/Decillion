import json
import os

import pytest

from decillion.errors import IntegrityError
from decillion.vault import MANIFEST, VaultError, WeightVault


def test_initialize_status_and_reopen(tmp_path):
    root = tmp_path / "external-vault"
    vault = WeightVault.initialize(root, quota_bytes=1000, reserve_bytes=0)
    status = vault.status()
    assert status.root == str(root.resolve())
    assert status.quota_bytes == 1000
    assert status.model_snapshots == 0
    assert WeightVault.open(root).config["vault_id"] == status.vault_id
    assert WeightVault.initialize(root).config["vault_id"] == status.vault_id


def test_vault_must_be_outside_git_tree(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(VaultError, match="outside"):
        WeightVault.initialize(tmp_path / "weights")


def test_open_and_capacity_fail_closed(tmp_path, monkeypatch):
    with pytest.raises(VaultError, match="not initialized"):
        WeightVault.open(tmp_path / "missing")
    vault = WeightVault.initialize(tmp_path / "vault", quota_bytes=5, reserve_bytes=0)
    with pytest.raises(VaultError, match="quota"):
        vault.require_capacity(6)
    with pytest.raises(VaultError, match="non-negative"):
        vault.require_capacity(-1)
    fake_usage = os.statvfs(tmp_path)
    monkeypatch.setattr(
        "decillion.vault.shutil.disk_usage",
        lambda path: type("Usage", (), {"free": 2, "total": 2, "used": 0})(),
    )
    vault.config["quota_bytes"] = 0
    with pytest.raises(VaultError, match="free-space"):
        vault.require_capacity(3)
    assert fake_usage.f_bsize > 0


def test_atomic_commit_verify_and_tamper_detection(tmp_path):
    vault = WeightVault.initialize(tmp_path / "vault", reserve_bytes=0)
    with vault.download_slot("org/model", "abc123") as staging:
        (staging / "config.json").write_text('{"model":"test"}\n')
        (staging / "weights.safetensors").write_bytes(b"weights")
        manifest = vault.commit_snapshot(
            staging, model_id="org/model", revision="abc123", license_name="mit"
        )
    assert manifest["total_bytes"] > 0
    assert len(manifest["files"]) == 2
    target = vault.snapshot_path("org/model", "abc123")
    assert (target / MANIFEST).is_file()
    assert vault.verify("org/model", "abc123") == manifest
    (target / "weights.safetensors").write_bytes(b"tampered")
    with pytest.raises(IntegrityError, match="SHA-256"):
        vault.verify("org/model", "abc123")


def test_lock_empty_snapshot_and_safe_paths(tmp_path):
    vault = WeightVault.initialize(tmp_path / "vault", reserve_bytes=0)
    with vault.download_slot("org/model", "revision") as staging:
        with pytest.raises(VaultError, match="already"):
            with vault.download_slot("org/model", "revision"):
                pass
        with pytest.raises(VaultError, match="empty"):
            vault.commit_snapshot(
                staging, model_id="org/model", revision="revision", license_name="mit"
            )
    with pytest.raises(VaultError, match="organization/name"):
        vault.snapshot_path("invalid", "revision")
    with pytest.raises(VaultError, match="unsafe"):
        vault.snapshot_path("org/model", "../escape")


def test_marker_corruption_is_rejected(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / ".decillion-vault.json").write_text("not-json")
    with pytest.raises(VaultError, match="unreadable"):
        WeightVault.open(root)
    (root / ".decillion-vault.json").write_text(json.dumps({"format_version": 999}))
    with pytest.raises(VaultError, match="unsupported"):
        WeightVault.open(root)
