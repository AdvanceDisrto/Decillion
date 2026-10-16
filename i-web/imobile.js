/* iMobile: numberless application identity over existing authorized connectivity.
   This widget NEVER bypasses SIM/eSIM or claims a transmission took place. */
(()=>{'use strict';
const section=document.createElement('section');section.id='imobile';section.className='view';
section.innerHTML=`<div class="glass imob">
<header class="imob-head"><div><small>i™ SOVEREIGN NETWORK LAB</small><h1>📡 iMobile™ Command Center</h1><p>Application-layer @username routing, signed test receipts, and off-grid recovery rehearsals.</p></div><span id="imobBadge">NETWORK UNPROVISIONED</span></header>
<div class="imob-grid">
<article><h2>Open Telco Infrastructure</h2><div id="imobTopology">Checking capability registry…</div></article>
<article><h2>🪪 @username Route Simulator</h2><p class="fine">Handles are simulated identifiers, not active subscriber accounts.</p><label>Source handle<input id="imobFrom" value="@sender" maxlength="41"></label><label>Destination handle<input id="imobTo" value="@buddy" maxlength="41"></label><label>Test message<textarea id="imobPayload" rows="3" maxlength="2048">Hello from iMobile network laboratory.</textarea></label><label>Proposed route<select id="imobTransport"><option value="authorized-ip-lan">Authorized LAN/IP</option><option value="connected-internet">Internet connection</option><option value="offline-store-forward">Offline store and forward (design simulation)</option></select></label><div class="imob-flex"><label>Logical nodes<input id="imobNodes" value="12" type="number" min="2" max="256"></label><label>Blackout percentage<input id="imobDrop" type="range" value="50" min="0" max="95" step="5"><output id="imobDropLabel">50%</output></label></div><button type="button" class="primary" id="imobRun">▶ Test 50% network outage</button><p id="imobStatus" role="status">No message has been transmitted.</p></article></div>
<div class="imob-grid"><article><h2>🧾 Test Receipt</h2><div class="imob-paper" id="imobReceipt">Awaiting packet simulation. Not a production certification or delivery record.</div><button type="button" id="imobExport" disabled>Save receipt JSON</button></article>
<article><h2>i™ Infrastructure Boundaries</h2><p>CAMARA: operator API registration required. M-CORD/Open5GS: separate deployment and licensed spectrum/RAN required. Cozystack: cluster installation required. SONiC: supported hardware and management authorization required.</p><p>Phone numbers are unnecessary for <strong>app handles</strong>, but cellular registration still requires authorized network credentials. Lifeline/public-assistance enrollment isn't provisioned here.</p><p class="fine">Not suitable for emergencies. Use your device's available emergency calling function.</p></article></div><pre id="imobLog" role="log" aria-live="polite">iMobile™ — no connected peer or carrier service verified.</pre></div>`;
const style=document.createElement('style');style.textContent=`
.imob{border:1px solid #8fead0;background:linear-gradient(135deg,#072d2b,#0b192b)}
.imob .imob-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:18px;align-items:start}
.imob .imob-head h1{font-size:clamp(25px,4vw,40px);margin:6px 0}
.imob #imobBadge{border:1px solid #f0ca84;border-radius:100px;color:#ffdda1;padding:8px 12px;font-size:11px}
.imob .imob-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0}
.imob article{border:1px solid #78eac060;border-radius:16px;background:#061c22c9;padding:16px;min-width:0}
.imob h2{font-size:18px;margin:0 0 12px}
.imob .imob-node{padding:12px;border-left:3px solid #f5cb85;background:#143c3b64;border-radius:9px;margin:8px 0}
.imob .imob-node strong,.imob .imob-node small{display:block}.imob .imob-node small{font-size:12px;opacity:.8}
.imob label{display:block;font-size:13px;margin:9px 0}.imob label input,.imob label textarea{width:100%;margin-top:5px}
.imob select{padding:10px;width:100%;background:#0a302c;color:#e2fff2;border-radius:10px}
.imob .imob-flex{display:grid;grid-template-columns:1fr 1fr;gap:8px}.imob input[type=range]{accent-color:#80e8b4}
.imob .imob-paper{background:linear-gradient(140deg,#f3fcf2,#c9eadd);color:#163f33;border-radius:6px 6px 17px 17px;padding:17px;min-height:140px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px ui-monospace,monospace}
.imob #imobLog{background:#031619;color:#9efcd0;padding:13px;border-radius:10px;white-space:pre-wrap;overflow-wrap:anywhere;font:12px ui-monospace,monospace}
@media(max-width:700px){.imob .imob-grid{grid-template-columns:1fr}.imob article{padding:12px}}
`;document.head.append(style);document.querySelector('main')?.append(section);
const nav=document.querySelector('nav');if(nav){const b=document.createElement('button');b.type='button';b.textContent='📡 iMobile';b.dataset.tab='imobile';b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v===section));document.querySelectorAll('nav [data-tab]').forEach(v=>v.classList.toggle('active',v===b))};nav.append(b)}
const $=id=>document.getElementById(id),api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
let last=null;const log=m=>{$('imobLog').textContent+="\n"+new Date().toISOString().slice(11,19)+" "+m};
async function fetchJSON(path,body){const c=new AbortController(),timer=setTimeout(()=>c.abort(),12000);try{const r=await fetch(api+path,{method:body?'POST':'GET',cache:'no-store',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(timer)}}
async function refresh(){try{const c=await fetchJSON('/v1/imobile/capabilities');const host=$('imobTopology');host.replaceChildren();for(const d of c.components){const node=document.createElement('div');node.className='imob-node';const label=document.createElement('strong');label.textContent=d.name+' — NOT DEPLOYED';const sub=document.createElement('small');sub.textContent=d.note;node.append(label,sub);host.append(node)}log('Capability check: '+c.components.length+' design adapters, no real carrier access.')}catch(e){$('imobTopology').textContent='Gateway unavailable: '+e.message;log('API unreachable; no connectivity claim')}}
$('imobDrop').oninput=()=>{$('imobDropLabel').textContent=$('imobDrop').value+'%'};
$('imobRun').onclick=async()=>{const button=$('imobRun');button.disabled=true;$('imobStatus').textContent='Running test scenario…';try{const response=await fetchJSON('/v1/imobile/simulate',{from_handle:$('imobFrom').value,to_handle:$('imobTo').value,payload:$('imobPayload').value,total_nodes:Number($('imobNodes').value),blackout_fraction:Number($('imobDrop').value)/100,transport:$('imobTransport').value});
last=response;const rec=response.receipt;
$('imobReceipt').textContent='i™ IMOBILE TEST RECEIPT\nSHA-256: '+rec.packet_sha256+'\nTest signature: '+rec.test_signature.slice(0,32)+'…\n'+response.nodes_offline+'/'+response.nodes_total+' simulated nodes offline\nSimulated path: '+response.route.join(' → ')+'\nNetwork delivery: NOT VERIFIED\nProduction certified: NO';
$('imobStatus').textContent='Passed software rehearsal; no radio transmission or message delivery occurred.';$('imobExport').disabled=false;log('Offline node simulation: '+response.nodes_offline+'/'+response.nodes_total+' down, '+response.nodes_available+' surviving; NOT transmitted');
window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:rec.packet_sha256,body:{kind:'imobile-packet-test',status:'not transmitted'}}}));
}catch(e){$('imobStatus').textContent='Test error: '+e.message;log('FAIL '+e.message)}finally{button.disabled=false}};
$('imobExport').onclick=()=>{if(!last)return;const b=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='i-mobile-rehearsal.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
refresh();
})();