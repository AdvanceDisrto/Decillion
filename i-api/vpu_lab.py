"""iCalcula VPU lab: bounded deterministic fixed-point ISA and fault tests.

The ISA/latency/emulated SERS below is SOFTWARE ONLY. No MMIO, PCI, FPGA,
Vortex RTL integration, secure-enclave key, or actual chip attestation.
"""
from __future__ import annotations
import hashlib,json,statistics,time
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field

router=APIRouter(prefix="/v1/vpu",tags=["iCalcula VPU Lab"])
# 32-bit encoding: [31:24] opcode [23:16] operand A [15:8] operand B [7:0] immediate
OPCODES={"NOP":0x00,"ADD":0x01,"MUL":0x02,"MAC":0x03,"STAMP":0x10,"RESET":0x11}
MAX32=(1<<31)-1
MIN32=-(1<<31)

def encode(op,a=0,b=0,imm=0):
    if op not in OPCODES or any(not 0<=x<=255 for x in (a,b,imm)):
        raise ValueError("Invalid encoding")
    return OPCODES[op]<<24|a<<16|b<<8|imm

def decode(word):
    op=(word>>24)&255
    if op not in OPCODES.values():raise ValueError("Unknown opcode")
    return {"op":next(k for k,v in OPCODES.items() if v==op),
            "a":(word>>16)&255,"b":(word>>8)&255,"imm":word&255}

class Program(BaseModel):
    words:list[int]=Field(min_length=1,max_length=512)
    registers:list[int]=Field(default_factory=lambda:[0]*8,min_length=8,max_length=8)
    fault_cycle:int|None=Field(default=None,ge=0,le=511)
    iterations:int=Field(default=100,ge=1,le=1000)

def bound(n):
    if n<MIN32 or n>MAX32:raise OverflowError("Fixed point arithmetic overflow")
    return n

def execute(req:Program):
    regs=req.registers.copy()
    if any(not MIN32<=v<=MAX32 for v in regs):
        raise ValueError("Register outside signed int32")
    trace=[];stamps=[];acc=0;fail=None
    for i,w in enumerate(req.words):
        if req.fault_cycle==i:
            fail={"cycle":i,"reason":"synthetic hardware fault injection"}
            break
        if not 0<=w<=0xffffffff:raise ValueError("Invalid 32-bit word")
        inst=decode(w);a=inst["a"];b=inst["b"];op=inst["op"]
        if a>=len(regs) or b>=len(regs):raise ValueError("Register index outside bank")
        if op=="ADD":regs[a]=bound(regs[a]+regs[b])
        elif op=="MUL":regs[a]=bound(regs[a]*regs[b])
        elif op=="MAC":
            acc=bound(acc+regs[a]*regs[b])
        elif op=="RESET":acc=0
        elif op=="STAMP":
            # Hash state for integrity; **NOT** a signature.
            state={"cycle":i,"registers":regs,"accumulator":acc}
            digest=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            stamps.append({"cycle":i,"state_sha256":digest,"cryptographic_signature":False})
        trace.append({"cycle":i,"op":op})
    body={"schema":"i-icalcula-emulated/1","registers":regs,"accumulator":acc,
        "trace":trace,"stamps":stamps,"fault":fail,"rtl_verified":False,
        "physical_mmio_accessed":False,"sers_hardware_signed":False}
    root=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {"status":"FAULT_INJECTED" if fail else "EMULATED_PASS",
            "state":body,"receipt":{"sha256":root,"signature":None,"certification":"NOT_ISSUED"}}

def benchmark(words,registers,iterations=100,fault_cycle=None):
    req=Program(words=words,registers=registers,fault_cycle=fault_cycle)
    overhead=[]
    for _ in range(iterations):
        start=time.perf_counter_ns();execute(req)
        overhead.append((time.perf_counter_ns()-start)/1000)
    s=sorted(overhead)
    return {"iterations":iterations,"emulated_only":True,
        "software_latency_microseconds_p50":round(statistics.median(s),3),
        "software_latency_microseconds_p95":round(s[min(len(s)-1,int(.95*len(s)))],3),
        "hardware_latency_measured":False,
        "environment":"Python wall-clock benchmark; includes hashing and program parsing"}

@router.get("/capabilities")
async def capabilities():
    return {"register_map":{"VPU_IO_BASE":"0xFE000000","PACKET_DATA":"0x00A0",
            "STAMP_CMD":"0x00B0","OUT_RECEIPT":"0x00C0"},
       "register_addresses":"reference-only, not probed",
       "device_present":False,"kernel_driver_loaded":False,
       "signed_by_hardware":False,"silicon_leakage_measured":False,
       "supported_opcodes":OPCODES,
       "backend":"Python fixed-point emulation","vortex_integration":"not validated"}

@router.post("/execute")
async def run(p:Program):
    try:return execute(p)
    except (ValueError,OverflowError) as exc:raise HTTPException(422,str(exc))
@router.post("/benchmark")
async def test_latency(p:Program):
    try:return benchmark(p.words,p.registers,p.iterations,p.fault_cycle)
    except (ValueError,OverflowError) as exc:raise HTTPException(422,str(exc))
