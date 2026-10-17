# i™ ICE — Independent Certification Engine (development implementation)

This service is an **independently keyed attestation issuer**. Its only implemented standard, `ICE-01-EVIDENCE-INTEGRITY/1`, checks that **three distinct operator-trusted Ed25519 witness identities** signed fresh snapshots whose SHA-256 digests match the supplied text. It does **not** determine whether the claim is true, whether the sources agree, whether the signers are real-world independent, or whether the evidence was truthfully captured.

## Local testing

```bash
python -m pip install "fastapi>=0.115,<1" "uvicorn>=0.30" "cryptography>=43,<47"
cd vcp-core
python -m unittest -v test_independent_certifier.py
```

For local API testing, configure **separately provisioned** private issuer key, private operator token, and JSON trusted-witness public-key mapping via environment variables:

- `ICE_ISSUER_PRIVATE_KEY_B64` — raw 32-byte Ed25519 key, base64 encoded. Never expose to Buddy, the PWA or Git.
- `ICE_OPERATOR_TOKEN` — randomly generated secret, at least 32 characters. This is only a DEVELOPMENT machine-to-machine token; use an actual machine identity provider/mTLS and rotation in production.
- `ICE_TRUSTED_WITNESS_KEYS_JSON` — JSON object mapping distinct approved witness IDs to base64 raw Ed25519 public keys.

Then start:

```bash
uvicorn independent_certifier:app --host 127.0.0.1 --port 8796
```

`POST /certify` requires `Authorization: Bearer <operator-token>` and the package schema used in `test_independent_certifier.py`. `GET /health` reports readiness without disclosing keys. **Do not bind to public interfaces or deploy publicly** before adding issuer governance, durable append-only audit, quotas, nonce/replay checks, source registry authority and key rotation/revocation.

## Separation of powers

- **Buddy / proposer:** requests model outputs and evidence; has *no signing key*.
- **Witnesses:** sign bound snapshot digests and source identifiers; membership is determined by the ICE operator's trusted public-key registry, never by a client-supplied key.
- **ICE:** independently validates the exact byte-oriented submitted evidence and signs a certificate scoped to *evidence integrity only*.
- **Independent validator:** checks the issuer's Ed25519 public key signature on the canonical certificate payload.
- **Execution gate:** remains separate and does not honor evidence integrity certification as authorization to take actions.

What this does not do: certify universal truth, verify C2PA, establish facts with three URLs, pin data to IPFS, create blockchain immutability, establish independent trust organizations or issue legally accredited certificates. Cryptographic signatures do not establish factual truth. Stronger factual certifications will require versioned domain standards and genuinely independent primary-source examination.

No existing authentication, database, Render deployment, or main branch is replaced by this experimental service.
