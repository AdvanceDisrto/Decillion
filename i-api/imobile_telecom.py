"""iMobile Sovereign Network — bounded @handle message transport rehearsal.

This is an app-layer demo over an existing authorized IP connection.
No SIM bypass, RAN access, actual CAMARA subscription, live telecom,
or emergency delivery occurs.
"""
from __future__ import annotations
import base64
import hashlib
import json
import math
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

router=APIRouter(prefix="/v1/imobile",tags=["iMobile"])

COMPONENTS=(
  ("CAMARA","Apache-2.0 API specification adapter, no operator subscription"),
  ("M-CORD","concept-only EPC integration, no running core"),
  ("Cozystack","edge deployment target, no linked cluster"),
  ("SONiC","switch management target, no linked switch"),
  ("libp2p","P2P transport target, no peers paired"),
)
def stable(d):return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def hexhash(d):return hashlib.sha256(stable(d)).hexdigest()

class RouteTest(BaseModel):
    from_handle:str=Field(default="@sender",min_length=2,max_length=41,pattern=r"^@[A-Za-z0-9_.-]{1,40}$")
    to_handle:str=Field(default="@buddy",min_length=2,max_length=41,pattern=r"^@[A-Za-z0-9_.-]{1,40}$")
    payload:str=Field(default="Test packet — no delivery attempted",min_length=1,max_length=2048)
    total_nodes:int=Field(default=12,ge=2,le=256)
    blackout_fraction:float=Field(default=.5,ge=0,lt=1)
    seed:int=Field(default=11,ge=0,le=1000000)
    transport:str=Field(default="authorized-ip-lan")

def simulate_route(req:RouteTest):
    if req.transport not in ("authorized-ip-lan","connected-internet","offline-store-forward"):
        raise HTTPException(422,"Unknown transport type")
    # HMAC or Ed25519 over real device keys would require real enrollment.
    # Ephemeral test signing proves deterministic packet bytes can be signed, not a user identity.
    import random
    rng=random.Random(req.seed)
    nodes=list(range(req.total_nodes))
    lost=set(rng.sample(nodes,math.floor(req.total_nodes*req.blackout_fraction)))
    available=[x for x in nodes if x not in lost]
    if not available:raise HTTPException(422,"No surviving simulated route")
    path=[available[i%len(available)] for i in range(min(3,len(available)))]
    packet={"schema":"i-mobile-test-packet/1","from":req.from_handle,
            "to":req.to_handle,"transport":req.transport,
            "message_digest":hashlib.sha256(req.payload.encode()).hexdigest(),
            "bytes":len(req.payload.encode()),"blackout_simulated":req.blackout_fraction,
            "route":[f"sim-node-{x}" for x in path],
            "carrier_authenticated":False,"sim_authenticated":False,
            "actually_delivered":False,"real_peer_connection":False}
    key=Ed25519PrivateKey.generate()
    sig=key.sign(stable(packet))
    pub=key.public_key()
    pub.verify(sig,stable(packet))
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
    receipt={"packet_sha256":hexhash(packet),
             "test_signature":base64.b64encode(sig).decode(),
             "test_public_key":base64.b64encode(pub.public_bytes(Encoding.Raw,PublicFormat.Raw)).decode(),
             "signature_scope":"ephemeral test key; not bound to a registered user or hardware",
             "production_certified":False,"network_delivery_verified":False}
    return {"status":"SIMULATED_NOT_TRANSMITTED",
            "nodes_total":req.total_nodes,"nodes_offline":len(lost),
            "nodes_available":len(available),"route":packet["route"],
            "packet":packet,"receipt":receipt}

@router.get("/capabilities")
async def capabilities():
    return {
        "project":"iMobile Sovereign Open Telco Lab",
        "components":[{"name":name,"status":"adapter-design-only","note":note} for name,note in COMPONENTS],
        "carrier_connected":False,"subscriber_authentication_bypassed":False,
        "numberless_app_id_supported":True,"numberless_cellular_subscription":False,
        "camara_api_authorized":False,"mcord_connected":False,
        "cozystack_connected":False,"sonic_connected":False,
        "real_local_radio_connected":False,
        "offline_transport":"store-and-forward design only; no physical peer attached",
        "free_public_assistance_provisioned":False,
        "service_not_for_emergency_use":True
    }

@router.post("/simulate")
async def simulate(req:RouteTest):
    return simulate_route(req)
