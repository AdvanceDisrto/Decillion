# External weight vault

The weight vault is a dedicated destination for Hugging Face snapshots. It must live outside the Git working tree, preferably on an encrypted mounted volume, dedicated local disk, NAS mount, or persistent block-storage volume.

## Guarantees

- The vault refuses initialization anywhere inside a Git working tree.
- Every model is stored under `models/<organization>/<name>/<immutable-revision>`.
- A per-revision lock prevents concurrent writers.
- Downloads land in a private staging directory and become visible through one atomic rename.
- Quota and free-space-reserve checks run before and after download.
- Every regular file receives a SHA-256 entry in `decillion-manifest.json`.
- Verification detects changed, missing, or added files.
- Symlinks are rejected from committed snapshots.

The vault does not make an unencrypted disk encrypted. Use BitLocker, LUKS, a hardware-encrypted device, or an encrypted cloud volume for encryption at rest. Do not expose the directory through a public file server.

## Windows external drive

From a cloned Decillion repository in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File ".\scripts\Initialize-WeightVault.ps1" `
  -VaultPath "E:\iDecillion\ModelVault" `
  -ReserveBytes 53687091200
```

This reserves 50 GiB of free capacity. A zero quota means the physical volume and reserve are the limits.

## Linux, WSL, or server volume

```bash
decillion-models vault-init \
  --destination /mnt/decillion-model-vault \
  --reserve-bytes 53687091200
```

For your WSL ext4 disk, a suitable destination is `/root/iDecillion/ModelVault` if that path is outside the repository. For a separately mounted volume, prefer `/mnt/decillion-model-vault`.

## Download an immutable model revision

The license supplied to the command must exactly match normalized Hub metadata:

```bash
decillion-models mirror deepseek-ai/DeepSeek-R1 \
  --license mit \
  --include-weights \
  --destination /mnt/decillion-model-vault
```

Limit a download to selected formats when necessary:

```bash
decillion-models mirror organization/model \
  --license mit \
  --include-weights \
  --allow-pattern '*.safetensors' \
  --allow-pattern '*.json' \
  --destination /mnt/decillion-model-vault
```

Verify later using the immutable revision SHA printed by the mirror command:

```bash
decillion-models vault-verify organization/model REVISION_SHA \
  --destination /mnt/decillion-model-vault
```

## Capacity warning

A one-trillion-parameter BF16 checkpoint is approximately 2 TB before auxiliary files. Your current 1 TB local volume cannot hold a complete 1T BF16 checkpoint. Use a larger external array or object/block-storage tier for that checkpoint; the vault will reject downloads that violate its configured reserve or quota.
