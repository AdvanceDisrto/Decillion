"""i™ VCP model gateway: real OpenAI-compatible chat completion plus policy-limited verification.
Never represent registry agreement as universal truth or as certification.
"""
import json, os, urllib.request, urllib.parse, urllib.error
from vcp import Engine, create_keypair

# Pin scoped assertions to independently reviewed evidence and temporal scope.
REGISTRY = {
  ("mars", "moons"): {"value":2, "reference":"https://science.nasa.gov/mars/moons/", "scope":"known natural satellites, reference snapshot"},
  ("napoleon", "death_year"): {"value":1821, "reference":"https://www.britannica.com/biography/Napoleon-I", "scope":"Napoleon Bonaparte death year"},
}
ALLOWED_MODELS = set(x.strip() for x in os.environ.get("VCP_ALLOWED_MODELS","").split(",") if x.strip())
def parse_claim(raw):
    if not isinstance(raw,str) or len(raw)>10000: raise ValueError("Invalid completion length")
    value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!={"entity","attribute","value"}:
        raise ValueError("Model must provide exactly entity, attribute, value")
    if not isinstance(value["entity"],str) or not isinstance(value["attribute"],str):
        raise ValueError("Invalid claim schema")
    if len(value["entity"])>120 or len(value["attribute"])>80 or isinstance(value["value"],(dict,list)):
        raise ValueError("Invalid claim values")
    return value
def model_proposal(prompt, model, *, api_key=None, base_url=None):
    key=api_key or os.environ.get("VCP_MODEL_API_KEY")
    base=base_url or os.environ.get("VCP_MODEL_BASE_URL")
    if not key or not base: raise RuntimeError("Live model gateway not configured")
    if not ALLOWED_MODELS or model not in ALLOWED_MODELS: raise ValueError("Model not authorized")
    url=urllib.parse.urlparse(base)
    if url.scheme!="https" or not url.hostname or url.username or url.password or url.fragment:
        raise ValueError("Gateway must use an explicit HTTPS origin")
    endpoint=base.rstrip("/")+"/chat/completions"
    body={"model":model,"temperature":0,
          "messages":[{"role":"system","content":"Propose exactly one atomic factual claim. Return only JSON keys entity, attribute, value. Never claim verification or certification."},
          {"role":"user","content":prompt[:4000]}]}
    request=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={
      "Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(request,timeout=18) as response:
        if response.status!=200: raise RuntimeError("Model gateway failed")
        data=response.read(100000)
    payload=json.loads(data)
    return parse_claim(payload["choices"][0]["message"]["content"])

def assess_claim(claim, provenance=None):
    """Ontology, provenance, coherence are separate evidence observations."""
    entity=str(claim.get("entity","")).strip().lower()
    attribute=str(claim.get("attribute","")).strip().lower()
    entry=REGISTRY.get((entity,attribute))
    ont={"status":"MATCHED_REGISTERED_ENTITY" if entry else "UNKNOWN",
         "note":"Registration only; not proof of independent physical existence"}
    prov={"status":"UNVERIFIED","note":"No independently validated origin signature"}
    if provenance:
        prov["note"]="Source URL submitted but not cryptographically authenticated"
        prov["source_url"]=str(provenance)[:500]
    if not entry:
        coh={"status":"INCONCLUSIVE","note":"No policy-approved reference for this specific predicate"}
    elif claim.get("value")!=entry["value"]:
        coh={"status":"CONTRADICTED_BY_REFERENCE","reference":entry["reference"],
             "expected":entry["value"],"scope":entry["scope"]}
    else:
        coh={"status":"CONSISTENT_WITH_REFERENCE","reference":entry["reference"],"scope":entry["scope"],
             "note":"Reference registry consistency, not independently certified factual truth"}
    status="REFERENCE_CONSISTENT" if coh["status"]=="CONSISTENT_WITH_REFERENCE" else (
        "REFERENCE_CONTRADICTED" if coh["status"]=="CONTRADICTED_BY_REFERENCE" else "INCONCLUSIVE")
    return {"status":status,"certified":False,"claim":claim,
            "checks":{"ontology":ont,"provenance":prov,"coherence":coh},
            "limitation":"Reference values are curated test fixtures; no live source or C2PA signature was verified."}
