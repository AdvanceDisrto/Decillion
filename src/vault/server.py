"""FastAPI read service with signed, replay-protected shard requests."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Body, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

from .access import ACL, AccessRequest, NonceCache, verify_request
from .receipts import VaultReceipts
from .store import VaultStore


def create_app(vault_dir: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Decillion Model-Weight Vault", version="1.0.0")
    root = Path(vault_dir or os.environ.get("IZETTA_VAULT", "./.vault"))
    store = VaultStore(root)
    acl = ACL(root / "acl.json")
    receipts = VaultReceipts(root / "receipts.sqlite", store.receipt_key())
    nonces = NonceCache()

    def authorize(request: AccessRequest, model_id: str, purpose: str) -> None:
        if request.model_id != model_id or request.purpose != purpose:
            raise HTTPException(403, "signed request does not match this operation")
        ok, reason = verify_request(request)
        if not ok:
            raise HTTPException(403, reason)
        if not nonces.accept(request.requester_pubkey, request.nonce):
            raise HTTPException(409, "request nonce was already used")
        if not acl.is_allowed(model_id, request.requester_pubkey):
            raise HTTPException(403, "not in ACL")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "models": len(store.list_manifests()), "receipts": receipts.count()}

    @app.get("/models")
    def models() -> list[dict]:
        return [
            {
                "model_id": item.model_id,
                "size_bytes": item.size_bytes,
                "n_shards": item.n_shards,
                "merkle_root": item.merkle_root,
                "license": item.license,
                "source": item.source,
            }
            for item in store.list_manifests()
        ]

    @app.get("/manifests/{model_id:path}")
    def manifest(model_id: str) -> dict:
        value = store.get_manifest(model_id)
        if value is None:
            raise HTTPException(404, "not found")
        return value.to_dict()

    @app.post("/models/{model_id:path}/open")
    def open_model(model_id: str, body: dict = Body(...)) -> dict:
        value = store.get_manifest(model_id)
        if value is None:
            raise HTTPException(404, "not found")
        try:
            request = AccessRequest(**body)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "malformed access request") from exc
        authorize(request, model_id, "open")
        receipt_id = receipts.emit(
            "vault.open",
            model_id,
            request.requester_pubkey,
            {"purpose": request.purpose, "request_nonce": request.nonce},
        )
        return {
            "ok": True,
            "n_shards": value.n_shards,
            "merkle_root": value.merkle_root,
            "receipt_id": receipt_id,
        }

    @app.get("/models/{model_id:path}/shards/{index}")
    def shard(
        model_id: str,
        index: int,
        x_vault_pubkey: str = Header(...),
        x_vault_nonce: str = Header(...),
        x_vault_signature: str = Header(...),
        x_vault_timestamp: float = Header(...),
    ) -> StreamingResponse:
        value = store.get_manifest(model_id)
        if value is None:
            raise HTTPException(404, "not found")
        request = AccessRequest(
            x_vault_pubkey,
            model_id,
            f"read:{index}",
            x_vault_nonce,
            x_vault_timestamp,
            x_vault_signature,
        )
        authorize(request, model_id, f"read:{index}")
        try:
            chunk = store.read_shard_plaintext(value, index)
        except IndexError as exc:
            raise HTTPException(404, "shard not found") from exc
        except Exception as exc:
            raise HTTPException(500, "shard integrity or decryption failure") from exc
        receipt_id = receipts.emit(
            "vault.shard_read",
            model_id,
            request.requester_pubkey,
            {"shard_index": index, "bytes": len(chunk)},
        )
        return StreamingResponse(
            iter([chunk]),
            media_type="application/octet-stream",
            headers={"X-Decillion-Receipt": receipt_id},
        )

    return app


if os.environ.get("IZETTA_VAULT_PASSPHRASE"):
    app = create_app()
else:
    app = FastAPI(title="Decillion Model-Weight Vault", version="1.0.0")

    @app.get("/health")
    def configuration_required() -> None:
        raise HTTPException(503, "set IZETTA_VAULT_PASSPHRASE before starting the vault")
