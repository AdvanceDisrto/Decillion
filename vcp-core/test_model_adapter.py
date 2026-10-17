import json, unittest
from unittest.mock import patch
from model_adapter import parse_claim, assess_claim, model_proposal
class SemanticTests(unittest.TestCase):
 def test_registered_consistent_is_not_certified(self):
  out=assess_claim({"entity":"mars","attribute":"moons","value":2})
  self.assertEqual(out["status"],"REFERENCE_CONSISTENT")
  self.assertFalse(out["certified"])
  self.assertEqual(out["checks"]["provenance"]["status"],"UNVERIFIED")
 def test_false_moon_count_rejected(self):
  self.assertEqual(assess_claim({"entity":"mars","attribute":"moons","value":5})["status"],"REFERENCE_CONTRADICTED")
 def test_unknown_is_inconclusive(self):
  self.assertEqual(assess_claim({"entity":"unknown","attribute":"moons","value":1})["status"],"INCONCLUSIVE")
 def test_fake_signature_never_verifies(self):
  v=assess_claim({"entity":"mars","attribute":"moons","value":2}, "SIG_SECURE_FAKE")
  self.assertEqual(v["checks"]["provenance"]["status"],"UNVERIFIED")
 def test_validate_exact_schema(self):
  with self.assertRaises(ValueError):parse_claim('{"entity":"mars","value":2}')
  with self.assertRaises(ValueError):parse_claim('{"entity":"mars","attribute":"moons","value":2,"certified":true}')
 def test_model_requires_configuration(self):
  with patch.dict("os.environ",{"VCP_MODEL_API_KEY":"","VCP_MODEL_BASE_URL":""}):
   with self.assertRaises(RuntimeError):model_proposal("Mars moons","any")
if __name__=="__main__":unittest.main()
