import hashlib
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from vault.access import ACL, NonceCache, merkle_proof, merkle_root, sign_request, verify_merkle
from vault.receipts import VaultReceipts
from vault.server import create_app
from vault.store import VaultStore


@pytest.fixture(autouse=True)
def passphrase(monkeypatch):
    monkeypatch.setenv("IZETTA_VAULT_PASSPHRASE", "correct horse battery staple")


def add_model(tmp_path, size=2_100_000):
    source = tmp_path / "model.safetensors"
    source.write_bytes(os.urandom(size))
    store = VaultStore(tmp_path / "vault")
    manifest = store.add_file(source, "org/model", "file://model", "MIT")
    return source, store, manifest


def test_encrypt_verify_stream_and_tamper(tmp_path):
    source, store, manifest = add_model(tmp_path)
    assert manifest.n_shards == 3
    assert store.verify(manifest) == (True, [])
    restored = b"".join(store.stream_plaintext(manifest))
    assert restored == source.read_bytes()
    assert manifest.metadata["file_sha256"] == hashlib.sha256(restored).hexdigest()
    assert not hasattr(manifest, "ephemeral_key")

    shard_path = store._shard_path(manifest.shards[0].ciphertext_hash)
    blob = bytearray(shard_path.read_bytes())
    blob[-1] ^= 1
    shard_path.write_bytes(blob)
    ok, errors = store.verify(manifest)
    assert not ok
    assert any("hash mismatch" in error for error in errors)


def test_wrong_passphrase_cannot_unwrap(tmp_path, monkeypatch):
    _, store, manifest = add_model(tmp_path, 10)
    monkeypatch.setenv("IZETTA_VAULT_PASSPHRASE", "wrong")
    with pytest.raises(Exception):
        store.read_shard_plaintext(manifest, 0)


def test_merkle_proof_and_nonce_replay():
    leaves = [hashlib.sha256(str(index).encode()).digest() for index in range(3)]
    root = merkle_root(leaves)
    assert verify_merkle(leaves[1], merkle_proof(leaves, 1), root)
    cache = NonceCache()
    assert cache.accept("pub", "nonce")
    assert not cache.accept("pub", "nonce")


def test_receipt_chain_signs_payload(tmp_path):
    receipts = VaultReceipts(tmp_path / "receipts.sqlite", b"r" * 32)
    receipts.emit("vault.add", "org/model", "actor", {"value": 1})
    assert receipts.verify_chain()[0]
    receipts.db.execute("UPDATE receipts SET payload_json='{}'")
    receipts.db.commit()
    assert not receipts.verify_chain()[0]


def test_signed_http_reads_and_replay_rejection(tmp_path):
    _, store, manifest = add_model(tmp_path, 100)
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw().hex()
    ACL(store.root / "acl.json").allow(manifest.model_id, public)
    client = TestClient(create_app(store.root))

    opened = sign_request(private, manifest.model_id, "open")
    response = client.post(f"/models/{manifest.model_id}/open", json=opened.to_dict())
    assert response.status_code == 200
    assert (
        client.post(f"/models/{manifest.model_id}/open", json=opened.to_dict()).status_code == 409
    )

    read = sign_request(private, manifest.model_id, "read:0")
    headers = {
        "X-Vault-Pubkey": read.requester_pubkey,
        "X-Vault-Nonce": read.nonce,
        "X-Vault-Signature": read.signature,
        "X-Vault-Timestamp": str(read.timestamp),
    }
    response = client.get(f"/models/{manifest.model_id}/shards/0", headers=headers)
    assert response.status_code == 200
    assert response.content == b"".join(store.stream_plaintext(manifest))
    assert response.headers["x-decillion-receipt"]
