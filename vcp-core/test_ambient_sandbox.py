import tempfile,unittest
from pathlib import Path
from ambient_sandbox import AmbientRoom,Lattice,Boundary,display_receipt
from independent_certifier import certify,cert_id
from ice_security import IceStore
from test_independent_certifier import ICETests,public
class AmbientTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=IceStore(Path(self.tmp.name)/"audit.sqlite3")
  self.fx=ICETests();self.fx.setUp()
  self.room=AmbientRoom("ALPHA");self.ledger=Lattice()
  self.node=Boundary(self.room,self.ledger,public(self.fx.issuer),self.store)
  self.cert=certify(self.fx.pkg,self.fx.trusted,self.fx.issuer,self.fx.now)["certificate"]
 def tearDown(self):self.fx.tearDown();self.tmp.cleanup()
 def test_centered_false_statement_not_certified(self):
  self.room.awaken([0.5,-0.5,0])
  outcome=self.node.process("Mars has 9000 moons",[0.5,-0.5,0])
  self.assertEqual(outcome["status"],"LOCAL_ONLY")
  self.assertEqual(self.ledger.published,[])
 def test_valid_evidence_certificate_scope_only(self):
  self.room.awaken([0.9,-0.4,0.33])
  outcome=self.node.process("Mars has two moons",[0.5,-0.5,0],self.cert)
  self.assertEqual(outcome["status"],"PUBLISHED_EVIDENCE_ATTESTATION")
  self.assertFalse(outcome["event"]["is_factual_truth_certified"])
  self.assertFalse(display_receipt(outcome)["physical_photons_emitted"])
 def test_revoked_receipt_cannot_cross(self):
  self.room.awaken([1,-1,0])
  self.store.revoke(cert_id(self.cert),"Operator revocation")
  self.assertEqual(self.node.process("any",[0,0,0],self.cert)["status"],"DENIED")
 def test_forgery_triggers_quarantine(self):
  self.room.awaken([1,0,0])
  self.cert["payload"]["status"]="CERTIFIED_ABSOLUTE_TRUTH"
  self.assertEqual(self.node.process("any",[0,0,0],self.cert)["status"],"QUARANTINED")
  self.assertTrue(self.room.quarantined)
  with self.assertRaises(PermissionError):self.room.awaken([1,2,3])
 def test_invalid_field(self):
  with self.assertRaises(ValueError):self.room.awaken([float('nan'),0,0])
if __name__=="__main__":unittest.main()
