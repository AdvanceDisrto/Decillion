import asyncio,hashlib,json,unittest
from dewi_mesh import Route,Link,Sync,Change,shortest,merge,capabilities,digest
class DewiTests(unittest.TestCase):
 def test_multihop(self):
  q=Route(source='phone',destination='edge',links=[
   Link(a='phone',b='router',latency_ms=3),
   Link(a='router',b='edge',latency_ms=4),
   Link(a='phone',b='edge',latency_ms=20)])
  r=shortest(q)
  self.assertEqual(r['route']['path'],['phone','router','edge'])
  self.assertEqual(r['route']['estimated_link_cost_ms'],7)
  self.assertEqual(r['route']['actual_packets_delivered'],0)
 def test_outage(self):
  q=Route(source='a',destination='c',links=[
   Link(a='a',b='b',latency_ms=1),Link(a='b',b='c',latency_ms=1)],offline_nodes=['b'])
  self.assertIsNone(shortest(q)['route']['path'])
 def test_merge_commutative(self):
  a=Change(doc='notes',key='title',value='A',counter=3,actor='alice')
  b=Change(doc='notes',key='title',value='B',counter=3,actor='bob')
  self.assertEqual(merge(Sync(left=[a],right=[b]))['state'],merge(Sync(left=[b],right=[a]))['state'])
 def test_merge_not_network_claim(self):
  r=merge(Sync(left=[Change(doc='x',key='y',value='z',counter=1,actor='node')]))
  self.assertFalse(r['receipt']['body']['network_sync_performed'])
  self.assertEqual(r['receipt']['sha256'],digest(r['receipt']['body']))
  self.assertIsNone(r['receipt']['signature'])
 def test_caps(self):
  c=asyncio.run(capabilities())
  self.assertEqual(c['connected_physical_mesh_nodes'],0)
  self.assertFalse(c['vpu_hardware_available'])
 def test_untrusted_transport_rejected(self):
  from fastapi import HTTPException
  with self.assertRaises(HTTPException):
   shortest(Route(source='a',destination='b',links=[Link(a='a',b='b',latency_ms=1,transport='cellular')]))
if __name__=='__main__':unittest.main()
