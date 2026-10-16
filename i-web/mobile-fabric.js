/* i™ mobile heterogeneous fabric: browser self-tests, capability registry and receipts. */
(()=>{'use strict';
const api=(window.I_CONFIG?.buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
const units={cpu:'CPU',gpu:'GPU',npu:'NPU',tpu:'TPU',apu:'APU',spu:'iSPU',imods:'iMods',igptm:'iGPTM'};
const info={cpu:'Browser JS / WASM processing',gpu:'Browser WebGPU compute',npu:'WebNN interface; chip not proven',tpu:'Authenticated remote TPU required',apu:'Unified mobile SoC; not reliably identifiable',spu:'Physical iSPU hardware not attested',imods:'Modular i™ event handlers',igptm:'Native model serving gateway'};
const status=Object.fromEntries(Object.keys(units).map(k=>[k,{state:'unverified',text:info[k]}]));
const css=document.createElement('style');css.textContent=`
#fabricLaunch{position:fixed;right:10px;bottom:max(83px,env(safe-area-inset-bottom));z-index:35;border:1px solid #8dffe1;background:linear-gradient(120deg,#065746,#072e32);box-shadow:0 0 28px #13ffbf77;font-weight:750;font-size:13px;padding:10px 14px}
#fabricDialog{position:fixed;inset:0;z-index:90;background:#001610e7;backdrop-filter:blur(18px);display:none;place-items:center;padding:12px}
#fabricDialog.open{display:grid}
#fabricPanel{background:linear-gradient(135deg,#0d4942,#041820);border:1px solid #6cffd1;box-shadow:0 0 75px #00fca73c;border-radius:21px;max-height:94dvh;overflow:auto;padding:19px;width:min(920px,100%)}
#fabricPanel h2{margin:0 0 10px}
#fabricPanel .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
#fabricPanel .chip{padding:12px;border:1px solid #56ffc37a;border-radius:15px;background:#baffd907;min-height:148px;overflow-wrap:anywhere}
#fabricPanel .chip h3{margin:0 0 9px;color:#a9ffe3}
#fabricPanel .chip strong{font-size:13px;color:#ffedb0}
#fabricPanel .chip strong.pass{color:#a4ffbd}
#fabricPanel .chip p{font-size:12px;color:#c1dfd5;line-height:1.45}
#fabricPanel .buttons{display:flex;flex-wrap:wrap;gap:8px;margin:13px 0}
#fabricPanel .fine{font-size:12px;line-height:1.5;color:#b7dbce}
#fabricPanel .receipts{max-height:125px;overflow:auto;font:11px ui-monospace,monospace;color:#a9f6da;overflow-wrap:anywhere}
#fabricClose{float:right}
@media(max-width:700px){#fabricPanel .grid{grid-template-columns:repeat(2,minmax(0,1fr))}#fabricLaunch{bottom:88px;right:5px;padding:8px 10px;font-size:11px}}
@media(max-width:380px){#fabricPanel .grid{grid-template-columns:1fr}}
`;document.head.append(css);
const launch=document.createElement('button');launch.id='fabricLaunch';launch.textContent='⚡ i™ FABRIC';launch.type='button';document.body.append(launch);
const dlg=document.createElement('section');dlg.id='fabricDialog';dlg.setAttribute('role','dialog');dlg.setAttribute('aria-modal','true');dlg.setAttribute('aria-label','iMobile accelerator fabric');
dlg.innerHTML='<div id="fabricPanel"><button id="fabricClose" aria-label="Close iFabric">✕</button><h2>i™ Mobile Fabric · iMods</h2><p class="fine">CPU · GPU · NPU · TPU · APU · iSPU · iMods · iGPTM. Hardware capabilities are reported as observed, available or not connected—never invented.</p><div class="grid" id="fabricGrid"></div><div class="buttons"><button id="fabricTest" class="primary">⚡ Execute local tests</button><button id="fabricScan">↻ Probe hardware &amp; models</button><button id="fabricExport">🧾 Export receipts</button></div><p class="fine">A browser probe is not device attestation. TPU/iSPU require secure external hardware nodes. A configured model endpoint does not certify native checkpoints.</p><div class="receipts" id="fabricReceipts"></div></div>';document.body.append(dlg);
const $=id=>document.getElementById(id);let focus;
function set(id,state,text){status[id]={state,text};draw()}
function draw(){const box=$('fabricGrid');box.replaceChildren();for(const id of Object.keys(units)){const el=document.createElement('article');el.className='chip';const title=document.createElement('h3');title.textContent=units[id];const st=document.createElement('strong');st.className=status[id].state==='operational'||status[id].state==='available'?'pass':'';st.textContent=status[id].state;const p=document.createElement('p');p.textContent=status[id].text;el.append(title,st,p);box.append(el)}}
function saved(){try{const x=JSON.parse(localStorage.getItem('i-fabric-receipts')||'[]');return Array.isArray(x)?x:[]}catch{return []}}
function show(){const list=$('fabricReceipts');list.replaceChildren();for(const item of saved().slice(-8).reverse()){const p=document.createElement('p');p.textContent=item.body.time+' · '+item.body.operation+' · '+item.hash.slice(0,25);list.append(p)}}
async function receipt(operation,result){const body={type:'i-fabric-local/0.1',operation,result,time:new Date().toISOString(),issuer:'browser-unattested'};const bytes=new TextEncoder().encode(JSON.stringify(body));const hash='sha256:'+Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');localStorage.setItem('i-fabric-receipts',JSON.stringify([...saved(),{body,hash}].slice(-100)));show();window.dispatchEvent(new CustomEvent('i-fabric-receipt',{detail:{body,hash}}));}
async function probe(){
 set('cpu','available','JavaScript local runtime, concurrency hint: '+(navigator.hardwareConcurrency||'unknown'));
 set('gpu',navigator.gpu?'available':'not available',navigator.gpu?'WebGPU is exposed (execution not yet tested)':'WebGPU not exposed by this browser');
 set('npu',navigator.ml?'available':'not available',navigator.ml?'WebNN API exposed; NPU physical execution not attested':'WebNN unavailable; no NPU claim');
 set('apu','not verified',info.apu);set('tpu','not connected',info.tpu);set('spu','not connected',info.spu);
 set('imods','operational','i™ event registry and receipt event dispatch loaded');
 set('igptm','checking','Probing Render iModels and Fabric API');
 try{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),8000);const res=await fetch(api+'/v1/fabric/capabilities',{signal:controller.signal,cache:'no-store'});clearTimeout(timer);if(!res.ok)throw Error('API '+res.status);const json=await res.json();for(const m of json.modules||[]){if((m.id==='igptm'||m.id==='tpu'||m.id==='spu')&&m.configured===true)set(m.id,'configured','Remote route configured; execution and physical attestation unverified')}if(json.protocol)set('igptm','available','iFabric gateway reachable · model weights not verified');}catch(e){set('igptm','unavailable','Remote registry unreachable: '+String(e.message||e).slice(0,70))}
}
async function gpuTest(){if(!navigator.gpu)return false;let device;try{const a=await navigator.gpu.requestAdapter();if(!a)throw Error('No adapter');device=await a.requestDevice();const source='@group(0) @binding(0) var<storage,read_write> o: array<u32>; @compute @workgroup_size(4) fn main(@builtin(global_invocation_id) i:vec3<u32>){ if(i.x<4u){o[i.x]=i.x*7u+3u;} }';const m=device.createShaderModule({code:source});const out=device.createBuffer({size:16,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC}),copy=device.createBuffer({size:16,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ});const layout=device.createBindGroupLayout({entries:[{binding:0,visibility:GPUShaderStage.COMPUTE,buffer:{type:'storage'}}]});const p=device.createComputePipeline({layout:device.createPipelineLayout({bindGroupLayouts:[layout]}),compute:{module:m,entryPoint:'main'}}),bind=device.createBindGroup({layout,entries:[{binding:0,resource:{buffer:out}}]});const e=device.createCommandEncoder(),pass=e.beginComputePass();pass.setPipeline(p);pass.setBindGroup(0,bind);pass.dispatchWorkgroups(1);pass.end();e.copyBufferToBuffer(out,0,copy,0,16);device.queue.submit([e.finish()]);await copy.mapAsync(GPUMapMode.READ);const data=Array.from(new Uint32Array(copy.getMappedRange().slice(0)));copy.unmap();out.destroy();copy.destroy();const ok=data.join(',')==='3,10,17,24';set('gpu',ok?'operational':'error','WebGPU shader output: '+data.join(','));await receipt('webgpu-dispatch',{ok,data});return ok}catch(e){set('gpu','not available','WebGPU compute error: '+String(e.message).slice(0,95));return false}finally{device?.destroy?.()}}
async function run(){const b=$('fabricTest');b.disabled=true;try{const t=performance.now();let x=0;for(let i=0;i<250000;i++)x+=(i*13)%997;const ms=Math.round(performance.now()-t);set('cpu','operational','JS loop executed '+ms+'ms; result '+x);await receipt('cpu-js-self-test',{ms,sum:x});await gpuTest()}finally{b.disabled=false}}
launch.onclick=()=>{focus=document.activeElement;dlg.classList.add('open');$('fabricClose').focus()};function close(){dlg.classList.remove('open');focus?.focus?.()}$('fabricClose').onclick=close;dlg.addEventListener('click',e=>{if(e.target===dlg)close()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&dlg.classList.contains('open'))close()});$('fabricScan').onclick=probe;$('fabricTest').onclick=run;$('fabricExport').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(saved(),null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='i-mobile-fabric-receipts.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)};
window.iMobileFabric={units,status,probe,run,receipt};draw();show();probe();
})();
