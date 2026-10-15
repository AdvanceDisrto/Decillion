# Buddy AI backend — gated production integration
This service is NOT live until secrets, a reachable model adapter and an active Supabase project are configured.
Requires SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_JWKS_URL, RECEIPT_SIGNING_PRIVATE_KEY_PEM, BUDDY_MODEL_URL, BUDDY_MODEL_TOKEN, PUBLIC_ORIGIN.
Model adapter contract: POST {message,user_id} with Bearer token -> JSON {answer:string}. Use an approved private adapter, never expose provider keys to browser.
POST /v1/actions requires valid Supabase signed-in JWT. On success it stores append-only user-owned receipt in Supabase RLS table. If persistence fails, API returns error instead of claiming completion; upstream model may already have responded.
Receipt signs SHA256 of canonical JSON with Ed25519; verify using returned public key only after validating it against a separately trusted published signing-key registry. This is not proof of physical-world truth.
Cross-device sync requires the same Supabase authenticated account on each device; GET /v1/receipts lists its latest 100 receipts.
IMPORTANT: Supabase BUDDY project was INACTIVE on 2026-10-15. No migration applied.
Run locally: pip install -r requirements.txt; uvicorn main:app --host 127.0.0.1 --port 8000.
Do not route igptm.com until existing homepage has been archived and rollback tested.
