import asyncio
import os
import unittest
from unittest.mock import AsyncMock,patch
from fastapi import HTTPException
from sorcery import allowed,principal,dispatch,Dispatch,WORKFLOWS
class SorceryAccessTests(unittest.TestCase):
 def test_operator_denied_by_default(self):
  with patch.dict(os.environ,{},clear=True):self.assertFalse(allowed("uid"))
 def test_operator_exact_match(self):
  with patch.dict(os.environ,{"I_SORCERY_OPERATOR_UIDS":"allowed,other"},clear=True):
   self.assertTrue(allowed("allowed"))
   self.assertFalse(allowed("allow"))
 def test_denied_before_upstream_dispatch(self):
  with patch.dict(os.environ,{},clear=True),patch("main.user_id",new_callable=AsyncMock) as auth:
   auth.return_value=("user","session")
   with self.assertRaises(HTTPException) as caught:
    asyncio.run(dispatch(Dispatch(workflow="android",confirmation="RUN android"),"Bearer test"))
   self.assertEqual(caught.exception.status_code,403)
 def test_confirmation_required(self):
  with patch.dict(os.environ,{"I_SORCERY_OPERATOR_UIDS":"admin"},clear=True),patch("main.user_id",new_callable=AsyncMock) as auth:
   auth.return_value=("admin","session")
   with self.assertRaises(HTTPException) as caught:
    asyncio.run(dispatch(Dispatch(workflow="android",confirmation="wrong"),"Bearer test"))
   self.assertEqual(caught.exception.status_code,400)
 def test_arbitrary_workflow_refused(self):
  with patch.dict(os.environ,{"I_SORCERY_OPERATOR_UIDS":"admin"},clear=True),patch("main.user_id",new_callable=AsyncMock) as auth:
   auth.return_value=("admin","session")
   with self.assertRaises(HTTPException) as caught:
    asyncio.run(dispatch(Dispatch(workflow="../../unknown.yml",confirmation="RUN ../../unknown.yml"),"Bearer test"))
   self.assertEqual(caught.exception.status_code,422)
class IntegrationInventoryTests(unittest.TestCase):
 def test_unconfigured_remains_unverified(self):
  from sorcery import integration_inventory
  with patch.dict(os.environ,{},clear=True):
   report=integration_inventory()
   self.assertFalse(report["github"]["configured"])
   self.assertFalse(report["github"]["authenticated"])
   self.assertFalse(report["apple-signing"]["live_call_verified"])
 def test_configured_does_not_mean_authenticated_and_no_secrets_leak(self):
  from sorcery import integration_inventory
  with patch.dict(os.environ,{"I_SORCERY_GITHUB_TOKEN":"very-secret"},clear=True):
   report=integration_inventory()
   self.assertTrue(report["github"]["configured"])
   self.assertFalse(report["github"]["authenticated"])
   self.assertNotIn("very-secret",str(report))

if __name__=="__main__": unittest.main()
