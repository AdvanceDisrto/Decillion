import os
from dataclasses import replace

import pytest

from decillion.engine import SovereignStorage
from decillion.errors import AttestationError, AuthorizationError, IntegrityError
from decillion.keys import LocalKeyProvider
from decillion.objects import FileObjectStore
from decillion.receipts import ReceiptSigner, merkle_root, verify_receipt


@pytest.fixture
def engine(tmp_path):
    return SovereignStorage(
        FileObjectStore(tmp_path / "objects"),
        LocalKeyProvider(os.urandom(32)),
        ReceiptSigner.generate(),
    )


def test_round_trip_and_signed_receipt(engine):
    stored = engine.upload("wallet-1", "training.jsonl", b'{"text":"hello"}\n')
    result = engine.download(stored.receipt, owner="wallet-1", filename="training.jsonl")
    assert result == b'{"text":"hello"}\n'
    verify_receipt(stored.receipt, engine.signer.public_key)
    assert "ephemeral_key" not in stored.receipt.__dict__
    assert "wrapped_key" in stored.receipt.__dict__


def test_owner_and_filename_are_bound(engine):
    receipt = engine.upload("wallet-1", "a.txt", b"secret").receipt
    with pytest.raises(AuthorizationError):
        engine.download(receipt, owner="wallet-2", filename="a.txt")
    with pytest.raises(AuthorizationError):
        engine.download(receipt, owner="wallet-1", filename="b.txt")


def test_tampered_receipt_fails(engine):
    receipt = engine.upload("wallet-1", "a.txt", b"secret").receipt
    with pytest.raises(Exception):
        engine.download(replace(receipt, plaintext_size=999), owner="wallet-1", filename="a.txt")
    with pytest.raises(IntegrityError):
        engine.download(
            replace(receipt, signature="not-base64!"), owner="wallet-1", filename="a.txt"
        )


def test_tampered_ciphertext_fails(tmp_path):
    store = FileObjectStore(tmp_path / "objects")
    engine = SovereignStorage(store, LocalKeyProvider(os.urandom(32)), ReceiptSigner.generate())
    receipt = engine.upload("wallet-1", "a.txt", b"secret").receipt
    path = store._path(receipt.object_id)
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(payload)
    with pytest.raises(IntegrityError):
        engine.download(receipt, owner="wallet-1", filename="a.txt")


def test_attestation_can_be_required(tmp_path):
    engine = SovereignStorage(
        FileObjectStore(tmp_path / "objects"),
        LocalKeyProvider(os.urandom(32), require_attestation=True),
        ReceiptSigner.generate(),
    )
    receipt = engine.upload("wallet-1", "a.txt", b"secret").receipt
    with pytest.raises(AttestationError):
        engine.download(receipt, owner="wallet-1", filename="a.txt")
    assert (
        engine.download(receipt, owner="wallet-1", filename="a.txt", attestation="test-evidence")
        == b"secret"
    )


def test_merkle_root_is_deterministic(engine):
    receipts = [engine.upload("wallet-1", f"{i}.txt", str(i).encode()).receipt for i in range(3)]
    assert merkle_root(receipts) == merkle_root(receipts)
    assert len(merkle_root(receipts)) == 64


def test_input_and_envelope_validation(engine):
    with pytest.raises(ValueError):
        engine.upload("", "a.txt", b"x")
    with pytest.raises(ValueError):
        engine.upload("wallet", "", b"x")
    assert len(merkle_root([])) == 64


def test_truncated_object_fails(tmp_path):
    store = FileObjectStore(tmp_path / "objects")
    engine = SovereignStorage(store, LocalKeyProvider(os.urandom(32)), ReceiptSigner.generate())
    receipt = engine.upload("wallet", "a.txt", b"x").receipt
    store._path(receipt.object_id).write_bytes(b"bad")
    with pytest.raises(IntegrityError):
        engine.download(receipt, owner="wallet", filename="a.txt")


def test_signer_is_persistent(tmp_path):
    path = tmp_path / "signing.key"
    first = ReceiptSigner.load_or_create(path)
    second = ReceiptSigner.load_or_create(path)
    receipt = (
        SovereignStorage(
            FileObjectStore(tmp_path / "objects"),
            LocalKeyProvider(os.urandom(32)),
            first,
        )
        .upload("wallet", "a.txt", b"x")
        .receipt
    )
    verify_receipt(receipt, second.public_key)
    assert path.stat().st_mode & 0o777 == 0o600
