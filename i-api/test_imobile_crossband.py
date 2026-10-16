import asyncio, hashlib, json, unittest
from imobile_crossband import Scenario,run_scenario,crossband_capabilities
class CrossBandTests(unittest.TestCase):
 def test_local_only(self):
  r=run_scenario(Scenario(packets=100,local_available=True))
  self.assertEqual(r['routes']['authorized-local-lan'],100)
  self.assertEqual(r['routes']['satellite-partner'],0)
  self.assertEqual(r['actual_deliveries'],0)
 def test_all_unavailable_stores_undelivered(self):
  r=run_scenario(Scenario(local_available=False,packets=123))
  self.assertEqual(r['store_and_forward_units'],123)
  self.assertEqual(r['actual_deliveries'],0)
 def test_hypothetical_routing(self):
  r=run_scenario(Scenario(packets=120,local_available=True,satellite_available=True,cellular_available=True))
  self.assertEqual(sum(r['routes'].values()),120)
  self.assertEqual(r['routes']['satellite-partner'],40)
 def test_satellite_outage(self):
  r=run_scenario(Scenario(packets=120,satellite_available=True,satellite_outage=True))
  self.assertEqual(r['routes']['satellite-partner'],0)
 def test_revenue_not_collected(self):
  r=run_scenario(Scenario(unit_price_usd_per_gb=100,packets=1000))
  self.assertGreater(r['receipt']['body']['projected_revenue_usd'],0)
  self.assertEqual(r['receipt']['body']['actual_revenue_usd'],0)
 def test_unsigned_receipt_consistent(self):
  r=run_scenario(Scenario())
  body=r['receipt']['body']
  self.assertEqual(r['receipt']['sha256'],hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest())
  self.assertIsNone(r['receipt']['signature'])
 def test_no_hardware_identifiers_or_public_assistance(self):
  r=run_scenario(Scenario())
  self.assertFalse(r['receipt']['body']['hardware_identifiers_collected'])
  self.assertFalse(r['receipt']['body']['government_eligibility_verified'])
 def test_caps(self):
  d=asyncio.run(crossband_capabilities())
  self.assertFalse(d['starlink_connected'])
  self.assertFalse(d['billing_active'])
 def test_bounds(self):
  with self.assertRaises(Exception):Scenario(packets=1000000)
if __name__=='__main__':unittest.main()
