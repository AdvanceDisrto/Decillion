/* i™ local LLM operator — returns only real inference from loaded browser model. */
(()=>{'use strict';
const ID='iLocalLLM',hosts=document.querySelector('#buddy>.glass'),form=document.getElementById('askform');
if(!hosts||!form)return;
const panel=document.createElement('section');panel.id=ID;panel.style.cssText='background:linear-gradient(125deg,#052e2c,#09292e);border:1px solid #69ffce73;border-radius:16px;padding:12px;margin:12px 0;grid-column:1/-1';
panel.innerHTML='<strong>🧠 i™ Local LLM · Device Weights</strong><p class="fine" id="localModelState">Not loaded. Choose a compatible real model before offline inference.</p><div style="display:flex;flex-wrap:wrap;gap:8px"><button type="button" id="localModelLoad">Load on-device model</button><button type="button" id="localModelUnload">Unload</button><label style="font-size:13px"><input type="checkbox" id="localOffline" style="width:auto"> Offline-only loading</label></div><p class="fine">On-device inference requires real model weights, sufficient memory and browser support. No cloud fallback is used in Local LLM mode.</p>';
hosts.insertBefore(panel,hosts.querySelector('.messages'));
const $=id=>document.getElementById(id);
let worker=null,ready=false,seq=0,requests=new Map(),model=null;
function state(message){$('localModelState').textContent=message}
function finish(req){const p=requests.get(req.requestId);if(!p)return;requests.delete(req.requestId);req.type==='error'?p.reject(Error(req.error)):p.resolve(req)}
function newWorker(){if(worker)return worker;worker=new Worker('./local-llm-worker.js',{type:'module'});worker.onmessage=e=>{const r=e.data||{};if(r.type==='loading')state('Loading real model… '+r.device);if(r.type==='progress'&&Number.isFinite(r.progress))state('Downloading '+(r.file||'model')+' '+r.progress.toFixed(0)+'%');if(r.type==='ready'){ready=true;model=r.model;state('Loaded '+r.model+' · '+r.device+' · real local inference available')}if(r.type==='error')state(r.error);finish(r)};worker.onerror=e=>{ready=false;state('Local model worker failed');for(const p of requests.values())p.reject(Error(e.message));requests.clear()};return worker}
function send(type,data,ms){return new Promise((resolve,reject)=>{const requestId=++seq;const timer=setTimeout(()=>{requests.delete(requestId);reject(Error('Local model request timed out'))},ms);requests.set(requestId,{resolve:r=>{clearTimeout(timer);resolve(r)},reject:e=>{clearTimeout(timer);reject(e)}});newWorker().postMessage({type,requestId,...data})})}
const chosen={id:'Xenova/TinyLlama-1.1B-Chat-v1.0',modelUrl:'onnx-community/TinyLlama-1.1B-Chat-v1.0-ONNX',dtype:'q4',files:['model.onnx']};
$('localModelLoad').onclick=async()=>{const b=$('localModelLoad');b.disabled=true;state('Checking on-device model compatibility and downloading weights…');try{await send('load',{manifest:chosen,preferGPU:true,offlineOnly:$('localOffline').checked},150000)}catch(e){state('Local model unavailable: '+e.message)}finally{b.disabled=false}};
$('localModelUnload').onclick=()=>{worker?.terminate();worker=null;ready=false;model=null;state('Unloaded from local memory')};
window.iLocalLLM={get ready(){return ready},get model(){return model},generate:async prompt=>{if(!ready)throw Error('On-device LLM has not loaded');const r=await send('generate',{prompt,maxTokens:96},120000);return r.answer}};
const selection=document.createElement('label');selection.style.cssText='display:flex;gap:10px;align-items:center;margin:6px 0;font-size:13px';selection.innerHTML='<input type="checkbox" id="localModelSelected" style="width:auto"><span>Use local i™ LLM weights (offline inference when cached)</span>';panel.append(selection);
})();
