"""i™ ICE independent evidence-attestation service. Certifies named *evidence conformance*
only, NEVER the factual truth of a claim. Proposer cannot provide trust roots.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from ice_security import IceStore
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

app=FastAPI(title="i™ Independent Certification Engine",version="0.1")
STANDARD="ICE-01-EVIDENCE-INTEGRITY/1"
def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
def b64decode(value):
    return base64.b64decode(value,validate=True)
def keyring():
    """Trusted witness public keys are owned by the ICE operator, not the proposer."""
    raw=os.environ.get("ICE_TRUSTED_WITNESS_KEYS_JSON","")
    keys=json.loads(raw) if raw else {}
    if not isinstance(keys,dict):raise ValueError("Invalid trusted witness keyring")
    return keys
class Source(BaseModel):
    witness_id:str=Field(min_length=1,max_length=80)
    source_id:str=Field(min_length=1,max_length=300)
    captured_at:int=Field(ge=1)
    evidence_text:str=Field(min_length=1,max_length=20000)
    sha256:str=Field(pattern=r"^[a-f0-9]{64}$")
    witness_signature_b64:str=Field(min_length=1,max_length=180)
class Package(BaseModel):
    claim:str=Field(min_length=1,max_length=1200)
    standard:str
    sources:list[Source]=Field(min_length=1,max_length=12)
def evidence_payload(s:Source):
    return {"schema":"i.ice.source/1","witness_id":s.witness_id,"source_id":s.source_id,
            "captured_at":s.captured_at,"sha256":s.sha256}
def assess(pkg:Package, trusted:dict,now:int|None=None):
    now=int(time.time()) if now is None else now
    if pkg.standard!=STANDARD:return False,"Unsupported standard"
    if len(pkg.sources)<3:return False,"At least three independently signed evidence snapshots required"
    witnessed=set()
    for s in pkg.sources:
        if s.witness_id in witnessed:return False,"Witness identifiers must be distinct"
        witnessed.add(s.witness_id)
        if not (now-86400<=s.captured_at<=now+60):return False,"Evidence capture outside policy window"
        if hashlib.sha256(s.evidence_text.encode()).hexdigest()!=s.sha256:return False,"Source text digest mismatch"
        key=trusted.get(s.witness_id)
        if not isinstance(key,str):return False,"Witness not in operator trusted keyring"
        try:
            Ed25519PublicKey.from_public_bytes(b64decode(key)).verify(
                b64decode(s.witness_signature_b64),canonical(evidence_payload(s)))
        except Exception:return False,"Witness signature invalid"
    return True,"Three distinct trusted witnesses signed the submitted snapshots; factual correctness NOT evaluated"
def issuer_key():
    raw=os.environ.get("ICE_ISSUER_PRIVATE_KEY_B64","")
    if not raw:raise RuntimeError("Issuer key unavailable")
    return Ed25519PrivateKey.from_private_bytes(b64decode(raw))
def certify(pkg:Package,trusted:dict,issuer:Ed25519PrivateKey,now:int|None=None):
    ok,detail=assess(pkg,trusted,now)
    if not ok:return {"status":"REJECTED","reason":detail,"certificate":None}
    issued=int(time.time()) if now is None else now
    payload={"schema":"i.ice.certificate/1","standard":STANDARD,"issued_at":issued,
             "claim_sha256":hashlib.sha256(pkg.claim.encode()).hexdigest(),
             "evidence":[evidence_payload(s) for s in pkg.sources],
             "status":"CERTIFIED_EVIDENCE_INTEGRITY_ONLY",
             "scope":"Three trusted signed evidence snapshots, not truth or independent factual agreement"}
    signature=base64.b64encode(issuer.sign(canonical(payload))).decode()
    return {"status":payload["status"],"certificate":{"payload":payload,"signature_b64":signature,
             "algorithm":"Ed25519"}}
def verify_certificate(certificate:dict,issuer_public_key_b64:str):
    try:
        pub=Ed25519PublicKey.from_public_bytes(b64decode(issuer_public_key_b64))
        pub.verify(b64decode(certificate["signature_b64"]),canonical(certificate["payload"]))
        return certificate["payload"]["schema"]=="i.ice.certificate/1" and certificate["payload"]["standard"]==STANDARD
    except Exception:return False
def auth(header:str):
    secret=os.environ.get("ICE_OPERATOR_TOKEN","")
    if len(secret)<32:raise HTTPException(503,"ICE operator authorization not configured")
    if not header.startswith("Bearer ") or not hmac.compare_digest(header[7:],secret):
        raise HTTPException(401,"Unauthorized")
@app.get("/health")
def health():
    return {"status":"ok","issuer_configured":bool(os.environ.get("ICE_ISSUER_PRIVATE_KEY_B64")),
            "operator_auth_configured":len(os.environ.get("ICE_OPERATOR_TOKEN",""))>=32,
            "trusted_witness_count":len(keyring()),"standard":STANDARD}
def store():
    path=os.environ.get("ICE_AUDIT_DB_PATH","").strip()
    if not path:raise HTTPException(503,"Persistent audit store not configured")
    return IceStore(path)
def cert_id(certificate):
    return hashlib.sha256(canonical(certificate["payload"])).hexdigest()
def verify_current(certificate,public_key,db):
    return verify_certificate(certificate,public_key) and db.integrity() and not db.is_revoked(cert_id(certificate))
class CertificationRequest(BaseModel):
    nonce:str=Field(min_length=20,max_length=128)
    package:Package
class RevocationRequest(BaseModel):
    cert_id:str=Field(pattern=r"^[a-f0-9]{64}$")
    reason:str=Field(min_length=1,max_length=250)
class ValidationRequest(BaseModel):
    certificate:dict
@app.post("/certify")
def request_certificate(request:CertificationRequest,authorization:str=Header(default="")):
    auth(authorization)
    try:
        db=store()
        if not db.integrity():raise HTTPException(503,"Audit chain integrity failed")
        result=certify(request.package,keyring(),issuer_key())
        if result.get("certificate"):result["cert_id"]=cert_id(result["certificate"])
        digest=hashlib.sha256(canonical(request.package.model_dump())).hexdigest()
        db.record_once(request.nonce,digest,result)
        return result
    except ValueError as ex:raise HTTPException(409,str(ex)[:180]) from ex
    except RuntimeError as ex:raise HTTPException(503,"ICE custody or audit unavailable") from ex
@app.post("/revoke")
def revoke(request:RevocationRequest,authorization:str=Header(default="")):
    auth(authorization)
    try:
        db=store()
        db.revoke(request.cert_id,request.reason)
        return {"revoked":True,"cert_id":request.cert_id,"audit_head":db.head()}
    except ValueError as ex:raise HTTPException(409,str(ex)[:180]) from ex
    except RuntimeError as ex:raise HTTPException(503,"Audit unavailable") from ex
@app.post("/validate")
def validate(request:ValidationRequest):
    public_key=os.environ.get("ICE_ISSUER_PUBLIC_KEY_B64","")
    if not public_key:raise HTTPException(503,"Issuer public key unavailable")
    db=store()
    cert=request.certificate
    return {"signature_valid":verify_certificate(cert,public_key),
            "currently_valid":verify_current(cert,public_key,db),
            "certificate_id":cert_id(cert) if isinstance(cert.get("payload"),dict) else None,
            "audit_head":db.head(),"scope":"evidence integrity only; not factual truth"}
