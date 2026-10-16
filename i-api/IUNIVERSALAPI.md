# iUniversalApi Grid v1 — installation and verification

This is a **working Python library and bounded load-simulation harness**, NOT a certified global mesh, signed OS installer or 10,000-live-socket deployment.

## API router

The module includes OpenAI-compatible endpoint schemas for OpenAI, Groq, DeepSeek and Google's compatible endpoint, plus an Anthropic Messages adapter. All providers are **unconfigured by default**. No API credentials or model IDs are committed.

```python
from iuniversalapi import Router, Provider, ScopedCache, Mesh, Telemetry
router=Router(providers=[
    Provider('openai','https://api.openai.com/v1','YOUR_ACTUAL_MODEL_ID','IAPI_OPENAI_KEY')
])
# Use an authenticated user scope; use_cache=True only with user consent.
answer=await router.complete("Hello Buddy",scope="authenticated-user-id",use_cache=False)
```

Set keys only as server-side environment secrets, then validate actual model ID, terms, latency/cost and rate limits. The current optimizer ranks configured models by **declared** price values. There is no learned predictive scoring, proven accuracy optimization or automatic monetary savings. A fallback is attempted when a provider returns an error; no synthetic model response is invented.

## Cache policy

Opt-in exact-prompt TTL cache. Scope, model ID and prompt are hashed into a cache key so one user's records are not retrieved for another user. Use encryption-at-rest and stronger consent/data retention controls before deploying to multiple tenants. Cached responses may be stale and do not count as new model inference.

## Encrypted peer envelopes

```python
import os
from iuniversalapi import Mesh
key=os.urandom(32)  # Provision securely between authorized peers; do NOT hard-code.
phone=Mesh(key,'phone')
pc=Mesh(key,'pc')
payload=phone.encrypt('pc',{'receipt_hash':'sha256:abc'})
print(pc.decrypt(payload))
```

AES-GCM with 256-bit keys encrypts authenticated payloads. The library has **no Bluetooth, Wi-Fi Direct, local LAN discovery, relay socket, exchange of secret keys or persistent anti-replay**. A production LAN/WAN transport needs mutually authenticated peers, safe pairing, lifecycle management and durable monotonic nonces. A PWA cannot arbitrarily control mobile radio interfaces and cannot promise operation across an internet blackout unless appropriate local physical networking already exists.

## Packaging reality

`Container.compile(target='universal_binary')` raises `NotImplementedError` intentionally. Docker images, Windows executables, signed macOS apps, Android APKs and iOS bundles require platform-specific toolchains and signing identities. Claiming those outputs exist from a text-only simulation would misrepresent deployment.

## Receipt reality

The stress-test result contains an SHA-256 digest of the event counts and metrics. It is **unsigned**, and there is no hardware attestation or global blockchain witness.

## Verification and reproducibility

From the repository root:

```bash
python -m pip install -r i-api/requirements.txt
cd i-api
python -m unittest -v test_iuniversalapi.py
python -m iuniversalapi.stress --events 10000 --concurrency 100
```

**What 10,000 means:** The harness schedules 10,000 bounded, in-process asynchronous **mock events** (maximum 100 concurrent tasks). It opens **zero real network connections**. Do not interpret event throughput as provider API RPS, 10,000 simultaneous users or device-mesh bandwidth.

## Roadmap to a deployable service

1. Add API-key-authenticated FastAPI ingress, abuse limits, spending caps and per-user usage receipts.
2. Set and test actual model IDs and securely manage secrets; send requests to real providers under explicit service authorization.
3. Add a production persistent cache, idempotency keys and retention rules.
4. Build optional LAN peer bridge with mutual authentication, platform-specific radio permissions and secure pairing.
5. Test on mobile and desktop physical devices, then build signed installers for each supported OS.
6. Integrate i™ receipt signing through a trusted key identity and independently verify the chain witness.

Protected branches are not merged by this feature branch.
