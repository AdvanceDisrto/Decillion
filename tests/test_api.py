import base64
import os

import pytest
from fastapi.testclient import TestClient

from decillion import api


def configured_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DECILLION_MASTER_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode())
    monkeypatch.setenv("DECILLION_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DECILLION_API_PRINCIPALS", '{"test-token":"wallet-1"}')
    monkeypatch.setenv("DECILLION_ENV", "production")
    api._services.cache_clear()
    return TestClient(api.app)


def test_health_and_authorization(tmp_path, monkeypatch):
    client = configured_client(tmp_path, monkeypatch)
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/v1/objects/missing").status_code == 401
    assert (
        client.get("/v1/objects/missing", headers={"Authorization": "Bearer wrong"}).status_code
        == 403
    )


def test_upload_download_and_merkle_root(tmp_path, monkeypatch):
    client = configured_client(tmp_path, monkeypatch)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post(
        "/v1/objects",
        headers=headers,
        files={"file": ("hello.txt", b"hello sovereign world")},
    )
    assert created.status_code == 201
    receipt = created.json()
    assert "ephemeral_key" not in receipt
    fetched = client.get(
        f"/v1/objects/{receipt['object_id']}",
        headers=headers,
        params={"filename": "hello.txt"},
    )
    assert fetched.status_code == 200
    assert fetched.content == b"hello sovereign world"
    root = client.get("/v1/receipts/root", headers=headers).json()
    assert root["count"] == 1
    assert len(root["merkle_root"]) == 64


def test_download_errors(tmp_path, monkeypatch):
    client = configured_client(tmp_path, monkeypatch)
    headers = {"Authorization": "Bearer test-token"}
    assert (
        client.get(
            "/v1/objects/" + "f" * 64,
            headers=headers,
            params={"filename": "missing.txt"},
        ).status_code
        == 404
    )
    created = client.post(
        "/v1/objects",
        headers=headers,
        files={"file": ("hello.txt", b"hello")},
    ).json()
    monkeypatch.setenv("DECILLION_API_PRINCIPALS", '{"other-token":"wallet-2"}')
    denied = client.get(
        f"/v1/objects/{created['object_id']}",
        headers={"Authorization": "Bearer other-token"},
        params={"filename": "hello.txt"},
    )
    assert denied.status_code == 403


def test_invalid_upload_metadata_returns_422(tmp_path, monkeypatch):
    client = configured_client(tmp_path, monkeypatch)
    response = client.post(
        "/v1/objects",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("x" * 1025, b"payload")},
    )
    assert response.status_code == 422


def test_principal_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv("DECILLION_ENV", "production")
    monkeypatch.setenv("DECILLION_API_PRINCIPALS", "not-json")
    with pytest.raises(RuntimeError):
        api._principals()


def test_services_require_master_key(tmp_path, monkeypatch):
    monkeypatch.delenv("DECILLION_MASTER_KEY", raising=False)
    monkeypatch.setenv("DECILLION_DATA_DIR", str(tmp_path))
    api._services.cache_clear()
    try:
        try:
            api._services()
            raise AssertionError("missing key should fail")
        except RuntimeError as exc:
            assert "DECILLION_MASTER_KEY" in str(exc)
    finally:
        api._services.cache_clear()
