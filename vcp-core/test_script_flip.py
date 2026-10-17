import math, unittest
from script_flip import negate_matrix,execute_script_flip
class InversionTests(unittest.TestCase):
 def test_double_negation_identity(self):
  matrix=[[0.45,-0.12],[-0.31,0.54]]
  self.assertEqual(negate_matrix(negate_matrix(matrix)),matrix)
 def test_not_inverse(self):
  self.assertNotEqual(negate_matrix([[2.0]]),[[0.5]])
 def test_no_truth_certificate(self):
  output=execute_script_flip([[1,-1],[4,8]])
  self.assertEqual(output["operation"],"ELEMENTWISE_NEGATION")
  self.assertFalse(output["factual_verification"])
  self.assertFalse(output["accelerated"])
 def test_invalid_shapes(self):
  for x in ([],[[1],[1,2]],[[float("nan")]],[[True]]):
   with self.assertRaises(ValueError):negate_matrix(x)
if __name__=="__main__":unittest.main()
