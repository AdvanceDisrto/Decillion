import os,unittest
from unittest.mock import patch,AsyncMock
from fastapi import HTTPException
from generative_seed import Request,ready,generate,allowed
class TestGenerative(unittest.IsolatedAsyncioTestCase):
 async def test_off_by_default(self):
  with patch.dict(os.environ,{"IAPI_GENERATIVE_PROVIDERS_ALLOWLIST":""}):
   self.assertFalse(ready("openai"))
   with self.assertRaises(HTTPException) as e:await generate(Request(prompt="Hello",provider="openai"))
   self.assertEqual(e.exception.status_code,503)
 async def test_unknown_provider(self):
  with patch.dict(os.environ,{"IAPI_GENERATIVE_PROVIDERS_ALLOWLIST":"openai"}):
   self.assertFalse(ready("madeup"))
 async def test_configured_request_never_certifies(self):
  class Response:
   def raise_for_status(self):pass
   def json(self):return {"choices":[{"message":{"content":"Proposed answer"}}]}
  class Client:
   async def __aenter__(self):return self
   async def __aexit__(self,*a):pass
   async def post(self,url,**kwargs):
    self_for_test.last_url=url;self_for_test.body=kwargs["json"]
    return Response()
  self_for_test=self
  with patch.dict(os.environ,{"IAPI_GENERATIVE_PROVIDERS_ALLOWLIST":"openai",
                              "IAPI_OPENAI_KEY":"sample-server-secret",
                              "IAPI_OPENAI_MODEL_ID":"configured-model"}),patch("generative_seed.httpx.AsyncClient",return_value=Client()):
   r=await generate(Request(prompt="Hello",provider="openai"))
   self.assertEqual(r["status"],"UNVERIFIED_PROPOSAL")
   self.assertFalse(r["certified"]);self.assertFalse(r["execution_authorized"])
   self.assertEqual(self.last_url,"https://api.openai.com/v1/chat/completions")
   self.assertEqual(self.body["model"],"configured-model")
if __name__=="__main__":unittest.main()
