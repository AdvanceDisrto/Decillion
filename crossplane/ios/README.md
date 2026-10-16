# i™ iOS Native Bridge (Swift)
The portable `crossplane` C++17 core is designed to compile with Apple Clang. The Swift adapter `ImCrossPlane.swift` calls the stable C ABI via a module map. This is an integration source package, not a compiled IPA, Xcode project, installed iPhone app, or proof of real local connectivity.

To build a native iOS client, configure an Xcode project/Swift Package exposing `im_crossplane.h`, compile `im_crossplane.cpp` for the target iOS SDK with Apple Clang, link the static library, and import the C module. Add lifecycle-safe CoreBluetooth/Network.framework transports only with user permission. BLE is not a high-throughput video mesh and iOS does not allow applications to bypass OS baseband or Wi-Fi privileges.

The existing PWA remains the functional iPhone access path until this native client is compiled and tested on an Apple device.
