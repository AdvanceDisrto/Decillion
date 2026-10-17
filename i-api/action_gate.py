"""Policy-only action gate. NEVER invokes a bank, email sender, shell or physical device.
Explicit human approval AND independent verified task authorization required.
A factual/evidence receipt alone is insufficient for execution.
"""
from dataclasses import dataclass
from typing import Literal
@dataclass(frozen=True)
class ActionDecision:
    allowed:bool
    reason:str
    dry_run:bool=True
def authorize(action:str,*,human_approved:bool=False,identity_authenticated:bool=False,
              task_scoped_authorization:bool=False,receipt_signature_valid:bool=False,
              receipt_not_revoked:bool=False,standard:str="",dry_run:bool=True)->ActionDecision:
    if not isinstance(action,str) or not action.strip():return ActionDecision(False,"Missing action")
    if not human_approved:return ActionDecision(False,"Human approval required")
    if not identity_authenticated:return ActionDecision(False,"Authenticated identity required")
    if not task_scoped_authorization:return ActionDecision(False,"Explicit task-scoped authorization required")
    if not (receipt_signature_valid and receipt_not_revoked):return ActionDecision(False,"Verified current independent receipt required")
    if standard!="ACTION-AUTHORIZATION/1":return ActionDecision(False,"Evidence integrity receipt is not action authorization")
    if not dry_run:return ActionDecision(False,"External execution adapter not installed; cannot execute")
    return ActionDecision(True,"All dry-run policy gates satisfied; no action executed",True)
