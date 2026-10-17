# i™ Sovereign iMobile/ICE compute fabric — implementation and procurement gate

**Target, not deployed hardware**: iPhone 17 Pro Max cockpit → Cloudflare One Client (WireGuard/MASQUE) → Cloudflare Zero Trust private application route / Cloudflare Tunnel → local inference API and independent ICE service → separately administered GPU cluster. Private networks should use Cloudflare private routing policy or Mesh where bidirectional site-to-site access is required, not assume that an SSH/WebSocket connection transports an entire Ethernet switch.

## Security zones

1. iPhone Buddy/iMobile: UI and client-side small model inference (optional), no certifier private keys, no direct 100GbE connection.
2. Cloudflare Access / device posture: identity-aware route for API, no unrestricted exposed SSH to GPUs, TLS/mTLS inside trusted boundary as applicable.
3. App API zone: Buddy, model-gateway, VCP proposer, read-only audit viewer; user JWT verification and quotas.
4. Verification zone: deterministic evaluators, witness collectors, vetted source snapshots, strict outbound allowlists.
5. ICE authorization zone: independent issuer process, operator identity, persistent audit, replay nonce database, trusted witness keyring, revocation.
6. GPU node zone: model inference endpoints with no authorization to issue ICE certificates. No GPU is required for deterministic VCP/ICE.
7. Inter-node data plane: separately designed 100GbE QSFP28 switches, matching NICs/DACs/optics and VLAN/network policy; 100Gbps is a link capacity, not an achieved end-to-end mobile bandwidth.

## Hardware corrections and requirements

- 8 × H200 **SXM** with 141GB each gives 1,128 GB nominal device memory (roughly 1.1TB) across GPUs. **Not** a single contiguous 1.1TB GPU address space. Tensor/model parallel software, KV cache, runtime buffers and pipeline network overhead must be budgeted.
- NVIDIA H200 SXM specification lists 4.8TB/s **per GPU HBM memory bandwidth**, not NVLink interconnect speed. NVLink rated up to 900GB/s per GPU.
- An HGX H200 8-GPU NVSwitch/SXM system is a purpose-built certified chassis/system. **Two 4-PCIe-slot AMD EPYC servers cannot be assumed to provide an HGX-style common NVLink fabric.** H200 NVL PCIe arrangements differ from HGX H200 SXM.
- A 1T-parameter FP8 weight matrix alone occupies approximately **1TB decimal** before quantization metadata, activations, expert routing, scratch buffers and KV cache. Capacity sufficiency depends on the exact dense/MoE architecture and distribution.
- Power, cooling (Telepath waterless cooling concept requires measured thermal validation), rack airflow, power supply, circuit design, networking, physical access and warranty compatibility remain procurement gates. No 8x H200 hardware was purchased or installed in this implementation.

## Model lanes

- Device local, offline: distinct writing and code reasoning models if independently compatible and licensed. GGUF model files need model-specific context/quantization compatibility and thermal/battery profiling; never guarantee token/s or total memory from file size alone. Local inference does not grant factual authority.
- Remote optional: on-prem model gateway, internet cloud model provider only when operator enables it.
- Deterministic local verification: arithmetic/formal methods and authenticated evidence checks. **LLM prompting never constitutes an independent certification authority.**
- ICE signing: isolated and governed. Prefer managed KMS/HSM over exporting raw signing material; test release uses environment provisioned Ed25519 as an explicitly weaker development-only substitute.

## Operational test plan

1. PWA/iOS authenticated user-to-Buddy call tested on actual iPhone hardware.
2. iPhone Cloudflare private route + authenticated remote API tested from cellular and Wi-Fi separately.
3. Local model loaded from verified GGUF manifest, with CPU/GPU memory, tokens/s, latency, temperature and battery logs.
4. Multi-node inference checked under partial network failures, including unauthorized requests and model fallback.
5. Source collection: signed witness snapshots, independent signer vetting, provenance integrity, source diversity and time windows.
6. ICE: key isolation, revoked certificates, replayed nonces, audit tampering and independent signature verification.
7. Storage recovery/backup: SQLite development audit is **not** an immutable globally witnessed ledger; external anchoring and disaster recovery are future acceptance requirements.

## Local Windows PowerShell validation

```powershell
git clone --branch feature/buddy-receipts-backend-20261015 https://github.com/AdvanceDisrto/Decillion.git
Set-Location .\Decillion\vcp-core
py -m pip install 'cryptography>=43,<47' 'fastapi>=0.115,<1'
py -m unittest -v
```

**Production prohibition**: do not publicly deploy ICE until operator identity, separate custody, external audit witness, source network egress controls, quotas and recovery have been independently assessed. Do not describe internal attestations as established third-party certification.
