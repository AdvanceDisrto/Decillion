"""Small dependency-free proof-contract fixture for CI; not a production certificate."""
import hashlib
import json
import unittest

def canon(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(o):
    return 'sha256:' + hashlib.sha256(canon(o)).hexdigest()

def decide(contract, attempt):
    if (contract['claim_id'], contract['claim_version']) != (attempt.get('claim_id'), attempt.get('claim_version')):
        return 'NOT_CERTIFIED'
    if not attempt.get('executed') or attempt.get('decision') != 'REQUIREMENTS_SATISFIED':
        return 'NOT_CERTIFIED'
    if attempt.get('checks_failed') or attempt.get('blocking_issues'):
        return 'NOT_CERTIFIED'
    if not set(contract['required_checks']).issubset(set(attempt.get('checks_passed', []))):
        return 'NOT_CERTIFIED'
    if any(attempt.get('evidence', {}).get(k) is None for k in contract['required_evidence']):
        return 'NOT_CERTIFIED'
    return 'CHECKS_SATISFIED_NOT_SIGNED'

class TestContract(unittest.TestCase):
    def setUp(self):
        self.c = {'claim_id':'demo', 'claim_version':'v1', 'required_checks':['test'], 'required_evidence':['input']}
        self.a = {'claim_id':'demo', 'claim_version':'v1', 'executed':True, 'decision':'REQUIREMENTS_SATISFIED', 'checks_passed':['test'], 'evidence':{'input':digest('x')}}
    def test_fixture(self): self.assertEqual(decide(self.c,self.a),'CHECKS_SATISFIED_NOT_SIGNED')
    def test_missing_evidence(self): self.a['evidence']={}; self.assertEqual(decide(self.c,self.a),'NOT_CERTIFIED')
    def test_refusal(self): self.a['decision']='REFUSED'; self.assertEqual(decide(self.c,self.a),'NOT_CERTIFIED')
    def test_unexecuted(self): self.a['executed']=False; self.assertEqual(decide(self.c,self.a),'NOT_CERTIFIED')
    def test_hash_canonicalization(self): self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))

if __name__ == '__main__': unittest.main()
