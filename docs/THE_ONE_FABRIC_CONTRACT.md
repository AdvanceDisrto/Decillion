# THE ONE ↔ Decillion integration contract (proposed)

THE ONE owns model selection, inference adapters, task policy, and latency measurements. Decillion owns encrypted objects, keys, signed receipts, and their verification. THE ONE's existing `decillion_bridge.verify_model_receipt` must verify a receipt using a caller-trusted Ed25519 public key and bind expected owner/object ID before constructing `VerifiedModel`. A receipt alone does **not** establish model license, weight revision, deployment authorization, or execution safety: enforce those separately before registering a route.

The optional `IntelligenceFabric` module in THE ONE accepts only explicitly registered `VerifiedModel` routes and invokes exactly one adapter per request. It never fetches weights, decrypts objects, calls an external provider, or stores prompt contents in its returned routing metadata. This is deterministic priority routing, **not** learned routing or a speed benchmark. Inference adapter output remains user content and may contain sensitive data; do not persist it in receipts without an explicit privacy policy.

Integration smoke acceptance: (1) verify a genuine Decillion receipt with a trusted public key; (2) register a verified model and a test adapter; (3) invoke one task; (4) confirm the selected model/object/receipt digest; (5) reject missing or invalid receipts, unsupported tasks, unavailable backends and unauthorized weights; (6) test license and immutable weight revision separately. These are proposed cross-repo checks; the standalone router unit tests do not prove the full acceptance gate.

No modifications to Decillion encryption, receipt formats, key provider, Telepath, or vault are required for this contract.
