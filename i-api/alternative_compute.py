"""i™ Research Lab: bounded CPU references. No exotic hardware is connected."""
from __future__ import annotations
import cmath
import hashlib
import json
import math
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
router=APIRouter(prefix="/v1/alternative-compute",tags=["i Research Lab"])

class LabRequest(BaseModel):
    engine: Literal["photonic","neuromorphic","quantum"]
    values: list[float]=Field(default_factory=lambda:[0.7,-0.3],min_length=2,max_length=2)
    phase:float=Field(default=0.4,ge=-6.283185307179586,le=6.283185307179586)
    steps:int=Field(default=12,ge=1,le=64)

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf8")

def finite(x):
    if not math.isfinite(x) or abs(x)>1000:
        raise ValueError("Input must be finite and within bounds")
    return x

def photonic(values,phase,steps):
    """Idealized balanced 2-port Mach-Zehnder mathematical reference, not photonic hardware."""
    a,b=[complex(finite(x)) for x in values];h=1/math.sqrt(2)
    u=(a+b)*h;v=(a-b)*h*cmath.exp(1j*phase)
    out=[(u+v)*h,(u-v)*h]
    original=abs(a)**2+abs(b)**2
    return {"output_intensity":[round(abs(x)**2,10) for x in out],
            "input_intensity":round(original,10),
            "energy_conservation_error":round(abs(sum(abs(x)**2 for x in out)-original),12),
            "model":"ideal-2-port-MZI-classical-wave",
            "limitations":"No laser, optical chip, ADC/DAC, noise, thermal drift or measured energy advantage."}

def neuromorphic(values,phase,steps):
    """Digital leaky integrate-and-fire toy model; no neurons or organoids are involved."""
    a,b=[finite(x) for x in values];v=0.0;spikes=[];trace=[]
    for t in range(steps):
        current=a*(1 if t%2==0 else -.35)+b+math.sin(phase+t*.25)*.15
        v=.82*v+current
        if v>=1:
            spikes.append(t);v=0.0
        trace.append(round(v,6))
    return {"spike_times":spikes,"final_potential":round(v,6),"trace":trace,
            "model":"digital-leaky-integrate-and-fire-reference",
            "limitations":"Software mathematical neuron; no tissue, biological learning or ethics approval."}

def quantum(values,phase,steps):
    """Classical statevector demonstration, not analog quantum hardware."""
    angle,_=[finite(x) for x in values]
    h=1/math.sqrt(2);c=math.cos(angle/2);s=math.sin(angle/2)
    state=[h*c,-1j*h*s,h*c,-1j*h*s*cmath.exp(1j*phase)]
    probabilities=[abs(x)**2 for x in state]
    return {"probabilities":[round(p,10) for p in probabilities],
            "normalization_error":round(abs(sum(probabilities)-1),12),
            "z0_expectation":round(probabilities[0]+probabilities[1]-probabilities[2]-probabilities[3],8),
            "model":"2-qubit-classical-statevector-reference",
            "limitations":"CPU emulation of tiny quantum circuit; no analog hardware, quantum speedup or instant solution."}

ENGINES={"photonic":photonic,"neuromorphic":neuromorphic,"quantum":quantum}

@router.get("/capabilities")
async def capabilities():
    return {"engines":[{"name":name,"mode":"cpu-reference-simulation","hardware_connected":False,
                       "execution_verified":True,"status":"software-only"} for name in ENGINES],
            "fabrication_verified":False,"biological_material_used":False,
            "message":"No photonic device, living organoid or analog quantum hardware is connected."}

@router.post("/run")
async def run(req:LabRequest):
    try:result=ENGINES[req.engine](req.values,req.phase,req.steps)
    except (ValueError,OverflowError) as e:raise HTTPException(422,str(e)) from e
    record={"schema":"i-research-receipt/1","engine":req.engine,
            "execution":"cpu-reference-simulation","input":req.model_dump(),
            "result":result,"verified_hardware":False}
    return {"receipt":{"sha256":hashlib.sha256(canonical(record)).hexdigest(),
                       "body":record,"signature":None,"anchored":False},"result":result}
