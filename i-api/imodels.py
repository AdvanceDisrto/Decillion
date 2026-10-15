"""iModels runtime adapter: explicitly configured, authenticated server-side native-model inference.
This does not claim possession of trained weights or that a configured model has been loaded."""
import os
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/models", tags=["iModels"])
BASE = os.getenv("IMODELS_INFERENCE_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("IMODELS_INFERENCE_API_KEY", "")
IDS = {"buddy":os.getenv("IMODELS_BUDDY_MODEL_ID", ""),"the-one":os.getenv("IMODELS_THE_ONE_MODEL_ID", "")}
def configured(name):
    return bool(BASE and IDS.get(name))
def valid_base():
    if not BASE:
        return False
    p=urlparse(BASE)
    return p.scheme=="https" or (p.scheme=="http" and p.hostname in {"localhost","127.0.0.1"})
def headers():
    return {"Authorization":"Bearer "+API_KEY} if API_KEY else {}
@router.get("")
async def registry():
    return {"models":[{"name":key,"model_id":value or None,
        "endpoint_configured":configured(key),
        "weights_verified":False,
        "inference_verified":False,
        "verification_note":"No checkpoint hash or completed sample-generation attestation available through this endpoint"}
        for key,value in IDS.items()],
        "api_protocol":"OpenAI-compatible /v1/chat/completions",
        "legacy_buddy_adapter_configured":bool(os.getenv("BUDDY_MODEL_URL") and os.getenv("BUDDY_MODEL_TOKEN"))}
@router.get("/probe")
async def probe():
    if not valid_base():
        return {"status":"not-configured","reason":"No trusted iModels inference endpoint configured"}
    try:
        async with httpx.AsyncClient(timeout=8,follow_redirects=False) as client:
            resp=await client.get(BASE+"/models",headers=headers())
        if resp.status_code!=200:
            return {"status":"unavailable","status_code":resp.status_code}
        data=resp.json()
        advertised={m.get("id") for m in data.get("data",[]) if isinstance(m,dict)}
        return {"status":"server-reachable","advertised_models":[{"name":name,"id":ID,"advertised":ID in advertised} for name,ID in IDS.items() if ID],
                "inference_sample_verified":False}
    except Exception:
        return {"status":"unavailable"}
async def complete(name,request):
    if name not in IDS:
        raise HTTPException(404,"Unknown iModels model")
    if not configured(name) or not valid_base():
        raise HTTPException(503,"No trusted inference endpoint and model ID configured for "+name)
    system="You are Buddy i™, the friendly voice-and-action assistant in the i™ ecosystem. Explain capabilities accurately. Never claim an external action was executed without evidence." if name=="buddy" else "You are i™ THE ONE, a reasoning model in the i™ ecosystem. Be precise and do not invent execution evidence."
    payload={"model":IDS[name],"messages":[{"role":"system","content":system},{"role":"user","content":request}],"max_tokens":768,"temperature":0.5,"stream":False}
    try:
        async with httpx.AsyncClient(timeout=70,follow_redirects=False) as client:
            resp=await client.post(BASE+"/chat/completions",headers={**headers(),"Content-Type":"application/json"},json=payload)
            resp.raise_for_status()
        data=resp.json()
        content=data["choices"][0]["message"]["content"]
        if not isinstance(content,str) or not content.strip():
            raise ValueError("Empty generation")
        return content,IDS[name]
    except Exception:
        raise HTTPException(502,"Configured "+name+" model did not return a valid response")
