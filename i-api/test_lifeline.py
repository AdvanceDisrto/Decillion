import asyncio
import hashlib
import json
import unittest
from fastapi import HTTPException
from lifeline import capabilities,mock_packet,estimate_power,Message,Power

class LifelineTests(unittest.TestCase):
 def test_zero_carrier_attachments(self):
  d=asyncio.run(capabilities())
  self.assertEqual(len(d["carriers"]),5)
  self.assertTrue(all(not c["connected"] for c in d["carriers"]))
  self.assertFalse(d["automatic_911_delivery"])
 def test_mock_not_delivered(self):
  out=asyncio.run(mock_packet(Message(handle="@test",message="test-only")))
  self.assertEqual(out["status"],"SIMULATED_NOT_DELIVERED")
  self.assertFalse(out["receipt"]["body"]["actually_transmitted"])
  self.assertEqual(out["receipt"]["signature"],None)
  data=json.dumps(out["receipt"]["body"],sort_keys=True,separators=(",",":")).encode()
  self.assertEqual(hashlib.sha256(data).hexdigest(),out["receipt"]["sha256"])
 def test_power_budget(self):
  p=asyncio.run(estimate_power(Power(battery_wh=100,solar_w=0,base_w=5,radio_w=5,duty_cycle=.5)))
  self.assertAlmostEqual(p["estimated_runtime_hours"],13.333,places=3)
 def test_unknown_route(self):
  with self.assertRaises(HTTPException):
   asyncio.run(mock_packet(Message(handle="@test",message="hello",route="fake")))
 def test_handle_validation(self):
  with self.assertRaises(Exception):Message(handle="not-a-handle",message="hello")

if __name__=="__main__":unittest.main()
