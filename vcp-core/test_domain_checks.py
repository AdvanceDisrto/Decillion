import unittest
from domain_checks import assess_temporal,assess_arithmetic
class DomainChecks(unittest.TestCase):
 def test_historical_date_scope(self):
  self.assertEqual(assess_temporal("united states","president","Joe Biden","2024-01-20")["status"],"REFERENCE_CONSISTENT")
  self.assertEqual(assess_temporal("united states","president","Joe Biden","2025-08-01")["status"],"REFERENCE_CONTRADICTED")
 def test_out_of_range_is_uncertain(self):
  self.assertEqual(assess_temporal("united states","president","someone","2035-02-01")["status"],"INCONCLUSIVE")
 def test_math(self):
  self.assertEqual(assess_arithmetic("2*(3+4)",14)["status"],"VERIFIED_ARITHMETIC")
  self.assertEqual(assess_arithmetic("2*(3+4)",12)["status"],"REJECTED_ARITHMETIC")
 def test_arbitrary_code_refused(self):
  self.assertEqual(assess_arithmetic("__import__('os').system('id')",0)["status"],"INCONCLUSIVE")
if __name__=="__main__":unittest.main()
