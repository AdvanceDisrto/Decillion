# i™ iSoftwareHardware (iSWH) 1.0 — Safe Device Standard / SLP-1.0 proposal

**Status: engineering proposal and software testbed; no silicon fabricated or vendor firmware modified.**

## Four initialization gates

1. **Hardware identity:** read and compare device identity against a separately approved inventory. Production: cryptographic TPM quote or manufacturer-backed attestation; never infer security merely from a self-reported string.
2. **Verifier integrity:** compare measured, signed firmware and VCP code identity with an administrator-signed approved manifest. Development version validates pinned SHA-256 digests only.
3. **Temporal and evidence readiness:** establish a trusted clock source and verify the audit store and local evidence registry. When offline, mark clock certainty explicitly, never invent a synchronized time.
4. **Independent control plane:** verification, model inference, independent certificate issuance, and action authorization must have separate principals. An LLM cannot hold an ICE signing key.

`iswh_boot.py` exposes an offline, non-destructive assessment with **READY_FOR_SCOPED_CHECKS** or **DENIED**; its current manifest is supplied by the caller, so this is **not** true secure measured boot. Build production attestation adapters for each vendor/hardware trust anchor and an operator-controlled root.

## SLP-1.0 compatibility protocol (proposed)

- Treat hardware through explicit backends (CPU, GPU, NPU, FPGA), each with unit tests and resource telemetry. Hardware differences remain real; vendor constraints are not erased.
- Inventory physical device, driver, firmware, acceleration, thermal limits, available memory, chip interconnect and model format support.
- Never erase BIOS, microcode, Apple secure firmware, NVIDIA firmware, or DRM. Unauthorized flashing is destructive and can disable hardware or invalidate critical security mechanisms. Provide only vendor-supported, reversible configuration workflows after explicit device approval and backups.
- Pin model weights/checksums, code signatures and verifiable build manifests. Keep vendor licenses, export controls and compatibility requirements visible.
- Off-grid inference requires power, storage, validated local data, running model weights and explicit provenance; it cannot validate newly occurring external events without evidence.
- Never claim that mirror tensors multiply physical compute bandwidth by 2.5× without independent benchmarks; negating a coordinate vector does not create more ALUs or RAM bandwidth.
- Never treat center-of-mass normalization as a proof of factual truth. A geometrically centered false assertion is still false.

## Physical hardware acceptance work

Before calling an iSWH device manufactured: produce schematics, BOM, PCBs, verified RTL, simulation reports, FPGA prototype, physical measurements, thermal and electromagnetic compliance, independent firmware signing, secure boot chain and prototype test reports. For Telepath waterless cooling, collect reproducible thermal results under full load. An iPhone cannot be modified into an ASIC simply by installing an app.

## Linux host and iPhone integration gates

- Implement trusted hardware attestation capture and verification using real TPM/Secure Enclave APIs, not caller-injected digest strings.
- Configure Tailscale or Cloudflare Zero Trust private routing. Check device posture and mutually authenticated service identities before accessing the model server.
- Provision physically inventoried GPU/CPU machines before claiming 8xH200 performance or 1T inference.
- Subject model proposals to independently authenticated evidence checks and governed ICE policies.
- Test certificate signature, revocation, nonce replay, audit persistence, clock failure and fail-closed inference on actual devices.
- Keep the independent ICE service outside the generative model’s authority.

The result is a realistic, testable product path for i™ iSWH, not an unhackable or 100%-truth device.
