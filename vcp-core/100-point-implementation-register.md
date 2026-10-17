# i™ VCP — 100-point specification implementation register

**Status:** design requirements only unless individually linked to passing evidence. **Nothing in this document constitutes certification.** The 100 points were provided as an aspirational specification, not measured acceptance results.

## Four architectural groups

| Group | Points | Implementation objective | Current verified status |
|---|---|---|---|
| A — Recursive topology | 1–25 | Isolated proposer/verifier, consistency critique, distributed evidence propagation | Local verification API boundary only; proposed network not implemented |
| B — Crucible | 26–50 | Defined checks per claim type, provenance, deterministic and formal evaluators | Bounded deterministic arithmetic in `vcp-core/vcp.py`; 90-check suite NOT implemented |
| C — Factual receipt | 51–75 | Signed, attributable, scope-limited certificates, append-only evidence | Ed25519 **VERIFIED** arithmetic receipts + local hash-chain; NOT globally immutable, accredited or externally witnessed |
| D — Spatial/Execution | 76–100 | Honest 3D views, native spatial interfaces, evidence-bound action enforcement | Action-denial guard in core; 3D hardware, AR, neural interfaces and global synchronization NOT implemented |

## Engineering specification replacements for non-testable absolutes

- **3 non-probabilistic meta-AI with infinite horizon:** a bounded deterministic rules engine + independently versioned evidence snapshots; disclose missing history.
- **8 instant global propagation:** eventual consistency with observable network partitions and maximum lag targets; never promise instantaneous universal propagation.
- **10 single unalterable meaning:** allow contested evidence, conflicting scopes, uncertainty and later corrections.
- **13 upward-only flow vs 9 feedback:** prohibit elevation without explicit revalidation, even when a proposal loops through stages.
- **19 infinite cache:** bounded storage with explicit TTL, provenance and invalidation.
- **26 90-Point Crash:** a 90-case machine-readable suite only when there are 90 independently specified checks, test fixtures, expected outcomes and coverage reports. Count is not evidence.
- **28 1000:1 compression:** measure compression separately; it cannot stand in for factual reliability.
- **29 physical constants for all text:** limit physical checking to claims for which quantities, units, reference frames and tolerances apply.
- **31 constrained decoding:** supplement with post-generation verifier, external checks and policy; constrained decoding alone cannot ensure truth.
- **33 century simulations:** mark as forecasts with models and uncertainty, never verified future facts.
- **42/60 quantum hash:** select a published, specified algorithm and implementation; no hash is "unhackable."
- **51/68/69/100 absolute truth:** certify *conformance to named tests*, not 100% truth, unanimity or perfect translation.
- **57 thousands of signatures:** no such endorsement is claimed unless actual distinct trusted signers and signatures are verified.
- **59 zero-knowledge:** requires a precise statement, circuit and proof/verification artifacts; privacy is not a substitute for truth.
- **66 block never erased:** record append-only/tamper evidence with defined storage availability and authority assumptions.
- **71 every-millisecond validation:** replace with event-driven/on-demand checks, revocation and validity windows.
- **84/85/93/97 hardware beam, ambient, zero latency, neural link:** hardware research and device validation, not deliverable through web UI alone.

## Roles (software agents, not independently qualified PhD personnel)

1. **Proposer** submits typed claims without rights to execute tools.
2. **Claim Normalizer** extracts atomic claims and tracks parse ambiguities.
3. **Domain Verifier** checks arithmetic, formal proofs, software execution or empirical measurements as appropriate.
4. **Provenance Analyst** validates evidence origins, C2PA where available, and timestamp scope.
5. **Adversarial Critic** tries counterexamples and reports method limitations.
6. **Consistency Auditor** flags contextual conflicts, preserves versioned revisions, never assumes old facts are eternally valid.
7. **Certification Authority** checks explicit policy/issuer authorization before issuing `CERTIFIED`.
8. **Ledger Custodian** signs and preserves evidence using controlled keys and externally witnessed append logs.
9. **Execution Guardian** separately verifies actor/action scope and authorization at the tool boundary.
10. **Spatial Renderer** displays actual signed results and distinguishes `VERIFIED`, `REJECTED` and `INCONCLUSIVE`.

## Release acceptance gates

- [x] Bounded deterministic arithmetic evaluation implemented.
- [x] Fail-closed unsigned/modified receipt validation implemented.
- [x] Local append-only hash-chain with tampering detection implemented.
- [x] Execution gate denies an arithmetic receipt as authority for transfers/deployments.
- [x] Automated adversarial unit tests passing in GitHub Actions.
- [ ] Real generative model proposer with independent structured outputs.
- [ ] Provenance retrieval adapters with reproducible source snapshots.
- [ ] Z3/Lean proof verification and controlled code execution.
- [ ] At least 90 independently tested and documented checks.
- [ ] Externally anchored, concurrency-safe ledger with signing-key governance.
- [ ] Authenticated, policy-scoped certification authority with revocation.
- [ ] Spatial UI connected to actual live verification events (not simulation).
- [ ] Independent model-provider evaluation and regression suite.
- [ ] Actual multi-node and hardware-in-the-loop acceptance.

**Operating principle:** NO EVIDENCE → INCONCLUSIVE; NO POLICY → NOT CERTIFIED; NO AUTHORIZATION → DENIED.
