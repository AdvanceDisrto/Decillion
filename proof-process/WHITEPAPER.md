# iNNOVULIS™ — Proof of Process (Technical Position)

A user, model or agent submits an **AttemptRecord** against a **ClaimContract** established before execution. A separate reviewer verifies mandatory checks, evidence binding, permissions and costs. Only then may a scoped **UR-1** be issued once for each claim/version.

The five export artifacts are claim_contract.json, attempt_record.json, UR-1_certificate.json, itm_proof_bundle.json and anchorage_ledger.ndjson. Hash chains are tamper-evident only under appropriate independent retention assumptions. A digest is not an Ed25519 signature; a signature does not by itself prove factual truth or reviewer independence.

## Deployment boundary

Production requires identity and key custody separate from generators; durable transactional uniqueness; signed revocation events; an authenticated API and rate limits; observability; retained proof material; recovery testing; an external anchor verifier if blockchain attestation is advertised. Cloudflare Workers may serve a *preview* of the public verifier but must not imply its backend has deployed or signed real executions without evidence.

## Important corrections

Temperature zero does **not** guarantee deterministic LLM outputs. A JSON schema does **not** establish factual accuracy. PUF cannot be claimed without real measured hardware. A local timestamp does **not** prove a public chain anchor. A legal citation whitelist does **not** prove the citation is applicable or the legal conclusion sound. The sample entitlement/finance/medical/defense examples in old design documents are not autonomous authorizations.

The production contract is simple: **specified AI processes become inspectable; specified checks become independently verifiable**.
