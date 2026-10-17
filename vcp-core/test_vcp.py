import json
import tempfile
import unittest
from pathlib import Path
from vcp import Engine, calculate, create_keypair, validate_receipt, authorize_execution

class VCPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"audit.jsonl"
        self.key,self.pub=create_keypair()
        self.engine=Engine(self.key,self.path)
    def tearDown(self): self.temp.cleanup()
    def test_verified_arithmetic_is_signed(self):
        outcome=self.engine.verify_math("2+2*3",8)
        self.assertEqual(outcome.status,"VERIFIED")
        self.assertTrue(validate_receipt(outcome.receipt,self.pub))
        self.assertTrue(self.engine.audit_integrity())
    def test_false_claim_denied(self):
        outcome=self.engine.verify_math("2+2",5)
        self.assertEqual(outcome.status,"REJECTED")
        self.assertIsNone(outcome.receipt)
    def test_code_injection_denied(self):
        self.assertEqual(self.engine.verify_math("__import__('os').system('echo bad')",1).status,"INCONCLUSIVE")
        self.assertEqual(self.engine.verify_math("2**10000",1).status,"INCONCLUSIVE")
    def test_zero_division(self): self.assertEqual(self.engine.verify_math("1/0",1).status,"INCONCLUSIVE")
    def test_invalid_signature_and_modified_claim(self):
        receipt=self.engine.verify_math("2+2",4).receipt
        receipt["signed"]["claimed"]=300
        self.assertFalse(validate_receipt(receipt,self.pub))
    def test_action_gate_denies_even_genuine_math_proof(self):
        receipt=self.engine.verify_math("2+2",4).receipt
        self.assertFalse(authorize_execution("transfer",receipt,self.pub,approved_actions={"transfer"},actor_authorized=True))
        self.assertFalse(authorize_execution("deploy",receipt,self.pub,approved_actions={"deploy"},actor_authorized=False))
    def test_tamper_detected_at_restart(self):
        self.engine.verify_math("2+2",4)
        raw=self.path.read_text().replace("VERIFIED","REJECTED")
        self.path.write_text(raw)
        self.assertFalse(self.engine.audit_integrity())
        with self.assertRaises(RuntimeError): Engine(self.key,self.path)
    def test_sequence_chain(self):
        self.engine.verify_math("2+2",4)
        self.engine.verify_math("6/2",3)
        self.assertEqual(len(self.path.read_text().splitlines()),2)
        self.assertTrue(Engine(self.key,self.path).audit_integrity())

if __name__=="__main__": unittest.main()
