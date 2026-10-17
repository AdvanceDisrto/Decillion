# iSWH 1.0 electrical / FPGA research starter
Development-only, no verified pinout, hardware fabrication, FPGA bitstream or validated JESD link.

* `iswh_ingest.vhd`: dual 14-bit **fabric-side** sampled data gate after vendor JESD RX link decoding, not raw AD9208 serial decoding.
* `iswh_vu19p_template.xdc`: deliberately **no unverified physical FPGA pin assignments**. Complete only from verified package-specific pin tables, board schematic and tested transceiver constraints.
* `power_budget.py`: rail/efficiency/nameplate estimates. At 700 W, 0.85 V: ~823.529 A load; ±0.5% is ±4.25 mV; 90%-efficient VRM loss ~77.778 W. These are not physical measurements.
* `test_power_budget.py`: arithmetic tests.

**Component corrections:** AMD XCVU19P has ~8.938M logic cells, 3840 DSP slices, 2072 I/O pins (not 2072 TeraMACs). AD9208 dual 14-bit 3 GSPS JESD204B requires proper high-speed SERDES and JESD RX IP. TI DLP9000X with DLPC910 is a 2560×1600 high-speed spatial light modulator, not by itself a free-space volumetric hologram. A PUF/specific secure element's physical claims require exact SKU validation. Do not use assumed 3200W PSU compatibility or liquid nitrogen cooling without specialist safety design.

**Source references**: AMD https://www.amd.com/en/products/adaptive-socs-and-fpgas/fpga/virtex-ultrascale-plus-vu19p.html ; ADI https://www.analog.com/en/products/AD9208.html ; TI https://www.ti.com/product/DLP9000X ; NXP https://www.nxp.com/pages/edgelock-se050-plug-and-trust-secure-element-family-enhanced-iot-security-with-high-flexibility:SE050 .

**Hardware acceptance gates:** select exact dev board & package; verify JESD RX using vendor supported IP with proper clock/GTY pinout; create legal XDC from board CAD; execute VHDL simulator plus Vivado timing/DRC; validate PDN load steps with instruments, SI/PI, thermal and optical safety; witness independent ICE crypto tests. The numerical stream gate enforces an externally supplied policy signal, **not truth detection**. No 2.5× performance result is established.
