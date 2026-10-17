"""i™ SAH-SIA environmental room simulation; no real smart-crystal, sensors or optics.
Only scoped certificate evidence can cross room boundary; geometric balance does not confer truth.
"""
from __future__ import annotations
from dataclasses import dataclass,field
import hashlib,json,math
from independent_certifier import verify_certificate,cert_id
from script_flip import negate_matrix

def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
@dataclass
class AmbientRoom:
    room_id:str
    state:str="DORMANT_SIMULATED"
    local_claims:list=field(default_factory=list)
    quarantined:bool=False
    def awaken(self,field_vector):
        if self.quarantined:raise PermissionError("Room quarantined")
        if not isinstance(field_vector,list) or len(field_vector)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in field_vector):
            raise ValueError("Expected finite 3D simulated field")
        self.state="ACTIVE_SIMULATED"
        return {"state":self.state,"inverted_field":negate_matrix([field_vector])[0],
                "hardware_real":False,"performance_multiplier":None}
    def sleep(self):self.state="DORMANT_SIMULATED"
    def quarantine(self):self.quarantined=True;self.state="QUARANTINED_SIMULATED"

@dataclass
class Lattice:
    published:list=field(default_factory=list)
    def add(self,event):self.published.append(event)

class Boundary:
    def __init__(self,room,ledger,issuer_pub_b64,revocation_registry):
        self.room,self.ledger,self.pub,self.revocations=room,ledger,issuer_pub_b64,revocation_registry
    def process(self,claim,vertices,certificate=None):
        self.room.local_claims.append({"sha256":hashlib.sha256(claim.encode()).hexdigest(),"status":"LOCAL_ONLY"})
        if self.room.quarantined:return {"status":"DENIED","reason":"Room quarantined"}
        if self.room.state!="ACTIVE_SIMULATED":return {"status":"DENIED","reason":"Room inactive"}
        if not isinstance(vertices,list) or not vertices or any(type(v) not in (float,int) or not math.isfinite(v) for v in vertices):
            return {"status":"DENIED","reason":"Invalid geometric representation"}
        closure=sum(vertices)
        geometry={"sum":closure,"note":"Closure is illustrative and is not a factual verifier"}
        if not certificate:return {"status":"LOCAL_ONLY","geometry":geometry,"reason":"No independent evidence-integrity certificate"}
        if not verify_certificate(certificate,self.pub):
            self.room.quarantine();return {"status":"QUARANTINED","reason":"Invalid certificate signature"}
        cid=cert_id(certificate)
        if not self.revocations.integrity() or self.revocations.is_revoked(cid):
            return {"status":"DENIED","reason":"Certificate revoked or audit unavailable"}
        if certificate["payload"].get("status")!="CERTIFIED_EVIDENCE_INTEGRITY_ONLY":
            return {"status":"DENIED","reason":"Unexpected certificate scope"}
        event={"schema":"i.sah-sia.boundary/1","claim_sha256":hashlib.sha256(claim.encode()).hexdigest(),
               "room_id":self.room.room_id,"certificate_id":cid,
               "classification":"CERTIFIED_EVIDENCE_INTEGRITY_ONLY",
               "geometry":geometry,"is_factual_truth_certified":False,
               "is_hardware_actuated":False}
        # This event does not contain raw private claim text or sensor data.
        self.ledger.add(event)
        return {"status":"PUBLISHED_EVIDENCE_ATTESTATION","event":event}

def display_receipt(result):
    """JSON projection instructions, not a physical hologram."""
    return {"device":"SIMULATED_VIEW","visible":result.get("status")=="PUBLISHED_EVIDENCE_ATTESTATION",
            "color":"amber" if result.get("status")=="PUBLISHED_EVIDENCE_ATTESTATION" else "red",
            "label":"Evidence integrity only — not verified fact",
            "physical_photons_emitted":False}
