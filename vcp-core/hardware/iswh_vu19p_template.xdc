# iSWH XCVU19P TEMPLATE, NOT A PCB PINOUT, NOT SAFE FOR MANUFACTURING
# Proposed pins AN12, BA2, etc. from prompt NOT VALIDATED.
# JESD204B RX lanes terminate at GTY MGT transceiver pins; ordinary LVDS fabric
# IBUFDS shift registers cannot replace compliant JESD204B RX and SYSREF logic.
# TODO: choose exact part/package/speed-grade and engineering evaluation board
# TODO: confirm GTY quads, REFCLK, dedicated clock paths, package pin table, rail voltages
# TODO: validated board schematic, trace impedance / lane skew / SI/PI/EMC, Vivado DRC
# Example only after validated clock exists:
# create_clock -name fabric_clk -period 4.000 [get_ports clk]
# NEVER apply guessed set_property PACKAGE_PIN assignments.
