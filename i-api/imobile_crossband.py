"""iMobile Cross-Band & Billing Lab — deterministic hypothetical routing only.

No real carrier, satellite, Wi-Fi Direct, BLE or user device is contacted. No
hardware identifiers, assistance identifiers or provider credentials accepted.
Revenue is a hypothetical projection, never settled or charged.
"""
from __future__ import annotations
import hashlib, json, math
from fastapi import APIRouter
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/imobile",tags=["iMobile Analysis"])
ROUTES=("authorized-local-lan","satellite-partner","cellular-partner")
class Scenario(BaseModel):
    packets:int=Field(default=1000,ge=1,le=100000)
    bytes_per_packet:int=Field(default=1024,ge=64,le=16384)
    local_available:bool=True
    satellite_available:bool=False
    cellular_available:bool=False
    satellite_outage:bool=False
    cellular_outage:bool=False
    unit_price_usd_per_gb:float=Field(default=2,ge=0,le=100)
    unit_cost_usd_per_gb:float=Field(default=1,ge=0,le=100)
    scenario_only:bool=True

def run_scenario(p:Scenario):
    """Use caller-declared hypothetical paths, never infer live capability."""
    reachable=[]
    if p.local_available:reachable.append(ROUTES[0])
    if p.satellite_available and not p.satellite_outage:reachable.append(ROUTES[1])
    if p.cellular_available and not p.cellular_outage:reachable.append(ROUTES[2])
    schedule={r:0 for r in ROUTES}
    queued=0
    for i in range(p.packets):
        if not reachable:queued+=1
        else:schedule[reachable[i%len(reachable)]]+=1
    bytes_assumed=p.packets*p.bytes_per_packet
    delivered=0  # No physical packet was ever transmitted.
    gb=bytes_assumed/1e9
    receipt_body={"schema":"i-mobile-crossband-simulation/1",
                  "routes":schedule,"not_transmitted_packets":p.packets,
                  "simulated_store_and_forward":queued,
                  "actual_packets_delivered":delivered,"scenario":p.model_dump(),
                  "usage_bytes_assumed":bytes_assumed,
                  "projected_revenue_usd":round(gb*p.unit_price_usd_per_gb,6),
                  "projected_cost_usd":round(gb*p.unit_cost_usd_per_gb,6),
                  "actual_revenue_usd":0,
                  "carrier_provisioning_verified":False,
                  "simulation_only":True,
                  "hardware_identifiers_collected":False,
                  "government_eligibility_verified":False}
    digest=hashlib.sha256(json.dumps(receipt_body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return {"routes":schedule,"store_and_forward_units":queued,
       "actual_deliveries":delivered,
       "receipt":{"body":receipt_body,"sha256":digest,
                  "signature":None,"hardware_attestation":False,
                  "certification":"NOT_ISSUED"}}

@router.post("/crossband-rehearsal")
async def crossband_rehearsal(body:Scenario):
    return run_scenario(body)

@router.get("/crossband-capabilities")
async def crossband_capabilities():
    return {"status":"simulation-only",
            "starlink_connected":False,"cellular_connected":False,
            "wifi_direct_connected":False,"lan_peer_authenticated":False,
            "billing_active":False,"lifeline_provisioned":False,
            "krdid_status":"not queried",
            "notice":"No subscriber unlocking, SSI authorization or carrier access is implemented."}
