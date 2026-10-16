"""i™ Gateway: server-side provider adapters, authenticated sessions and usage evidence.

Cloud access is opt-in, disabled by default. Local/free models remain Apache-2.0 only.
Receipts are unsigned SHA-256 unless a separate ledger signer is integrated.
Wallet debits and native MPC are NOT performed here.
"""
from __future__ import annotations
import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
import jwt
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime,timezone
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/gateway",tags=["i™ Unified AI Gateway"])
PROVIDERS={
 "openai":("https://api.openai.com/v1","OPENAI_API_KEY","IAPI_OPENAI_MODEL_ID","openai"),
 "anthropic":("https://api.anthropic.com/v1","ANTHROPIC_API_KEY","IAPI_ANTHROPIC_MODEL_ID","anthropic"),
 "deepseek":("https://api.deepseek.com/v1","DEEPSEEK_API_KEY","IAPI_DEEPSEEK_MODEL_ID","openai"),
 "google":("https://generativelanguage.googleapis.com/v1beta/openai","GOOGLE_API_KEY","IAPI_GOOGLE_MODEL_ID","openai"),
 "mistral":("https://api.mistral.ai/v1","MISTRAL_API_KEY","IAPI_MISTRAL_MODEL_ID","openai"),
 "cohere":("https://api.cohere.com/v2","COHERE_API_KEY","IAPI_COHERE_MODEL_ID","cohere"),
}
TIERS={"free":(12,False),"paid":(60,True),"enterprise":(240,True)}
# Memory is explicitly volatile across restarts/replicas. Not a financial ledger.
THREADS:dict[tuple[str,str],list[dict]]= {}
USAGE:dict[str,list[dict]]=defaultdict(list)
REQUESTS:dict[str,deque]=defaultdict(deque)
GUARD=asyncio.Lock()
MAX_THREADS=1000
MAX_SESSIONS_PER_USER=20
MAX_MESSAGES=24
MAX_PROMPT=4000
MAX_RESPONSE_TOKENS=1024

class Chat(BaseModel):
 message:str=Field(min_length=1,max_length=MAX_PROMPT)
 thread_id:str|None=Field(default=None,min_length=10,max_length=80)
 task:str=Field(default="chat",pattern="^(chat|code|reasoning|vision|completion)$")
 max_tokens:int=Field(default=512,ge=1,le=MAX_RESPONSE_TOKENS)
 max_cost_usd:float=Field(default=1.00,ge=0,le=100)
 preferred_provider:str|None=Field(default=None,max_length=32)
 stream:bool=False

def token_digest(secret:str, token:str)->str:
 return hmac.new(secret.encode(),token.encode(),hashlib.sha256).hexdigest()

def configured():
 out={}
 for id,(_,key_env,model_env,_) in PROVIDERS.items():
  out[id]=bool(os.getenv(key_env) and os.getenv(model_env) and os.getenv("I_GATEWAY_PAID_ENABLED")=="true")
 return out

def selected_tier(uid:str,claim_tier:str|None=None)->str:
 # A tier must be resolved from verified server-side authorization, not the
 # user's request. Claim tier explicitly NOT trusted here.
 allowed={x.strip() for x in os.getenv("I_GATEWAY_PAID_USER_IDS","").split(",") if x.strip()}
 enterprise={x.strip() for x in os.getenv("I_GATEWAY_ENTERPRISE_USER_IDS","").split(",") if x.strip()}
 if uid in enterprise:return "enterprise"
 if uid in allowed:return "paid"
 return "free"

def eligible_providers(tier:str,preferred:str|None=None):
 if tier=="free" or os.getenv("I_GATEWAY_PAID_ENABLED")!="true":
  return ["apache2-licensed-llm"] if preferred in (None,"apache2-licensed-llm","local") else []
 candidates=[pid for pid,enabled in configured().items() if enabled]
 if preferred:
  candidates=[p for p in candidates if p==preferred]
 # Keep the user's configured provider order; not unsupported cost ranking.
 return candidates

def safe_provider_data(name:str,data:dict,elapsed_ms:int,requested:str):
 if name=="anthropic":
  content="".join(part.get("text","") for part in data.get("content",[]) if part.get("type")=="text")
  ins=data.get("usage",{}).get("input_tokens")
  outs=data.get("usage",{}).get("output_tokens")
 elif name=="cohere":
  content="".join(part.get("text","") for part in data.get("message",{}).get("content",[]) if part.get("type")=="text")
  usage=data.get("usage",{}).get("tokens",{})
  ins=usage.get("input_tokens")
  outs=usage.get("output_tokens")
 else:
  content=data.get("choices",[{}])[0].get("message",{}).get("content","")
  usage=data.get("usage",{})
  ins=usage.get("prompt_tokens")
  outs=usage.get("completion_tokens")
 if not isinstance(content,str) or not content.strip():raise ValueError("Empty model response")
 return {"answer":content[:50000],"reported_model":data.get("model"),
         "requested_model":requested,"tokens_in":ins if isinstance(ins,int) else None,
         "tokens_out":outs if isinstance(outs,int) else None,"latency_ms":elapsed_ms}

