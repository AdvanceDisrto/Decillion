/* i™ DeWi local mesh laboratory; real links are never implied. */
(()=>{'use strict';const main=document.querySelector('main');if(!main)return;
const section=document.createElement('section');section.className='view';section.id='dewi';
section.innerHTML=`<div class="glass dewi"><h1>🌐 i™ DeWi Community Mesh</h1><p>Multi-hop routing, resilient offline state merge, and OpenWrt physical-node preparation.</p>
<p class="dewi-notice">SOFTWARE TEST · No paired radio hardware, live LoRa, real Internet uplink, or VPU signature accelerator is connected.</p>
<div class="dewi-grid"><article><h2>Network Path Lab</h2><p>Phone → Home router → Edge node</p><label><input type="checkbox" id="dewiBreak"> Simulate router outage</label><button id="dewiRoute">Find Best Path</button><pre id="dewiRouteResult">Run a route test.</pre></article>
<article><h2>Offline Document Sync</h2><label>Node A note<input id="dewiLeft" value="Hello from phone"></label><label>Node B note<input id="dewiRight" value="Updated from laptop"></label><button id="dewiSync">Resolve Version Conflict</button><pre id="dewiSyncResult">Local-first synchronization demo.</pre></article>
<article><h2>Physical Network Readiness</h2><div id="dewiHardware">Checking backend…</div><p>802.11s + batman-adv router configuration requires supported OpenWrt radios, key management, an authorized link and hardware acceptance tests.</p></article>
<article><h2>🧾 Evidence Receipts</h2><div id="dewiReceipt">No test executed.</div><button id="dewiExport" disabled>Export JSON</button><p>SHA-256 only. Not independent certification or silicon attestation.</p></article></div>
<p>Future integration slots: Meshtastic/LoRa text relay; Matrix WebRTC video over reachable IP; libp2p paired transport; NextGraph documented CRDT bridge; verified VPU device driver. These are not currently connected.</p></div>`;
const style=document.createElement('style');style.textContent=`
.dewi{background:linear-gradient(125deg,#0a302b,#071d30);border:1px solid #76f5d0;color:#eafff7}
.dewi h1{font-size:clamp(26px,4vw,39px)}.dewi h2{font-size:17px}
.dewi .dewi-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.dewi article{padding:16px;min-width:0;background:#081c25bd;border:1px solid #6ef0c977;border-radius:15px}
.dewi label{display:block;margin:12px 0}.dewi label input:not([type=checkbox]){display:block;width:100%;margin-top:5px}
.dewi button{min-height:44px;margin:8px 0}.dewi pre{font:12px ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.dewi-notice{padding:12px;border-radius:10px;background:#664b234e;border:1px solid #e2bb82}
@media(max-width:700px){.dewi .dewi-grid{grid-template-columns:1fr}}
`;document.head.append(style);main.append(section);
const nav=document.querySelector('nav');if(nav){const b=document.createElement('button');b.textContent='🌐 Mesh';b.type='button';b.dataset.tab='dewi';b.onclick=()=>{document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x===section));nav.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b))};nav.append(b)}
const $=id=>document.getElementById(id),api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');let last=null;
async function req(path,body){const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const r=await fetch(api+path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}
function evidence(v){last=v.receipt;$('dewiReceipt').textContent='SHA-256: '+last.sha256+'\nHardware attestation: NOT VERIFIED';$('dewiExport').disabled=false;window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:last.sha256,body:{kind:'dewi-software-test',status:'not-certified'}}}))}
$('dewiRoute').onclick=async()=>{try{const d=await req('/v1/dewi/route',{source:'phone',destination:'edge',offline_nodes:$('dewiBreak').checked?['router']:[],links:[{a:'phone',b:'router',latency_ms:3,transport:'wifi'},{a:'router',b:'edge',latency_ms:4,transport:'ethernet'},{a:'phone',b:'edge',latency_ms:20,transport:'lan'}]});$('dewiRouteResult').textContent=JSON.stringify(d.route,null,2);evidence(d)}catch(e){$('dewiRouteResult').textContent='Unavailable: '+e.message}};
$('dewiSync').onclick=async()=>{try{const d=await req('/v1/dewi/merge',{left:[{doc:'community',key:'note',value:$('dewiLeft').value,counter:1,actor:'phone'}],right:[{doc:'community',key:'note',value:$('dewiRight').value,counter:2,actor:'laptop'}]});$('dewiSyncResult').textContent=JSON.stringify(d.state,null,2);evidence(d)}catch(e){$('dewiSyncResult').textContent='Unavailable: '+e.message}};
$('dewiExport').onclick=()=>{if(!last)return;const u=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='i-dewi-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
req('/v1/dewi/capabilities').then(c=>{$('dewiHardware').textContent='Simulated software routing: '+(c.software_mesh_routing?'ready':'unavailable')+' · Connected physical nodes: '+c.connected_physical_mesh_nodes+' · VPU hardware: '+(c.vpu_hardware_available?'verified':'not connected')}).catch(e=>{$('dewiHardware').textContent='Backend unavailable: '+e.message});
})();