# i™ iMobile release gates

Native project code is not the same as store submission. Before EAS build and App Store/Google Play release: owner approval; Apple Developer and Google Play organization access; production package IDs, app icons/splash assets, privacy policy, consent dialog for microphone/camera, data deletion, support contacts, accessibility and real-device QA.

Buddy sign-in is provided through a **Supabase Auth password/token REST implementation** in `src/auth.js` with session refresh. Supply an **operator-approved Supabase project URL and publishable key**; do not embed service_role secrets. Never expose ICE issuer private keys to phone. Keep refresh tokens in SecureStore, rotate and destroy on logout, enforce production TLS, server-side JWT authorization and production session revocation policy. Formal passkey/Face ID enrollment is an additional step and does not automatically make the app an independent cryptographic certifier.

`src/certificate.js` calls the independent ICE `/validate` endpoint over HTTPS, but does **not** independently verify Ed25519 locally. Therefore it can only present ICE server attestation claims subject to authenticated endpoint security, not claim fully offline independent validation. Build a native Ed25519 verifier with pinned issuer root and revocation sync before public release.

For future native hardware discovery use explicitly provisioned BLE advertisements with signed device identities; ARKit/LiDAR and UWB do not magically detect material in invisible walls. Real sensor nodes, BLE/UWB permissions and hardware provisioning are NOT supplied by this release. No automatic microphone recording.

Use `npm test`, `npx expo config --type public`, then hardware tests on both iOS and Android before submission. App Store/TestFlight requires signing credentials, enrollment and manual review, and no release has been initiated by these files.
