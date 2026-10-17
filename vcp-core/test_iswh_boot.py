import unittest
from dataclasses import replace
from iswh_boot import Manifest,boot
DIGEST="a"*64
class BootTests(unittest.TestCase):
 def setUp(self):
  self.m=Manifest("device01",DIGEST,DIGEST,DIGEST,"device01",DIGEST,DIGEST,DIGEST,
                  1800000000,True,True,False,True)
 def test_ready_scoped_only(self):
  out=boot(self.m,1800000000)
  self.assertEqual(out["status"],"READY_FOR_SCOPED_CHECKS")
  self.assertIn("NOT certified truth",out["phases"][-1]["detail"])
 def test_firmware_mismatch(self):
  self.assertEqual(boot(replace(self.m,firmware_digest="b"*64),1800000000)["status"],"DENIED")
 def test_stale_clock(self):
  self.assertEqual(boot(self.m,1800000500)["status"],"DENIED")
 def test_model_cannot_possess_signer(self):
  self.assertEqual(boot(replace(self.m,model_can_sign=True),1800000000)["status"],"DENIED")
 def test_execution_gate_required(self):
  self.assertEqual(boot(replace(self.m,execution_gate_active=False),1800000000)["status"],"DENIED")
 def test_audit_required(self):
  self.assertEqual(boot(replace(self.m,audit_healthy=False),1800000000)["status"],"DENIED")
 def test_device_binding(self):
  self.assertEqual(boot(replace(self.m,device_id="unexpected"),1800000000)["status"],"DENIED")
if __name__=="__main__":unittest.main()
