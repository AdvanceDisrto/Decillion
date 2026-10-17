# i™ THE ONE — Expo cockpit (development)

Native React Native Expo client implementing authenticated **existing** Buddy VCP assessment API `POST /v1/vcp/assess`. This API yields `EVIDENCE_RETRIEVED` or `INCONCLUSIVE`, **never iCERTIFY certification**. The native client does **not** directly call local ICE `/certify`: that operation requires three distinct trusted witness signatures, an independent issuer and a separate authorized service identity.

## Local run
```sh
cd i-mobile
npm install
npm test
npx expo start
```
Run Expo Go on a supported real device or create a supported development build. Store session only with affirmative user consent; this MVP accepts an existing Buddy JWT rather than implementing the complete sign-in screen. Saved session is in Expo SecureStore, not an independent hardware-secure certificate authority. The default hosted URL is an example gateway; production readiness and account permissions must be verified.

Do not assume iPhone `127.0.0.1` refers to the Linux/Windows server. Use a valid HTTPS private-network gateway with TLS and identity checks. No public-access launch has been performed. Biometric binding, ARKit/UWB discovery, real sensor mesh, Apple Watch, app-store approval and haptic hardware measurements are separate phases. LiDAR cannot detect hypothetical invisible crystals; hardware nodes need documented and authorized discovery protocols. User-initiated input only, no automatic microphones.

## Acceptance
`npm test` executes request validation, authenticated network transport formatting, unsupported-certification checks and error-state tests. End-to-end device acceptance requires separately authorized Buddy credentials and a reachable configured model provider. Haptic **success** indicates the request returned an assessment only, not factual truth.
