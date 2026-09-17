"""Command-line management and an end-to-end vault smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .access import ACL, sign_request, verify_request
from .receipts import VaultReceipts
from .store import VaultStore


def _components(path: str) -> tuple[VaultStore, VaultReceipts]:
    store = VaultStore(path)
    receipts = VaultReceipts(Path(path) / "receipts.sqlite", store.receipt_key())
    return store, receipts


def cmd_init(args: argparse.Namespace) -> None:
    store, _ = _components(args.vault)
    ACL(store.root / "acl.json")
    print(f"vault initialized: {store.root}")


def cmd_add(args: argparse.Namespace) -> None:
    store, receipts = _components(args.vault)
    manifest = store.add_file(args.file, args.model_id, args.source, args.license)
    receipt_id = receipts.emit(
        "vault.add",
        manifest.model_id,
        "cli",
        {
            "size_bytes": manifest.size_bytes,
            "n_shards": manifest.n_shards,
            "merkle_root": manifest.merkle_root,
        },
    )
    print(json.dumps({**manifest.to_dict(), "receipt_id": receipt_id}, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    store = VaultStore(args.vault)
    for manifest in store.list_manifests():
        print(
            f"{manifest.model_id:60s} {manifest.size_bytes / 1e6:10.2f} MB "
            f"{manifest.n_shards:5d} shards {manifest.license}"
        )


def cmd_verify(args: argparse.Namespace) -> None:
    store, receipts = _components(args.vault)
    manifests = [store.get_manifest(args.model_id)] if args.model_id else store.list_manifests()
    if any(item is None for item in manifests):
        raise SystemExit(f"not found: {args.model_id}")
    success = True
    for manifest in manifests:
        assert manifest is not None
        ok, errors = store.verify(manifest)
        success &= ok
        print(f"{manifest.model_id}: {'OK' if ok else 'FAIL'}")
        for error in errors:
            print(f"  {error}")
    chain_ok, head = receipts.verify_chain()
    success &= chain_ok
    print(
        f"receipt chain: {'OK' if chain_ok else 'FAIL'} ({receipts.count()} receipts; {head[:12]})"
    )
    if not success:
        raise SystemExit(1)


def cmd_stats(args: argparse.Namespace) -> None:
    print(json.dumps(VaultStore(args.vault).stats(), indent=2))


def cmd_smoke(args: argparse.Namespace) -> None:
    os.environ.setdefault("IZETTA_VAULT_PASSPHRASE", "smoke-" + secrets.token_hex(16))
    root = Path(args.vault)
    root.mkdir(parents=True, exist_ok=True)
    store, receipts = _components(str(root))
    with tempfile.NamedTemporaryFile(suffix=".safetensors", dir=root, delete=False) as handle:
        handle.write(os.urandom(2 * 1024 * 1024 + 17))
        source = Path(handle.name)
    try:
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest = store.add_file(source, "smoke/fake-model", "file://smoke", "MIT")
        receipts.emit("vault.add", manifest.model_id, "smoke", manifest.to_dict())
        ok, errors = store.verify(manifest)
        assert ok, errors
        restored = b"".join(store.stream_plaintext(manifest))
        assert hashlib.sha256(restored).hexdigest() == original_hash
        private = Ed25519PrivateKey.generate()
        request = sign_request(private, manifest.model_id, "read")
        assert verify_request(request) == (True, "ok")
        acl = ACL(root / "acl.json")
        acl.allow(manifest.model_id, request.requester_pubkey)
        assert acl.is_allowed(manifest.model_id, request.requester_pubkey)
        receipts.emit(
            "vault.open", manifest.model_id, request.requester_pubkey, {"purpose": "read"}
        )
        assert receipts.verify_chain()[0]
        print(json.dumps(store.stats(), indent=2))
        print("SMOKE TEST: BUILD GREEN")
    finally:
        source.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(prog="decillion-vault")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--vault", required=True)
    init.set_defaults(fn=cmd_init)
    add = commands.add_parser("add")
    add.add_argument("--vault", required=True)
    add.add_argument("--file", required=True)
    add.add_argument("--model-id", required=True)
    add.add_argument("--source", default="file://")
    add.add_argument("--license", default="unknown")
    add.set_defaults(fn=cmd_add)
    listing = commands.add_parser("list")
    listing.add_argument("--vault", required=True)
    listing.set_defaults(fn=cmd_list)
    verify = commands.add_parser("verify")
    verify.add_argument("--vault", required=True)
    verify.add_argument("--model-id")
    verify.set_defaults(fn=cmd_verify)
    stats = commands.add_parser("stats")
    stats.add_argument("--vault", required=True)
    stats.set_defaults(fn=cmd_stats)
    smoke = commands.add_parser("smoke")
    smoke.add_argument("--vault", default="./.vault-smoke")
    smoke.set_defaults(fn=cmd_smoke)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
