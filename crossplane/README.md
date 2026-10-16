# i™ Portable Shared Core (iCrossPlane)

Compiled portable C++17 library with a C ABI for **Android NDK and Apple Clang**. A compiler for a target is needed before claiming its binary exists. Android uses JNI and iOS uses Swift bridging/Obj-C wrapper, but this is **not a hypervisor**; sandbox boundaries remain enforced by iOS and Android.

The first implemented library provides SHA-256 integrity digests and a deterministic 20,000-node synthetic mesh stress test (50% dropout). It does not perform real cross-platform network synchronization, hardware signaling, SERS signatures, credential authorization or end-to-end encryption.

```bash
cmake -S crossplane -B /tmp/i-crossplane-build
cmake --build /tmp/i-crossplane-build
ctest --test-dir /tmp/i-crossplane-build --output-on-failure
```

C++ header: `include/im_crossplane.h`. Build output is a static library `libim_crossplane.a`. Consumers on Android link via NDK CMake; iOS can expose the C ABI through `module.modulemap`. Always use secure OS key storage and peer authentication for production. No background BLE, Wi-Fi Direct or satellite transport is implied.
