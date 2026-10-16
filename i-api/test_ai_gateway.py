import asyncio
import os
import unittest
from unittest.mock import patch,AsyncMock
from fastapi import HTTPException
from ai_gateway import (Chat,configured,eligible_providers,selected_tier,rate_check,run_gateway,
                        safe_provider_data,receipt,status,THREADS,REQUESTS,USAGE,agent_loop_demo,invoice_preview,check_auth,issue_key)

class GatewayTests(unittest.TestCase):
 def setUp(self):
  THREADS.clear();REQUESTS.clear();USAGE.clear()
 def test_no_real_providers_by_default(self):
  with patch.dict(os.environ,{},clear=True):
   self.assertFalse(any(configured().values()))
   self.assertEqual(eligible_providers('free'),['apache2-licensed-llm'])
   self.assertEqual(eligible_providers('paid'),['apache2-licensed-llm'])
 def test_tier_not_accepted_from_client(self):
  with patch.dict(os.environ,{'I_GATEWAY_PAID_USER_IDS':'user-a'},clear=True):
   self.assertEqual(selected_tier('user-a'),'paid')
   self.assertEqual(selected_tier('user-b','enterprise'),'free')
 def test_config_enabled_requires_optin_and_credentials(self):
  env={'OPENAI_API_KEY':'secret','IAPI_OPENAI_MODEL_ID':'gpt-test'}
  with patch.dict(os.environ,env,clear=True):self.assertFalse(configured()['openai'])
  with patch.dict(os.environ,{**env,'I_GATEWAY_PAID_ENABLED':'true'},clear=True):
   self.assertTrue(configured()['openai'])
   self.assertNotIn('secret',str(asyncio.run(status())))
 def test_no_credential_no_paid_call(self):
  with patch.dict(os.environ,{'I_GATEWAY_PAID_USER_IDS':'alice','I_GATEWAY_PAID_ENABLED':'true'},clear=True):
   with self.assertRaises(HTTPException) as cm:
    asyncio.run(run_gateway(Chat(message='hello'), 'alice'))
   self.assertEqual(cm.exception.status_code,403)
 def test_no_known_price_never_calls_provider(self):
  with patch.dict(os.environ,{'I_GATEWAY_PAID_USER_IDS':'alice','I_GATEWAY_PAID_ENABLED':'true',
         'OPENAI_API_KEY':'not-used','IAPI_OPENAI_MODEL_ID':'model'},clear=True):
   with patch('ai_gateway.remote_infer',new_callable=AsyncMock) as mocked:
    with self.assertRaises(HTTPException):asyncio.run(run_gateway(Chat(message='hello'),'alice'))
    mocked.assert_not_called()
 def test_rate_limited(self):
  with patch.dict(os.environ,{},clear=True):
   for _ in range(12):asyncio.run(rate_check('u','free'))
   with self.assertRaises(HTTPException) as ex:asyncio.run(rate_check('u','free'))
   self.assertEqual(ex.exception.status_code,429)
 def test_model_response_not_independent_attestation(self):
  x=safe_provider_data('openai',{'model':'actual','choices':[{'message':{'content':'Hi'}}],
      'usage':{'prompt_tokens':3,'completion_tokens':4}},1,'requested')
  self.assertEqual(x['reported_model'],'actual')
  self.assertEqual(x['tokens_in'],3)
  r=receipt({'claimed_model':'actual'})
  self.assertFalse(r['certified'])
  self.assertIsNone(r['ledger_anchor'])
 def test_no_cross_user_thread_access(self):
  env={}
  with patch.dict(os.environ,env,clear=True),patch('universal_router.infer',new_callable=AsyncMock) as inferred:
   inferred.return_value=('Hello','apache2-licensed-llm/model')
   original=asyncio.run(run_gateway(Chat(message='one'),'owner'))
   with self.assertRaises(HTTPException) as ex:
    asyncio.run(run_gateway(Chat(message='two',thread_id=original['thread_id']),'outsider'))
   self.assertEqual(ex.exception.status_code,404)
 def test_free_refuses_cloud_preference(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(HTTPException) as ex:
    asyncio.run(run_gateway(Chat(message='hello',preferred_provider='anthropic'),'u'))
   self.assertEqual(ex.exception.status_code,403)

 def test_paid_fallback_requires_explicit_prompt_sharing_opt_in(self):
  env={'I_GATEWAY_PAID_USER_IDS':'alice','I_GATEWAY_PAID_ENABLED':'true',
       'OPENAI_API_KEY':'test-key','IAPI_OPENAI_MODEL_ID':'test-model',
       'ANTHROPIC_API_KEY':'test-key','IAPI_ANTHROPIC_MODEL_ID':'test-model',
       'I_GATEWAY_OPENAI_INPUT_COST_PER_1K':'0','I_GATEWAY_OPENAI_OUTPUT_COST_PER_1K':'0',
       'I_GATEWAY_ANTHROPIC_INPUT_COST_PER_1K':'0','I_GATEWAY_ANTHROPIC_OUTPUT_COST_PER_1K':'0'}
  async def provider(provider,messages,max_tokens):
   if provider=='openai':raise HTTPException(502,'upstream unavailable')
   return {'answer':'authorized fallback','requested_model':'test-model',
           'reported_model':'test-model','tokens_in':1,'tokens_out':1,'latency_ms':1}
  with patch.dict(os.environ,env,clear=True),patch('ai_gateway.remote_infer',side_effect=provider) as remote:
   with self.assertRaises(HTTPException) as failure:
    asyncio.run(run_gateway(Chat(message='private prompt'),'alice'))
   self.assertEqual(failure.exception.status_code,503)
   self.assertEqual(remote.call_count,1)
   remote.reset_mock()
   reply=asyncio.run(run_gateway(Chat(message='opted in prompt',allow_cross_provider_fallback=True),'alice'))
   self.assertEqual(reply['answer'],'authorized fallback')
   self.assertEqual(remote.call_count,2)

 def test_multiagent_proof_is_real_local_only(self):
  v=agent_loop_demo('  Validate     this code  ','code')
  self.assertEqual(len(v['execution']['stages']),3)
  self.assertEqual(v['execution']['provider_apis_called'],0)
  self.assertFalse(v['execution']['real_multi_model_exchange'])
  self.assertFalse(v['receipt']['certified'])
 def test_proxy_token_issue_requires_verified_primary_auth(self):
  import jwt
  secret='A'*40
  with patch.dict(os.environ,{'I_GATEWAY_TOKEN_SECRET':secret},clear=True):
   with patch('main.user_id',new_callable=AsyncMock) as auth:
    auth.return_value=('owner','primary-token')
    issued=asyncio.run(issue_key('Bearer primary-token'))
    self.assertTrue(issued['token'].startswith('iat.'))
    self.assertFalse(issued['mpc'])
    verified=asyncio.run(check_auth('Bearer '+issued['token']))
    self.assertEqual(verified,'owner')
    auth.assert_awaited_once()
 def test_invoice_preview_never_fakes_charge(self):
  with patch('main.user_id',new_callable=AsyncMock) as auth:
   auth.return_value=('owner','primary-token')
   result=asyncio.run(invoice_preview('Bearer valid'))
   self.assertEqual(result['verified_charges_usd'],0)
   self.assertFalse(result['wallet_debit_performed'])
if __name__=='__main__':unittest.main()
