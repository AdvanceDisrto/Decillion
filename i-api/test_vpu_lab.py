import unittest
from vpu_lab import encode, decode, execute, Program
class VPUTest(unittest.TestCase):
 def test_math(self):
  p=Program(words=[encode('ADD',0,1),encode('STAMP')],registers=[6,7,0,0,0,0,0,0])
  r=execute(p)
  self.assertEqual(r['state']['registers'][0],13)
  self.assertIsNone(r['receipt']['signature'])
 def test_fault(self):
  p=Program(words=[encode('ADD',0,1)],registers=[6,7,0,0,0,0,0,0],fault_cycle=0)
  self.assertEqual(execute(p)['status'],'FAULT_INJECTED')
if __name__=='__main__':unittest.main()
