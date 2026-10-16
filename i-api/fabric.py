"""i™ Fabric registry. Capability != successful execution, advertised hardware != attested hardware."""
import os
from fastapi import APIRouter
router=APIRouter(prefix="/v1/fabric",tags=["iFabric"])
UNITS={
 "cpu":("browser-local","JavaScript/WASM on client; backend Python runtime"),
 "gpu":("client-or-remote","WebGPU on client, GPU model-serving node when configured"),
 "npu":("client-conditional","WebNN where available; physical NPU path not proven"),
 "apu":("device-specific","Unified mobile SoC; hardware identity unavailable to browser"),
 "tpu":("remote-only","TPU requires separately authorized serving node"),
 "spu":("remote-only","iSPU hardware requires runtime and independently verifiable device evidence"),
 "imods":("software","Capability-limited event/action modules and registry"),
 "igptm":("remote-model","iModels text generation via authenticated API")
}
@router.get("/capabilities")
async def capabilities():
    return {"protocol":"i-fabric/0.1","mode":"honest-discovery",
      "modules":[{"id":k,"route":v[0],"description":v[1],
        "configured":bool(os.getenv("IMODELS_INFERENCE_BASE_URL") and os.getenv("IMODELS_BUDDY_MODEL_ID")) if k=="igptm"
          else bool(os.getenv("IFABRIC_TPU_URL")) if k=="tpu"
          else bool(os.getenv("IFABRIC_SPU_URL")) if k=="spu"
          else True if k in ("cpu","imods") else None,
        "execution_verified":False,"physical_attestation":False}
        for k,v in UNITS.items()],
      "verification_note":"Browser and server configuration do not certify actual silicon or model weights"}
