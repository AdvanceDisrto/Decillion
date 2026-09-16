import base64
import os

from fastapi.testclient import TestClient

from decillion import api


def configured_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DECILLION_MASTER_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode())
    monkeypatch.setenv("DECILLION_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DECILLION_API_TOKENS", "test-token")
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
        data={"wallet": "wallet-1"},
        files={"file": ("hello.txt", b"hello sovereign world")},
    )
    assert created.status_code == 201
    receipt = created.json()
    assert "ephemeral_key" not in receipt
    fetched = client.get(
        f"/v1/objects/{receipt['object_id']}",
        headers=headers,
        params={"wallet": "wallet-1", "filename": "hello.txt"},
    )
    assert fetched.status_code == 200
    assert fetched.content == b"hello sovereign world"
    root = client.get("/v1/receipts/root", headers=headers, params={"wallet": "wallet-1"}).json()
    assert root["count"] == 1
    assert len(root["merkle_root"]) == 64


def test_download_errors(tmp_path, monkeypatch):
    client = configured_client(tmp_path, monkeypatch)
    headers = {"Authorization": "Bearer test-token"}
    assert (
        client.get(
            "/v1/objects/" + "f" * 64,
            headers=headers,
            params={"wallet": "wallet-1", "filename": "missing.txt"},
        ).status_code
        == 404
    )
    created = client.post(
        "/v1/objects",
        headers=headers,
        data={"wallet": "wallet-1"},
        files={"file": ("hello.txt", b"hello")},
    ).json()
    denied = client.get(
        f"/v1/objects/{created['object_id']}",
        headers=headers,
        params={"wallet": "wallet-2", "filename": "hello.txt"},
    )
    assert denied.status_code == 403


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
