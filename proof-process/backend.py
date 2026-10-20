"""Buddy Proof API reference. No synthetic certification or external chain claim."""
import hashlib
import hmac
import json
import os
import sqlite3
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="iNNOVULIS Buddy Proof", version="0.2.0")


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def auth(authorization: str | None = Header(default=None)):
    token = os.getenv("BUDDY_API_TOKEN")
    if not token or not authorization or not hmac.compare_digest(
        authorization, "Bearer " + token
    ):
        raise HTTPException(401, "Buddy authorization required")


def state():
    keyfile = os.getenv("BUDDY_SIGNER_KEY_FILE")
    path = os.getenv("BUDDY_PROOF_DB")
    if not keyfile or not path or not Path(keyfile).is_file():
        raise HTTPException(503, "durable signer and database required")
    try:
        signer = Ed25519PrivateKey.from_private_bytes(Path(keyfile).read_bytes())
        db = sqlite3.connect(path)
        db.execute(
            "CREATE TABLE IF NOT EXISTS issued("
            "claim_id TEXT, version TEXT, cert TEXT, revoked INTEGER DEFAULT 0,"
            "PRIMARY KEY(claim_id,version))"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS events("
            "seq INTEGER PRIMARY KEY, body TEXT, digest TEXT)"
        )
        return signer, db
    except (ValueError, sqlite3.Error):
        raise HTTPException(503, "invalid signer or database")


def event(db, kind, payload):
    row = db.execute("SELECT digest FROM events ORDER BY seq DESC LIMIT 1").fetchone()
    body = {"kind": kind, "payload": payload, "prev": row[0] if row else "genesis"}
    hash_value = digest(body)
    db.execute(
        "INSERT INTO events(body,digest) VALUES(?,?)",
        (canon(body).decode(), hash_value),
    )
    return hash_value


class Submission(BaseModel):
    contract: dict
    attempt: dict
    reviewer_public_key: str
    reviewer_signature: str


@app.get("/health")
def health():
    return {"status": "reference", "external_anchor": False, "live_ai": False}


@app.post("/v1/proofs/submit", dependencies=[Depends(auth)])
def submit(data: Submission):
    c, a = data.contract, data.attempt
    keys = json.loads(os.getenv("BUDDY_REVIEWER_KEYS_JSON", "[]"))
    if data.reviewer_public_key not in keys:
        raise HTTPException(403, "reviewer key not registered")
    if (c.get("claim_id"), c.get("claim_version")) != (
        a.get("claim_id"), a.get("claim_version")
    ) or not c.get("claim_id") or not c.get("claim_version"):
        raise HTTPException(422, "claim/version mismatch")
    if c.get("criteria_version") != a.get("criteria_version"):
        raise HTTPException(422, "criteria changed")
    if a.get("generator_public_key") == data.reviewer_public_key:
        raise HTTPException(422, "generator cannot review")
    try:
        reviewer = Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(data.reviewer_public_key)
        )
        reviewer.verify(
            bytes.fromhex(data.reviewer_signature),
            canon({"contract": c, "attempt": a}),
        )
    except Exception:
        raise HTTPException(422, "invalid reviewer signature")
    if not a.get("executed") or a.get("decision") != "REQUIREMENTS_SATISFIED":
        raise HTTPException(422, "attempt not satisfied")
    if a.get("checks_failed") or a.get("blocking_issues"):
        raise HTTPException(422, "blocking checks")
    if not set(c.get("required_checks", [])).issubset(
        set(a.get("checks_passed", []))
    ):
        raise HTTPException(422, "required check missing")
    evidence = a.get("evidence", {})
    for name in c.get("evidence_requirements", []):
        value = evidence.get(name, "")
        if not isinstance(value, str) or not value.startswith("sha256:"):
            raise HTTPException(422, "evidence missing")
    spent, budget = a.get("spent_usd"), c.get("budget_usd")
    if (not isinstance(spent, (int, float)) or
            not isinstance(budget, (int, float)) or
            not 0 <= spent <= budget):
        raise HTTPException(422, "budget exceeded")
    signer, db = state()
    try:
        pub = signer.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        ).hex()
        body = {
            "certificate_type": "Buddy_Certified_UR1",
            "claim_id": c["claim_id"],
            "claim_version": c["claim_version"],
            "contract_hash": digest(c), "attempt_hash": digest(a),
            "reviewer_public_key": data.reviewer_public_key,
            "reviewer_signature": data.reviewer_signature,
            "issuer_public_key": pub,
            "scope": c.get("scope", "declared checks only"),
            "limits": "No universal factual truth, PUF or external anchor proven",
        }
        cert = dict(body)
        cert["signature"] = signer.sign(canon(body)).hex()
        cert["ur1_receipt"] = "urn:ur1:" + digest(body)
        try:
            with db:
                db.execute(
                    "INSERT INTO issued(claim_id,version,cert) VALUES(?,?,?)",
                    (c["claim_id"], c["claim_version"], canon(cert).decode()),
                )
                event(db, "issued", {"receipt": cert["ur1_receipt"]})
        except sqlite3.IntegrityError:
            raise HTTPException(409, "certificate already issued")
        return {"contract": c, "attempt": a, "certification": cert}
    finally:
        db.close()


@app.post("/v1/proofs/verify")
def verify(bundle: dict):
    try:
        c, a, cert = (
            bundle["contract"], bundle["attempt"], bundle["certification"]
        )
        body = {k: v for k, v in cert.items() if k not in
                ("signature", "ur1_receipt")}
        if body["contract_hash"] != digest(c) or body["attempt_hash"] != digest(a):
            raise ValueError("mismatched digest")
        if cert["ur1_receipt"] != "urn:ur1:" + digest(body):
            raise ValueError("receipt mismatch")
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(body["issuer_public_key"])
        ).verify(bytes.fromhex(cert["signature"]), canon(body))
        Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(body["reviewer_public_key"])
        ).verify(
            bytes.fromhex(body["reviewer_signature"]),
            canon({"contract": c, "attempt": a}),
        )
        return {"integrity_verified": True, "revocation_checked": False,
                "external_anchor_verified": False}
    except Exception:
        return {"integrity_verified": False, "revocation_checked": False,
                "external_anchor_verified": False}


@app.get("/v1/proofs/{claim_id}/{version}", dependencies=[Depends(auth)])
def status(claim_id: str, version: str):
    _, db = state()
    try:
        row = db.execute(
            "SELECT cert,revoked FROM issued WHERE claim_id=? AND version=?",
            (claim_id, version),
        ).fetchone()
        if not row:
            raise HTTPException(404, "unknown claim")
        return {"certificate": json.loads(row[0]), "revoked": bool(row[1])}
    finally:
        db.close()
