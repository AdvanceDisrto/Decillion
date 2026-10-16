# i™ THE ONE — Master Visual Portal

**Design authority:** Uploaded 1536×1024 original image on October 15, 2026. The exact original JPEG is included in the deliverable `i-the-one-master-release.zip` generated in this conversation, which also contains the working responsive website and a deployment script.

**Protected deployment:** Render preview service `srv-db8l460473hc73a0ovu0`, branch `deploy/i-the-one-pwa-20261015`. This feature branch does **not** auto-deploy.

## Acceptance requirements
- Desktop: the original supplied artwork, not a reinterpretation, spans the exact hero scene. Native transparent dashboard hotzones open working panels for nine ecosystem sections, Buddy, receipts and live status.
- Mobile: full-height cinematic image crop, a separate readable headline, accessible 44px+ tap targets, stable lower navigation and insets. No intrusive PWA update bar or Mini Buddy overlapping primary actions.
- Buddy: local conversational interface, browser voice start (user initiated), optional recognition, honest model availability; **do not** claim proprietary voice, rigged 3D animation or trained models without evidence.
- Receipts: SHA-256 browser integrity receipts can be exported; never call these hardware attestation or blockchain finality.
- Features: actual navigation, accessible content, offline service worker assets; integrations remain contingent on working endpoints.
- Preserving production: archive the existing deployment branch before publishing; never merge to main without approval.

## Deployment
Download `i-the-one-master-release.zip` from this ChatGPT conversation and run `publish-to-render.ps1` from its extracted folder on a GitHub-authorized Windows computer. This uploads the **exact image bytes** plus the complete HTML, JS, CSS, PWA icons, manifest and service worker to the existing auto-deployed Render branch. The publish script backs up the existing preview branch to a timestamped archive first.

**Why the image is not on GitHub yet:** The GitHub connector exposes text/encoded blob APIs but cannot directly read the uploaded image bytes from the local ChatGPT file sandbox in this session. A preview that omits that asset would fail the visual acceptance requirement, so the new portal has not been substituted for the old production site by this branch alone.
