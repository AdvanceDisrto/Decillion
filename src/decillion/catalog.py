"""A durable SQLite receipt catalog."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .receipts import Receipt


class ReceiptCatalog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS receipts (
                object_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                receipt_json TEXT NOT NULL,
                created_at TEXT NOT NULL
                )"""
            )
            db.execute("CREATE INDEX IF NOT EXISTS receipts_owner ON receipts(owner, created_at)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def add(self, receipt: Receipt) -> None:
        encoded = json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"))
        with self._connect() as db:
            db.execute(
                "INSERT INTO receipts VALUES (?, ?, ?, ?)",
                (receipt.object_id, receipt.owner, encoded, receipt.created_at),
            )

    def get(self, object_id: str) -> Receipt | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT receipt_json FROM receipts WHERE object_id = ?", (object_id,)
            ).fetchone()
        return Receipt(**json.loads(row[0])) if row else None

    def list_owner(self, owner: str, limit: int = 100) -> list[Receipt]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT receipt_json FROM receipts WHERE owner = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (owner, min(max(limit, 1), 1000)),
            ).fetchall()
        return [Receipt(**json.loads(row[0])) for row in rows]
