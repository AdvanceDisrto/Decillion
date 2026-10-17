"""i™ ICE durability/replay/revocation controls. SQLite single-node development custody.
Transaction-bound nonce prevents reusing request IDs; audit is tamper-evident, NOT immutable.
"""
import hashlib,json,sqlite3,time
from pathlib import Path

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
class IceStore:
    def __init__(self,path):
        self.path=str(path)
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS requests(nonce TEXT PRIMARY KEY, request_hash TEXT NOT NULL, response TEXT NOT NULL, created INTEGER NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, prev_hash TEXT NOT NULL, event_json TEXT NOT NULL, chain_hash TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS revoked(id TEXT PRIMARY KEY, reason TEXT NOT NULL, created INTEGER NOT NULL)")
    def connect(self):
        c=sqlite3.connect(self.path,timeout=10,isolation_level="IMMEDIATE")
        c.execute("PRAGMA busy_timeout=10000")
        c.execute("PRAGMA synchronous=FULL")
        return c
    def integrity(self):
        with self.connect() as c:
            prev="0"*64
            for before,data,digest in c.execute("SELECT prev_hash,event_json,chain_hash FROM events ORDER BY id"):
                if before!=prev or hashlib.sha256((prev+data).encode()).hexdigest()!=digest:return False
                prev=digest
            return True
    def record_once(self,nonce,request_hash,response):
        if not isinstance(nonce,str) or len(nonce)<20 or len(nonce)>128:raise ValueError("Nonce length invalid")
        with self.connect() as c:
            if c.execute("SELECT 1 FROM requests WHERE nonce=?",(nonce,)).fetchone():
                raise ValueError("Replay rejected: nonce already spent")
            if not self._integrity_conn(c):raise RuntimeError("Audit integrity check failed")
            body=json.dumps(response,sort_keys=True,separators=(",",":"))
            c.execute("INSERT INTO requests VALUES(?,?,?,?)",(nonce,request_hash,body,int(time.time())))
            self._append(c,{"event":"certification_decision","nonce_hash":hashlib.sha256(nonce.encode()).hexdigest(),
                            "request_hash":request_hash,"response_hash":hashlib.sha256(body.encode()).hexdigest()})
    def _integrity_conn(self,c):
        prev="0"*64
        for before,data,digest in c.execute("SELECT prev_hash,event_json,chain_hash FROM events ORDER BY id"):
            if before!=prev or hashlib.sha256((prev+data).encode()).hexdigest()!=digest:return False
            prev=digest
        return True
    def _append(self,c,event):
        row=c.execute("SELECT chain_hash FROM events ORDER BY id DESC LIMIT 1").fetchone()
        prev=row[0] if row else "0"*64
        raw=canonical(event).decode()
        digest=hashlib.sha256((prev+raw).encode()).hexdigest()
        c.execute("INSERT INTO events(prev_hash,event_json,chain_hash) VALUES(?,?,?)",(prev,raw,digest))
    def revoke(self,cert_id,reason):
        if len(cert_id)!=64 or any(x not in "0123456789abcdef" for x in cert_id):raise ValueError("Invalid certificate ID")
        if not reason or len(reason)>250:raise ValueError("Invalid reason")
        with self.connect() as c:
            if not self._integrity_conn(c):raise RuntimeError("Audit integrity check failed")
            if c.execute("SELECT 1 FROM revoked WHERE id=?",(cert_id,)).fetchone():raise ValueError("Already revoked")
            c.execute("INSERT INTO revoked VALUES(?,?,?)",(cert_id,reason,int(time.time())))
            self._append(c,{"event":"revocation","cert_id":cert_id,"reason":reason})
    def is_revoked(self,cert_id):
        with self.connect() as c:return bool(c.execute("SELECT 1 FROM revoked WHERE id=?",(cert_id,)).fetchone())
    def head(self):
        with self.connect() as c:
            row=c.execute("SELECT chain_hash FROM events ORDER BY id DESC LIMIT 1").fetchone()
            return row[0] if row else "0"*64
