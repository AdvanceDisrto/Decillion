import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from vcp_live import parse_proposal, assess, VerificationRequest

class VCPIntegrationTests(unittest.TestCase):
    def test_structural_claim_schema(self):
        self.assertEqual(parse_proposal('{"entity":"Mars","attribute":"moons","value":2}')["value"],2)
        for raw in ['{"entity":"Mars","attribute":"moons","value":2,"certified":true}','{}','not json']:
            with self.assertRaises((ValueError,json.JSONDecodeError)):
                parse_proposal(raw)
    def test_missing_auth_denied(self):
        with patch("main.user_id", new=AsyncMock(side_effect=HTTPException(401,"Not authenticated"))):
            with self.assertRaises(HTTPException) as ex:
                asyncio.run(assess(VerificationRequest(prompt="How many moons does Mars have?"),authorization=""))
            self.assertEqual(ex.exception.status_code,401)
    def test_live_source_assessment_never_certifies(self):
        with patch("main.user_id", new=AsyncMock(return_value=("user1","token"))), \
             patch("vcp_live.infer", new=AsyncMock(return_value=('{"entity":"Mars","attribute":"moons","value":2}',"test/model"))), \
             patch("vcp_live.source_snapshot", new=AsyncMock(return_value={"title":"Mars","url":"https://en.wikipedia.org/?curid=14640471"})):
            result=asyncio.run(assess(VerificationRequest(prompt="How many moons does Mars have?"),authorization="Bearer token"))
        self.assertEqual(result["status"],"EVIDENCE_RETRIEVED")
        self.assertFalse(result["certified"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["checks"]["coherence"]["status"],"NOT_EVALUATED")
        self.assertEqual(len(result["record_sha256"]),64)
    def test_source_unavailable_no_fake_proof(self):
        with patch("main.user_id", new=AsyncMock(return_value=("u","token"))), \
             patch("vcp_live.infer", new=AsyncMock(return_value=('{"entity":"unknown","attribute":"x","value":5}',"test/model"))), \
             patch("vcp_live.source_snapshot", new=AsyncMock(return_value=None)):
            result=asyncio.run(assess(VerificationRequest(prompt="What is this unknown quantity?"),authorization="Bearer token"))
        self.assertEqual(result["status"],"INCONCLUSIVE")
        self.assertIsNone(result["source"])
if __name__=="__main__":unittest.main()
