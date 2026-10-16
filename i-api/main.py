"""Buddy receipt API. Requires externally configured auth, signing and persistence."""
import base64
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any
import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from imodels import router as model_router, complete as imodel_complete, configured as imodel_configured
from fabric import router as fabric_router
from alternative_compute import router as alternative_compute_router
from omnisync import router as omnisync_router
from imirror import router as mirror_router
from lifeline import router as lifeline_router
from telecom_orchestra import router as telecom_orchestra_router
from universal_router import router as universal_router, infer as universal_infer, active as universal_active

app = FastAPI(title="i THE ONE Buddy Receipts", version="0.4.0")
app.include_router(model_router)
app.include_router(fabric_router)
app.include_router(alternative_compute_router)
app.include_router(omnisync_router)
app.include_router(mirror_router)
app.include_router(lifeline_router)
app.include_router(telecom_orchestra_router)
app.include_router(universal_router)
origin = os.environ.get("PUBLIC_ORIGIN", "").rstrip("/")
app.add_middleware(CORSMiddleware, allow_origins=[origin] if origin else [], allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["Authorization","Content-Type"])
PROJECT_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
ANON_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SIGNING_KEY = os.environ.get("RECEIPT_SIGNING_PRIVATE_KEY_PEM", "")
MODEL_URL = os.environ.get("BUDDY_MODEL_URL", "")
MODEL_TOKEN = os.environ.get("BUDDY_MODEL_TOKEN", "")
JWKS_URL = os.environ.get("SUPABASE_JWKS_URL", (PROJECT_URL+"/auth/v1/.well-known/jwks.json") if PROJECT_URL else "")
def ready():
    return all([PROJECT_URL, ANON_KEY, SIGNING_KEY, JWKS_URL])
def signing_key():
    try:
        key = serialization.load_pem_private_key(SIGNING_KEY.encode(), password=None)
        if not isinstance(key, Ed25519PrivateKey): raise ValueError("Not Ed25519")
        return key
    except Exception:
        raise HTTPException(503, "Receipt signing key not configured correctly")
def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
async def user_id(auth: str):
    if not auth.startswith("Bearer "): raise HTTPException(401,"Bearer token required")
    token=auth[7:]
    if not ready(): raise HTTPException(503,"Auth/storage/signing not configured")
    try:
        jwks=jwt.PyJWKClient(JWKS_URL)
        key=jwks.get_signing_key_from_jwt(token).key
        claims=jwt.decode(token,key,algorithms=["RS256","ES256"],audience="authenticated",issuer=PROJECT_URL+"/auth/v1",options={"require":["exp","sub","aud"]})
        if claims.get("is_anonymous"): raise HTTPException(403,"Anonymous sessions not supported")
        return claims["sub"],token
    except HTTPException: raise
    except Exception: raise HTTPException(401,"Invalid authentication token")
class Action(BaseModel):
    request: str = Field(min_length=1,max_length=4000)
    parent_id: str | None = None
    model: str = Field(default="buddy", pattern="^(buddy|the-one)$")
async def persist(row:dict, token:str):
    headers={"apikey":ANON_KEY,"Authorization":"Bearer "+token,"Content-Type":"application/json","Prefer":"return=representation"}
    async with httpx.AsyncClient(timeout=12) as client:
        response=await client.post(PROJECT_URL+"/rest/v1/i_receipts",headers=headers,json=row)
    if response.status_code not in (200,201): raise HTTPException(503,"Receipt persistence unavailable")
@app.get("/health")
async def health():
    return {"status":"ok","storage_auth_signing_configured":ready(),"model_configured":bool(universal_active()),"universal_provider_count":len(universal_active())}
@app.post("/v1/actions")
async def action(body:Action, authorization:str=Header(default="")):
    uid,token=await user_id(authorization)
    # One allowed route: operator-declared Apache-2.0 iModel weights.
    # Other registered adapters are disabled for inference by user policy.
    answer,actual_model=await universal_infer(body.request)
    payload={"protocol":"i-receipt/0.3","action_id":str(uuid.uuid4()),"user_id":uid,"request":body.request,"result":answer,"created_at":datetime.now(timezone.utc).isoformat(),"parent_id":body.parent_id,"execution":{"kind":"model-response","status":"completed","model_attestation":"inference-response-only; native-weights-unverified","model_id":actual_model}}
    digest=hashlib.sha256(canonical(payload)).hexdigest()
    key=signing_key()
    signature=base64.b64encode(key.sign(bytes.fromhex(digest))).decode()
    receipt={"id":digest,"body":payload,"signature":signature,"signature_alg":"Ed25519","public_key":base64.b64encode(key.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)).decode()}
    await persist({"id":digest,"user_id":uid,"receipt":receipt},token)
    return {"answer":answer,"receipt":receipt}
@app.get("/v1/receipts")
async def receipts(authorization:str=Header(default="")):
    uid,token=await user_id(authorization)
    headers={"apikey":ANON_KEY,"Authorization":"Bearer "+token}
    async with httpx.AsyncClient(timeout=12) as client:
        response=await client.get(PROJECT_URL+"/rest/v1/i_receipts",headers=headers,params={"select":"receipt,created_at","user_id":"eq."+uid,"order":"created_at.desc","limit":"100"})
    if response.status_code!=200: raise HTTPException(503,"Receipt storage unavailable")
    return response.json()

@app.post("/v1/models/{model_name}/generate")
async def generate_model(model_name: str, body: Action, authorization: str=Header(default="")):
    if model_name not in {"buddy","the-one"}:
        raise HTTPException(404,"Unknown model")
    body.model=model_name
    return await action(body, authorization)
