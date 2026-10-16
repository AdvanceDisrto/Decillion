# i™-Silo-1 VPU — ISA draft 0.1 (architecture proposal)

**Status:** specification only; not a fabricated device, verified silicon, implemented kernel driver, or cryptographic proof system.

## Register model

- `R0..R15`: 64-bit general control registers.
- `T0..T7`: logical tensor descriptors (base address, shape, stride, dtype, bounds).
- `S0..S3`: isolated logical weight-slot handles; no user-mode raw key or physical-address exposure.
- `C0`: capability descriptor and revision.
- `C1`: monotonic sequence counter.
- `C2`: last completed receipt digest.
- `C3`: execution error/status.
- `C4`: firmware measurement and attestation certificate reference.

## 32-bit instruction envelope (proposed)

```text
31..26 opcode | 25..22 destination | 21..18 source A | 17..14 source B | 13..0 immediate
```

| Opcode | Mnemonic | Semantics |
|---|---|---|
| 0x00 | NOP | No state change |
| 0x01 | CAP | Query device capabilities and firmware measurement |
| 0x02 | BIND | Bind checked tensor descriptor to a bounded slot |
| 0x03 | LOADW | Load signed/hashed model page into protected weight slot |
| 0x04 | SEALW | Seal weight-slot generation for execution |
| 0x08 | MATMUL | Deterministic fixed-point tile multiply under declared rounding mode |
| 0x09 | ACT | Activation with specified numeric semantics |
| 0x0A | ATTEND | Attention tile operation |
| 0x10 | HASH | Cryptographic digest of canonical execution manifest |
| 0x11 | STAMP | Request signature of digest using non-exportable provisioned key |
| 0x12 | COMMIT | Atomically publish output only if manifest/receipt completion succeeded |
| 0x13 | CHECK | Validate sequence, manifest hash and device state |
| 0x1F | FENCE | Enforce ordering between tensor execution and receipt DMA |

**Critical constraints:** real SHA-256 or equivalent is required; XOR is not a hash. Cryptographic signing needs an audited cryptographic IP block, secure key provisioning and measured boot. Fixed-point determinism is not a proof of semantic truth or hallucination prevention. A secure signature does not prove the arithmetic was performed correctly without a separately verified execution mechanism.

## SOURCECHAIN inter-node protocol proposal

`NodeHello(node_id, cert_chain, firmware_measurement, supported_isa, nonce)` →
`Lease(node_id, workload_digest, expiry, nonce)` →
`ExecutionReceipt(node_id, lease_id, seq, parent_hash, input_digest, model_digest, output_digest, signature)` →
`WitnessAck(ledger_height, receipt_digest, witness_signature)`.

A receiver must verify certificate chains, signed workload and firmware measurements, sequence monotonicity, lease expiry, nonce freshness, input/model/output digest format, and signature before acknowledging. Disconnected nodes append locally and replay in order after reconnection. Network-wide finality is **not** implemented by the local SQLite ledger.

## Physical attack model and mitigations

Threats include invasive probing, fault injection, voltage/clock glitching, side-channel analysis, malicious firmware and rollback. Candidate mitigations: secure boot, encrypted authenticated weight storage, key isolation, anti-rollback counters, active shields, tamper sensors, constant-time signing, zeroization and independent side-channel testing. These are design requirements, not measured security claims. One-time fuse locking should not be used for ordinary model updates; use versioned encrypted slots with authenticated re-provisioning and rollback prevention.

## Linux driver contract (future)

Prefer a standard kernel driver with `/dev/im_vpu0`, bounded `ioctl` requests and DMA/IOMMU mappings. Never assume a fixed physical MMIO address, expose raw key registers, spin indefinitely without timeout, or mmap arbitrary registers from untrusted user space. Device-tree/PCI enumeration, interrupt handling, memory barriers, safe teardown and privilege separation must be defined before any physical deployment.
