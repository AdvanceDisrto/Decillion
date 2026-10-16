# i™ iMobile iOS — build, sign and acceptance

The SwiftUI iOS application is defined by `imobile-ios/project.yml` (XcodeGen). It embeds the existing i™ PWA using WKWebView and adds a native Sorcery backend health sheet. This is not yet a complete native feature-for-feature port.

## iOS CI
`.github/workflows/imobile-ios-app.yml` generates the project and attempts an unsigned iOS Simulator build and an unsigned iOS-device `.xcarchive` on a macOS runner. An unsigned archive is not an installable signed IPA.

## Signing credentials — never commit
For device installation / TestFlight distribution, obtain a legitimate Apple Developer team, matching App ID, distribution certificate/private key and provisioning profile. Configure a protected build environment with restricted GitHub Actions secrets (`APPLE_TEAM_ID`, `APPLE_CERTIFICATE_P12_BASE64`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_PROVISIONING_PROFILE_BASE64`, plus an App Store Connect API key if distributing with Apple tooling). Do not put any signing credentials into Swift, frontend JavaScript, receipts, build artifacts or logs. The distribution signing workflow is **not** enabled yet; no credentials are presumed to exist.

## Real-device acceptance checklist
1. Provision an authorized test iPhone; confirm Apple signing and installation.
2. Verify app launch, PWA connectivity, and offline failure handling.
3. Verify sign-in, session expiry, and Sorcery access as an authorized account.
4. Verify background/foreground transitions and microphone permission UX before enabling audio.
5. Test iPhone / Android network transport only after real peer pairing exists.
6. Export build SHA-256 and actual device logs; mark attestation and external receipt anchoring unverified unless independently established.

## Phone build and PowerShell
Sorcery dispatches *reviewed workflows* on ephemeral GitHub runners. `scripts/sorcery/inspect.ps1` is the initial read-only PowerShell diagnostic. There is no arbitrary host PowerShell command execution, remote desktop takeover, or access to a persistent machine. That would require an independently sandboxed execution broker with per-command authorization, quotas, audit logs and filesystem/network restrictions.

## Operator enablement
Render backend must be configured with a verified Supabase user identity and `I_SORCERY_OPERATOR_UIDS`, and restricted GitHub/Render tokens. Do not store these tokens on the phone. API acceptance and manual dispatch are not implied by a green compiler job.
