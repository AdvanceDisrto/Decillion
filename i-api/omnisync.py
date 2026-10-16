"""Project Omni-Sync optional renderer gateway: no fake jobs, authenticated user requests.
Serves browser PWA only once JWT auth and an external renderer are configured."""
import os
import secrets
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/omnisync",tags=["Omni-Sync"])
URL=os.getenv("OMNISYNC_PROVIDER_URL","").rstrip("/")
TOKEN=os.getenv("OMNISYNC_PROVIDER_TOKEN","")
def configured():
    p=urlparse(URL)
    return bool(p.scheme=="https" and p.hostname and TOKEN)
class RenderJob(BaseModel):
    archetype:str=Field(pattern="^(human|anime|creature)$")
    prompt:str=Field(min_length=8,max_length=1200)
@router.get("/capabilities")
async def capabilities():
    return {"archetypes":["human","anime","creature"],"local_preview":True,
      "provider_configured":configured(),"remote_vram_unlimited":False,
      "neural_render_verified":False,"hardware_attested":False}
@router.post("/jobs")
async def create_job(req:RenderJob,authorization:str=Header(default="")):
    from main import user_id
    await user_id(authorization)
    if not configured():raise HTTPException(503,"External GPU renderer is not connected")
    job_id=secrets.token_hex(16)
    try:
        async with httpx.AsyncClient(timeout=20,follow_redirects=False) as client:
            resp=await client.post(URL,headers={"Authorization":"Bearer "+TOKEN},
               json={"job_id":job_id,"archetype":req.archetype,"prompt":req.prompt})
            resp.raise_for_status()
        data=resp.json()
        if data.get("status") not in {"queued","running","completed"}:raise ValueError("invalid provider response")
        return {"id":str(data.get("id") or job_id),"status":data["status"]}
    except Exception as exc:
        raise HTTPException(502,"GPU provider error: "+type(exc).__name__)
@router.get("/jobs/{job_id}")
async def get_job(job_id:str,authorization:str=Header(default="")):
    from main import user_id
    await user_id(authorization)
    if not configured():raise HTTPException(503,"External GPU renderer is not connected")
    if not (8<=len(job_id)<=128 and all(c.isalnum() or c in "_-" for c in job_id)):
        raise HTTPException(400,"Invalid job ID")
    try:
        async with httpx.AsyncClient(timeout=15,follow_redirects=False) as client:
            resp=await client.get(URL+"/"+job_id,headers={"Authorization":"Bearer "+TOKEN})
            resp.raise_for_status()
        result=resp.json()
        clean={"id":str(result.get("id") or job_id),"status":str(result.get("status") or "unknown")}
        video=result.get("output_url")
        if isinstance(video,str) and urlparse(video).scheme=="https":clean["output_url"]=video
        return clean
    except Exception as exc:
        raise HTTPException(502,"GPU provider error: "+type(exc).__name__)
