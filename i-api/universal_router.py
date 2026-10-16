"""i™ Universal API Router — production-wired, configuration-gated AI inference.

Never advertises inactive keys/models as active. MIT and Apache-2.0 are
licenses for self-hosted model weights, not API companies.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
router=APIRouter(prefix="/v1/universal",tags=["iUniversalApi"])

@dataclass(frozen=True)
class Endpoint:
    id:str
    url:str
    model_env:str
    key_env:str
    protocol:str="openai"
    def model(self):return os.getenv(self.model_env,"").strip()
    def token(self):return os.getenv(self.key_env,"").strip()
    def ready(self):return bool(self.model() and self.token() and safe_url(self.url))
    def status(self):return {"id":self.id,"model":self.model() or None,
      "configured":self.ready() and self.id=="apache2-licensed-llm" and apache_policy_ready(),"last_inference_verified":False,
      "status":("eligible-unverified" if self.id=="apache2-licensed-llm" and self.ready() and apache_policy_ready() else "disabled-by-apache-only-policy" if self.id!="apache2-licensed-llm" else "not-configured")}

def safe_url(value):
    try:
        u=urlsplit(value)
        return u.scheme=="https" and bool(u.hostname) and not u.username and not u.password and not u.fragment
    except ValueError:return False

def env_endpoint(name, env_prefix):
    return Endpoint(name,os.getenv(env_prefix+"_BASE_URL","").rstrip("/"),
                    env_prefix+"_MODEL_ID",env_prefix+"_API_KEY")

ENDPOINTS=(
 Endpoint("openai","https://api.openai.com/v1","IAPI_OPENAI_MODEL_ID","IAPI_OPENAI_KEY"),
 Endpoint("anthropic","https://api.anthropic.com/v1","IAPI_ANTHROPIC_MODEL_ID","IAPI_ANTHROPIC_KEY","anthropic"),
 Endpoint("groq","https://api.groq.com/openai/v1","IAPI_GROQ_MODEL_ID","IAPI_GROQ_KEY"),
 Endpoint("deepseek","https://api.deepseek.com/v1","IAPI_DEEPSEEK_MODEL_ID","IAPI_DEEPSEEK_KEY"),
 Endpoint("google","https://generativelanguage.googleapis.com/v1beta/openai","IAPI_GOOGLE_MODEL_ID","IAPI_GOOGLE_KEY"),
 Endpoint("huggingface","https://router.huggingface.co/v1","IAPI_HF_MODEL_ID","IAPI_HF_TOKEN"),
 env_endpoint("mit-licensed-llm","IAPI_MIT"),
 env_endpoint("apache2-licensed-llm","IAPI_APACHE2"),
)
def apache_policy_ready():
    """Operator-declared Apache-2.0 source and immutable revision.
    Declaration is NOT independent license or weight verification."""
    revision=os.getenv("IAPI_APACHE2_MODEL_REVISION_SHA","").strip().lower()
    return (os.getenv("IAPI_APACHE2_LICENSE_SPDX","").strip()=="Apache-2.0"
            and len(revision)==64 and all(c in "0123456789abcdef" for c in revision))

def active():
    return tuple(e for e in ENDPOINTS if e.id=="apache2-licensed-llm"
                 and e.ready() and apache_policy_ready())

@router.get("/providers")
async def providers():
    return {"providers":[e.status() for e in ENDPOINTS],
            "routing":"apache-2.0-only","keys_exposed":False,"apache_policy_declared":apache_policy_ready(),
            "note":"MIT and Apache-2.0 are licenses, not networks; these routes target your separately hosted licensed model."}

async def infer(prompt:str,max_tokens:int=512,preferred:str|None=None):
    if not 1<=len(prompt)<=4000 or not 1<=max_tokens<=2048:
        raise HTTPException(422,"Prompt/token bound exceeded")
    candidates=list(active())
    if preferred:
        candidates=[p for p in candidates if p.id==preferred]
        if not candidates:raise HTTPException(503,"Requested AI provider is not configured")
    if not candidates:raise HTTPException(503,"No iUniversalApi provider credentials and model IDs configured")
    for p in candidates:
        try:
            async with httpx.AsyncClient(timeout=38,follow_redirects=False) as client:
                if p.protocol=="anthropic":
                    res=await client.post(p.url+"/messages",
                      headers={"x-api-key":p.token(),"anthropic-version":"2023-06-01",
                               "Content-Type":"application/json"},
                      json={"model":p.model(),"max_tokens":max_tokens,"messages":[{"role":"user","content":prompt}]})
                    res.raise_for_status()
                    output="".join(c.get("text","") for c in res.json()["content"] if c.get("type")=="text")
                else:
                    res=await client.post(p.url+"/chat/completions",
                      headers={"Authorization":"Bearer "+p.token(),"Content-Type":"application/json"},
                      json={"model":p.model(),"max_tokens":max_tokens,
                            "messages":[{"role":"user","content":prompt}],"stream":False})
                    res.raise_for_status()
                    output=res.json()["choices"][0]["message"]["content"]
                if not isinstance(output,str) or not output.strip():raise ValueError("Empty AI response")
                return output,p.id+"/"+p.model()
        except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError):
            if preferred:raise HTTPException(502,"Selected provider inference failed")
            continue
    raise HTTPException(502,"All configured providers failed to complete inference")

class ChatRequest(BaseModel):
    request:str=Field(min_length=1,max_length=4000)
    provider:str|None=None
    max_tokens:int=Field(default=512,ge=1,le=2048)

@router.post("/chat")
async def chat(body:ChatRequest,authorization:str=Header(default="")):
    from main import user_id
    uid,_=await user_id(authorization)
    text,model=await infer(body.request,body.max_tokens,body.provider)
    # This endpoint is intentionally not called a certified receipt.
    return {"answer":text,"model":model,"user_authenticated":bool(uid),
            "receipt_status":"use /v1/actions for signed, persisted receipts"}
