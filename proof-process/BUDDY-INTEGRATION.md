# Buddy backend integration (review only)

Routes: GET /health, POST /v1/proofs/submit, POST /v1/proofs/verify, GET /v1/proofs/{claim_id}/{version}.

Buddy must use its **server-side identity**, not an exposed browser token. Set BUDDY_API_TOKEN on backend and Buddy internal service; BUDDY_SIGNER_KEY_FILE points to a persistent protected 32-byte Ed25519 seed file (never in Git or a frontend); BUDDY_PROOF_DB points to a persistent SQLite file; BUDDY_REVIEWER_KEYS_JSON names independently registered review keys.

This reference is **not production hardened**. Public release is blocked until: audited issuer custody in KMS/HSM; reviewer approval identity authorization; durable audited DB and backups; per-tenant authorization; rate limiting; independent monitoring and external anchoring; signed revocation proofs; and end-to-end deployed HTTP smoke checks.

The reviewer signs canonical JSON of {"contract": contract, "attempt": attempt}; the reviewer private key is never possessed by Buddy or a generating head. A UR-1 certifies the declared checks, not universal factual truth. SHA-256 chaining is tamper-evident, not automatically permanent; public blockchain anchoring is not implemented.
