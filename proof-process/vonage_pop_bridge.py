"""Vonage communications receipt bridge.

This module deliberately separates:
- Vonage API acceptance from downstream delivery;
- application-level receipt signing from Vonage webhook verification;
- software-key (T0) evidence from hardware attestation.

The canonicalization here is a deterministic JSON profile. It is NOT claimed
to be RFC 8785 JCS.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def mint_signed_receipt(
    *,
    channel: str,
    vonage_response: dict[str, Any],
    signer_priv: ed25519.Ed25519PrivateKey,
    signer_id: str,
    signer_tier: str = "T0",
) -> dict[str, Any]:
    if signer_tier not in {"T0", "T0.5", "T2"}:
        raise ValueError(f"unsupported signer tier: {signer_tier}")

    public_key_hex = signer_priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()

    body = {
        "spec": "innovulis-vonage-receipt/1.1",
        "created_at": utc_now(),
        "channel": channel,
        "vonage_response": vonage_response,
        "signer": {
            "id": signer_id,
            "tier": signer_tier,
            "public_key_hex": public_key_hex,
        },
        "anchor": None,
        "proves": [
            f"the Vonage {channel} API response fields recorded here were returned to this client",
            "the recorded receipt body is unchanged since signing when verification succeeds",
            f"the receipt signature is valid for the pinned Ed25519 key ({signer_tier})",
        ],
        "does_not_prove": [
            f"the signer key is hardware-backed ({signer_tier}=software)",
            "carrier delivery beyond the provider response status",
            "recipient reading or acknowledgement",
            "that the signer key was not exposed from process memory",
            "that any external blockchain anchor exists",
        ],
        "disclosures": [
            (
                "this receipt binds the recorded Vonage response fields, "
                "not an unrecorded HTTP byte stream"
            ),
            (
                "delivery status must arrive through a verified Vonage webhook "
                "before it is treated as provider evidence"
            ),
            (
                "the receipt signature uses a deterministic JSON serialization profile; "
                "RFC 8785 JCS is not claimed"
            ),
        ],
        "genesis_authority": None,
    }

    receipt_id = sha256_hex(canonical_json(body))
    body["receipt_id"] = receipt_id
    body["signature"] = signer_priv.sign(canonical_json(body)).hex()
    return body


def verify_vonage_receipt(
    receipt: dict[str, Any],
    expected_pubkey_hex: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    required = (
        "spec",
        "receipt_id",
        "signature",
        "channel",
        "vonage_response",
        "signer",
        "proves",
        "does_not_prove",
        "disclosures",
    )
    for key in required:
        if key not in receipt:
            errors.append(f"missing key: {key}")
    if errors:
        return {"ok": False, "errors": errors}

    body_without_id_or_sig = {
        k: v for k, v in receipt.items() if k not in {"receipt_id", "signature"}
    }
    if sha256_hex(canonical_json(body_without_id_or_sig)) != receipt["receipt_id"]:
        errors.append("receipt_id mismatch")

    pk_hex = expected_pubkey_hex or receipt["signer"].get("public_key_hex", "")
    try:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pk_hex))
        body_without_sig = {k: v for k, v in receipt.items() if k != "signature"}
        public_key.verify(bytes.fromhex(receipt["signature"]), canonical_json(body_without_sig))
    except Exception as exc:
        errors.append(f"signature invalid: {exc}")

    tier = receipt["signer"].get("tier")
    if tier == "T0" and not any(
        "software" in item.lower() or "process memory" in item.lower()
        for item in receipt["does_not_prove"]
    ):
        errors.append("T0 signer missing software-key limitation")

    anchor = receipt.get("anchor")
    if anchor is not None:
        for key in ("chain", "block_height", "txid", "ots_file"):
            if anchor.get(key) is None:
                errors.append("anchor is partial")
                break

    return {"ok": not errors, "errors": errors}


def verify_vonage_webhook(
    authorization_header: str,
    body_bytes: bytes,
    signature_secret: str,
    max_age_seconds: int = 300,
) -> dict[str, Any]:
    """Verify a Vonage signed webhook.

    Vonage's current webhook documentation specifies HS256 with the account's
    signature secret for Messages/Dispatch/Verify/Voice webhooks. The JWT's
    payload_hash is checked against the raw request body.
    """

    try:
        import jwt
    except ImportError:
        return {"ok": False, "reason": "pyjwt not installed", "payload": None}

    if not authorization_header.startswith("Bearer "):
        return {"ok": False, "reason": "missing Bearer header", "payload": None}

    token = authorization_header[7:].strip()
    try:
        decoded = jwt.decode(
            token,
            signature_secret,
            algorithms=["HS256"],
            options={"require": ["iat", "jti", "payload_hash"]},
        )
    except Exception as exc:
        return {"ok": False, "reason": f"jwt verify: {exc}", "payload": None}

    age = time.time() - int(decoded["iat"])
    if age < -30 or age > max_age_seconds:
        return {"ok": False, "reason": f"stale iat: {age:.0f}s", "payload": None}

    expected_hash = hashlib.sha256(body_bytes).hexdigest()
    if decoded["payload_hash"] != expected_hash:
        return {"ok": False, "reason": "payload_hash mismatch", "payload": None}

    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        return {"ok": False, "reason": "invalid JSON body", "payload": None}

    return {
        "ok": True,
        "reason": "verified",
        "payload": payload,
        "jti": decoded["jti"],
        "application_id": decoded.get("application_id"),
        "api_key": decoded.get("api_key"),
    }
