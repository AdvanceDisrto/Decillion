# iModels native inference gateway

This is an **inference router**, not a training run or published native model checkpoint. It can call an existing private self-hosted model through the OpenAI-compatible chat completions API (for example, vLLM or an equivalent serving runtime).

Render service: https://i-the-one-buddy-api.onrender.com
Current service auto-deploy branch: feature/buddy-receipts-backend-20261015.

## Runtime configuration (Render, server-side only)

- `IMODELS_INFERENCE_BASE_URL`: trusted HTTPS URL ending in `/v1`. It must point at **your serving GPUs/model weights**, not Render's free web instance. Don't use localhost unless the inference runtime actually shares the Render host (not configured here).
- `IMODELS_INFERENCE_API_KEY`: private inference bearer token (optional only if the endpoint is protected by another mechanism).
- `IMODELS_BUDDY_MODEL_ID`: *actual served model ID* for Buddy.
- `IMODELS_THE_ONE_MODEL_ID`: *actual served model ID* for THE ONE.
- Existing `BUDDY_MODEL_URL` and `BUDDY_MODEL_TOKEN` remain as fallback for a compatible Buddy adapter.

Do **not** put these settings in `i-web/config.js` or commit keys to GitHub. Render's UI sets secrets on the service. Never expose a GPU inference port to the whole internet solely relying on vLLM API-key protection; secure the proxy and network too.

## Native model acceptance

1. Locate actual owned `.safetensors` / `.pt` weights and tokenizer + architecture configuration.
2. Match cryptographic hashes against authentic training receipts/manifests, verify complete shards.
3. Load the checkpoint into a GPU model-serving runtime and verify sample generation with a model ID.
4. Configure the HTTPS inference endpoint and secrets above.
5. Check `GET /v1/models` and `GET /v1/models/probe`. These check **configuration/reachability**, not training authenticity.
6. Sign in from the i™ PWA, call `POST /v1/models/buddy/generate` or `POST /v1/models/the-one/generate` (JSON: `{"request":"Hello"}`), and verify the returned signed execution receipt. This route requires valid Supabase auth, DB connectivity and Ed25519 signing config.

If no GPU endpoint and loaded checkpoint are available, the server returns a transparent availability error. A historical training manifest, an owned GitHub repository, a large stated parameter count, and a web UI are **not** by themselves proof of a loaded production model.

## What is currently not certified

No physical weight files or complete model load/evaluation have been independently checked by this adapter. Its `weights_verified:false` and `inference_verified:false` fields are intentional until a separate evidence validation and sample generation is run. The generated Buddy GLB is a graphics model, **not** an LLM or ML checkpoint.
