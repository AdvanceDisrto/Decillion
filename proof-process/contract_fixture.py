"""Dependency-free scoped proof-contract fixture, not a certificate."""
import hashlib
import json
import unittest


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(obj):
    return "sha256:" + hashlib.sha256(canon(obj)).hexdigest()


def decide(contract, attempt):
    expected = (contract["claim_id"], contract["claim_version"])
    actual = (attempt.get("claim_id"), attempt.get("claim_version"))
    if expected != actual:
        return "NOT_CERTIFIED"
    if not attempt.get("executed"):
        return "NOT_CERTIFIED"
    if attempt.get("decision") != "REQUIREMENTS_SATISFIED":
        return "NOT_CERTIFIED"
    if attempt.get("checks_failed") or attempt.get("blocking_issues"):
        return "NOT_CERTIFIED"
    passed = set(attempt.get("checks_passed", []))
    if not set(contract["required_checks"]).issubset(passed):
        return "NOT_CERTIFIED"
    evidence = attempt.get("evidence", {})
    if any(evidence.get(key) is None for key in contract["required_evidence"]):
        return "NOT_CERTIFIED"
    return "CHECKS_SATISFIED_NOT_SIGNED"


class TestContract(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "claim_id": "demo",
            "claim_version": "v1",
            "required_checks": ["test"],
            "required_evidence": ["input"],
        }
        self.attempt = {
            "claim_id": "demo",
            "claim_version": "v1",
            "executed": True,
            "decision": "REQUIREMENTS_SATISFIED",
            "checks_passed": ["test"],
            "evidence": {"input": digest("x")},
        }

    def test_fixture(self):
        self.assertEqual(decide(self.contract, self.attempt), "CHECKS_SATISFIED_NOT_SIGNED")

    def test_missing_evidence(self):
        self.attempt["evidence"] = {}
        self.assertEqual(decide(self.contract, self.attempt), "NOT_CERTIFIED")

    def test_refusal(self):
        self.attempt["decision"] = "REFUSED"
        self.assertEqual(decide(self.contract, self.attempt), "NOT_CERTIFIED")

    def test_unexecuted(self):
        self.attempt["executed"] = False
        self.assertEqual(decide(self.contract, self.attempt), "NOT_CERTIFIED")

    def test_hash_canonicalization(self):
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
