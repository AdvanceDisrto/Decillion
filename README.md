# Decillion Sovereign Storage

Decillion is a zero-trust encrypted object-storage and receipt-verification engine for human and AI workloads. It provides AES-256-GCM encryption, envelope key wrapping, signed receipts, Merkle aggregation, a FastAPI gateway, and license-gated Hugging Face model ingestion.

> **Scale statement:** a U.S. decillion is `10^33`. Storing one 32-byte receipt per operation would require `3.2 × 10^34` bytes: **32,000 quettabytes** before replication, indexes, and backups. Decillion therefore aggregates receipts into Merkle roots and supports retention policies; it does not claim that a single deployment physically stores a decillion receipts.

## Security model

- Every chunk receives a random 256-bit data-encryption key and 96-bit nonce.
- The data key is wrapped by a key-encryption key; plaintext keys never enter receipts.
- Object identity and ownership are bound as AES-GCM authenticated data.
- Receipts are Ed25519-signed and can be independently verified.
- Filesystem writes are atomic and content-addressed.
- Model weights and customer ciphertext are excluded from Git.
- Hardware attestation is represented by a deny-by-default interface. A production KMS/TEE provider must verify evidence before releasing a wrapped key.

The built-in local key provider is for development and single-node operation. Production deployments should implement `KeyProvider` using a cloud KMS, HSM, or attested enclave.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
export DECILLION_MASTER_KEY="$(python -m decillion.cli generate-master-key)"
uvicorn decillion.api:app --host 127.0.0.1 --port 8000
```

Upload and retrieve:

```bash
curl -H 'Authorization: Bearer development-token' \
  -F 'file=@README.md' \
  http://127.0.0.1:8000/v1/objects
```

Set `DECILLION_API_PRINCIPALS` to a JSON object mapping strong tokens to owner IDs before starting the API, for example `{"strong-token":"wallet-001"}`. The development token is accepted only when `DECILLION_ENV=development` and is bound to `development-owner`.

## Model registry and import

Model weights are never committed to this repository. The importer queries Hugging Face, records immutable metadata, checks a normalized license allowlist, and downloads only when `--include-weights` is explicitly supplied.

```bash
# Metadata only (safe default)
decillion-models discover --license mit --limit 100 --output var/catalog.json

# Explicit weight snapshot to an external volume
decillion-models mirror deepseek-ai/DeepSeek-R1 \
  --license mit --include-weights --destination /mnt/model-vault
```

Initialize the external destination first with `decillion-models vault-init --destination /mnt/model-vault`. The vault provides download locks, atomic publication, capacity enforcement, immutable revision directories, and full SHA-256 file inventories. Windows users can initialize the `E:` drive with `scripts/Initialize-WeightVault.ps1`. See [WEIGHT_VAULT.md](docs/WEIGHT_VAULT.md).

“Open weight” is not synonymous with MIT. Apache-2.0, Llama Community, modified MIT, research-only, and custom licenses require their own policy decision. The importer fails closed on missing or mismatched license metadata.

## Encrypted sharded weight vault

The external-drive vault accepts `.safetensors`, `.pt`, and `.bin` files. It splits them into 1 MiB shards, encrypts every shard with AES-256-GCM and fresh nonces, wraps the model DEK under a passphrase-derived vault key, and stores ciphertext by SHA-256. A Merkle root identifies the encrypted shard set. No plaintext DEK is returned, logged, or placed in a manifest.

```bash
export IZETTA_VAULT_PASSPHRASE='use-a-long-unique-secret'
decillion-vault init --vault /mnt/external/decillion-vault
decillion-vault add --vault /mnt/external/decillion-vault \
  --file /mnt/downloads/model.safetensors \
  --model-id org/model --source hf:org/model --license Apache-2.0
decillion-vault verify --vault /mnt/external/decillion-vault
decillion-vault smoke --vault /mnt/external/vault-smoke
```

`uvicorn vault.server:app --host 127.0.0.1 --port 8100` exposes signed, ACL-controlled shard reads. Set `IZETTA_VAULT` to the drive path first. Keep the default loopback bind unless the service is placed behind TLS, a VPN, or another authenticated encrypted tunnel.

## Telepath peer transfer

Telepath moves real plaintext shards between authorized peers after opening a signed, model-bound, TTL- and budget-limited session. It includes replay prevention, a size-bounded RAM cache, tier accounting, peer observations, transfer receipts, and whole-file SHA-256 verification after atomic reassembly.

```bash
# End-to-end local TCP test; no GPU or cloud account required
decillion-telepath vault-smoke --workdir /mnt/external/telepath-smoke

# Vault host (Pi or PC)
decillion-telepath serve --host 127.0.0.1 --port 7788 \
  --name vault-node --vault /mnt/external/decillion-vault

# Authorized peer
decillion-telepath pull-model --peer-host 127.0.0.1 --peer-port 7788 \
  --model-id org/model --dest /mnt/external/pulled
```

Ed25519 authenticates messages but does not encrypt the TCP payload. Plain TCP is appropriate only on loopback or an already encrypted trusted network. For two-machine operation, use TLS termination, WireGuard, or an equivalent encrypted tunnel. This repository contains no Vercel configuration and performs no cloud deployment.

The optional `decillion-accelerators` command detects CUDA, MPS, DirectML, TPU, and CPU at runtime. PyTorch is not a required dependency; CPU remains available on a Pi or PC without a GPU.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/smoke.py
python scripts/smoke_vault.py
python scripts/verify_repo.py
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md), [SECURITY.md](SECURITY.md), and the [operations guide](docs/OPERATIONS.md).

## Status

This repository contains a tested single-node reference implementation and extension interfaces. Multi-region consensus, a live Solana program, production KMS integration, FUSE/Dokan mounts, and audited TEE attestation are tracked as deployment milestones and are not falsely represented as complete.

## License

Apache-2.0. Imported model artifacts retain their original licenses and are not relicensed by Decillion.
