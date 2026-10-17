"""ICE witness-side authenticated HTTPS collection.
Source authenticity means validated TLS connection to an explicitly allowlisted host,
not proof of the remote author's integrity or a factual claim.
"""
import hashlib, urllib.parse, urllib.request, ipaddress, socket, time, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from independent_certifier import Source,evidence_payload,canonical
def collect(url,witness_id,private_key,*,allowed_hosts,now=None):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!="https" or parsed.port not in (None,443) or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Source must be HTTPS on 443 without credentials or fragment")
    host=(parsed.hostname or "").lower().rstrip(".")
    if host not in allowed_hosts:raise ValueError("Host not allowlisted")
    if not isinstance(private_key,Ed25519PrivateKey):raise ValueError("Signing key missing")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise ValueError("Redirect refused")
    # Require caller-managed DNS policy/egress firewall too; DNS rebinding prevention at
    # network perimeter is essential. No public service should trust just this function.
    req=urllib.request.Request(url,headers={"User-Agent":"i-ICE-Witness/0.1","Accept":"text/plain"})
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=8) as resp:
        if resp.status!=200:raise ValueError("Non-200 source response")
        content_type=resp.headers.get_content_type()
        if content_type not in ("text/plain","application/json"):raise ValueError("Unsupported source media type")
        raw=resp.read(20001)
    if len(raw)>20000:raise ValueError("Evidence snapshot too large")
    text=raw.decode("utf-8","strict")
    stamp=int(time.time()) if now is None else now
    s=Source(witness_id=witness_id,source_id=url,captured_at=stamp,evidence_text=text,
             sha256=hashlib.sha256(text.encode()).hexdigest(),witness_signature_b64="pending")
    s.witness_signature_b64=base64.b64encode(private_key.sign(canonical(evidence_payload(s)))).decode()
    return s
