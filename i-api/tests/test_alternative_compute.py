import asyncio
import math
import unittest
from hashlib import sha256
from alternative_compute import LabRequest,photonic,neuromorphic,quantum,run,capabilities,canonical

class AlternativeComputeTests(unittest.TestCase):
    def test_photonic_energy_conserved(self):
        for phase in (0,.2,math.pi,-math.pi):
            self.assertLess(photonic([.7,-.3],phase,12)["energy_conservation_error"],1e-9)
    def test_photonic_phase_changes_output(self):
        self.assertNotEqual(photonic([.7,.3],0,1)["output_intensity"],
                            photonic([.7,.3],math.pi,1)["output_intensity"])
    def test_neuromorphic_reproducible(self):
        result=neuromorphic([.8,.1],.2,20)
        self.assertEqual(len(result["trace"]),20)
        self.assertEqual(result,neuromorphic([.8,.1],.2,20))
    def test_quantum_norm(self):
        for angle in (-2,0,.4,3):
            r=quantum([angle,.2],.3,10)
            self.assertLess(r["normalization_error"],1e-9)
            self.assertAlmostEqual(sum(r["probabilities"]),1,places=9)
    def test_reject_nan(self):
        with self.assertRaises(ValueError):photonic([float("nan"),0],0,1)
    def test_capabilities_do_not_claim_hardware(self):
        info=asyncio.run(capabilities())
        self.assertEqual(len(info["engines"]),3)
        self.assertFalse(info["fabrication_verified"])
        self.assertFalse(info["biological_material_used"])
        self.assertTrue(all(x["hardware_connected"] is False for x in info["engines"]))
    def test_receipt_integrity(self):
        r=asyncio.run(run(LabRequest(engine="quantum")))["receipt"]
        self.assertEqual(r["sha256"],sha256(canonical(r["body"])).hexdigest())
        self.assertFalse(r["anchored"])
        self.assertIsNone(r["signature"])
    def test_request_bounds(self):
        with self.assertRaises(Exception):LabRequest(engine="quantum",steps=999)

if __name__=="__main__":
    unittest.main()
