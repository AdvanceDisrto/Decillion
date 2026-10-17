import unittest
from power_budget import budget
class PDNTests(unittest.TestCase):
 def test_700w_current(self):self.assertAlmostEqual(budget()["rail_amps"],823.529,3)
 def test_ripple(self):self.assertEqual(budget()["max_voltage_excursion_mV"],4.25)
 def test_loss(self):self.assertAlmostEqual(budget()["vrm_loss_watts"],77.778,3)
 def test_invalid(self):
  with self.assertRaises(ValueError):budget(efficiency=1.2)
if __name__=="__main__":unittest.main()
