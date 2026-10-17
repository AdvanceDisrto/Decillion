"""i™ VCP domain-specific policy checks.
Finite, explicitly curated historical interval fixtures. Consistency is not truth certification.
"""
from datetime import date
from decimal import Decimal,InvalidOperation
from vcp import calculate
HISTORICAL_POLICIES={
 ("united states","president"): [
  {"start":"2021-01-20","end":"2025-01-20","value":"Joe Biden","scope":"Presidential term date interval"},
  {"start":"2025-01-20","end":"2029-01-20","value":"Donald Trump","scope":"Scheduled term interval, may change; verify contemporary sources"}
 ]
}
def assess_temporal(entity,attribute,value,as_of):
    try: stamp=date.fromisoformat(as_of)
    except (TypeError,ValueError):return {"status":"INCONCLUSIVE","reason":"Exact ISO date required"}
    rules=HISTORICAL_POLICIES.get((entity.strip().lower(),attribute.strip().lower()))
    if not rules:return {"status":"INCONCLUSIVE","reason":"No curated temporal fixture"}
    for item in rules:
        if date.fromisoformat(item["start"])<=stamp<date.fromisoformat(item["end"]):
            return {"status":"REFERENCE_CONSISTENT" if value==item["value"] else "REFERENCE_CONTRADICTED",
                    "reference_value":item["value"],"validity_window":[item["start"],item["end"]],
                    "limitation":"Finite reference fixture, not up-to-date factual certification"}
    return {"status":"INCONCLUSIVE","reason":"No matching temporal interval"}
def assess_arithmetic(expression,expected):
    try:
        if isinstance(expected,bool) or not isinstance(expected,(int,float)):
            raise ValueError("Expected number")
        measured=calculate(expression)
        return {"status":"VERIFIED_ARITHMETIC" if measured==expected else "REJECTED_ARITHMETIC",
                "calculated":measured,"scope":"Bounded deterministic arithmetic only"}
    except (TypeError,ValueError,ZeroDivisionError,SyntaxError,OverflowError):
        return {"status":"INCONCLUSIVE","reason":"Expression outside supported arithmetic domain"}
