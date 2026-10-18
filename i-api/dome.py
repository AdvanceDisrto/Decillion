"""Evidence-scoped iDome verifier: exact decimal checks, no PUF or absolute-truth claims."""
import hashlib
import json
import re
from decimal import Decimal
from fastapi import APIRouter
from pydantic import BaseModel, Field

router=APIRouter(prefix="/v1/dome",tags=["dome"])
RULESET="DOME-MATH-1"
RULE=re.compile(r"^\s*(-?(?:0|[1-9]\d{0,11})(?:\.\d{1,6})?)\s*([+\-*/])\s*(-?(?:0|[1-9]\d{0,11})(?:\.\d{1,6})?)\s*=\s*(-?(?:0|[1-9]\d{0,11})(?:\.\d{1,6})?)\s*$")
POLICY={"ruleset":RULESET,"authorized_actions":[],"human_approval":"required"}
def digest(obj):
    return "sha256:"+hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def grade(statement):
    match=RULE.fullmatch(statement)
    if not match: return "U","Not in pinned arithmetic grammar",None
    aa,op,bb,cc=match.groups()
    a,b,c=Decimal(aa),Decimal(bb),Decimal(cc)
    if op=="/" and b==0: return "U","Division by zero",None
    result={"+":lambda:a+b,"-":lambda:a-b,"*":lambda:a*b,"/":lambda:a/b}[op]()
    calc={"left":aa,"operation":op,"right":bb,"result":str(result),"claimed":cc}
    return ("A","Exact arithmetic agrees",calc) if result==c else ("D","Exact arithmetic contradicts claim",calc)
def evaluate_claim(text):
    decision,reason,calc=grade(text)
    request={"text":text}
    trace={"intake_hash":digest(request),"contract_hash":digest(RULESET),"calculation":calc,
           "warrant":decision,"runtime":"Python Decimal; ruleset DOME-MATH-1","policy_hash":digest(POLICY)}
    th=digest(trace)
    if grade(text)!=(decision,reason,calc):
        return {"status":"REFUSED","grade":"U","reason":"replay mismatch","trace_hash":th}
    if decision!="A":
        return {"status":"REFUSED","grade":decision,"reason":reason,"trace_hash":th,
                "refusal_hash":digest({"trace_hash":th,"grade":decision,"reason":reason}),
                "human_approval":"PENDING"}
    body={"schema":"idome-evidence/1","request_hash":trace["intake_hash"],"trace_hash":th,
          "policy_hash":trace["policy_hash"],"output_hash":digest(calc),"ruleset":RULESET,"grade":"A",
          "scope":"exact arithmetic identity","replay":"MATCH","human_approval":"PENDING",
          "hardware_attested":False,"externally_anchored":False,"independent_certification":False,
          "signature":None}
    return {"status":"SUPPORTED_IN_DEFINED_SCOPE","grade":"A","receipt":{"body":body,"id":digest(body)},"trace":trace}
class Request(BaseModel):
    text:str=Field(min_length=1,max_length=512)
@router.get("/health")
def dome_health():
    return {"status":"ok","mode":"arithmetic_warrant_only","persistent_ledger":False,
            "hardware_attestation":False,"human_approval_workflow":False}
@router.post("/evaluate")
def dome_evaluate(body:Request):
    return evaluate_claim(body.text)
