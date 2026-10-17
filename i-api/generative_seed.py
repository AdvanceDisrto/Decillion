"""i™ multi-provider Generative Seed, explicitly opt-in and never self-certifying.

Operator enables vendors via IAPI_GENERATIVE_PROVIDERS_ALLOWLIST comma list.
Provider keys never exposed to client. Responses cannot authorize external actions.
"""
from __future__ import annotations
import os
import httpx
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,Field

router=APIRouter(prefix="/v1/generative",tags=["iGenerativeSeed"])
SPECS={
 "openai":("https://api.openai.com/v1","IAPI_OPENAI_KEY","IAPI_OPENAI_MODEL_ID","openai"),
 "anthropic":("https://api.anthropic.com/v1","IAPI_ANTHROPIC_KEY","IAPI_ANTHROPIC_MODEL_ID","anthropic"),
 "gemini":("https://generativelanguage.googleapis.com/v1beta/openai","IAPI_GOOGLE_KEY","IAPI_GOOGLE_MODEL_ID","openai"),
 "openrouter":("https://openrouter.ai/api/v1","IAPI_OPENROUTER_KEY","IAPI_OPENROUTER_MODEL_ID","openai"),
}
def allowed():
    ids={x.strip().lower() for x in os.getenv("IAPI_GENERATIVE_PROVIDERS_ALLOWLIST","").split(",") if x.strip()}
    return ids & SPECS.keys()
def ready(provider):
    if provider not in allowed():return False
    _,key,model,_=SPECS[provider]
    return bool(os.getenv(key,"").strip() and os.getenv(model,"").strip())
class Request(BaseModel):
    prompt:str=Field(min_length=1,max_length=3500)
    provider:str=Field(min_length=1,max_length=24)
    max_tokens:int=Field(default=350,ge=1,le=1024)
async def generate(body:Request):
    if not ready(body.provider):
        raise HTTPException(503,"Provider not enabled and configured by operator")
    base,key_env,model_env,protocol=SPECS[body.provider]
    key=os.environ[key_env].strip();model=os.environ[model_env].strip()
    system="You are an unverified proposal generator. Never claim independent certification or authority to execute actions."
    async with httpx.AsyncClient(timeout=45,follow_redirects=False,trust_env=False) as client:
        try:
            if protocol=="anthropic":
                response=await client.post(base+"/messages",headers={
                    "x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
                    json={"model":model,"max_tokens":body.max_tokens,"system":system,
                          "messages":[{"role":"user","content":body.prompt}]})
                response.raise_for_status()
                result="".join(c.get("text","") for c in response.json()["content"] if c.get("type")=="text")
            else:
                response=await client.post(base+"/chat/completions",headers={
                    "Authorization":"Bearer "+key,"Content-Type":"application/json"},
                    json={"model":model,"max_tokens":body.max_tokens,"stream":False,
                          "messages":[{"role":"system","content":system},{"role":"user","content":body.prompt}]})
                response.raise_for_status()
                result=response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError,KeyError,IndexError,ValueError,TypeError) as e:
            raise HTTPException(502,"Configured provider failed; no certification issued") from e
    if not isinstance(result,str) or not result.strip():raise HTTPException(502,"Empty provider output")
    return {"schema":"i.generative.proposal/1","provider":body.provider,"model":model,
            "answer":result[:16000],"status":"UNVERIFIED_PROPOSAL","certified":False,
            "execution_authorized":False,"scope":"Generation only; independent evidence/ICE checks not performed"}
@router.get("/providers")
async def provider_status():
    return {"providers":[{"id":name,"enabled":name in allowed(),"configured":ready(name)} for name in SPECS],
            "keys_exposed":False,"note":"This route is separate from existing Apache-2.0-only licensed-model policy."}
@router.post("/chat")
async def propose(body:Request,authorization:str=Header(default="")):
    from main import user_id
    await user_id(authorization)
    return await generate(body)
