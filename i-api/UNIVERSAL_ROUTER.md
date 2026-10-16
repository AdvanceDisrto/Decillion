# Apache-2.0-only live iModels policy

**Exclusive allowed inference provider**: separately hosted Apache-2.0-licensed model through the OpenAI-compatible endpoint. The previous commercial, Hugging Face and MIT adapters remain visible in the provider registry for reference, but are disabled for inference by policy. Buddy, THE ONE, /v1/actions and /v1/universal/chat all obey the gate.

**Render server environment configuration** (private; never in PWA or GitHub):

- IAPI_APACHE2_BASE_URL: HTTPS model server base URL ending /v1.
- IAPI_APACHE2_API_KEY: inference-service bearer credential.
- IAPI_APACHE2_MODEL_ID: exact served model ID.
- IAPI_APACHE2_LICENSE_SPDX: Apache-2.0.
- IAPI_APACHE2_MODEL_REVISION_SHA: full 64-character lowercase SHA-256 from a genuine model source revision/manifest record.

This is an *operator declaration*, not automatic license authentication or independent verification of checkpoint weights. Before accepting the source, audit its exact model card, weight license, dependencies, tokenizer license and provenance; a GitHub project licensed Apache-2.0 does not necessarily license downloaded model weights identically.

**Acceptance**: GET /v1/universal/providers shows apache2 route configured only when endpoint + keys + license declaration are provided. An authenticated POST /v1/universal/chat should return actual generated text; GET /v1/models/probe reports configuration not independent inference verification. Signing and persistence still require Supabase configuration and an Ed25519 private signing key.

**Privacy and safety**: don't put provider keys into frontend credential fields. Render's service environment editor is the credentials configuration matrix. The Web Bluetooth API does not imply paired devices, and PWAs cannot directly invoke Wi-Fi Direct radio discovery. iMirror is a browser-level dual-plane observation, optional local camera preview, and in-memory fault simulation, not cloud state recovery or signed hardware certification.

**No main merge** without explicit approval.
