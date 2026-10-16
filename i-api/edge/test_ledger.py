import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ledger import Ledger, ContinuityError, GENESIS

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Ledger(Path(self.tmp.name) / "receipts.sqlite3")
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_append_verify_pending_ack(self):
        first = self.db.append("buddy", {"token": "hello"})
        second = self.db.append("buddy", {"token": "world"})
        self.assertEqual(first["parent_hash"], GENESIS)
        self.assertEqual(second["parent_hash"], first["receipt_hash"])
        self.assertEqual(self.db.verify()["count"], 2)
        self.assertEqual(len(self.db.pending()), 2)
        self.assertFalse(self.db.acknowledge(1, "wrong"))
        self.assertTrue(self.db.acknowledge(1, first["receipt_hash"]))
        self.assertEqual(len(self.db.pending()), 1)
        self.assertEqual(self.db.verify()["head"], second["receipt_hash"])
    def test_tamper_detected(self):
        self.db.append("buddy", {"token": "hello"})
        self.db.db.execute("UPDATE receipts SET payload_json='{}' WHERE sequence=1")
        with self.assertRaises(ContinuityError):
            self.db.verify()
    def test_empty_chain(self):
        self.assertEqual(self.db.verify()["head"], GENESIS)
    def test_invalid_payload(self):
        with self.assertRaises(ValueError):
            self.db.append("", {})
        with self.assertRaises(ValueError):
            self.db.append("buddy", "text")
    def test_reopen(self):
        self.db.append("buddy", {"a": 1})
        self.db.close()
        self.db = Ledger(Path(self.tmp.name) / "receipts.sqlite3")
        self.assertEqual(self.db.verify()["count"], 1)

if __name__ == "__main__":
    unittest.main()
