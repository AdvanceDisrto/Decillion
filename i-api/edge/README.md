# i™ Edge Runtime / SOURCECHAIN continuity

This directory implements an **actual model-serving integration path** using a local Unix-socket gRPC server and `llama-cpp-python`. It does not fabricate token output, hardware signatures, silicon capabilities, or global chain commits.

## Running a real local GGUF checkpoint (Linux / WSL)

```bash
cd i-api/edge
python -m venv .venv
source .venv/bin/activate
python -m pip install grpcio grpcio-tools llama-cpp-python
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. inference.proto
python -m unittest -v test_ledger.py
python server.py --model /absolute/path/to/verified-model.gguf --socket /tmp/i-edge.sock
```

The model file **must exist**. Conversion of arbitrary .pt/.safetensors is model-architecture-specific and must be validated against the source tokenizer and training receipt. GGUF support depends on the model architecture and llama.cpp version. GPU offload requires an appropriately built llama.cpp backend; set `I_EDGE_GPU_LAYERS` only after verifying that build. CPU-only is the default.

The gRPC socket is restricted to local user access (mode 0600); the runtime is **not exposed on the public internet**. A Render service cannot access a phone's Unix socket. The iPhone PWA also cannot host a Python gRPC server or read local model files. A native iOS/Android host app or an authenticated edge relay is required to bridge mobile devices. Do not expose the socket through an unauthenticated TCP port.

## Receipts and offline continuity

Each generated text chunk is recorded in a durable SQLite WAL database with canonical JSON, SHA-256 hash and a previous-hash pointer. `Ledger.verify()` recomputes and validates the entire chain. `Ledger.pending()` returns unsynchronized entries. `Ledger.acknowledge()` marks a receipt synchronized **only after an authenticated server acknowledgment has been validated by the caller**. The ledger never drops acknowledged receipts.

**Security boundary:** A hash chain is not tamper-proof against a hostile administrator who can rewrite the entire database and genesis history. Anchor the latest chain head to a trusted external witness, with a signed public key identity and monotonic sequence, to detect such rewrites. This module does not claim to implement SOURCECHAIN, secure-enclave attestation, blockchain finality, or cryptographic proof of correct inference.

## Apple / Android / multi-accelerator

Apple: Core ML and Metal/ANE selection is controlled by the model compiler/runtime and hardware; a single Apple GPU has many cores, not automatically many independent GPUs. Android: ExecuTorch/XNNPACK, Vulkan, and Qualcomm QNN delegates have distinct support matrices; NNAPI is deprecated on newer Android versions. Neither platform guarantees zero-copy cross-accelerator tensor sharding. Benchmark and verify device-specific model graphs.

The current edge service executes a real GGUF checkpoint through llama.cpp when provided, with CPU or GPU offload as supported. Multi-GPU tensor parallelism, Core ML, QNN, ExecuTorch, and on-device secure enclave signing are **future native adapters**, not claimed as implemented here.

## VPU and SOURCECHAIN

See `VPU-ISA.md` for a versioned ISA and trust-boundary proposal. Never hard-code a hardware signing private key in HDL or source code. A software ECDSA key is **not** a Secure Enclave or StrongBox key. Real hardware attestation requires vendor-specific provisioning, certificate chain validation, anti-replay and trusted execution measurements. A signed output hash proves signing-key possession, not mathematically correct tensor computation.

This edge runtime is intentionally isolated from the deployed Render service until model weights and an authenticated relay are configured and tested. The Render backend's `/v1/models` routes remain the hosted orchestration surface.
