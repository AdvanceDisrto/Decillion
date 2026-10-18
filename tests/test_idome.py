import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"i-api"))
from dome import evaluate_claim, digest
def test_true():
    r=evaluate_claim("2 + 2 = 4")
    assert r["status"]=="SUPPORTED_IN_DEFINED_SCOPE"
    assert r["receipt"]["id"]==digest(r["receipt"]["body"])
def test_wrong():
    r=evaluate_claim("2 + 2 = 5")
    assert r["status"]=="REFUSED" and r["grade"]=="D" and "receipt" not in r
def test_unknown():
    assert evaluate_claim("Mars has 5 moons")["grade"]=="U"
def test_zero_division():
    assert evaluate_claim("1 / 0 = 0")["grade"]=="U"
def test_deterministic():
    assert evaluate_claim("0.1+0.2=0.3")==evaluate_claim("0.1+0.2=0.3")
def test_tampering():
    r=evaluate_claim("2*3=6")["receipt"]
    r["body"]["grade"]="U"
    assert r["id"]!=digest(r["body"])
def test_human_gate():
    r=evaluate_claim("5-4=1")["receipt"]["body"]
    assert r["human_approval"]=="PENDING" and not r["hardware_attested"] and r["signature"] is None
