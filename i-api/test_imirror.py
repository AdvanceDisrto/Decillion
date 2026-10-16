import asyncio
import unittest
from hashlib import sha256
from imirror import iMirror, FaultTolerance, MirrorRequest, compare, capabilities, canonical

class MirrorTests(unittest.TestCase):
 def test_no_physical_claim(self):
  c=asyncio.run(capabilities())
  self.assertFalse(c["cloud_mirror_persistent"])
  self.assertFalse(c["fault_recovery_verified"])
 def test_exact_field_alignment(self):
  m=iMirror()
  m.local={"status":"online","v":4}
  m.remote={"status":"online","v":3}
  s=m.sync_reflective_matrix(real_time=True)
  self.assertEqual(s["symmetry_index"],0.5)
  self.assertFalse(s["live_cloud_sync"])
 def test_empty_has_unknown_alignment(self):
  self.assertIsNone(iMirror().sync_reflective_matrix()["symmetry_index"])
 def test_crash_snapshot_receipt(self):
  out=asyncio.run(compare(MirrorRequest(local={"a":1},remote={"a":1},inject_mock_crash=True)))
  self.assertTrue(out["fault_simulation"]["snapshot_match"])
  self.assertFalse(out["fault_simulation"]["actual_device_crashed"])
  self.assertFalse(out["result"]["live_cloud_sync"])
  self.assertEqual(out["receipt"]["sha256"],sha256(canonical(out["receipt"]["body"])).hexdigest())
 def test_camera_no_biometrics(self):
  self.assertEqual(iMirror.Camera().status()["depth_points_measured"],0)
 def test_fault_registration_is_simulated(self):
  self.assertFalse(FaultTolerance.register_crash_handler()["physical_device_recovered"])

if __name__=="__main__":unittest.main()