async def remote_infer(provider:str,messages:list,max_tokens:int):
 base,key_env,model_env,protocol=PROVIDERS[provider]
 token=os.getenv(key_env,"");model=os.getenv(model_env,"")
 if not token or not model:raise HTTPException(503,"Provider not configured")
 headers={"Content-Type":"application/json"}
 if protocol=="anthropic":
  url=base+"/messages"
  headers.update({"x-api-key":token,"anthropic-version":"2023-06-01"})
  body={"model":model,"max_tokens":max_tokens,"messages":messages}
 elif protocol=="cohere":
  url=base+"/chat";headers["Authorization"]="Bearer "+token
  body={"model":model,"messages":messages,"max_tokens":max_tokens}
 else:
  url=base+"/chat/completions";headers["Authorization"]="Bearer "+token
  body={"model":model,"messages":messages,"max_tokens":max_tokens,"stream":False}
 start=time.monotonic()
 async with httpx.AsyncClient(timeout=32,follow_redirects=False,trust_env=False) as client:
  resp=await client.post(url,headers=headers,json=body)
 if resp.status_code==401:raise HTTPException(502,"Provider authentication rejected")
 if not resp.is_success:raise HTTPException(502,"AI provider unavailable")
 try:return safe_provider_data(provider,resp.json(),round((time.monotonic()-start)*1000),model)
 except (ValueError,TypeError,KeyError,IndexError) as exc:raise HTTPException(502,"Provider returned invalid response") from exc

def receipt(record:dict):
 canonical=json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 return {"sha256":hashlib.sha256(canonical).hexdigest(),"body":record,
         "signature":None,"ledger_anchor":None,"certified":False}

async def check_auth(auth:str):
 # Scoped ephemeral i™ proxy tokens are only issued to an existing verified
 # user. They are never provider API keys, are not MPC and cannot bypass auth.
 if auth.startswith("Bearer iat."):
  secret=os.getenv("I_GATEWAY_TOKEN_SECRET","")
  if len(secret)<32:raise HTTPException(503,"Scoped token verification not configured")
  try:
   claim=jwt.decode(auth[11:],secret,algorithms=["HS256"],
     audience="i-gateway",issuer="i-gateway",options={"require":["exp","sub","aud","iss","scope"]})
   if claim.get("scope")!="gateway:chat":raise HTTPException(403,"Wrong API token scope")
   return claim["sub"]
  except jwt.PyJWTError:raise HTTPException(401,"Invalid or expired i™ proxy token")
 from main import user_id
 uid,_=await user_id(auth)
 return uid

@router.post("/keys/issue")
async def issue_key(authorization:str=Header(default="")):
 from main import user_id
 uid,_=await user_id(authorization)
 secret=os.getenv("I_GATEWAY_TOKEN_SECRET","")
 if len(secret)<32:raise HTTPException(503,"Scoped API token issuer not configured")
 now=int(time.time())
 signed=jwt.encode({"iss":"i-gateway","aud":"i-gateway","sub":uid,
   "scope":"gateway:chat","iat":now,"exp":now+900,"jti":secrets.token_hex(16)},
   secret,algorithm="HS256")
 return {"token":"iat."+signed,"expires_in_seconds":900,
   "scope":"gateway:chat","issuer":"i-gateway",
   "mpc":False,"cloud_provider_credentials_included":False}

async def rate_check(uid:str,tier:str):
 now=time.monotonic()
 async with GUARD:
  queue=REQUESTS[uid]
  while queue and now-queue[0]>60:queue.popleft()
  if len(queue)>=TIERS[tier][0]:raise HTTPException(429,"User tier rate limit exceeded")
  queue.append(now)

