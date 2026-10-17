# i™ THE ONE / Sovereign compute operator runbook

Includes a **development-only** Open WebUI interface and a separately isolated independent certification engine. This is **not** a 1T/H200 deployment and no local GPUs are automatically provisioned.

## Security architecture

iPhone → authenticated private network (WireGuard/Tailscale or Cloudflare Zero Trust) → Open WebUI user session → optional private vLLM proposal endpoint.

ICE is on a *different internal-only Docker network*, has separate signing-key custody, and can only be reached through its localhost-bound port by the operator. The model-proposal Pipe does **not** submit an ICE certification request or have an issuer signing key. Never configure Open WebUI on a public interface without reverse-proxy identity, HTTPS, session hardening and host-firewall rules.

The model response is always **NOT VERIFIED / NOT CERTIFIED**, even if it sounds confident. The ICE service remains governed by signed witness packages, evidence-integrity standard, revocation, and audit records. The new Pipe deliberately does not pretend to have independently verified inference.

## Start locally on a Linux Docker host

1. Provision independent issuer and witness keys under an operator-controlled secret manager. Never reuse the Proposer's model keys as issuer keys. Do not paste secrets into web chat, GitHub, or the iPhone application.
2. Create a local `.env` based on `sovereign.env.example`; its placeholder values must be replaced with actual, separately generated secrets. Never commit it.
3. In `vcp-core`, run:

```sh
docker compose -f compose.sovereign.yml config --quiet
docker compose -f compose.sovereign.yml up -d --build
docker compose -f compose.sovereign.yml ps
curl -fsS http://127.0.0.1:8796/health
```

4. Open `http://127.0.0.1:3000` on the **Docker host**; set up an Open WebUI account. To access from iPhone, use a **private, authenticated** tunnel or reverse proxy; localhost on the phone itself will not reach the Linux host.
5. As an Open WebUI **administrator**, inspect `openwebui_pipe.py`, add it under Functions → Create New → Pipe. Configure admin Valves: `VLLM_URL` for your already running **private** vLLM service, `MODEL_ID` for the exact served ID and `VLLM_API_KEY` for its real API token. Only the hostname allowlist in the Pipe is accepted. Do not install unknown executable Pipe source.
6. The openwebui image uses a moving `main` tag for exploratory use; **pin a reviewed immutable digest before production**.
7. Keep vLLM private and separately authenticated. Official server examples can vary by specific transformer architecture. Do not assume `deepseek-ai/DeepSeek-V3-1T` is a real model ID. Check the exact model repository, licenses, available GPUs, quantization, topology, and memory headroom before launch. The existing 8×H200 proposal is **not** proof that such hardware is installed.
8. Audit backups: externalize the SQLite database hash-chain head to an independent witness; run backup, restore and replay tests. A local hash chain is not immutable.

## Real-world acceptance gates

- [ ] An authenticated iPhone over private VPN accesses the UI without any public listener.
- [ ] A real private vLLM inference returns an unverified proposal.
- [ ] A live independently signed source package is sent to the isolated ICE through authorized service identity.
- [ ] The source package is accepted/rejected under a published standard.
- [ ] Signature verification and revocation are checked on another device.
- [ ] Audit restore/rollback and replay attacks are detected.
- [ ] 8×H200 or alternative GPU nodes physically inventoried and benchmarked.
- [ ] Explicitly measured per-model latency, throughput, context, GPU memory, thermals and link utilization.

Never claim local inference prevents hallucinations or guarantees medically safe advice. VCP/ICE permits only scoped conclusions under evidenced, tested policies.
