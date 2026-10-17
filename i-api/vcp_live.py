"""i™ VCP authenticated live model + source evidence endpoint.
This is source corroboration, never certification. Uses existing Buddy JWT auth.
"""
from __future__ import annotations
import hashlib, json, re, time
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from universal_router import infer
router=APIRouter(prefix="/v1/vcp",tags=["i VCP verification"])
class VerificationRequest(BaseModel):
    prompt: str=Field(min_length=3,max_length=1600)
    provider: str|None=None

def parse_proposal(text:str):
    if not isinstance(text,str) or len(text)>12000: raise ValueError("Invalid model response")
    raw=text.strip()
    if raw.startswith("```"):
        raw=re.sub(r"^\x60{3}(?:json)?\s*|\s*\x60{3}$","",raw,flags=re.I)
    obj=json.loads(raw)
    if not isinstance(obj,dict) or set(obj)!={"entity","attribute","value"}:
        raise ValueError("Claim must contain exactly entity, attribute, value")
    if any(not isinstance(obj[k],str) or not obj[k].strip() or len(obj[k])>120 for k in ("entity","attribute")):
        raise ValueError("Invalid claim terms")
    if isinstance(obj["value"],(list,dict)) or obj["value"] is None or isinstance(obj["value"],str) and len(obj["value"])>160:
        raise ValueError("Invalid predicate value")
    return obj

async def source_snapshot(entity: str):
    """Independent live source text, not an asserted fact or C2PA verification.
    Fixed HTTPS host. No caller-controlled URL; no redirects."""
    async with httpx.AsyncClient(timeout=9,follow_redirects=False) as client:
        r=await client.get("https://en.wikipedia.org/w/api.php",params={
            "action":"query","prop":"extracts","exintro":"1","explaintext":"1","redirects":"1",
            "titles":entity[:120],"format":"json","formatversion":"2"
        },headers={"User-Agent":"iVCP-Research/0.1 (source evidence; no truth certification)"})
        r.raise_for_status()
    page=r.json().get("query",{}).get("pages",[{}])[0]
    extract=str(page.get("extract") or "")[:3000]
    if page.get("missing") or not extract: return None
    return {"title":str(page.get("title") or entity)[:160],"pageid":page.get("pageid"),
            "url":"https://en.wikipedia.org/?curid="+str(page.get("pageid")),
            "snapshot_sha256":hashlib.sha256(extract.encode()).hexdigest(),
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "excerpt":extract[:1000],"source_type":"encyclopedia tertiary reference",
            "authenticated_source_signature":False}

@router.post("/assess")
async def assess(body:VerificationRequest,authorization:str=Header(default="")):
    from main import user_id
    uid,_=await user_id(authorization)
    instruction=('Return only JSON with EXACT keys entity, attribute, value. '
        'Propose one simple atomic factual proposition from the question. '
        'Never assert that it is verified or certified. Prompt: '+body.prompt)
    try:
        proposed,model=await infer(instruction,240,body.provider)
        claim=parse_proposal(proposed)
    except (ValueError,TypeError,KeyError,json.JSONDecodeError):
        raise HTTPException(422,"Model did not return a supported atomic claim; not verified")
    except HTTPException:
        raise
    try:
        source=await source_snapshot(claim["entity"])
    except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError):
        source=None
    checks={
      "ontology":{"status":"REFERENCE_FOUND" if source else "UNCONFIRMED"},
      "provenance":{"status":"SOURCE_SNAPSHOT_ONLY" if source else "UNCONFIRMED",
                    "note":"Source signature and original claim provenance not established"},
      "coherence":{"status":"NOT_EVALUATED",
                   "note":"A source excerpt does not independently validate the precise predicate, truth or causation."},
      "temporal":{"status":"UNDETERMINED","note":"No policy-bounded historical validity range provided"}
    }
    status="EVIDENCE_RETRIEVED" if source else "INCONCLUSIVE"
    record={"schema":"i.vcp.assessment/1","id":hashlib.sha256((uid+str(time.time_ns())).encode()).hexdigest()[:32],
            "status":status,"certified":False,"verified":False,"model":model,
            "claim":claim,"checks":checks,"source":source,
            "limitations":["No universal factual truth or certification claim","No historical semantic-drift validation",
                           "No independent primary-source corroboration","No execution authorization"],
            "timestamp":datetime.now(timezone.utc).isoformat()}
    record["record_sha256"]=hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    return record
