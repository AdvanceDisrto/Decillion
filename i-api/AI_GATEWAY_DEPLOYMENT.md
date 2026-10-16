# i™ Universal AI Gateway — Deployment & Acceptance (2026-10-16)

## What is deployed
FastAPI routes mounted in `i-api/main.py`:
- `GET /v1/gateway/status`: non-secret adapter configuration and feature gates.
- `POST /v1/gateway/chat`: authenticated server-side model dispatch, bounded prompts, protected in-memory threads and SHA-256 evidence.
- `POST /v1/gateway/stream`: authenticated SSE *buffered response* chunks after upstream completion. Not token-level upstream streaming yet.
- `GET /v1/gateway/threads` and `/usage`: authenticated principal-isolated, **volatile** runtime views.
- `POST /v1/gateway/keys/issue`: optional 15-minute signed, scoped **i™ virtual API token**. Issuer first authenticates a real account token; `I_GATEWAY_TOKEN_SECRET` must be at least 32 characters. These tokens do not generate other companies' API keys and are **not MPC key shards**.
- `GET /v1/gateway/keys/status`: metadata only, never credentials.
- `POST /v1/gateway/agents/demo`: real deterministic local planner/validator/boundary *software test*. No OpenAI/Anthropic/KRDiD model is invoked. Its receipt correctly says not certified.
- `GET /v1/gateway/invoice-preview`: reports unbilled readiness only, no debits or invoices.
- `i-web/ai-gateway.js`: UI tab invoking this API through the existing i™ account auth closure (never returns bearer token to widgets).

## Authentication
The API's existing `main.user_id` verifies Supabase bearer JWTs, issuer and signature. In the current implementation, this requires Supabase auth/storage/signing configuration. **Do not trust a request-body user ID or plan.** Server chooses tier from verified UID against configured allowlists. Signed virtual tokens can be used only for `gateway:chat`, expire in 15 minutes, and are scoped to the verified UID.

## Configuration in Render service environment (never check secrets into GitHub)
Required for existing Supabase session authentication (see `i-api/main.py`):
- `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWKS_URL`, `RECEIPT_SIGNING_PRIVATE_KEY_PEM`.
- Web origin `PUBLIC_ORIGIN=https://i-the-one-buddy-preview.onrender.com`.
- Set `i-web/config.js` **public** Supabase project URL + publishable key to actually enable UI sign-in; no service-role key in browser.

Free users: `IAPI_APACHE2_BASE_URL` (authorized reachable **HTTPS** endpoint), `IAPI_APACHE2_API_KEY`, `IAPI_APACHE2_MODEL_ID`, `IAPI_APACHE2_LICENSE_SPDX=Apache-2.0`, and **real verified** checkpoint revision SHA `IAPI_APACHE2_MODEL_REVISION_SHA` (64 hex). This is only an *operator declaration* until independently checked against source weights and NOTICE.

Optional paid cloud adapters (all explicitly OFF by default):
- `I_GATEWAY_PAID_ENABLED=true`
- `I_GATEWAY_PAID_USER_IDS=<comma-separated verified UID allowlist>` ; `I_GATEWAY_ENTERPRISE_USER_IDS=<comma-separated verified UID allowlist>`
- OpenAI: `OPENAI_API_KEY`, `IAPI_OPENAI_MODEL_ID`
- Anthropic: `ANTHROPIC_API_KEY`, `IAPI_ANTHROPIC_MODEL_ID`
- DeepSeek: `DEEPSEEK_API_KEY`, `IAPI_DEEPSEEK_MODEL_ID`
- Google Gemini OpenAI-compatible gateway: `GOOGLE_API_KEY`, `IAPI_GOOGLE_MODEL_ID`
- Mistral: `MISTRAL_API_KEY`, `IAPI_MISTRAL_MODEL_ID`
- Cohere: `COHERE_API_KEY`, `IAPI_COHERE_MODEL_ID`
- **For each enabled paid provider**: operator-configured conservative cost bounds `I_GATEWAY_<PROVIDER>_INPUT_COST_PER_1K` and `I_GATEWAY_<PROVIDER>_OUTPUT_COST_PER_1K`; missing price bounds reject requests. These are **not** independently verified live price feeds.
- Optional short-lived app token minting: `I_GATEWAY_TOKEN_SECRET=<32+ random characters>` supplied through Render secret settings. Rotate it under an explicit revocation plan. No MPC hardware, threshold signing or key shares are implemented.

Do not store provider secrets in the PWA, browser localStorage, commit history, receipts, telemetry, or response metadata. Paid provider use incurs real third-party cost. The gateway makes no third-party charges while provider integration is disabled.

## API examples (PowerShell)
```powershell
$Base = "https://i-the-one-buddy-api.onrender.com"
Invoke-RestMethod "$Base/v1/gateway/status" | ConvertTo-Json -Depth 8

# Requires a *real* verified account access token. Never share it in chat.
$Token = Read-Host "i account access token" -AsSecureString
$Bearer = [System.Net.NetworkCredential]::new("",$Token).Password
$Headers = @{ Authorization = "Bearer $Bearer" }
$Request = @{ message = "Explain Merkle roots"; max_tokens = 300; max_cost_usd = 1 } | ConvertTo-Json
Invoke-RestMethod "$Base/v1/gateway/chat" -Method Post -Headers $Headers -ContentType "application/json" -Body $Request
Remove-Variable Bearer,Headers,Token
```

## Production gaps (no false certification)
1. **Credentials and model weights**: no keys or licenses are verified by a placeholder variable. All paid cloud models off until operator config and explicit user plan authorization.
2. **Pricing and billing**: conservative operator price ceilings; no authoritative tariff refresh, token-funded wallet deduction, invoice settlement, tax, or Stripe integration. `actual_bill_usd` remains null.
3. **Persistence**: threads and usage are process memory only; cold restart/redeployment and multi-replica do **not** preserve sessions. Requires database with row-level isolation.
4. **Streaming**: SSE output is buffered (response computed upstream before chunks). True provider incremental streaming is a next integration gate.
5. **Audit**: provider-reported model ID is a claim, not an attested execution identity. SHA-256 receipt is not an immutable external ledger anchor or Ed25519 signature.
6. **MPC**: signed virtual proxy bearer tokens are real cryptographic tokens, but actual threshold/MPC sharding is **not** implemented.
7. **KRDiD**: identity explanation should follow deterministic signature verification; it must not authorize claims or access.
8. **Carrier/Android/iOS**: the gateway uses HTTPS API calls; mobile OS APIs, VPU MMIO, RF hardware and offline mesh are separate independently tested systems.
9. **Legal**: patents, software licenses and terms of API redistribution require review; do not assume a patent claim is valid or covers an integration.

## CI
`python -m unittest -v test_ai_gateway.py` from `i-api/`. Github `Buddy Universal API Live Integration` runs this and the existing backend tests and Docker smoke. Production model calls require authorized live keys and separate canary tests.

No merge to main and no deletion; preview deployment only.
