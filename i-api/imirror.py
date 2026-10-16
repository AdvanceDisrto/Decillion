"""iMirror: explicit finite snapshots and software-only fault recovery.

This is not a digital twin of unobserved physical hardware or proof of
cloud synchronization. No camera streams or biometrics pass through this API.
"""
import hashlib
import json
import time
from fastapi import APIRouter
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/imirror",tags=["iMirror"])

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

class iMirror:
    def __init__(self):
        self.local={}
        self.remote={}
    def sync_reflective_matrix(self,real_time=False):
        # No remote transfer takes place. Caller must explicitly supply remote observations.
        fields=set(self.local)|set(self.remote)
        aligned=sum(self.local.get(k)==self.remote.get(k) for k in fields)
        return {"matched_fields":aligned,"total_fields":len(fields),
                "symmetry_index":aligned/len(fields) if fields else None,
                "live_cloud_sync":False,"real_time_requested":bool(real_time)}
    class Camera:
        def status(self):
            return {"state":"requires-explicit-browser-permission",
                    "server_camera_stream":False,"depth_points_measured":0}

class FaultTolerance:
    @staticmethod
    def register_crash_handler(failover="iMirror_Cloud_State"):
        return {"mode":"snapshot-simulation-only","failover_requested":failover,
                "physical_device_recovered":False}

class MirrorRequest(BaseModel):
    local:dict[str,str|int|bool|None]=Field(default_factory=dict,max_length=32)
    remote:dict[str,str|int|bool|None]=Field(default_factory=dict,max_length=32)
    inject_mock_crash:bool=False

@router.get("/capabilities")
async def capabilities():
    return {"physical_radio_connected":False,"camera_depth_verified":False,
            "cloud_mirror_persistent":False,"fault_recovery_verified":False,
            "status":"software-simulation-and-browser-telemetry"}

@router.post("/compare")
async def compare(body:MirrorRequest):
    m=iMirror()
    m.local=dict(body.local)
    m.remote=dict(body.remote)
    state=m.sync_reflective_matrix(real_time=False)
    recovery=None
    if body.inject_mock_crash:
        snapshot=canonical(m.local);started=time.perf_counter_ns()
        m.local={};m.local=json.loads(snapshot)
        recovery={"snapshot_match":canonical(m.local)==snapshot,
                  "measured_in_memory_ms":(time.perf_counter_ns()-started)/1_000_000,
                  "actual_device_crashed":False,"cloud_recovery_verified":False}
    record={"schema":"i-mirror-test/1","result":state,"fault_simulation":recovery,
            "hardware_verified":False,"signature":None,"anchored":False}
    return {"result":state,"fault_simulation":recovery,
            "receipt":{"body":record,"sha256":digest(record),"certification":"not-issued"}}