async def run_gateway(req:Chat,uid:str):
 tier=selected_tier(uid)
 await rate_check(uid,tier)
 eligible=eligible_providers(tier,req.preferred_provider)
 # Operator-configured price ceilings are required before any paid request.
 # Missing prices fail shut instead of risking unlimited third-party charges.
 if tier!="free":
  bounded=[]
  for p in eligible:
   try:
    vin=float(os.getenv("I_GATEWAY_"+p.upper()+"_INPUT_COST_PER_1K",""))
    vout=float(os.getenv("I_GATEWAY_"+p.upper()+"_OUTPUT_COST_PER_1K",""))
    valid=0<=vin<100 and 0<=vout<100
    # Deliberately conservative upper bound rather than actual invoice.
    projected=(MAX_PROMPT*MAX_MESSAGES*vin+req.max_tokens*vout)/1000
    if valid and projected<=req.max_cost_usd:bounded.append(p)
   except (ValueError,OverflowError):pass
  eligible=bounded
 if not eligible:raise HTTPException(403,"Provider disabled or unavailable under user's server-authorized tier")
 # No user-controlled userId. Sessions cannot be read across principal boundaries.
 thread_id=req.thread_id or uuid.uuid4().hex
 key=(uid,thread_id)
 async with GUARD:
  if req.thread_id and key not in THREADS:raise HTTPException(404,"Thread not found")
  previous=THREADS.get(key,[])[-MAX_MESSAGES:]
 messages=previous+[{"role":"user","content":req.message}]
 provider_used=None;actual=None;last_error=None
 for target in eligible:
  try:
   if target=="apache2-licensed-llm":
    from universal_router import infer
    answer,actual_model=await infer(req.message,max_tokens=req.max_tokens)
    actual={"answer":answer,"requested_model":actual_model,"reported_model":None,
            "tokens_in":None,"tokens_out":None,"latency_ms":None}
   else:actual=await remote_infer(target,messages,req.max_tokens)
   provider_used=target;break
  except (HTTPException,httpx.HTTPError,ValueError) as e:
   last_error=e
   if req.preferred_provider:break
 if not actual:raise HTTPException(503,"No eligible model completed the request")
 # Estimate is not a charge; require trusted current price feed + provider usage to bill.
 inp,out=actual["tokens_in"],actual["tokens_out"]
 record={"schema":"i-gateway-usage/0.1","id":uuid.uuid4().hex,
    "user_ref":hashlib.sha256(uid.encode()).hexdigest()[:16],
    "thread_id":thread_id,"provider":provider_used,
    "requested_model":actual["requested_model"],"provider_reported_model":actual["reported_model"],
    "model_identity_attested":False,"token_input_reported":inp,"token_output_reported":out,
    "latency_ms":actual["latency_ms"],"actual_bill_usd":None,"wallet_debited":False,
    "price_verified":False,"user_max_cost_usd":req.max_cost_usd,
    "timestamp":datetime.now(timezone.utc).isoformat(),"external_ledger_anchor":None}
 evidence=receipt(record)
 async with GUARD:
  if key not in THREADS and sum(1 for u,_ in THREADS if u==uid)>=MAX_SESSIONS_PER_USER:
   raise HTTPException(429,"Too many in-memory sessions")
  if len(THREADS)>=MAX_THREADS and key not in THREADS:raise HTTPException(503,"Gateway temporary session capacity reached")
  THREADS[key]=(messages+[{"role":"assistant","content":actual["answer"]}])[-MAX_MESSAGES:]
  USAGE[uid].append({**record,"sha256":evidence["sha256"]})
  if len(USAGE[uid])>500:USAGE[uid]=USAGE[uid][-500:]
 return {"thread_id":thread_id,"answer":actual["answer"],"tier":tier,
    "provider_hidden_from_client":True,"receipt":evidence,
    "billing":"unmetered-preview: no wallet debit or verified pricing"}

@router.get("/status")
async def status():
 return {"gateway":"configured-adapters-only","plans":["free","paid","enterprise"],
   "paid_enabled":os.getenv("I_GATEWAY_PAID_ENABLED")=="true",
   "provider_configured":configured(),"provider_keys_exposed":False,
   "free_route":"apache2-licensed-llm only","paid_authorization":"server-issued user allowlist",
   "persistent_threads":False,"wallet_billing":False,"mpc_key_sharding":False,
   "real_ledger_anchor":False,"provider_license_certified":False}

@router.post("/chat")
async def chat(body:Chat,authorization:str=Header(default="")):
 uid=await check_auth(authorization)
 return await run_gateway(body,uid)

@router.post("/stream")
async def stream(body:Chat,authorization:str=Header(default="")):
 uid=await check_auth(authorization)
 result=await run_gateway(body,uid)
 # SSE transport: gateway response is buffered; upstream token streaming NOT yet wired.
 async def chunks():
  yield "event: meta\ndata: "+json.dumps({"thread_id":result["thread_id"],"buffered":True})+"\n\n"
  answer=result["answer"]
  for i in range(0,len(answer),256):
   yield "event: text\ndata: "+json.dumps({"text":answer[i:i+256]})+"\n\n"
  yield "event: done\ndata: "+json.dumps({"receipt_sha256":result["receipt"]["sha256"]})+"\n\n"
 return StreamingResponse(chunks(),media_type="text/event-stream",headers={"Cache-Control":"no-store","X-Accel-Buffering":"no"})

@router.get("/threads")
async def threads(authorization:str=Header(default="")):
 uid=await check_auth(authorization)
 async with GUARD:
  return {"threads":[{"thread_id":id,"messages":len(v)} for (u,id),v in THREADS.items() if u==uid],
          "persistent":False,"user_isolation":True}

@router.get("/usage")
async def usage(authorization:str=Header(default="")):
 uid=await check_auth(authorization)
 async with GUARD:
  return {"records":list(USAGE[uid]),"wallet_charges":0,"invoice_status":"not implemented",
          "ledger_anchored":False}

@router.get("/keys/status")
async def key_status(authorization:str=Header(default="")):
 uid=await check_auth(authorization)
 return {"principal_authenticated":bool(uid),"provider_keys_exposed":False,
   "configured":configured(),"virtual_issuer":"not enabled",
   "mpc_key_split":"not implemented"}
