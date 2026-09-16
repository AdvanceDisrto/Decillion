# Architecture

## Data plane

1. The authenticated caller uploads an object and owner identifier.
2. Decillion generates a random AES-256 data-encryption key (DEK) and nonce.
3. The object is encrypted with AES-GCM. Owner and filename digest are authenticated data.
4. A key provider wraps the DEK with a key-encryption key (KEK).
5. Ciphertext is stored under its SHA-256 content address using an atomic write.
6. A canonical receipt is signed with Ed25519 and indexed in SQLite.
7. Receipt batches produce Merkle roots suitable for external anchoring.

No plaintext DEK appears in a receipt. A blockchain anchor should contain only a signed root and minimal non-sensitive metadata, never a customer key or filename.

## Control plane

The API authenticates bearer tokens and requires exact owner/filename bindings during retrieval. Production deployments replace static tokens with OIDC/mTLS, the local object backend with redundant object storage, SQLite with a replicated metadata database, and the local key provider with KMS/HSM or attested TEE key release.

## Model plane

Hugging Face discovery and mirroring are deliberately separate from the storage data plane. Metadata discovery is the default. Weight mirroring requires all of:

- an exact model identifier;
- an immutable revision SHA;
- a license matching the operator's explicit policy; and
- `--include-weights` plus an external destination.

The source repository never becomes a weight warehouse.

Downloaded snapshots are committed to an external `WeightVault`. The vault separates staging from immutable revision paths, enforces capacity policy, and generates a SHA-256 inventory before atomic publication. Storage-device encryption and backup remain infrastructure responsibilities.

## Scale strategy

Decillion-scale *operations* are addressed through horizontal partitioning, aggregation, tiered retention, and cryptographic commitments. It is physically infeasible for today's infrastructure to preserve `10^33` independent 32-byte receipts. Merkle aggregation compresses verification state while underlying detailed receipts follow contractual retention rules.
