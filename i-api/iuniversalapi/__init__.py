"""iUniversalApi: provider router, opt-in scoped cache, sealed LAN payloads.

Only configured providers are queried. No implicit cross-user cache sharing,
pretend provider connections, GPU bypass, hardware certification or billing.
"""
from __future__ import annotations
import asyncio, base64, hashlib, json, os, secrets, sqlite3, time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import httpx

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()

@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    key_env: str
    mode: str = 'openai'
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    def available(self):
        return self.base_url.startswith('https://') and bool(self.model and os.getenv(self.key_env))

PROVIDERS = (
    Provider('openai','https://api.openai.com/v1','', 'IAPI_OPENAI_KEY'),
    Provider('anthropic','https://api.anthropic.com/v1','', 'IAPI_ANTHROPIC_KEY','anthropic'),
    Provider('groq','https://api.groq.com/openai/v1','', 'IAPI_GROQ_KEY'),
    Provider('deepseek','https://api.deepseek.com/v1','', 'IAPI_DEEPSEEK_KEY'),
    Provider('google','https://generativelanguage.googleapis.com/v1beta/openai','', 'IAPI_GOOGLE_KEY'),
)
# Model IDs and cost estimates must be configured and updated from current
# provider documentation before use. Never infer them from provider names.

class ScopedCache:
    def __init__(self, path=':memory:', ttl=3600):
        self.ttl=max(1,min(int(ttl),86400))
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, expires REAL NOT NULL, result TEXT NOT NULL)')
        self.db.commit()
    @staticmethod
    def key(user_scope, model, prompt):
        if not user_scope or not model:raise ValueError('Explicit user and model scope required')
        return digest({'scope':user_scope,'model':model,'prompt':prompt})
    def get(self, scope, model, prompt):
        row=self.db.execute('SELECT result,expires FROM cache WHERE key=?',(self.key(scope,model,prompt),)).fetchone()
        return json.loads(row[0]) if row and row[1]>time.time() else None
    def put(self, scope, model, prompt, result):
        self.db.execute('INSERT OR REPLACE INTO cache(key,expires,result) VALUES (?,?,?)',
                        (self.key(scope,model,prompt),time.time()+self.ttl,json.dumps(result)))
        self.db.commit()

class Router:
    def __init__(self,providers=PROVIDERS,cache=None):
        self.providers=tuple(providers)
        self.cache=cache or ScopedCache()
    def optimize(self):
        # A transparent configuration-based heuristic, NOT a trained predictor.
        return sorted((p for p in self.providers if p.available()),
            key=lambda p:(p.input_per_million+p.output_per_million,p.name))
    async def complete(self, prompt, *, scope, use_cache=False, max_tokens=256):
        if not prompt or not scope:raise ValueError('Nonempty prompt and authenticated scope required')
        if len(prompt)>16000 or max_tokens<1 or max_tokens>2048:raise ValueError('Request bounds exceeded')
        providers=self.optimize()
        if not providers:raise RuntimeError('No configured, authorized providers')
        # Only cache identical prompts for the same user and selected model.
        for p in providers:
            if use_cache:
                cached=self.cache.get(scope,p.name+'/'+p.model,prompt)
                if cached is not None:return {'provider':p.name,'response':cached,'cache_hit':True,'model':p.model}
            try:
                async with httpx.AsyncClient(timeout=25,follow_redirects=False) as client:
                    if p.mode=='anthropic':
                        resp=await client.post(p.base_url+'/messages',
                            headers={'x-api-key':os.environ[p.key_env],
                                     'anthropic-version':'2023-06-01'},
                            json={'model':p.model,'max_tokens':max_tokens,'messages':[{'role':'user','content':prompt}]})
                    else:
                        resp=await client.post(p.base_url+'/chat/completions',
                            headers={'Authorization':'Bearer '+os.environ[p.key_env]},
                            json={'model':p.model,'max_tokens':max_tokens,
                                  'messages':[{'role':'user','content':prompt}]})
                    resp.raise_for_status()
                    data=resp.json()
                    if p.mode=='anthropic':
                        answer=''.join(x.get('text','') for x in data['content'] if x.get('type')=='text')
                    else:
                        answer=data['choices'][0]['message']['content']
                    if not isinstance(answer,str) or not answer.strip():raise ValueError('Empty response')
                    if use_cache:self.cache.put(scope,p.name+'/'+p.model,prompt,answer)
                    return {'provider':p.name,'response':answer,'cache_hit':False,'model':p.model}
            except (httpx.HTTPError,KeyError,ValueError,TypeError):
                continue
        raise RuntimeError('Every configured provider failed: no fake fallback result')

class Mesh:
    """AES-GCM-256 application envelope for explicitly paired peers.
    Does not discover Bluetooth, Wi-Fi Direct or create transport channels."""
    def __init__(self,key:bytes,node_id:str):
        if len(key)!=32 or not node_id:raise ValueError('32-byte secret and node ID required')
        self.aes=AESGCM(key);self.node_id=node_id
        self.seen=set()
    def sync_nodes(self):return {'node':self.node_id,'mode':'paired-envelope-only','radio_connected':False}
    def encrypt(self,peer_id:str,payload:dict):
        if not peer_id:raise ValueError('Peer required')
        nonce=secrets.token_bytes(12)
        aad=canonical({'from':self.node_id,'to':peer_id,'version':1})
        cipher=self.aes.encrypt(nonce,canonical(payload),aad)
        return {'from':self.node_id,'to':peer_id,'version':1,'nonce':base64.b64encode(nonce).decode(),
                'ciphertext':base64.b64encode(cipher).decode()}
    def decrypt(self,envelope):
        if envelope['to']!=self.node_id or envelope['version']!=1:raise ValueError('Wrong recipient/version')
        nonce=base64.b64decode(envelope['nonce'],validate=True)
        if len(nonce)!=12:raise ValueError('Bad nonce')
        marker=(envelope['from'],envelope['nonce'])
        if marker in self.seen:raise ValueError('Replay rejected')
        aad=canonical({'from':envelope['from'],'to':self.node_id,'version':1})
        result=json.loads(self.aes.decrypt(nonce,base64.b64decode(envelope['ciphertext'],validate=True),aad))
        self.seen.add(marker)
        if len(self.seen)>100000:self.seen=set(list(self.seen)[-50000:]) # demo-memory only; durable replay database required in production
        return result

class Telemetry:
    @staticmethod
    def optimize_cross_plane(events):
        total=len(events)
        ok=sum(1 for x in events if x.get('ok'))
        cached=sum(1 for x in events if x.get('cache_hit'))
        return {'requests':total,'successful':ok,'cache_hits':cached,
                'success_rate':(ok/total if total else 0),
                'cache_hit_rate':(cached/total if total else 0),
                'scope':'observed events only; no inferred money savings'}

class Container:
    @staticmethod
    def compile(target='universal_binary'):
        raise NotImplementedError('Cross-OS signed native binaries require per-platform toolchains, packaging and signing')
