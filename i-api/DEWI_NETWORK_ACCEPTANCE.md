# i™ DeWi Network — physical acceptance and safety

This implementation is a **working software mesh-routing and offline-state comparison lab**, not a global carrier replacement.

## Implemented
- `GET /v1/dewi/capabilities`: reports actual hardware integration boundaries (zero connected physical nodes).
- `POST /v1/dewi/route`: deterministic multihop shortest-path calculation on an explicit Wi-Fi/LAN/LoRa graph; includes offline node exclusion and a SHA-256 receipt.
- `POST /v1/dewi/merge`: CRDT-inspired deterministic last-write-wins (counter, actor, value) local state merge and a SHA-256 receipt. **Not** a NextGraph smart contract or network replication.
- `i-web/dewi.js`: i™ Mesh tab with routing, failure injection, sync conflicts, hardware readiness and evidence downloads.
- `scripts/openwrt-mesh-candidate.sh --dry-run`: prints OpenWrt batman-adv/802.11s UCI *candidate commands*, never alters the router.
- `i-api/test_dewi_mesh.py`: graph resilience and deterministic sync tests.

## Actual physical build — gates
1. Acquire two supported OpenWrt routers or Linux nodes with compatible 802.11s radios. Connect to a private lab SSID; preserve a management uplink.
2. Verify `iw phy` mesh capability, legal channels, OpenWrt release, matching radio drivers, WPA3/SAE mesh support and firewall isolation. Follow the up-to-date official OpenWrt batman-adv guide.
3. Run `sh scripts/openwrt-mesh-candidate.sh --dry-run i-lab` and inspect the output. Install *only after manual review* of the router-specific interface names, safe-key handling and rollback plan.
4. Validate two-node authenticated 802.11s association with the actual `iw`/`batctl` tool output; measure link throughput/loss and 50% topology failure under hardware.
5. On an authorized IP mesh, deploy a signed-in messaging transport (Matrix, WebRTC signaling, or appropriate libp2p host). **WebRTC does not remove the need for signaling and reachable ICE candidate paths; relays may be needed.**
6. For LoRa/Meshtastic, test tiny text/telemetry only within radio regulations and duty cycle limits. **LoRa is not a broadband WebRTC video transport.**
7. Optional internet bridging requires an ISP that permits sharing, real uplink capacity, network abuse controls, and user consent.
8. For NextGraph, integrate the official CRDT APIs only after checking exact protocol, document permissions and version. The current LWW demonstration is a separate model.
9. VPU / i-Silo-1 hardware requires actual PCI/MMIO enumeration, device-tree or PCI IDs, a driver spec, bounds checks, DMA safety, timeout handling, scatter-gather rules and cryptographic attestation. **Do not insert the supplied kernel driver into Linux.** It uses unverified fixed register addresses, unsafe packet resizing, an unbounded spin loop and a transmit recursion hazard. No hardware driver has been loaded by this feature.
10. Request independent verification only after cryptographic identity proof, audited E2EE code, observed packet delivery and signed witnesses. Digest-only records are NOT certified.

## Why free and private cannot be guaranteed
User-hosted nodes still incur radio hardware, power, maintenance, internet backhaul and spectrum costs. Encryption does not eliminate metadata exposure, physical radio observation, jamming, or compromise. A completely offline local mesh works only where a physical path exists.

## Licensing
Netmaker's currently published repository describes Apache-2.0 for the primary tree with separate terms for `pro/` and third-party components. Reconfirm for pinned source revision. Linux kernel code and external open telecom software may have independent GPL, AGPL, or other terms. An Apache-2.0-only iModels policy does not magically relicense every telecommunications dependency.

## Testing
```bash
cd i-api
python -m unittest -v test_dewi_mesh.py
```
Github CI `Buddy Universal API Live Integration` also runs the iDeWi unit tests and its existing container HTTP smoke.

## User privacy
Do not use real IMEI, MAC addresses, ICCID, eSIM EID, government assistance IDs, or credential tokens as public routing handles. App-level identities should use device-generated keys with explicit registration, secure backup, rotation and recovery.
