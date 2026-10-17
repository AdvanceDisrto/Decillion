import unittest
from action_gate import authorize
class TestActionGate(unittest.TestCase):
 def test_no_execution_on_raw_model_output(self):
  self.assertFalse(authorize("transfer $10,000").allowed)
 def test_evidence_certificate_cannot_transfer(self):
  d=authorize("transfer $10,000",human_approved=True,identity_authenticated=True,task_scoped_authorization=True,receipt_signature_valid=True,receipt_not_revoked=True,standard="ICE-01-EVIDENCE-INTEGRITY/1")
  self.assertFalse(d.allowed)
 def test_dry_run_only(self):
  options=dict(human_approved=True,identity_authenticated=True,task_scoped_authorization=True,receipt_signature_valid=True,receipt_not_revoked=True,standard="ACTION-AUTHORIZATION/1")
  self.assertTrue(authorize("propose",**options).allowed)
  self.assertFalse(authorize("transfer",dry_run=False,**options).allowed)
if __name__=="__main__":unittest.main()
