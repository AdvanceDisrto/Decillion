"""i™ Lifeline network lab: bounded, non-emergency route planning.
No carrier interconnect, satellite access, Lifeline enrollment, or emergency delivery.
"""
from __future__ import annotations
import hashlib
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/lifeline",tags=["iLifeline"])
ROUTES=("starlink-direct-to-cell","att","verizon","t-mobile","solar-wifi-local")

class Message(BaseModel):
    handle:str=Field(min_length=2,max_length=41,pattern=r"^@[a-zA-Z0-9_.-]{1,40}$")
    message:str=Field(min_length=1,max_length=1024)
    route:str=Field(default="solar-wifi-local")
    simulate_outage:bool=False

class Power(BaseModel):
    battery_wh:float=Field(gt=0,le=200000)
    solar_w:float=Field(ge=0,le=100000)
    base_w:float=Field(gt=0,le=10000)
    radio_w:float=Field(ge=0,le=10000)
    duty_cycle:float=Field(ge=0,le=1)

def power_budget(body:Power):
    draw=body.base_w+body.radio_w*body.duty_cycle
    net=body.solar_w-draw
    runtime=None if net>=0 else round(body.battery_wh/(-net),3)
    return {"estimated_consumption_w":round(draw,3),"estimated_net_power_w":round(net,3),
            "estimated_runtime_hours":runtime,"scope":"simplified energy budget, not measured photovoltaic generation or certified hardware"}

@router.get("/capabilities")
async def capabilities():
    return {"carriers":[{"id":route,"connected":False,"provisioned":False} for route in ROUTES],
       "subscriber_bypass":False,"automatic_911_delivery":False,"pwa_carrier_radio_access":False,
       "network_delivery_available":False,"test_mode":"local-packet-simulation",
       "message":"No satellite or carrier network is attached. This cannot replace an emergency call."}

@router.post("/mock-packet")
async def mock_packet(packet:Message):
    if packet.route not in ROUTES:raise HTTPException(422,"Unknown simulated route")
    body={"schema":"i-lifeline-test/1","route":packet.route,"handle":packet.handle,
        "message_sha256":hashlib.sha256(packet.message.encode()).hexdigest(),
        "bytes":len(packet.message.encode()),"outage_simulated":packet.simulate_outage,
        "actually_transmitted":False,"peer_authenticated":False,"emergency_dispatched":False}
    h=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {"status":"SIMULATED_NOT_DELIVERED","receipt":{"body":body,"sha256":h,
        "signature":None,"anchored":False,"certification":"not-issued"}}

@router.post("/power-budget")
async def estimate_power(body:Power):
    return power_budget(body)
