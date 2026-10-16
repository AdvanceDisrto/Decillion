# i™ Beyond-Silicon Fabric — OPU / iNeuro / iQuantum

This is a **research-software integration** with the Buddy Render API, not a claim to physical accelerator hardware.

## Installed endpoints
- GET `/v1/alternative-compute/capabilities` — identifies each engine as `cpu-reference-simulation`, with `hardware_connected:false`.
- POST `/v1/alternative-compute/run` — input: `{"engine":"photonic"|"neuromorphic"|"quantum","values":[0.7,-0.3],"phase":0.4,"steps":12}`.
- Returns a reference calculation and `i-research-receipt/1` SHA-256 digest. This is a **local integrity receipt**, `signature:null`, `anchored:false`, `verified_hardware:false`.

## What the engines mean
**iOPU photonic**: Ideal two-port Mach–Zehnder interferometer, classical complex amplitudes, balanced beam splitters and a phase shifter; tests check squared-amplitude conservation. Not a physical optical chip. Real OPUs still need memory, detection, laser control and electronic/optical conversions. Overlapping light beams can **interfere**; they do not guarantee unlimited independent calculations.

**iNeuro neuromorphic / organoid concept**: CPU leaky-integrate-and-fire neuron reference, discrete time, threshold and reset. No living material or organoids are in this project. A real organoid study needs specialized laboratory infrastructure, documented consent/provenance, ethics approvals and harm assessment before experimentation. Brain energy figures are not comparable to the full operational cost of an organoid computer.

**iQuantum analog simulator**: Classical CPU statevector of two qubits. The example checks normalization. This cannot claim quantum advantage or that physical quantum systems deliver instant correct answers. A future instrument-backed connector must return observed measurement counts, actual device identity, provenance, timestamp and uncertainty.

## Honest capabilities contract
- `mode:cpu-reference-simulation` always means mathematical emulation.
- Real devices require signed vendor/device measurements, instrument drivers and calibrated verification. Device claims remain false until validated.
- Backend HTTP LIVE status is not hardware verification; the API requires actual invocation to confirm responses.
- A receipt hash guarantees its body matches the hash **only**; do not confuse this with chain finality, hardware attestation, an independently verified experiment or biological welfare compliance.

## Production admission gates
1. Implement a **sandboxed** device adapter, independent of simulation.
2. Bench against CPU baselines: accuracy, energy per work, throughput, latency, memory, thermal constraints and uncertainty.
3. Validate immutable input/result IDs, replay-resistance, signed device identity and external witness anchoring.
4. Require operator consent for experiment-specific risks. Organoid-related work must remain **software-only** until a qualified ethical governance process explicitly authorizes biological research.
5. Only then allow Buddy/iMods routing to label a real iOPU/iNeuro/iQuantum node `hardware-verified`.

## Tests
`cd i-api && python -m unittest -v tests/test_alternative_compute.py` (install i-api requirements). Eight tests were run against a matching local source copy on 2026-10-15 and passed. CI result for the GitHub branch should be checked independently.

## Sources
- Wadan (2025), Organoid Intelligence and Biocomputing Advances. https://spj.science.org/doi/10.1016/j.bosn.2025.01.002
- Photonic memristive in-memory matrix operation (2026): https://link.springer.com/article/10.1186/s43074-026-00242-6
- Integrated optoelectronic computing constraints (2026): https://link.springer.com/article/10.1007/s44519-026-00008-4
