import asyncio, hashlib, json, unittest
from crossplane_audit import AuditRequest,audit,capabilities,canonical
class CrossPlaneAuditTests(unittest.TestCase):
 def test_budget_and_zero_actual_charge(self):
  r=audit(AuditRequest(task='code',claimed_provider='openai',claimed_model='example',
        input_tokens=1000,output_tokens=1000,quoted_input_usd_per_1k=1,
        quoted_output_usd_per_1k=2,cost_ceiling_usd=2))
  self.assertEqual(r['event']['projected_cost_usd'],3)
  self.assertFalse(r['event']['budget_eligible'])
  self.assertEqual(r['event']['actual_billed_usd'],0)
  self.assertFalse(r['event']['provider_identity_verified'])
 def test_proofs_never_invented(self):
  r=audit(AuditRequest())
  self.assertIsNone(r['receipt']['signature'])
  self.assertFalse(r['receipt']['immutable_ledger_proof'])
  self.assertEqual(r['receipt']['sha256'],hashlib.sha256(canonical(r['event'])).hexdigest())
 def test_policy_stays_apache_only(self):
  r=audit(AuditRequest(claimed_provider='google',claimed_model='gemini'))
  self.assertEqual(r['event']['routing_permission'],'DENIED_UNVERIFIED')
 def test_task_filter(self):
  with self.assertRaises(ValueError):audit(AuditRequest(task='carrier_bypass'))
 def test_caps(self):
  c=asyncio.run(capabilities())
  self.assertEqual(c['inference_policy'],'Apache-2.0-only locally configured model')
  self.assertEqual(c['ledger_anchor'],'not connected')
if __name__=='__main__':unittest.main()
