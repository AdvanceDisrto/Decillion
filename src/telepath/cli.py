"""Telepath server, pull client, and real TCP vault smoke test."""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import shutil
from pathlib import Path

from vault.access import ACL
from vault.receipts import VaultReceipts
from vault.store import VaultStore

from .node import TelepathNode


async def serve(args: argparse.Namespace) -> None:
    store = acl = receipts = None
    if args.vault:
        store = VaultStore(args.vault)
        acl = ACL(Path(args.vault) / "acl.json")
        receipts = VaultReceipts(Path(args.vault) / "receipts.sqlite", store.receipt_key())
    node = TelepathNode(
        args.host, args.port, args.name, vault_store=store, vault_acl=acl, receipts=receipts
    )
    await node.start()
    print(f"{args.name} listening on {args.host}:{node.port}; pubkey={node.pub}")
    try:
        await asyncio.Event().wait()
    finally:
        await node.stop()


async def pull(args: argparse.Namespace) -> None:
    node = TelepathNode(port=0, name=args.name)
    await node.start()
    try:
        peer = await node.connect(args.peer_host, args.peer_port)
        result = await node.pull_model(peer, args.model_id, args.dest)
        print(result)
    finally:
        await node.stop()


async def smoke(args: argparse.Namespace) -> None:
    os.environ.setdefault("IZETTA_VAULT_PASSPHRASE", "smoke-" + secrets.token_hex(16))
    root = Path(args.workdir)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    source = root / "source.safetensors"
    source.write_bytes(os.urandom(2 * 1024 * 1024 + 31))
    store = VaultStore(root / "vault")
    manifest = store.add_file(source, "smoke/model", "file://smoke", "MIT")
    acl = ACL(root / "vault" / "acl.json")
    receipts = VaultReceipts(root / "vault" / "receipts.sqlite", store.receipt_key())
    server = TelepathNode(port=0, name="alpha", vault_store=store, vault_acl=acl, receipts=receipts)
    client = TelepathNode(port=0, name="bravo")
    await server.start()
    await client.start()
    try:
        acl.allow(manifest.model_id, client.pub)
        peer = await client.connect("127.0.0.1", server.port)
        result = await client.pull_model(peer, manifest.model_id, root / "received")
        assert Path(result["path"]).read_bytes() == source.read_bytes()
        assert receipts.verify_chain()[0]
        assert client.reputation.summary()[0]["score"] == 1.0
        print(client.state())
        print("SMOKE TEST: BUILD GREEN")
    finally:
        await client.stop()
        await server.stop()


def main() -> None:
    parser = argparse.ArgumentParser(prog="decillion-telepath")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=7788)
    server.add_argument("--name", default="node")
    server.add_argument("--vault")
    server.set_defaults(fn=serve)
    client = commands.add_parser("pull-model")
    client.add_argument("--peer-host", required=True)
    client.add_argument("--peer-port", required=True, type=int)
    client.add_argument("--name", default="client")
    client.add_argument("--model-id", required=True)
    client.add_argument("--dest", required=True)
    client.set_defaults(fn=pull)
    test = commands.add_parser("vault-smoke")
    test.add_argument("--workdir", default="./.telepath-smoke")
    test.set_defaults(fn=smoke)
    args = parser.parse_args()
    try:
        asyncio.run(args.fn(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
