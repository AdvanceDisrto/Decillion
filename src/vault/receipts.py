"""Persistent HMAC-linked audit receipts for vault operations."""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from pathlib import Path


class VaultReceipts:
    def __init__(self, db_path: str | Path, signing_key: bytes):
        if len(signing_key) < 32:
            raise ValueError("receipt signing key must be at least 32 bytes")
        self.key = signing_key
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT UNIQUE NOT NULL,
                ts REAL NOT NULL,
                kind TEXT NOT NULL,
                model_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                prev_sig TEXT NOT NULL,
                sig TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_receipt_model ON receipts(model_id, seq);
            """
        )
        self.db.commit()

    def _sign(self, body: str) -> str:
        return hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _body(
        receipt_id: str,
        timestamp: float,
        kind: str,
        model_id: str,
        actor: str,
        payload_json: str,
        previous: str,
    ) -> str:
        return json.dumps(
            [receipt_id, timestamp, kind, model_id, actor, payload_json, previous],
            separators=(",", ":"),
        )

    def emit(self, kind: str, model_id: str, actor: str, payload: dict) -> str:
        receipt_id = uuid.uuid4().hex
        timestamp = time.time()
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        row = self.db.execute("SELECT sig FROM receipts ORDER BY seq DESC LIMIT 1").fetchone()
        previous = row[0] if row else "genesis"
        signature = self._sign(
            self._body(receipt_id, timestamp, kind, model_id, actor, payload_json, previous)
        )
        with self.db:
            self.db.execute(
                "INSERT INTO receipts(receipt_id,ts,kind,model_id,actor,payload_json,prev_sig,sig) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (receipt_id, timestamp, kind, model_id, actor, payload_json, previous, signature),
            )
        return receipt_id

    def verify_chain(self) -> tuple[bool, str]:
        previous = "genesis"
        rows = self.db.execute(
            "SELECT receipt_id,ts,kind,model_id,actor,payload_json,prev_sig,sig "
            "FROM receipts ORDER BY seq"
        )
        for receipt_id, timestamp, kind, model_id, actor, payload, stored_previous, sig in rows:
            if stored_previous != previous:
                return False, f"chain break at {receipt_id}"
            expected = self._sign(
                self._body(receipt_id, timestamp, kind, model_id, actor, payload, stored_previous)
            )
            if not hmac.compare_digest(expected, sig):
                return False, f"bad signature at {receipt_id}"
            previous = sig
        return True, previous

    def for_model(self, model_id: str, limit: int = 50) -> list[dict]:
        rows = self.db.execute(
            "SELECT receipt_id,ts,kind,actor,payload_json FROM receipts "
            "WHERE model_id=? ORDER BY seq DESC LIMIT ?",
            (model_id, min(max(limit, 1), 1000)),
        ).fetchall()
        return [
            {
                "receipt_id": row[0],
                "ts": row[1],
                "kind": row[2],
                "actor": row[3],
                "payload": json.loads(row[4]),
            }
            for row in rows
        ]

    def count(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0])
