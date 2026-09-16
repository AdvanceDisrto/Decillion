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
  -F 'file=@README.md' -F 'wallet=user-001' \
  http://127.0.0.1:8000/v1/objects
```

Set `DECILLION_API_TOKENS` to a comma-separated list of strong tokens before starting the API. The development token is accepted only when `DECILLION_ENV=development`.

## Model registry and import

Model weights are never committed to this repository. The importer queries Hugging Face, records immutable metadata, checks a normalized license allowlist, and downloads only when `--include-weights` is explicitly supplied.

```bash
# Metadata only (safe default)
decillion-models discover --license mit --limit 100 --output var/catalog.json

# Explicit weight snapshot to an external volume
decillion-models mirror deepseek-ai/DeepSeek-R1 \
  --license mit --include-weights --destination /mnt/model-vault
```

“Open weight” is not synonymous with MIT. Apache-2.0, Llama Community, modified MIT, research-only, and custom licenses require their own policy decision. The importer fails closed on missing or mismatched license metadata.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/smoke.py
python scripts/verify_repo.py
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md), [SECURITY.md](SECURITY.md), and the [operations guide](docs/OPERATIONS.md).

## Status

This repository contains a tested single-node reference implementation and extension interfaces. Multi-region consensus, a live Solana program, production KMS integration, FUSE/Dokan mounts, and audited TEE attestation are tracked as deployment milestones and are not falsely represented as complete.

## License

Apache-2.0. Imported model artifacts retain their original licenses and are not relicensed by Decillion.
