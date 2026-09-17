# Sharded Weight Vault and Telepath

## Trust boundary

The external disk is the persistence boundary. It contains encrypted shard blobs, wrapped model keys, manifests, ACLs, and a chained receipt database. Application source and customer/model payloads remain separate.

- AES-256-GCM authenticates every shard with model ID, shard index, and plaintext hash as associated data.
- A per-vault random 128-bit salt feeds scrypt (`N=32768`, `r=8`, `p=1`) to derive the local wrapping key.
- Each model has an independent random 256-bit DEK; only wrapped DEKs are persisted.
- Ciphertext SHA-256 determines the shard path. Manifests never supply arbitrary filesystem paths.
- The Merkle root commits to ordered ciphertext hashes. Whole-file SHA-256 verifies Telepath reassembly.
- Ed25519 requests bind requester, model, purpose, nonce, and timestamp. Replay caches reject reused nonces.
- Receipt HMACs cover the complete payload and previous receipt signature and are ordered by SQLite sequence.

Fresh nonces and independent DEKs intentionally mean identical plaintext shards normally produce different ciphertext. The vault supports exact ciphertext reuse, not equality-leaking convergent-encryption deduplication.

## Telepath protocol

Each request opens one length-prefixed JSON connection and receives one signed response. Sessions bind the requester public key to a model ID, shard budget, and expiration time. The server decrypts only the requested shard; the client never receives or handles the DEK.

The transport authenticates messages but plain TCP does not provide confidentiality. Bind to loopback by default. Use an SSL context in an embedding application or place cross-machine traffic inside WireGuard/TLS. Do not expose port 7788 directly to the public Internet.

## Operational backup

Back up the entire vault directory as one consistency unit. A backup missing `vault.json`, `keys/`, or the receipt database is incomplete. Store the passphrase in a password manager or hardware-backed secret store; losing it makes the model DEKs unrecoverable. Copying the passphrase beside the vault defeats the physical separation.
