import http from 'node:http';
import { createHash, randomUUID } from 'node:crypto';

// Hash canonical server-generated JSON, not untrusted client-provided attestations.
const canonical = v => Array.isArray(v)
  ? '[' + v.map(canonical).join(',') + ']'
  : v && typeof v === 'object'
    ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canonical(v[k])).join(',') + '}'
    : JSON.stringify(v);
export const digest = value => createHash('sha256').update(canonical(value)).digest('hex');
const send = (res,status,obj) => {
  res.writeHead(status, {'content-type':'application/json', 'cache-control':'no-store', 'x-content-type-options':'nosniff'});
  res.end(JSON.stringify(obj));
};
export function createServer({supabaseUrl=process.env.SUPABASE_URL, publishableKey=process.env.SUPABASE_PUBLISHABLE_KEY, fetchImpl=fetch}={}) {
  return http.createServer(async(req,res)=>{
    if(req.method==='GET' && req.url==='/health')
      return send(res,200,{status:'ok',storageConfigured:!!(supabaseUrl&&publishableKey),precisionVerified:false,hardwareAttested:false});
    if(req.method!=='POST' || req.url!=='/v1/clock/events')
      return send(res,404,{error:'not_found'});
    if(!supabaseUrl || !publishableKey)
      return send(res,503,{error:'storage_not_configured'});
    const auth=req.headers.authorization||'';
    if(!/^Bearer [A-Za-z0-9._~-]+$/.test(auth))
      return send(res,401,{error:'valid_user_bearer_required'});
    let raw='';
    try {
      for await (const c of req) {
        raw+=c.toString();
        if(Buffer.byteLength(raw)>16384) return send(res,413,{error:'too_large'});
      }
    } catch { return send(res,400,{error:'read_failed'}); }
    let input;
    try { input=JSON.parse(raw); } catch { return send(res,400,{error:'invalid_json'}); }
    if(!input || typeof input.event!=='string' || !input.event.trim() || input.event.length>160 ||
       typeof input.details!=='string' || input.details.length>8000)
      return send(res,422,{error:'invalid_event'});
    let identity;
    try {
      const u=await fetchImpl(supabaseUrl.replace(/\/$/,'')+'/auth/v1/user',
        {headers:{authorization:auth,apikey:publishableKey}});
      if(!u.ok) return send(res,401,{error:'invalid_session'});
      identity=await u.json();
    } catch { return send(res,503,{error:'authentication_unavailable'}); }
    if(!/^[0-9a-f-]{36}$/i.test(identity.id||''))
      return send(res,401,{error:'invalid_identity'});
    const body={schema:'iclock-server-evidence/1',event:input.event.trim(),details:input.details,
      observedAt:new Date().toISOString(),clockSource:'server system wall clock',
      precisionClaim:'none',hardwareAttested:false,independentlyCertified:false,nonce:randomUUID()};
    const proof=digest(body);
    let persisted;
    try {
      const r=await fetchImpl(supabaseUrl.replace(/\/$/,'')+'/rest/v1/i_clock_evidence',{
        method:'POST',headers:{authorization:auth,apikey:publishableKey,'content-type':'application/json',prefer:'return=representation'},
        body:JSON.stringify({owner_id:identity.id,body,sha256:proof})
      });
      if(!r.ok) return send(res,503,{error:'persistence_failed'});
      const items=await r.json();
      if(!Array.isArray(items)||items.length!==1||items[0].sha256!==proof)
        return send(res,503,{error:'persistence_unconfirmed'});
      persisted=items[0];
    } catch { return send(res,503,{error:'persistence_unavailable'}); }
    return send(res,201,{status:'recorded',receipt:{id:persisted.id,body,sha256:proof},certification:'not-issued'});
  });
}
if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href) {
  createServer().listen(Number(process.env.PORT||8090),'0.0.0.0');
}
