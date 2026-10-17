"""
title: i™ THE ONE — VCP Proposal Gate
author: iNNOVULiS
version: 0.1.0
description: Calls an operator-controlled OpenAI-compatible inference endpoint. Treats all model answers as unverified proposals, not ICE certificates.
"""
from pydantic import BaseModel, Field
import httpx
import json

class Pipe:
    class Valves(BaseModel):
        VLLM_URL: str = Field(default="http://host.docker.internal:8000/v1", description="Admin-configured private vLLM API base URL")
        MODEL_ID: str = Field(default="",description="Exact deployed vLLM served model ID")
        VLLM_API_KEY: str = Field(default="",description="Server-side API token. Never place into user messages.")
        MAX_TOKENS: int = Field(default=512,ge=32,le=2048)
    def __init__(self):
        self.valves=self.Valves()
        self.name="i™ THE ONE — Unverified Proposals"
    async def pipe(self,body:dict):
        config=self.valves
        if not config.MODEL_ID or not config.VLLM_API_KEY:
            return "VCP unavailable: administrator must configure a private model and API token."
        from urllib.parse import urlsplit
        url=urlsplit(config.VLLM_URL)
        if url.scheme!="http" or url.hostname not in ("127.0.0.1","localhost","host.docker.internal","vllm") or url.username or url.password or url.fragment:
            return "VCP unavailable: vLLM endpoint must be a configured private local address."
        prompt=[]
        for m in body.get("messages",[])[-12:]:
            if not isinstance(m,dict) or m.get("role") not in ("user","assistant"):continue
            val=m.get("content")
            if isinstance(val,str):prompt.append({"role":m["role"],"content":val[:6000]})
        if not any(m["role"]=="user" for m in prompt):return "No user prompt supplied."
        messages=[{"role":"system","content":"You are i™ generative seed. Answer the question cautiously. Never say an output is verified or certified. Mark hypotheses and uncertainty. You cannot authorize tool execution."}]+prompt
        try:
            async with httpx.AsyncClient(timeout=90,follow_redirects=False,trust_env=False) as client:
                response=await client.post(config.VLLM_URL.rstrip("/")+"/chat/completions",
                    headers={"Authorization":"Bearer "+config.VLLM_API_KEY,"Content-Type":"application/json"},
                    json={"model":config.MODEL_ID,"stream":False,"max_tokens":config.MAX_TOKENS,
                          "messages":messages})
                response.raise_for_status()
                text=response.json()["choices"][0]["message"]["content"]
                if not isinstance(text,str) or not text.strip():raise ValueError("Empty model response")
            return ("### i™ Model Proposal — NOT VERIFIED / NOT CERTIFIED\n\n"+
                    text[:20000]+"\n\n---\n"
                    "No independent VCP or ICE evidence assessment was performed. "
                    "This text has no action-execution authority.")
        except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError):
            return "VCP model proposal unavailable. No verification or certificate issued."
