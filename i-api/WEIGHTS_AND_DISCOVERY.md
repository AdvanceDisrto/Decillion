# i™ Weight Discovery + Native LAN/BLE/Wi-Fi Diagnostic

## Verified repository observations (2026-10-15)
- Decillion `main` Git tree: 70 entries; **zero actual `.safetensors`, `.gguf`, `.pt`, `.pth`, `.ckpt`, `.onnx` blobs** in that tree. The vault is intentionally external to Git.
- The README references checkpoints as inputs or examples. The vault smoke script creates a tiny fake `model.safetensors` placeholder, not a language model.
- The iModels endpoint records `weights_verified:false` and `inference_verified:false` until authentic full shards and generation are independently checked.
- This does NOT establish that local E: storage, RunPod, Hugging Face private repositories, or other branches have no weights. Run the local read-only inventory below to discover those.

## Security correction to submitted environment manifest
The previously pasted placeholder `http://127.0.0` is not a valid remote public model-serving URL; `127.0.0.1` would refer to the Render container itself, not your desktop. Provide an authenticated HTTPS hostname for the actual inference node.
The bearer key pasted into chat should be considered disclosed. **Generate a new secret and do not commit or paste it into frontend code or any shared log**.
An arbitrary 64-hex string is not proof of hardware attestation or the SHA-256 of the model data. Use a digest derived from the actual model manifest and independent license review.
Only Apache-2.0 weight models are permitted by the current routing policy; no training/fine-tuning checkpoint is fabricated by the router.

## Windows read-only weight discovery
```powershell
git clone https://github.com/AdvanceDisrto/Decillion.git
Set-Location .\Decillion
git fetch origin feature/buddy-receipts-backend-20261015
git switch --detach origin/feature/buddy-receipts-backend-20261015
.\scripts\Find-iModelWeights.ps1
```
Inventory JSON is written to `$HOME\Desktop\iModel-Weight-Audit`. This script does not delete or upload files; it hashes only smaller candidate weight files for time and safety.

## Native discovery (trusted PC or Linux edge node; not PWA or Render)
```powershell
py -m pip install bleak zeroconf
py .\i-api\local_discovery.py --ble --lan --wifi --seconds 4
```
- BLE: an opt-in OS advertisement scan, if hardware, permissions and `bleak` support it. Does not pair or authenticate.
- LAN: a real opt-in mDNS service scan using `zeroconf`. Does not create or authenticate a peer connection.
- Wi-Fi Direct: a Windows/Linux driver capability read using `netsh` or `iw`. It does not create a Wi-Fi Direct session. Native Wi-Fi Direct sessions require OS platform-specific companion code and user authorization.
- TCP/UDP: actual socket binds to **127.0.0.1 only** prove the local socket stack works, not an authenticated remote link.
- The script never reports `p2p_authenticated:true` or `encrypted_session_established:true` unless a later actual pairing/transport implementation supplies proof.

## Model host acceptance
Identify complete weights, tokenizer, architecture, real license and provenance; calculate manifest hash and run an actual text generation on the licensed serving runtime. Configure server-side `IAPI_APACHE2_BASE_URL`, `IAPI_APACHE2_MODEL_ID`, `IAPI_APACHE2_API_KEY`, `IAPI_APACHE2_LICENSE_SPDX=Apache-2.0` and `IAPI_APACHE2_MODEL_REVISION_SHA` with **real** values. Only then verify /v1/universal/providers and authenticated Buddy generation. A PWA cannot connect to loopback on a different PC or arbitrarily discover local radios.
