# i™ Proof of Process Hub — reference implementation

**We make specified AI processes inspectable and their checks verifiable.**

This review branch adds a portable reference for the five-artifact protocol:
(1) frozen claim contract, (2) attempt record, (3) UR-1 scoped receipt, (4) independently verifiable bundle, (5) hash-chained ledger entry.

No production backend, hardware PUF, Bitcoin anchor, general truth claim, or agent containment is asserted here. Signed receipts commit to exact evidence and contractual checks; they do not prove all underlying facts are true.

## Engineering gates

- Validate immutable claim ID/version and the frozen acceptance criteria.
- Reject incomplete evidence and unexecuted claims.
- Require independently registered reviewer signatures.
- Enforce budget, mandatory checks and blocking-issue policies.
- Use database uniqueness on claim/version for issuance.
- Preserve revocation and original evidence.
- Do not treat local file anchoring as external blockchain confirmation.
- Test tampering, replay, wrong signer, duplicate issuance and revocation.

## Local tests

The complete Python reference and its test suite are distributed as a separate review bundle for now; the repository-side workflow in this branch independently verifies the proof-contract fixture using the standard library.

**Compatibility note:** Existing CiH/iDome pages and APIs are unchanged. This is a proposed integration path, not a claim the website uses this engine yet.

## Public positioning

iNNOVULIS™ — Inspectable Processes. Verifiable Checks. 🧾
