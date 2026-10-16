# i™ iMobile Android Native Hybrid (engineering preview)

This is an actual compilable Android Studio project with a JNI C++ library, an app-private append-only bootstrap journal and a secure-transport-only WebView for the existing i™ PWA.

**Current implementation:** Android Application boot → `System.loadLibrary("im_under_the_hood")` → JNI validates an app-private directory → initializes a local ledger → WebView loads `https://i-the-one-buddy-preview.onrender.com/` → shows an offline info page if the service cannot be reached.

**Not included:** live VPU MMIO, SERS hardware signatures, Apache-model weights, true gRPC worker, Netmaker/WireGuard tunnels, local radio mesh, OS kernel control, APK background network privileges, direct Bluetooth discovery, a downloaded/on-device model, native iOS build, production app signing or Google Play distribution. These require separately implemented and verified native platform modules.

### On Linux with SDK and NDK

```bash
gradle -p imobile-android :app:assembleDebug
sha256sum imobile-android/app/build/outputs/apk/debug/app-debug.apk
```

Requires JDK 17, Gradle 8.9, Android SDK 35, Android NDK 27.2.12479018, CMake 3.22.1.

### On Windows PowerShell

```powershell
Set-Location "$HOME\Decillion"
git fetch origin feature/buddy-receipts-backend-20261015
git switch --detach origin/feature/buddy-receipts-backend-20261015
gradle -p imobile-android :app:assembleDebug
```

Install Android Studio or Android command line tools, Gradle 8.9 and JDK 17 first. The GitHub Actions workflow is able to compile without local toolchain setup and publishes the generated **debug, non-production-signed** APK as a workflow artifact. It does NOT broadcast or auto-install it on devices.

### Security notes

Never paste IMEI, ICCID, EID, Wi-Fi/Bluetooth MAC or mobile subscription credentials into the source. Do not disable certificate validation or change the Spectrum WiFi profile to run this application. The Android OS enforces carrier, SIM/eSIM, radio, background and storage restrictions. JNI C++ does not override those protections. The app never tries to do so. All screenshots supplied of iPhone Settings are input for conceptual interoperability, not Android device capabilities.

### Release gate

Before release, require real Android device testing, background lifecycle handling, navigation security, permissions review, isolated signing key, update policy, accessibility, privacy policy, license audit, and reproducible artifact verification. This repository intentionally preserves the existing main branch and does not automatically publish a mobile app.
