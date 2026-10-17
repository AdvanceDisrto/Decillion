import hashlib,tempfile,unittest
from pathlib import Path
from ice_security import IceStore
from independent_certifier import verify_current,certify,cert_id
from test_independent_certifier import ICETests,public
class DurableIceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.db=IceStore(Path(self.tmp.name)/"ice.db")
 def tearDown(self):self.tmp.cleanup()
 def test_unique_nonce_survives_restart(self):
  self.db.record_once("nonce-very-long-and-unique-0001","a"*64,{"status":"REJECTED"})
  reopened=IceStore(self.db.path)
  with self.assertRaisesRegex(ValueError,"Replay"):
   reopened.record_once("nonce-very-long-and-unique-0001","a"*64,{"status":"REJECTED"})
  self.assertTrue(reopened.integrity())
 def test_hash_tampering_detected(self):
  self.db.record_once("nonce-very-long-and-unique-0002","b"*64,{"status":"REJECTED"})
  with self.db.connect() as c:
   c.execute("UPDATE events SET event_json='{}' WHERE id=1")
  self.assertFalse(self.db.integrity())
  with self.assertRaises(RuntimeError):
   self.db.record_once("nonce-very-long-and-unique-0003","c"*64,{"status":"REJECTED"})
 def test_certificate_revocation(self):
  fx=ICETests();fx.setUp()
  try:
   certificate=certify(fx.pkg,fx.trusted,fx.issuer,fx.now)["certificate"]
   self.assertTrue(verify_current(certificate,public(fx.issuer),self.db))
   self.db.revoke(cert_id(certificate),"Operator withdrew the attestation")
   self.assertFalse(verify_current(certificate,public(fx.issuer),self.db))
   self.assertTrue(self.db.integrity())
  finally:fx.tearDown()
 def test_duplicate_revocation(self):
  self.db.revoke("a"*64,"incorrect signature")
  with self.assertRaises(ValueError):self.db.revoke("a"*64,"again")
if __name__=="__main__":unittest.main()
