"""FastAPI gateway for Decillion storage."""

from __future__ import annotations

import os
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response

from .catalog import ReceiptCatalog
from .engine import SovereignStorage
from .errors import AuthorizationError, IntegrityError
from .keys import LocalKeyProvider
from .objects import FileObjectStore
from .receipts import ReceiptSigner, merkle_root

app = FastAPI(title="Decillion Sovereign Storage", version="0.1.0")


def _tokens() -> set[str]:
    configured = {
        value.strip() for value in os.getenv("DECILLION_API_TOKENS", "").split(",") if value.strip()
    }
    if os.getenv("DECILLION_ENV", "development") == "development":
        configured.add("development-token")
    return configured


def authorize(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    if authorization.removeprefix("Bearer ") not in _tokens():
        raise HTTPException(status_code=403, detail="invalid API token")


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


@app.post("/v1/objects", dependencies=[Depends(authorize)], status_code=201)
async def upload(file: UploadFile = File(...), wallet: str = Form(...)) -> dict:
    engine, catalog = _services()
    stored = engine.upload(wallet, file.filename or "unnamed", await file.read())
    catalog.add(stored.receipt)
    return asdict(stored.receipt)


@app.get("/v1/objects/{object_id}", dependencies=[Depends(authorize)])
def download(
    object_id: str,
    wallet: str,
    filename: str,
    x_decillion_attestation: str | None = Header(None),
) -> Response:
    engine, catalog = _services()
    receipt = catalog.get(object_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="object not found")
    try:
        payload = engine.download(
            receipt,
            owner=wallet,
            filename=filename,
            attestation=x_decillion_attestation,
        )
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(payload, media_type="application/octet-stream")


@app.get("/v1/receipts/root", dependencies=[Depends(authorize)])
def receipt_root(wallet: str, limit: int = 1000) -> dict:
    _, catalog = _services()
    receipts = catalog.list_owner(wallet, limit)
    return {"wallet": wallet, "count": len(receipts), "merkle_root": merkle_root(receipts)}
