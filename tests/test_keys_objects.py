import base64
import os

import pytest

from decillion.keys import LocalKeyProvider, generate_master_key
from decillion.objects import FileObjectStore


def test_key_provider_environment(monkeypatch):
    raw = os.urandom(32)
    monkeypatch.setenv("DECILLION_MASTER_KEY", base64.urlsafe_b64encode(raw).decode())
    provider = LocalKeyProvider.from_env()
    wrapped = provider.wrap(b"x" * 32, b"context")
    assert provider.unwrap(wrapped, b"context") == b"x" * 32
    assert len(base64.urlsafe_b64decode(generate_master_key())) == 32


def test_invalid_key_configuration(monkeypatch):
    monkeypatch.delenv("DECILLION_MASTER_KEY", raising=False)
    with pytest.raises(RuntimeError):
        LocalKeyProvider.from_env()
    monkeypatch.setenv("DECILLION_MASTER_KEY", "not-base64!")
    with pytest.raises((ValueError, Exception)):
        LocalKeyProvider.from_env()
    with pytest.raises(ValueError):
        LocalKeyProvider(b"too-short")


def test_object_store_validation_and_exists(tmp_path):
    store = FileObjectStore(tmp_path)
    object_id = "a" * 64
    assert not store.exists(object_id)
    store.put(object_id, b"payload")
    assert store.exists(object_id)
    assert store.get(object_id) == b"payload"
    with pytest.raises(ValueError):
        store.get("../escape")
