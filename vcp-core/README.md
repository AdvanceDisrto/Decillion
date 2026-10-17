# i™ VCP Core — policy-bounded cryptographic verification

A concrete first step toward the 100-point VCP architecture. These are **not** 100 completed controls and this does **not** certify absolute truth. The current verifier evaluates bounded arithmetic claims, maintains a local hash-chained event log, signs passing records with Ed25519 and rejects action requests without independently scoped authorization.

## Run

With Python 3.11+:

```sh
python -m pip install 'cryptography>=43,<47'
cd vcp-core
python -m unittest -v
```

Do not check private signing keys into GitHub. For production use, provision key custody through KMS/HSM, identity-bound issuers, an append-only external witness, key rotation/revocation, durable concurrency-safe storage, benchmarked validators and versioned certification policies.

## Critical semantics

- VERIFIED means only that the given expression was checked under the specified policy. It is **not** a fact about the wider world.
- The audit log is *tamper-evident*, not immutable: a privileged operator could rewrite a file. Anchor heads externally to strengthen independent verification.
- An arithmetic verification receipt **cannot** authorize deployment, transfers, physical actuation, or any other operation.
- This deliberately does not produce CERTIFIED receipts until issuer governance, policy conformance and external validation exist.
- Future independent verifiers: formal proof checkers, evaluation harness, source provenance checks, explicit uncertainty classification, artifact attestations.
- Visualization is a view of records, never a source of truth. UI colors must be mapped to verified engine statuses, not invented percentages.

## Agent disciplines

Verifier Agent: normalize claims and submit to deterministic or controlled checks.
Provenance Agent: collect evidence and verify source identity and time scope.
Critic Agent: independently challenge verdicts and flag contradictions, avoiding blind consensus.
Policy Agent: apply a versioned certification standard without self-authorization.
Ledger Agent: sign and export evidence and maintain audited key custody.
Security Agent: attempt bypass, tamper, replay, and unauthorized action tests.
Spatial Agent: project signed states faithfully; never promote visualization to a certificate.
Evaluator Agent: reproduce tests against known-good and adversarial model outputs.

Claims unsupported by an appropriate method must remain INCONCLUSIVE. There is no fixed notion of 100% truth, universal consensus or instantaneous global synchronization.

## Phone-first Semantic Isometry interface

From the `vcp-core` directory:

```sh
python mobile_server.py
```

Open `http://127.0.0.1:8795` **on the same device running the Python server**. This localhost-only implementation intentionally cannot be accessed from another phone across a network.

The **Check** action uses a finite curated evidence registry (currently Mars moon count and Napoleon death year) without any model or external network request. It returns `REFERENCE_CONSISTENT`, `REFERENCE_CONTRADICTED`, or `INCONCLUSIVE`, **never CERTIFIED**.

To enable **Ask model**, provide server-side environment variables, never paste an API key into the page:

```sh
export VCP_MODEL_BASE_URL="https://openrouter.ai/api/v1"
export VCP_MODEL_API_KEY="<private-provider-key>"
export VCP_ALLOWED_MODELS="<authorized-exact-model-id>"
python mobile_server.py
```

An authorized OpenAI-compatible gateway returns only a **proposed** structured claim. The curated registry then compares the proposition against supported values. A model-generated answer cannot approve itself. No provider calls are made unless `/model` is intentionally requested. Model calls may incur costs.

The HTML canvas illustrates the recorded status; it does not fabricate 70% pass rates or 100% truth. The output may be downloaded as JSON evidence. This HTML is a 2D spatial lattice preview, **not** a hardware hologram or a Three.js 3D scene. The prior standalone 3D MVP is separate.

On iPhone, a-Shell/iSH environment compatibility with this standard-library server depends on app restrictions; if localhost service execution is unsupported there, use a supported Python host. Native iOS background hosting is not implied.

Security: this is a **local development server**. It has no user authentication or rate limits and must not be publicly exposed. A later production gateway needs identity, key custody, per-user quotas, provider domain allowlists, durable auditable provenance and a separate certification authority.
