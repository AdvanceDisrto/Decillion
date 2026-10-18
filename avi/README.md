# i™ Artificial Verified Intelligence — Closed Domain Oracle
This branch tracks the runnable Node.js AVI oracle delivered in `iAVI_Truth_Oracle_Build.zip` in the build conversation. Local verified build: 10/10 tests PASS (Node 22).

## A-side / i-side
The A side proposes a claim. The i side runs explicit pinned rules, returns SUPPORTED_IN_DEFINED_SCOPE, REFUTED_IN_DEFINED_SCOPE or UNKNOWN, and generates SHA-256 + Ed25519 signed evidence receipts with rule-set version hash. Hardware attestation, ZKP, C2PA, live provenance validation, and independent certification are explicitly **NOT implemented**.

A signed record is not a universal truth guarantee; it is a claim about reproducible closed-domain evaluation and integrity. Production release requires persisted signing keys, append-only audited storage, source governance, authenticated access, and a deployed Node service. Do not merge this review branch until reviewed.

**No evidence, no verification. No defined standard, no certification. No authorization, no execution.**
