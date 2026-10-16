# i™-Silo-1 / iCalcula hardware acceptance

This repo now includes three executable engineering prototypes: a standalone Verilog decoder, a bounded Python fixed-point emulator, and separate edge synchronization/IPC tools.

## What is verified in GitHub CI
- Standalone Verilog decoder: `silicon/icalcula/im_icalcula_decoder.v`.
- HDL simulation: `silicon/icalcula/tb_icalcula_decoder.v`, compiled and executed with Icarus Verilog.
- Python ISA emulator: `i-api/vpu_lab.py`, with opcode, fault and SHA-256 testing.
- Go offline store-and-forward: `edge/continuity/main.go`, local build and unit test.
- Real localhost gRPC roundtrip: `i-api/vpu_grpc_benchmark.py`, reporting measured host IPC p50/p95.
- i™ PWA VPU dashboard: `i-web/vpu-lab.js`, publishing benchmark controls and unsigned receipts.

## Hardware status (not yet verified)
The `0xFE000000` reference address, SERS command offsets and proposed `im_receipt0` driver are **unverified design references**, not a discovered bus device. No silicon register is mapped, no physical transmitter is controlled, no SERS private key fuse is present, and no chip-signed receipt has been issued.

**Do not load the previously supplied im_vpu_net.c kernel sketch**. It lacks device binding/probe identity, buffer expansion bounds checks, interruption/timeout paths, proper netdev handling, and a non-recursive transmit path; its fixed MMIO address could access unrelated host hardware. This branch does not compile or load that driver.

The SHA-256 output from the Python emulator is a deterministic software integrity digest, not Ed25519, hardware attestation, a secure enclave certificate, or proof of zero memory leakage.

## ISA prototype
Instruction word 32 bits: opcode [31:24], register A [23:16], register B [15:8], immediate [7:0].
Supported operations: NOP 0x00, ADD 0x01, MUL 0x02, MAC 0x03, STAMP 0x10, RESET 0x11.
Signed int32 arithmetic with overflow rejection in Python; Verilog tests exercise ADD/MUL/MAC, overflow, fault injection, simulation tag and reset.
The RTL does not yet instantiate Vortex GPGPU components or a real cryptographic SERS core. Its XOR `state_tag` is expressly noncryptographic.

## iMojo/Vortex/KAI/GPUStack acceptance
To integrate a compiler and scheduler, pin an actual upstream source revision and review licenses of the **specific files and included model weights** (the project's brand name or a generic Apache claim is insufficient).
1. Define stable iCalcula custom opcodes and ABI; validate reference golden vectors in Python and Icarus testbench.
2. Add a Vortex pipeline bridge **only** after checking the target revision's actual decoder/issue/ALU handshake interface. Keep the standalone module independently testable.
3. Implement a real SHA-256 or supported signature core with a proper key-enrollment hierarchy, nonce and verifier. Never hard-code cryptographic private keys in RTL.
4. Run formal lint, CDC/reset checks, constrained randomness, coverage, synthesis and FPGA timing. Vortex or FPGA simulated PASS is not ASIC proof.
5. Integrate Mojo only after compiling a valid source file using the installed, pinned compiler: the pasted `external_call["volatile_store"]` sequence is not a verified Mojo or hardware ABI. Floating point and compiler optimizations do not imply universal bit-exact replication across devices.
6. Integrate KAI/GPUStack only after provisioning Kubernetes, registering a real device plugin and hardware resources, creating a non-privileged container profile, and demonstrating actual scheduler placement with accountable GPU memory use.

## Local verification
On Linux with Python dependencies and Icarus Verilog:
```bash
cd i-api && python -m unittest -v test_vpu_lab.py
cd ../
iverilog -g2012 -Wall -s tb -o /tmp/icalcula_test silicon/icalcula/im_icalcula_decoder.v silicon/icalcula/tb_icalcula_decoder.v
vvp /tmp/icalcula_test
cd edge/continuity && go test -v ./... && go build .
```
Optional gRPC loopback benchmark (no remote transport):
```bash
python -m pip install 'grpcio>=1.67,<1.81'
cd i-api && python vpu_grpc_benchmark.py
```

## Go continuity queue usage
```bash
cd edge/continuity
go run . enqueue ./local-state "non-sensitive-event"
go run . status ./local-state
```
The sync command requires **explicit** `I_CONTINUITY_SYNC_URL=https://<authorized-receiver>` and `I_CONTINUITY_BEARER_TOKEN`, plus a receiving service implementing idempotent event acceptance. The `main.go` daemon does not autonomously replicate to SOURCECHAIN and does not deliver NextGraph, Matrix or Netmaker integration. Never put secrets into shell logs.

## Acceptance states
- Emulator/RTL unit tests: testable via CI; hardware proof: **not issued**.
- Go queue: compiles and stores local events; actual remote service integration: **not wired**.
- gRPC: real localhost transport round-trip, **not hardware or distributed networking**.
- iModels: Apache-2.0-exclusive policy; actual model weights and inference: separately configured and not verified by this module.
- No "zero leakage", "100% physical mirror", "instant failover" or unlimited memory/VRAM performance claims are permitted without independent measurements.
