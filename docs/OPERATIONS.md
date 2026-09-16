# Operations guide

## Required configuration

| Variable | Purpose |
|---|---|
| `DECILLION_MASTER_KEY` | URL-safe base64 encoded 32-byte local KEK |
| `DECILLION_API_TOKENS` | Comma-separated API tokens |
| `DECILLION_DATA_DIR` | External state directory; defaults to `var` |
| `DECILLION_ENV` | Set `production` to disable the development token |
| `DECILLION_REQUIRE_ATTESTATION` | Set `true` to deny unwrap without evidence |

Generate a local key with `decillion generate-master-key`. Do not commit the value, place it in shell history on a shared host, or use the local key provider as a substitute for production KMS/HSM.

## Backups

Back up the object store, receipt catalog, persistent signing key, and KMS configuration independently. Test restore and decrypt operations. Losing the KEK or signing key can make objects unrecoverable or receipts unverifiable.

## Solana anchoring

Anchor a signed Merkle root, batch identifier, algorithm/version, and timestamp. Do not place plaintext keys, wrapped keys, names, access tokens, customer data, or raw receipts on a public ledger. A Solana/Anchor adapter should be implemented and audited as a separate integration.

## TEE integration

`KeyProvider.unwrap` accepts an attestation value, but the local implementation only enforces presence. Production adapters must validate vendor evidence, measurement allowlists, freshness/nonces, revocation status, and workload identity before key release. Presence checking alone is not hardware attestation.
