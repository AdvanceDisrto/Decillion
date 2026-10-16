"""iModels — strict Apache-2.0-only execution policy.
Legacy model addresses may exist but are never called through this module.
The license is operator-declared pending independent checkpoint audit.
"""
import os
from fastapi import APIRouter, HTTPException
from universal_router import active, infer, apache_policy_ready

router=APIRouter(prefix="/v1/models",tags=["iModels"])
IDS={"buddy":os.getenv("IMODELS_BUDDY_MODEL_ID",""),
     "the-one":os.getenv("IMODELS_THE_ONE_MODEL_ID","")}

def configured(name):
    return name in IDS and bool(active())

@router.get("")
async def registry():
    enabled=bool(active())
    return {"models":[{
        "name":name,"model_id":os.getenv("IAPI_APACHE2_MODEL_ID") if enabled else None,
        "endpoint_configured":enabled,
        "license_policy":"Apache-2.0-only",
        "license_declared":apache_policy_ready(),
        "weights_verified":False,"inference_verified":False,
        "verification_note":"Declared SPDX/revision and API configuration are not independently verified weights or inference"
        } for name in IDS],
        "legacy_buddy_adapter_configured":False,
        "api_protocol":"OpenAI-compatible /v1/chat/completions",
        "other_provider_inference_allowed":False}

@router.get("/probe")
async def probe():
    if not active():
        return {"status":"not-configured","reason":"Apache-2.0-only licensed model endpoint and declaration required",
                "inference_sample_verified":False}
    return {"status":"configured-not-probed","license_declared":apache_policy_ready(),
            "model_id":os.getenv("IAPI_APACHE2_MODEL_ID"),"inference_sample_verified":False}

async def complete(name,request):
    if name not in IDS:raise HTTPException(404,"Unknown iModels model")
    return await infer(request,preferred="apache2-licensed-llm")
