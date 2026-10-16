"""i™ Wireless Mesh Lab — verifiable software topology, app identities, merge tests.

No Wi-Fi/LoRa/Cellular hardware or VPU MMIO is operated by this service.
Graph routing is a deterministic local simulation; receipt digests are unsigned.
"""
from __future__ import annotations
import hashlib, heapq, json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/dewi",tags=["iDeWi Mesh"])
class Link(BaseModel):
    a:str=Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    b:str=Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    latency_ms:float=Field(gt=0,le=100000)
    transport:str="wifi"
class Route(BaseModel):
    source:str=Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    destination:str=Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    links:list[Link]=Field(max_length=128)
    offline_nodes:list[str]=Field(default_factory=list,max_length=128)

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def shortest(req:Route):
    allowed={"wifi","ethernet","lora","lan"}
    edges={}
    for e in req.links:
        if e.transport not in allowed:raise HTTPException(422,"Unsupported transport label")
        if e.a==e.b:raise HTTPException(422,"Self-loop not permitted")
        edges.setdefault(e.a,[]).append((e.latency_ms,e.b,e.transport))
        edges.setdefault(e.b,[]).append((e.latency_ms,e.a,e.transport))
    offline=set(req.offline_nodes)
    path=None; transports=[];cost=None
    if req.source not in offline and req.destination not in offline:
        heap=[(0.0,req.source,[req.source],[])]
        seen=set()
        while heap:
            d,n,p,t=heapq.heappop(heap)
            if n in seen:continue
            seen.add(n)
            if n==req.destination:path=p;transports=t;cost=round(d,4);break
            for weight,v,label in edges.get(n,[]):
                if v not in seen and v not in offline:
                    heapq.heappush(heap,(d+weight,v,p+[v],t+[label]))
    record={"schema":"i-dewi-route-simulation/1","source":req.source,
      "destination":req.destination,"path":path,"transports":transports,
      "estimated_link_cost_ms":cost,"offline_nodes":sorted(offline),
      "physical_network_connected":False,"actual_packets_delivered":0,
      "identity_authenticated":False,"carrier_access_bypassed":False,
      "vpu_hardware_stamp":False}
    return {"route":record,"receipt":{"body":record,"sha256":digest(record),
             "signature":None,"certified":False}}

class Change(BaseModel):
    doc:str=Field(min_length=1,max_length=64)
    key:str=Field(min_length=1,max_length=64)
    value:str=Field(max_length=1024)
    counter:int=Field(ge=0,le=1000000000)
    actor:str=Field(min_length=1,max_length=64)
class Sync(BaseModel):
    left:list[Change]=Field(default_factory=list,max_length=100)
    right:list[Change]=Field(default_factory=list,max_length=100)

def merge(req:Sync):
    # CRDT-inspired LWW register with deterministic (counter, actor, value)
    # ordering. This IS NOT the NextGraph protocol or a smart contract.
    merged={}
    for event in req.left+req.right:
        k=(event.doc,event.key)
        old=merged.get(k)
        if old is None or (event.counter,event.actor,event.value)>(old.counter,old.actor,old.value):
            merged[k]=event
    state=[{"doc":d,"key":k,"value":v.value,"counter":v.counter,"actor":v.actor}
           for (d,k),v in sorted(merged.items())]
    body={"schema":"i-dewi-merge-prototype/1","state":state,
          "algorithm":"deterministic LWW demo; not NextGraph",
          "replica_authority_verified":False,"network_sync_performed":False}
    return {"state":state,"receipt":{"body":body,"sha256":digest(body),
        "signature":None,"certified":False}}

@router.get("/capabilities")
async def capabilities():
    return {"software_mesh_routing":True,"simulated_offline_recovery":True,
      "sync_algorithm":"LWW demo (not NextGraph)","connected_physical_mesh_nodes":0,
      "pwa_wifi_direct_control":False,"pwa_lora_control":False,
      "openwrt_managed_routers":0,"vpu_hardware_available":False,
      "global_internet_uplink":False,"real_webrtc_calls_verified":False}

@router.post("/route")
async def route(req:Route):return shortest(req)
@router.post("/merge")
async def merge_state(req:Sync):return merge(req)
