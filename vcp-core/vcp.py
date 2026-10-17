"""i™ VCP verification core v0.1: bounded deterministic checks, Ed25519 receipts,
append-only hash-chained audit log and capability-bound execution gates.
No general truth guarantee, global consensus, or hardware attestation.
"""
from __future__ import annotations
import ast
import base64
import hashlib
import json
import operator
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

SCHEMA = "i.vcp.receipt/1"
POLICY = "i-vcp-deterministic-v1"
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv}
def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def calculate(expr: str) -> float | int:
    """No eval, names, attributes, exponentiation or function invocation."""
    if len(expr) > 180:
        raise ValueError("Expression too long")
    root = ast.parse(expr, mode="eval")
    def walk(node, depth=0):
        if depth > 20:
            raise ValueError("Expression too deep")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth+1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e12: raise ValueError("Operand too large")
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = walk(node.operand, depth+1)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            a, b = walk(node.left, depth+1), walk(node.right, depth+1)
            if abs(a) > 1e12 or abs(b) > 1e12: raise ValueError("Operand too large")
            result = OPS[type(node.op)](a, b)
            if abs(result) > 1e12: raise ValueError("Result too large")
            return result
        raise ValueError("Unsupported mathematical syntax")
    return walk(root)

def create_keypair():
    private = Ed25519PrivateKey.generate()
    pub = private.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
    return private, base64.b64encode(pub).decode()

def validate_receipt(receipt: dict, public_key_b64: str) -> bool:
    try:
        signed = receipt["signed"]
        signature = base64.b64decode(receipt["signature"], validate=True)
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64,validate=True))
        pub.verify(signature, canonical(signed))
        return signed["schema"] == SCHEMA and signed["policy"] == POLICY and signed["status"] == "VERIFIED"
    except (KeyError, ValueError, TypeError, Exception):
        return False

@dataclass
class Result:
    status: str
    reason: str
    receipt: dict | None

class Engine:
    def __init__(self, private_key: Ed25519PrivateKey, audit_path: str | Path):
        self.key = private_key
        self.path = Path(audit_path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.last_hash = "0"*64
        if self.path.exists():
            if not self.audit_integrity():
                raise RuntimeError("Audit chain corrupted; refusing to issue receipts")
            for line in self.path.read_text().splitlines():
                self.last_hash = json.loads(line)["chain_hash"]

    def audit_integrity(self) -> bool:
        prev = "0"*64
        try:
            for line in self.path.read_text().splitlines():
                item=json.loads(line)
                if item["previous"] != prev: return False
                hashed=hashlib.sha256(canonical({"previous":prev,"event":item["event"]})).hexdigest()
                if hashed != item["chain_hash"]: return False
                prev=hashed
            return True
        except (OSError,ValueError,KeyError):
            return False

    def log(self,event:dict):
        payload={"previous":self.last_hash,"event":event}
        item={**payload,"chain_hash":hashlib.sha256(canonical(payload)).hexdigest()}
        with self.path.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(item,sort_keys=True)+"\n")
            handle.flush()
            import os
            os.fsync(handle.fileno())
        self.last_hash=item["chain_hash"]

    def verify_math(self,expression:str,claimed:float|int) -> Result:
        claim_id=str(uuid.uuid4())
        try:
            if type(claimed) not in (int,float): raise ValueError("Expected numerical claim")
            actual=calculate(expression)
            if actual != claimed:
                decision=Result("REJECTED",f"Recalculation produced {actual!r}, not {claimed!r}",None)
            else:
                signed={"schema":SCHEMA,"policy":POLICY,"claim_id":claim_id,"domain":"arithmetic",
                        "expression":expression,"claimed":claimed,"actual":actual,"status":"VERIFIED",
                        "issued_at":int(time.time()),"scope":"Specified expression only",
                        "authority":"i VCP local evaluator; not third-party accredited"}
                signature=base64.b64encode(self.key.sign(canonical(signed))).decode()
                receipt={"signed":signed,"signature":signature,"signature_algorithm":"Ed25519"}
                decision=Result("VERIFIED","Deterministic arithmetic equality",receipt)
        except (ValueError,ZeroDivisionError,OverflowError,SyntaxError) as ex:
            decision=Result("INCONCLUSIVE",f"Cannot verify expression: {str(ex)[:140]}",None)
        self.log({"claim_id":claim_id,"status":decision.status,"expression_hash":hashlib.sha256(expression.encode()).hexdigest(),"reason":decision.reason,
                  "receipt_hash":hashlib.sha256(canonical(decision.receipt)).hexdigest() if decision.receipt else None})
        return decision

def authorize_execution(action: str, receipt: dict | None, public_key_b64: str, *,
                        approved_actions: set[str], actor_authorized: bool) -> bool:
    """Receipt is necessary but NOT sufficient: separate user permission + action allowlist.
    Arithmetic proof deliberately cannot authorize a transfer, deployment or hardware command.
    """
    if not actor_authorized or action not in approved_actions or not receipt: return False
    if not validate_receipt(receipt, public_key_b64): return False
    return receipt["signed"].get("domain") == "action_permission" and receipt["signed"].get("action") == action
