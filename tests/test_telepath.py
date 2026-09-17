import asyncio
import os
from pathlib import Path

from telepath.node import TelepathNode
from vault.access import ACL
from vault.receipts import VaultReceipts
from vault.store import VaultStore


def test_real_tcp_vault_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("IZETTA_VAULT_PASSPHRASE", "mesh test passphrase")
    source = tmp_path / "weights.bin"
    source.write_bytes(os.urandom(1_100_000))
    store = VaultStore(tmp_path / "vault")
    manifest = store.add_file(source, "org/mesh", "file://weights", "Apache-2.0")
    acl = ACL(store.root / "acl.json")
    receipts = VaultReceipts(store.root / "receipts.sqlite", store.receipt_key())

    async def scenario():
        server = TelepathNode(
            port=0, name="server", vault_store=store, vault_acl=acl, receipts=receipts
        )
        client = TelepathNode(port=0, name="client")
        await server.start()
        await client.start()
        try:
            acl.allow(manifest.model_id, client.pub)
            peer = await client.connect("127.0.0.1", server.port)
            result = await client.pull_model(peer, manifest.model_id, tmp_path / "received")
            assert Path(result["path"]).read_bytes() == source.read_bytes()
            assert client.cache.summary()["entries"] == manifest.n_shards
            assert client.reputation.summary()[0]["score"] == 1.0
        finally:
            await client.stop()
            await server.stop()

    asyncio.run(scenario())
    assert receipts.verify_chain()[0]
    assert receipts.count() == manifest.n_shards + 1


def test_acl_denies_unknown_peer(tmp_path, monkeypatch):
    monkeypatch.setenv("IZETTA_VAULT_PASSPHRASE", "mesh deny passphrase")
    source = tmp_path / "weights.pt"
    source.write_bytes(b"weights")
    store = VaultStore(tmp_path / "vault")
    manifest = store.add_file(source, "org/private", "file://weights", "MIT")

    async def scenario():
        server = TelepathNode(port=0, vault_store=store, vault_acl=ACL(store.root / "acl.json"))
        client = TelepathNode(port=0)
        await server.start()
        await client.start()
        try:
            peer = await client.connect("127.0.0.1", server.port)
            try:
                await client.open_session(peer, manifest.model_id, 1)
            except PermissionError:
                return
            raise AssertionError("session should have been denied")
        finally:
            await client.stop()
            await server.stop()

    asyncio.run(scenario())
