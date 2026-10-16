/* i™ iMirror: honest device/cloud digital twin, camera opt-in, crash simulation.
   No cloud state recovery, OS radio discovery or biometric extraction is claimed. */
(()=>{'use strict';
const root=document.createElement('section');root.id='mirror';root.className='view';
root.innerHTML=`<div class="glass i-mirror">
<h1>🪞 iMirror™ · Twin-Plane Control</h1><p class="fine">Physical browser observations versus actual reachable cloud gateway. The reflection slider simulates interpolation, not device synchronization.</p>
<div class="im-grid"><article class="im-plane"><h3>⌘ Physical Plane</h3><p id="imPhysical">Observing device…</p><div class="im-flags"><span id="imBLE">BLE: unverified</span><span id="imWiFi">Wi-Fi Direct: no browser socket</span><span id="imLAN">LAN: not discovered</span></div></article>
<article class="im-plane"><h3>☁ Virtual Routing Plane</h3><p id="imVirtual">Probing authenticated service status…</p><div id="imProviders">No independently verified provider endpoints.</div></article></div>
<label class="im-range">Reflective Sync-Wave Factor (visual interpolation) <strong id="imWaveValue">50%</strong><input type="range" id="imWave" min="0" max="100" value="50"></label>
<div class="im-grid"><article class="im-plane"><h3>📷 Visual Reflection Camera</h3><div class="im-camera"><video id="imVideo" playsinline muted autoplay></video><svg id="imGuide" viewBox="0 0 320 240" aria-label="Illustrative alignment guide"><ellipse cx="160" cy="105" rx="57" ry="76" stroke="#6bffd5" stroke-width="2" fill="none" stroke-dasharray="5 5"/><circle cx="144" cy="91" r="3" fill="#6bffd5"/><circle cx="178" cy="91" r="3" fill="#6bffd5"/><path d="M145 139 Q161 149 177 139" stroke="#6bffd5" fill="none"/></svg></div><p id="imCameraStatus" class="fine">Camera off. Guide is illustrative; no biometric landmarks or depth measured.</p><button id="imCameraStart">Start camera (permission required)</button><button id="imCameraStop">Stop camera</button></article>
<article class="im-plane"><h3>🛡 Fault Tolerance &amp; Integrity</h3><p id="imFaultStatus">No fault test executed</p><button id="imFault">Simulate network / device crash</button><button id="imCheck">Probe cloud status</button><button id="imReceipt">🧾 Export evidence</button><pre id="imReceiptView">A SHA-256 integrity record will appear here.</pre></article></div>
<p class="fine">No false 100% synchronization claims: offline states can diverge. Recovery is an in-memory snapshot simulation, not a real device failure or cloud restore. Physical camera tracking requires a verified on-device perception model.</p>
</div>`;
const css=document.createElement('style');css.textContent=`
.i-mirror{border:1px solid #bad9e5;background:linear-gradient(125deg,#112d31,#061a25);box-shadow:0 14px 50px #0008}
.i-mirror .im-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.i-mirror .im-plane{background:#061b21bd;border:1px solid #63dab866;border-radius:16px;padding:14px;overflow:hidden}
.i-mirror .im-plane h3{color:#c5fff2;font-size:16px;margin:0 0 12px}
.i-mirror .im-plane button{margin:4px}
.i-mirror .im-flags span{display:block;font-size:12px;padding:6px;background:#0d3633;margin:5px 0;border-radius:7px}
.i-mirror .im-range{display:block;padding:14px;margin:14px 0;border-radius:12px;background:#376d6433}
.i-mirror .im-range input{display:block;width:100%;accent-color:#7cffc5}
.i-mirror .im-camera{position:relative;background:#010d11;border-radius:12px;overflow:hidden;aspect-ratio:4/3;max-height:340px}
.i-mirror .im-camera video,.i-mirror .im-camera svg{position:absolute;width:100%;height:100%;inset:0;object-fit:cover}
.i-mirror .im-camera svg{pointer-events:none;opacity:.45}
.i-mirror #imReceiptView{font:11px/1.5 ui-monospace,monospace;overflow-wrap:anywhere;white-space:pre-wrap}
@media(max-width:700px){.i-mirror .im-grid{grid-template-columns:1fr}.i-mirror .im-plane{padding:10px}}
`;document.head.append(css);document.querySelector('main')?.append(root);
const nav=document.querySelector('nav');if(nav){const b=document.createElement('button');b.textContent='🪞 Mirror';b.type='button';b.dataset.tab='mirror';b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id==='mirror'));document.querySelectorAll('nav [data-tab]').forEach(v=>v.classList.toggle('active',v===b))};nav.append(b)}
const $=id=>document.getElementById(id),api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
let stream=null,last=null,cloud={reachable:false},lastFault=null;
function physical(){return {time:new Date().toISOString(),online:navigator.onLine,secure:isSecureContext,
  logical_cores:navigator.hardwareConcurrency||null,webgpu_exposed:!!navigator.gpu,
  bluetooth_api_exposed:!!navigator.bluetooth,ble_paired:false,
  wifi_direct_socket_connected:false,lan_socket_connected:false,source:'browser-observation'};}
