/* i™-Silo-1 VPU diagnostics: all figures are software-emulated unless proven otherwise. */
(()=>{'use strict';
const root=document.createElement('section');root.id='vpu-lab';root.className='view';
root.innerHTML=`<div class="glass silolab">
<header><div><small>i™ SILICON BEDROCK / iCALCULA</small><h1>⚡ VPU Control Matrix</h1><p>Deterministic instruction decoding, state-hash receipts, injected faults and local IPC benchmarks.</p></div><span class="silo-badge">EMULATOR · NO CHIP CONNECTED</span></header>
<div class="silo-registers"><div>VPU BASE<strong>0xFE000000</strong></div><div>PACKET DATA<strong>0x00A0</strong></div><div>STAMP CMD<strong>0x00B0</strong></div><div>OUT RECEIPT<strong>0x00C0</strong></div></div>
<div class="silo-plane"><span>Matrix / NextGraph<br><small>integration pending</small></span><span>Netmaker / im_receipt0<br><small>device driver absent</small></span><span>iCalcula VPU<br><small>Python + RTL simulation</small></span><span>OpenWrt / Pi<br><small>not provisioned</small></span></div>
<div class="silo-grid">
<article><h2>🧮 Instruction Laboratory</h2>
<label>A (signed int32)<input type="number" id="siloA" value="6"></label>
<label>B (signed int32)<input type="number" id="siloB" value="7"></label>
<label>Program<select id="siloOp"><option value="mul">MUL → STAMP</option><option value="add">ADD → STAMP</option><option value="mac">MAC → STAMP</option></select></label>
<label><input type="checkbox" id="siloFault" style="width:auto"> Inject fault at cycle zero</label>
<button id="siloExecute">Run test</button>
<button id="siloBenchmark">Measure software latency</button><pre id="siloOutput" role="status">No instruction executed.</pre></article>
<article><h2>📦 Software & Hardware Boundary</h2><p id="siloCapabilities">Checking backend…</p><div class="silo-facts"><p>⚪ Vortex: standalone candidate RTL, not integrated</p><p>⚪ SERS: SHA-256 software record only, not secure signing</p><p>⚪ KAI/GPUStack: not deployed as schedulers</p><p>⚪ Go daemon: separate local durable queue tool</p><p>⚪ gRPC: localhost-only performance benchmark</p></div>
<h2>🧾 Integrity Evidence</h2><pre id="siloReceipt">No receipt.</pre><button id="siloExport" disabled>Export evidence</button></article>
</div>
<details><summary>📋 i™ register safety contract</summary><p>No MMIO address is accessed by the PWA or backend. The proposed kernel network driver is not loaded: fixed-address mapping, unbounded busy loops and packet tail writes must not be trusted without verified silicon, bus enumeration, bounds and timeout controls. Cryptographic stamping requires an independently verified SERS key and verifier.</p></details>
</div>`;
const style=document.createElement('style');style.textContent=`
.silolab{background:linear-gradient(145deg,#071d26,#0a3b35 66%,#061d30);border:1px solid #c2ffff7d}
.silolab header{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.silolab h1{font-size:clamp(26px,4vw,39px)}.silolab h2{font-size:18px}
.silolab .silo-badge{border:1px solid #cfbf96;border-radius:30px;padding:8px;color:#ffdea0;font-size:11px;align-self:start}
.silolab .silo-registers{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:16px 0}
.silolab .silo-registers div{border:1px solid #7ef0cc8c;border-radius:10px;background:#081b22;padding:12px;font-size:11px;overflow-wrap:anywhere}
.silolab .silo-registers strong{font:15px ui-monospace,monospace;display:block;margin-top:8px;color:#b9ffeb}
.silolab .silo-plane{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:18px 0}
.silolab .silo-plane span{border:1px solid #6dfed073;border-radius:12px;padding:12px;background:#0c42446b;min-width:0;font-size:13px}
.silolab .silo-plane small{font-size:11px;opacity:.78}
.silolab .silo-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.silolab article{background:#041d22ac;border:1px solid #62dcb58f;border-radius:15px;padding:15px;min-width:0}
.silolab label{display:block;margin:10px 0;font-size:13px}.silolab label input:not([type=checkbox]),.silolab label select{display:block;width:100%;margin-top:6px}
.silolab button{min-height:44px;margin:5px}.silolab pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace}
.silolab details{margin-top:17px}
@media(max-width:760px){.silolab .silo-registers{grid-template-columns:repeat(2,1fr)}.silolab .silo-plane,.silolab .silo-grid{grid-template-columns:1fr}}
`;document.head.append(style);document.querySelector('main')?.append(root);
const nav=document.querySelector('nav');if(nav){const btn=document.createElement('button');btn.type='button';btn.textContent='⚡ VPU';btn.dataset.tab='vpu-lab';btn.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v===root));nav.querySelectorAll('[data-tab]').forEach(v=>v.classList.toggle('active',v===btn))};nav.append(btn)}
const $=id=>document.getElementById(id);
const api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
async function query(path,body){const ctrl=new AbortController(),timeout=setTimeout(()=>ctrl.abort(),12000);try{const response=await fetch(api+path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:ctrl.signal});if(!response.ok)throw Error('HTTP '+response.status);return await response.json()}finally{clearTimeout(timeout)}}
let last=null;
function program(){const op=$('siloOp').value;let code=op==='add'?1:op==='mac'?3:2;const a=Number($('siloA').value),b=Number($('siloB').value);if(!Number.isSafeInteger(a)||!Number.isSafeInteger(b))throw Error('Signed integers required');return {words:[(code<<24)|1,0x10000000],registers:[a,b,0,0,0,0,0,0],fault_cycle:$('siloFault').checked?0:null,iterations:100}}
$('siloExecute').onclick=async()=>{try{const d=await query('/v1/vpu/execute',program());last=d.receipt;$('siloOutput').textContent=d.status+'\nRegisters: '+d.state.registers.join(', ')+'\nAccumulator: '+d.state.accumulator+'\nFault: '+JSON.stringify(d.state.fault);$('siloReceipt').textContent='SHA-256 '+last.sha256+'\nSignature: NOT ISSUED\nSilicon: NOT PROBED';$('siloExport').disabled=false}catch(e){$('siloOutput').textContent='Error: '+e.message}};
$('siloBenchmark').onclick=async()=>{try{const d=await query('/v1/vpu/benchmark',program());$('siloOutput').textContent='Python software latency p50: '+d.software_latency_microseconds_p50+' µs\np95: '+d.software_latency_microseconds_p95+' µs\nActual silicon latency: NOT MEASURED'}catch(e){$('siloOutput').textContent='Benchmark error: '+e.message}};
$('siloExport').onclick=()=>{if(!last)return;const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='i-vpu-lab-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
query('/v1/vpu/capabilities').then(d=>{$('siloCapabilities').textContent='Physical device: '+(d.device_present?'verified':'NOT connected')+' · Driver: '+(d.kernel_driver_loaded?'loaded':'not loaded')+' · Backend: '+d.backend}).catch(e=>{$('siloCapabilities').textContent='Backend unavailable: '+e.message});
})();
