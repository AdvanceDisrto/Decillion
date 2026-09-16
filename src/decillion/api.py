"""FastAPI gateway for Decillion storage."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response

from .catalog import ReceiptCatalog
from .engine import SovereignStorage
from .errors import AuthorizationError, IntegrityError
from .keys import LocalKeyProvider
from .objects import FileObjectStore
from .receipts import ReceiptSigner, merkle_root

app = FastAPI(title="Decillion Sovereign Storage", version="0.1.0")


def _principals() -> dict[str, str]:
    try:
        configured = json.loads(os.getenv("DECILLION_API_PRINCIPALS", "{}"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("DECILLION_API_PRINCIPALS must be a JSON object") from exc
    if not isinstance(configured, dict) or not all(
        isinstance(token, str) and isinstance(owner, str) for token, owner in configured.items()
    ):
        raise RuntimeError("DECILLION_API_PRINCIPALS must map tokens to owner IDs")
    if os.getenv("DECILLION_ENV", "development") == "development":
        configured.setdefault("development-token", "development-owner")
    return configured


def authorize(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    owner = _principals().get(authorization.removeprefix("Bearer "))
    if owner is None:
        raise HTTPException(status_code=403, detail="invalid API token")
    if not owner or len(owner) > 512:
        raise RuntimeError("configured owner ID must contain 1-512 characters")
    return owner


@lru_cache(maxsize=1)
def _services() -> tuple[SovereignStorage, ReceiptCatalog]:
    root = Path(os.getenv("DECILLION_DATA_DIR", "var")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not os.getenv("DECILLION_MASTER_KEY"):
        raise RuntimeError("DECILLION_MASTER_KEY is required; run `decillion generate-master-key`")
    signer = ReceiptSigner.load_or_create(root / "receipt-signing.key")
    engine = SovereignStorage(
        FileObjectStore(root / "objects"), LocalKeyProvider.from_env(), signer
    )
    return engine, ReceiptCatalog(root / "receipts.sqlite3")


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok", "service": "decillion", "version": app.version}


@app.post("/v1/objects", status_code=201)
async def upload(file: UploadFile = File(...), owner: str = Depends(authorize)) -> dict:
    engine, catalog = _services()
    try:
        stored = engine.upload(owner, file.filename or "unnamed", await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    catalog.add(stored.receipt)
    return asdict(stored.receipt)


@app.get("/v1/objects/{object_id}")
def download(
    object_id: str,
    filename: str,
    x_decillion_attestation: str | None = Header(None),
    owner: str = Depends(authorize),
) -> Response:
    engine, catalog = _services()
    receipt = catalog.get(object_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="object not found")
    try:
        payload = engine.download(
            receipt,
            owner=owner,
            filename=filename,
            attestation=x_decillion_attestation,
        )
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(payload, media_type="application/octet-stream")


@app.get("/v1/receipts/root")
def receipt_root(limit: int = 1000, owner: str = Depends(authorize)) -> dict:
    _, catalog = _services()
    receipts = catalog.list_owner(owner, limit)
    return {"owner": owner, "count": len(receipts), "merkle_root": merkle_root(receipts)}