function paint(){const p=physical();$('imPhysical').textContent='Network: '+(p.online?'browser reports online':'browser reports offline')+' · WebGPU API: '+(p.webgpu_exposed?'exposed':'not exposed');
$('imBLE').textContent='BLE: '+(p.bluetooth_api_exposed?'API exposed; no pairing':'not exposed')+' · not connected';
$('imWiFi').textContent='Wi-Fi Direct: not connected (requires native adapter)';
$('imLAN').textContent='Local LAN: no authorized peer established';}
async function probe(){paint();$('imVirtual').textContent='Contacting Buddy gateway…';
try{const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),8500);let response;
try{response=await fetch(api+'/v1/universal/providers',{signal:abort.signal,cache:'no-store'})}finally{clearTimeout(timer)}
if(!response.ok)throw Error('HTTP '+response.status);
const data=await response.json(),p=Array.isArray(data.providers)?data.providers:[];
cloud={reachable:true,provider_count:p.length,eligible:p.filter(x=>x.configured).length,policy:data.routing||'unknown'};
$('imVirtual').textContent='Gateway reachable · '+cloud.eligible+' eligible Apache-2.0 iModel route(s)';
$('imProviders').textContent='Configured-but-unverified: '+p.filter(x=>x.configured).map(x=>x.id).join(', ')+' · No hardware attestation.';
}catch(e){cloud={reachable:false,error:String(e.message||e)};$('imVirtual').textContent='Gateway not reachable; no cloud reflection performed';$('imProviders').textContent=cloud.error}
}
function stable(x){if(Array.isArray(x))return '['+x.map(stable).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}';return JSON.stringify(x)}
async function issue(kind,body){const payload={schema:'i-mirror-observation/1',kind,created_at:new Date().toISOString(),body,signing:'none',hardware_attested:false,cloud_restored:false,certification:'not-issued'};
const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(stable(payload)));const hash=Array.from(new Uint8Array(bytes),v=>v.toString(16).padStart(2,'0')).join('');
last={payload,sha256:hash};$('imReceiptView').textContent='🧾 LOCAL INTEGRITY RECORD\n'+hash+'\n'+kind+'\nUnsigned · not certified';window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:hash,body:{kind,status:'observed'}}}));return last}
$('imWave').oninput=()=>{$('imWaveValue').textContent=$('imWave').value+'%';root.style.setProperty('--wave',Number($('imWave').value)/100)};
$('imCameraStart').onclick=async()=>{if(!navigator.mediaDevices?.getUserMedia){$('imCameraStatus').textContent='Camera unavailable in this browser';return}try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});$('imVideo').srcObject=stream;$('imCameraStatus').textContent='Live local camera preview. Alignment guide is illustrative, not tracked.'}catch(e){$('imCameraStatus').textContent='Camera denied or unavailable: '+e.name}};
$('imCameraStop').onclick=()=>{stream?.getTracks().forEach(t=>t.stop());stream=null;$('imVideo').srcObject=null;$('imCameraStatus').textContent='Camera off'};
function cleanup(){stream?.getTracks().forEach(t=>t.stop());stream=null;}
window.addEventListener('pagehide',cleanup);
$('imFault').onclick=async()=>{
const snapshot={physical:physical(),cloud:{...cloud},wave:Number($('imWave').value)},initial=stable(snapshot),t=performance.now();
$('imFaultStatus').textContent='[FAULT INJECTED] Simulation: transport disconnected and volatile view reset.';
cloud={reachable:false,simulated:true};await Promise.resolve();const restored=JSON.parse(initial);
cloud=restored.cloud;const elapsed=performance.now()-t;const equal=stable(restored)===initial;
lastFault={recovery_ms:Math.round(elapsed*1000)/1000,snapshot_match:equal,cloud_recovery_verified:false,
    scope:'in-memory crash simulation; no device actually crashed'};
$('imFaultStatus').textContent='[iMIRROR TEST] Local snapshot '+(equal?'matched':'diverged')+' · '+lastFault.recovery_ms+' ms (in-memory only). Cloud restore NOT tested.';
await issue('mock-crash-recovery',{...lastFault});
};
$('imCheck').onclick=async()=>{await probe();await issue('live-capability-observation',{physical:physical(),cloud})};
$('imReceipt').onclick=()=>{if(!last){$('imReceiptView').textContent='Run a test before exporting';return}const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='i-mirror-'+last.sha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
window.iMirror={physical,probe,issue};paint();probe();
})();
