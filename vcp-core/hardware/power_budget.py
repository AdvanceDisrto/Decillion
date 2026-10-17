"""Uncertified initial PDN arithmetic; not a VRM layout or thermal certification."""
def budget(volts=0.85,watts=700.0,ripple_percent=0.5,efficiency=0.90,psu_count=4,psu_watts=3200):
    if not (0<volts and 0<watts and 0<ripple_percent<100 and 0<efficiency<=1 and psu_count>0 and psu_watts>0):
        raise ValueError("Invalid electrical assumptions")
    return {"rail_amps":round(watts/volts,3),
            "max_voltage_excursion_mV":round(volts*ripple_percent*10,3),
            "vrm_input_watts":round(watts/efficiency,3),
            "vrm_loss_watts":round(watts/efficiency-watts,3),
            "total_psu_nameplate_watts":psu_count*psu_watts,
            "n_minus_one_nameplate_watts":(psu_count-1)*psu_watts,
            "qualifier":"Estimates only; validate VRM phase current, PDN impedance, PSU redundancy, thermal, transients and PCB design."}
if __name__=="__main__":
    import json
    print(json.dumps(budget(),indent=2))
