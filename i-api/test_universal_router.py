"""iUniversalApi routing tests: never claim an unconfigured provider is connected."""
import asyncio
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from universal_router import ENDPOINTS, active, infer, providers, safe_url

class TestUniversalRouter(unittest.TestCase):
    def test_expected_adapters(self):
        self.assertEqual({e.id for e in ENDPOINTS},
          {"openai","anthropic","groq","deepseek","google","huggingface","mit-licensed-llm","apache2-licensed-llm"})
    def test_self_hosted_requires_explicit_setup(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(len(active()),0)
            self.assertFalse(next(e for e in ENDPOINTS if e.id=="mit-licensed-llm").ready())
    def test_configuration_status_has_no_secret(self):
        with patch.dict("os.environ",{"IAPI_HF_TOKEN":"test-secret","IAPI_HF_MODEL_ID":"a/b"},clear=True):
            item=asyncio.run(providers())
            hf=next(i for i in item["providers"] if i["id"]=="huggingface")
            self.assertTrue(hf["configured"])
            self.assertNotIn("test-secret",str(item))
    def test_blocks_bad_urls(self):
        for s in ("","http://localhost/v1","https://user:pass@host/v1","javascript:abc"):
            self.assertFalse(safe_url(s))
    def test_no_inference_without_providers(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaises(HTTPException) as ex:
                asyncio.run(infer("Hello"))
            self.assertEqual(ex.exception.status_code,503)
    def test_input_bounds(self):
        with self.assertRaises(HTTPException):
            asyncio.run(infer(""))

if __name__=="__main__":unittest.main()
