"""i™ Script-Flip numeric reference HAL. Mathematical negation only.

No accelerated hardware, performance guarantee, or factual certification.
"""
from __future__ import annotations
import math
import time

def negate_matrix(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix or not isinstance(matrix,list):
        raise ValueError("Nonempty matrix required")
    if any(not isinstance(row,list) or not row for row in matrix):
        raise ValueError("Rectangular numeric matrix required")
    width=len(matrix[0])
    if width>4096 or len(matrix)>4096:raise ValueError("Matrix dimensions too large")
    if any(len(row)!=width for row in matrix):raise ValueError("Jagged matrix")
    out=[]
    for row in matrix:
        values=[]
        for n in row:
            if type(n) not in (int,float) or not math.isfinite(n):
                raise ValueError("Finite real-valued matrix elements only")
            values.append(-n)
        out.append(values)
    return out

def execute_script_flip(matrix):
    start=time.perf_counter_ns()
    transformed=negate_matrix(matrix)
    elapsed_ns=time.perf_counter_ns()-start
    return {"schema":"i.swh.script-flip/1","operation":"ELEMENTWISE_NEGATION",
            "vertices":transformed,"elapsed_monotonic_ns":elapsed_ns,
            "factual_verification":False,"accelerated":False,
            "note":"-A is not matrix inverse; elapsed time is not a wall-clock event timestamp"}
