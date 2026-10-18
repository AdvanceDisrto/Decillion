# i THE ONE: native Tauri v2 + Rust ↔ C++ candidate

A complete Tauri project with Rust bridge, C++ engine, local browser UI and tests is available in the companion build package. Native tests were executed with g++ 12; 5 assertions passed. This repository stage carries a portable C++ core and test, not a compiled iOS app.

Compile and run: `g++ -std=c++17 -Wall -Wextra -Werror native/engine.cpp native/tests/native_test.cpp -o /tmp/innovulis-native-test && /tmp/innovulis-native-test`.

Numeric vector closure is NOT factual truth, PUF attestation, GPU access or physical clock evidence. Rust ↔ unsafe C++ still needs careful FFI review. iOS native builds require macOS/Xcode according to Tauri documentation. Do not deploy command-execution APIs from static web hosting.
