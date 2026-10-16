import asyncio
import os
import tempfile
import unittest
from cryptography.exceptions import InvalidTag
from iuniversalapi import ScopedCache,Mesh,Router,Provider,Telemetry,Container,digest
from iuniversalapi.stress import stress

class GridTests(unittest.TestCase):
 def test_scoped_cache(self):
  c=ScopedCache()
  c.put('alice','m1','hi','private')
  self.assertEqual(c.get('alice','m1','hi'),'private')
  self.assertIsNone(c.get('bob','m1','hi'))
  self.assertIsNone(c.get('alice','m2','hi'))
 def test_no_claimed_providers(self):
  with self.assertRaises(RuntimeError):
   asyncio.run(Router(providers=[]).complete('hello',scope='u'))
 def test_provider_requires_key_model_and_https(self):
  p=Provider('local','http://localhost:8080','m','MISSING_UNITTEST_KEY')
  self.assertFalse(p.available())
 def test_envelope_roundtrip(self):
  k=os.urandom(32);a=Mesh(k,'phone');b=Mesh(k,'pc')
  blob=a.encrypt('pc',{'value':42,'source':'buddy'})
  self.assertEqual(b.decrypt(blob)['value'],42)
  with self.assertRaises(ValueError):b.decrypt(blob)
 def test_envelope_tamper(self):
  k=os.urandom(32);a=Mesh(k,'phone');b=Mesh(k,'pc')
  blob=a.encrypt('pc',{'token':'hello'})
  blob['ciphertext']='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
  with self.assertRaises((InvalidTag,ValueError)):b.decrypt(blob)
 def test_no_native_binary_misclaim(self):
  with self.assertRaises(NotImplementedError):Container.compile()
 def test_telemetry_zero(self):
  self.assertEqual(Telemetry.optimize_cross_plane([])['success_rate'],0)
 def test_10k_mock_events(self):
  result=asyncio.run(stress(10000,100))
  self.assertEqual(result['requested_events'],10000)
  self.assertEqual(result['actual_network_connections'],0)
  self.assertEqual(result['telemetry']['successful'],10000)
  self.assertTrue(result['receipt_sha256'])
  self.assertIsNone(result['signature'])

if __name__=='__main__':unittest.main()
