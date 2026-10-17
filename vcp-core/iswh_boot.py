"""iSoftwareHardware (iSWH) 1.0: non-destructive measured-boot policy gates.
This DOES NOT flash firmware, erase data, control physical transistors, attest
a TPM remotely, or claim that any AI answer is absolutely true.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib, json, time

class BootPhase(str,Enum):
    POWER="POWER_INITIALIZATION"
    KERNEL="VERIFIER_INTEGRITY"
    EVIDENCE="EVIDENCE_AND_CLOCK"
    LATTICE="SERVICE_ISOLATION"
    READY="READY_FOR_SCOPED_CHECKS"
    DENIED="DENIED"
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

@dataclass(frozen=True)
class Manifest:
    device_id:str
    firmware_digest:str
    verifier_digest:str
    source_registry_digest:str
    expected_device_id:str
    approved_firmware_digest:str
    approved_verifier_digest:str
    approved_source_registry_digest:str
    clock_unix:int
    audit_healthy:bool
    ice_isolated:bool
    model_can_sign:bool
    execution_gate_active:bool

def boot(manifest:Manifest, now:int|None=None):
    now=int(time.time()) if now is None else now
    history=[]
    def phase(stage,ok,detail):
        history.append({"phase":stage.value,"passed":ok,"detail":detail})
        return ok
    device=manifest.device_id==manifest.expected_device_id and bool(manifest.device_id)
    if not phase(BootPhase.POWER,device,"Device identity matches trusted operator baseline" if device else "Device identity mismatch"):
        return decision(False,history,manifest)
    for title,actual,expected in (
        ("firmware",manifest.firmware_digest,manifest.approved_firmware_digest),
        ("verifier",manifest.verifier_digest,manifest.approved_verifier_digest)):
        valid=(len(actual)==64 and all(c in "0123456789abcdef" for c in actual) and actual==expected)
        if not phase(BootPhase.KERNEL,valid,title+" matched pinned digest" if valid else title+" digest mismatch"):
            return decision(False,history,manifest)
    valid=(len(manifest.source_registry_digest)==64 and
           manifest.source_registry_digest==manifest.approved_source_registry_digest and
           abs(now-manifest.clock_unix)<=120 and manifest.audit_healthy)
    if not phase(BootPhase.EVIDENCE,valid,"Clock, audit and approved registry checked" if valid else "Clock, audit or registry failed"):
        return decision(False,history,manifest)
    valid=manifest.ice_isolated and not manifest.model_can_sign and manifest.execution_gate_active
    if not phase(BootPhase.LATTICE,valid,"Issuer separate from model; action gate present" if valid else "Critical trust boundary absent"):
        return decision(False,history,manifest)
    phase(BootPhase.READY,True,"Ready only for individually verified operations; NOT certified truth")
    return decision(True,history,manifest)

def decision(ready,history,manifest):
    output={"schema":"i.swh.boot-assessment/1",
            "status":"READY_FOR_SCOPED_CHECKS" if ready else "DENIED",
            "phases":history,"device_id":manifest.device_id,
            "limitations":["Self-reported hashes are not independent measured-boot attestation",
                           "Requires TPM/Secure Enclave trust chain for hardware assurance",
                           "No hardware writes or vendor firmware modification performed",
                           "No AI factual certainty or performance multiplier established"]}
    output["assessment_sha256"]=hashlib.sha256(canonical(output)).hexdigest()
    return output
