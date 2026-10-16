"""i™ local append-only receipt chain, transactional SQLite WAL storage.

A chain detects tampering relative to a trusted checkpoint. It does NOT prove
the GPU executed a token, provide a global blockchain commitment, or attest
that the host is uncompromised.
"""
import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path

GENESIS = "0" * 64

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

class ContinuityError(RuntimeError):
    pass

class Ledger:
    def __init__(self, path):
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False, timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS receipts(
          sequence INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NOT NULL,
          parent_hash TEXT NOT NULL,
          receipt_hash TEXT NOT NULL UNIQUE,
          payload_json TEXT NOT NULL,
          created_at_ns INTEGER NOT NULL,
          acknowledged INTEGER NOT NULL DEFAULT 0)""")

    def append(self, session_id, payload):
        if not session_id or not isinstance(payload, dict):
            raise ValueError("session_id and dict payload required")
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                previous = self.db.execute(
                    "SELECT receipt_hash FROM receipts ORDER BY sequence DESC LIMIT 1"
                ).fetchone()
                parent = previous[0] if previous else GENESIS
                body = {"schema": "i-continuity/1", "session_id": session_id,
                        "parent_hash": parent, "payload": payload, "created_at_ns": time.time_ns()}
                receipt_hash = digest(body)
                self.db.execute(
                    "INSERT INTO receipts(session_id,parent_hash,receipt_hash,payload_json,created_at_ns) VALUES (?,?,?,?,?)",
                    (session_id, parent, receipt_hash, canonical(body).decode(), body["created_at_ns"]))
                sequence = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
                self.db.execute("COMMIT")
                return {"sequence": sequence, "receipt_hash": receipt_hash, **body,
                        "acknowledged": False, "scope": "local-chain-only"}
            except BaseException:
                self.db.execute("ROLLBACK")
                raise

    def verify(self):
        with self.lock:
            rows = self.db.execute(
                "SELECT sequence,parent_hash,receipt_hash,payload_json FROM receipts ORDER BY sequence"
            ).fetchall()
            parent = GENESIS
            for seq, stored_parent, receipt_hash, data in rows:
                body = json.loads(data)
                if stored_parent != parent or body.get("parent_hash") != parent or digest(body) != receipt_hash:
                    raise ContinuityError(f"receipt chain mismatch at sequence {seq}")
                parent = receipt_hash
            return {"valid": True, "count": len(rows), "head": parent,
                    "scope": "local-chain-only; no remote or hardware attestation"}

    def pending(self, limit=100):
        with self.lock:
            rows = self.db.execute(
                "SELECT sequence,receipt_hash,payload_json FROM receipts WHERE acknowledged=0 ORDER BY sequence LIMIT ?",
                (max(1, min(int(limit), 1000)),)).fetchall()
            return [{"sequence": seq, "receipt_hash": h, "body": json.loads(body)} for seq,h,body in rows]

    def acknowledge(self, sequence, receipt_hash):
        """Only call after verifying an authenticated server acknowledgement."""
        with self.lock:
            cur = self.db.execute("UPDATE receipts SET acknowledged=1 WHERE sequence=? AND receipt_hash=?",
                                  (sequence, receipt_hash))
            return cur.rowcount == 1

    def close(self):
        self.db.close()
