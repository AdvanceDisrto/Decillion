import base64, hashlib, unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from independent_certifier import (Source,Package,STANDARD,assess,certify,verify_certificate,
                                   evidence_payload,canonical)
def b64(data):return base64.b64encode(data).decode()
def public(k):return b64(k.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
class ICETests(unittest.TestCase):
 def setUp(self):
  self.issuer=Ed25519PrivateKey.generate()
  self.keys={x:Ed25519PrivateKey.generate() for x in ("a","b","c")}
  self.trusted={name:public(key) for name,key in self.keys.items()}
  self.now=1760000000
  self.sources=[]
  for i,name in enumerate(self.keys):
   text="Independent evidence fixture "+name
   s=Source(witness_id=name,source_id="fixture://"+name,captured_at=self.now-10,
            evidence_text=text,sha256=hashlib.sha256(text.encode()).hexdigest(),
            witness_signature_b64="placeholder")
   s.witness_signature_b64=b64(self.keys[name].sign(canonical(evidence_payload(s))))
   self.sources.append(s)
  self.pkg=Package(claim="Mars has two moons",standard=STANDARD,sources=self.sources)
 def test_real_signatures_certify_only_evidence_integrity(self):
  r=certify(self.pkg,self.trusted,self.issuer,self.now)
  self.assertEqual(r["status"],"CERTIFIED_EVIDENCE_INTEGRITY_ONLY")
  self.assertTrue(verify_certificate(r["certificate"],public(self.issuer)))
  self.assertIn("not truth",r["certificate"]["payload"]["scope"])
 def test_one_source_rejected(self):
  self.pkg.sources=self.sources[:1]
  self.assertEqual(certify(self.pkg,self.trusted,self.issuer,self.now)["status"],"REJECTED")
 def test_fake_hash_rejected(self):
  self.sources[0].sha256="a"*64
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
 def test_forged_signature_rejected(self):
  self.sources[1].witness_signature_b64=b64(b"0"*64)
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
 def test_untrusted_key_rejected(self):
  del self.trusted["c"]
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
 def test_stale_witness_rejected(self):
  self.sources[2].captured_at=self.now-86401
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
 def test_same_witness_cannot_fake_three(self):
  for s in self.sources:s.witness_id="a"
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
 def test_forged_certificate_rejected(self):
  r=certify(self.pkg,self.trusted,self.issuer,self.now)
  r["certificate"]["payload"]["scope"]="Guaranteed universal truth"
  self.assertFalse(verify_certificate(r["certificate"],public(self.issuer)))
 def test_issuer_key_is_necessary(self):
  r=certify(self.pkg,self.trusted,self.issuer,self.now)
  self.assertFalse(verify_certificate(r["certificate"],public(Ed25519PrivateKey.generate())))
 def test_unsupported_standard(self):
  self.pkg.standard="UNLIMITED_TRUTH"
  self.assertFalse(assess(self.pkg,self.trusted,self.now)[0])
if __name__=="__main__":unittest.main()
