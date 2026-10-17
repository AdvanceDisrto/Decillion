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
