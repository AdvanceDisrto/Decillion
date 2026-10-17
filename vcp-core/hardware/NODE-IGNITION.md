# iSWH 1.0 — node ignition / reality check

## Executable, supported sequence

1. Simulation reset → isolated output (zero data, tx_valid=0).
2. A separately authenticated interface provides `identity_valid`, `policy_allow`, and `link_healthy`.
3. The HDL gate enters IDLE; only a healthy, authorized packet is forwarded.
4. Policy revocation or link failure immediately blanks **at next clock edge** and enters quarantine.
5. A recovered node passes through isolation before resuming output.

`network_isolate` is **a digital simulation signal**, not a physical breaker or power-cycling relay. The 256-bit word in the user's draft is not proof of post-quantum verification, and forwarding a 64-bit payload is not quantum entanglement, encryption or a LoRa/FSO transceiver.

## Run the real simulation

```sh
cd vcp-core/hardware
ghdl -a --std=08 iswh_mesh_gate.vhd tb_iswh_mesh_gate.vhd
ghdl -e --std=08 tb_iswh_mesh_gate
ghdl -r --std=08 tb_iswh_mesh_gate --stop-time=90ns --assert-level=error
```

This must be tested in GitHub CI before recording success. No room sensors, lasers, bitstream, 3200W PSUs, secure elements, 1T cluster or physical node are connected by this code. An actual device needs approved photonic safety engineering and authenticated cryptographic inputs. Do not silently capture ambient speech.

## Firmware and physical safety

Never drive a high-power laser, high-current rail or life-safety systems from this simulation or the status of an LLM answer. Real FPGA secure boot depends on device-specific vendor-supported encrypted/authenticated bitstreams, secure configuration, protected debug access and genuine device attestation. A SE050 is not automatically a secure-boot gate for every FPGA and its key never makes facts true.

## Public announcement gate

No open-source release, fabricated ASIC, physical assembly or enterprise deployment is claimed. Publish only approved, reviewed IP after owner approval. This prototype demonstrates an FPGA-fabric **policy-gated stream interface**.
