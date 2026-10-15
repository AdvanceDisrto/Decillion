/* iModels: observe actual inference state; do not mislabel a deployed API as a trained LLM. */
(()=>{
const url=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
const target=document.getElementById('imodelStatus');
const button=document.getElementById('checkIModels');
async function readJson(path,timeout=8000){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeout);
 try{const res=await fetch(url+path,{signal:controller.signal,cache:'no-store'});if(!res.ok)throw new Error('HTTP '+res.status);return await res.json()}finally{clearTimeout(timer)}
}
async function refresh(){
 if(!target)return;target.textContent='Connecting to the iModels gateway…';if(button)button.disabled=true;
 try{
  const [health,registry]=await Promise.all([readJson('/health'),readJson('/v1/models')]);
  const models=Array.isArray(registry.models)?registry.models:[];
  const lines=[
   'Buddy API: '+(health.status==='ok'?'reachable':'unavailable'),
   'Authenticated storage and signatures: '+(health.storage_auth_signing_configured?'configured':'not configured'),
   'Model-serving endpoint: '+(health.model_configured?'configured':'not configured'),
   ...models.map(m=>m.name+' ('+(m.model_id||'no model ID')+'): '+(m.endpoint_configured?'endpoint configured':'not connected')+' · checkpoint '+(m.weights_verified?'verified':'not verified'))
  ];
  target.replaceChildren();
  for(const line of lines){const p=document.createElement('p');p.textContent=line;p.className='fine';p.style.margin='4px 0';target.append(p)}
  return {health,registry}
 }catch{target.textContent='The model registry is not available right now. Local receipt tools remain available.';return null}
 finally{if(button)button.disabled=false}
}
button?.addEventListener('click',refresh);
window.iModels={refresh,registry:()=>readJson('/v1/models'),probe:()=>readJson('/v1/models/probe')};
refresh();
})();
