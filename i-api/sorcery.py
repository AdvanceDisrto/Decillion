"""Sorcery mobile operations. Explicit server allowlist, never arbitrary shell."""
import os
import hashlib
import json
from datetime import datetime,timezone
import httpx
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel
router=APIRouter(prefix="/v1/sorcery",tags=["Sorcery"])
REPO="AdvanceDisrto/Decillion"
REF="feature/buddy-receipts-backend-20261015"
WORKFLOWS={
 "android": "imobile-android-apk.yml",
 "ios-core": "im-crossplane.yml",
 "backend-tests": "iuniversalapi-live.yml"
}
def allowed(uid):
 return uid in set(filter(None,(x.strip() for x in os.getenv("I_SORCERY_OPERATOR_UIDS","").split(","))))
async def principal(auth):
 from main import user_id
 uid,_=await user_id(auth)
 if not allowed(uid):raise HTTPException(403,"Sorcery operator permission required")
 return uid
def gh_headers():
 token=os.getenv("I_SORCERY_GITHUB_TOKEN","")
 if not token:raise HTTPException(503,"GitHub operations not configured")
 return {"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
@router.get("/status")
async def status(authorization:str=Header(default="")):
 await principal(authorization)
 return {"github_configured":bool(os.getenv("I_SORCERY_GITHUB_TOKEN")),
         "render_configured":bool(os.getenv("I_SORCERY_RENDER_API_KEY")),
         "workflows":list(WORKFLOWS),"arbitrary_shell_enabled":False,
         "ios_target":"iOS static library and Swift module; not signed IPA",
         "android_target":"unsigned-for-distribution debug APK"}
@router.get("/github/runs")
async def runs(authorization:str=Header(default="")):
 await principal(authorization)
 url="https://api.github.com/repos/"+REPO+"/actions/runs"
 async with httpx.AsyncClient(timeout=15,trust_env=False,follow_redirects=False) as client:
  r=await client.get(url,headers=gh_headers(),params={"per_page":12})
 if r.status_code!=200:raise HTTPException(502,"GitHub workflow listing unavailable")
 return {"runs":[{"id":x["id"],"name":x["name"],"status":x["status"],"conclusion":x.get("conclusion"),"html_url":x["html_url"],"head_sha":x["head_sha"]} for x in r.json().get("workflow_runs",[])[:12]]}
@router.get("/render/deploys")
async def deploys(authorization:str=Header(default="")):
 await principal(authorization)
 token=os.getenv("I_SORCERY_RENDER_API_KEY")
 if not token:raise HTTPException(503,"Render operations not configured")
 ids={"backend":"srv-db8lihnavr4c7387m5dg","frontend":"srv-db8l460473hc73a0ovu0"}
 out={}
 async with httpx.AsyncClient(timeout=15,trust_env=False,follow_redirects=False) as client:
  for name,service in ids.items():
   r=await client.get("https://api.render.com/v1/services/"+service+"/deploys",params={"limit":3},headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
   if r.status_code!=200:out[name]={"error":"Render API status "+str(r.status_code)};continue
   out[name]=[{"id":entry.get("deploy",entry).get("id"),"status":entry.get("deploy",entry).get("status"),
    "commit":entry.get("deploy",entry).get("commit",{}).get("id")} for entry in r.json()[:3]]
 return {"deployments":out,"keys_exposed":False}
class Dispatch(BaseModel):
 workflow:str
 confirmation:str
@router.post("/github/dispatch")
async def dispatch(body:Dispatch,authorization:str=Header(default="")):
 uid=await principal(authorization)
 if body.workflow not in WORKFLOWS:raise HTTPException(422,"Workflow not allowlisted")
 if body.confirmation!="RUN "+body.workflow:raise HTTPException(400,"Explicit workflow confirmation required")
 headers=gh_headers()
 url="https://api.github.com/repos/"+REPO+"/actions/workflows/"+WORKFLOWS[body.workflow]+"/dispatches"
 async with httpx.AsyncClient(timeout=15,trust_env=False,follow_redirects=False) as client:
  r=await client.post(url,headers=headers,json={"ref":REF})
 if r.status_code!=204:raise HTTPException(502,"GitHub rejected dispatch; verify token permission and workflow_dispatch trigger")
 event={"schema":"i-sorcery-dispatch/1","actor_sha256":hashlib.sha256(uid.encode()).hexdigest(),"operation":body.workflow,
 "ref":REF,"timestamp":datetime.now(timezone.utc).isoformat(),"github_accepted":True,
 "workflow_completed":False,"receipt_signed":False}
 return {"accepted":True,"execution_pending":True,"evidence_sha256":hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest(),"record":event}
