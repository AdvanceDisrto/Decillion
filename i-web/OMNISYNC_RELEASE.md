# Project Omni-Sync v0.2 — Master i™ PWA integration
This release uses the byte-identical October 15 2026 reference artwork and **does not** substitute the rejected older white Buddy GLB.

## Working release prepared and locally verified
The conversation attachment `i-the-one-omnisync-release.zip` contains the full frontend, exact JPEG artwork, on-device camera capture (permission required), local .glb preview with animation detection, responsive iPhone/tablet/desktop layout, nine i™ sections, receipts, and a locally testable secured optional FastAPI gateway. The ZIP also contains `publish-to-render.ps1`, which archives the previous preview branch and then updates the existing Render-tracked frontend **only on the owner's Windows GitHub-authorized machine**.

Local verification: Node JS syntax tests passed; 10 Python package/backend security tests passed; original JPEG SHA-256 c4aae6d23088ef16f5aa6282ab8e66b171d90f70200aa0202fadc319d649a3ce. Browser visual automation was blocked by the runner's network/file navigation restriction, so no mobile visual acceptance or successful production cloud video generation is claimed.

## Live backend
Backend branch `feature/buddy-receipts-backend-20261015` contains new `i-api/omnisync.py` and mounts the router in main.py. Routes:
- GET /v1/omnisync/capabilities: truthful capabilities and provider availability.
- POST /v1/omnisync/jobs: requires authenticated Supabase Bearer identity, configured HTTPS GPU-rendering provider and server-side token.
- GET /v1/omnisync/jobs/{id}: authenticated status. No invented completed jobs.

Requires OMNISYNC_PROVIDER_URL and OMNISYNC_PROVIDER_TOKEN on Render. Render is orchestration, not allocated VRAM. No automatic camera activation. Future hooks for Unreal/MetaHuman, ComfyUI/AnimateDiff, EbSynth, NeRF and 52-point facial capture need those engines/services licensed and deployed before showing availability.

## Browser release status
This feature branch is staging only. The actual reference image **is not stored on the GitHub preview branch yet** because the GitHub connector cannot transfer binary files directly from the user's ChatGPT file sandbox. The preview site has NOT been visually replaced as part of this feature branch. Do not merge main without explicit user approval.
