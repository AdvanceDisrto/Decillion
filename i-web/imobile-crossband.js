/* iMobile route + billing lab. Uses synthetic observations, never device IDs. */
(()=>{'use strict';const parent=document.getElementById('imobile');if(!parent)return;
const card=document.createElement('article');card.className='imob-crossband';card.innerHTML=`
<h2>📡 Cross-Band & Revenue Rehearsal</h2>
<p class="fine">Enable hypothetical paths for a bounded software test. No phone hardware identifiers or assistance credentials are used. Real Starlink/carrier routes remain disconnected.</p>
<div class="imob-flex"><label>Test packets <input id="xcbPackets" type="number" min="1" max="100000" value="1000"></label><label>Bytes per packet<input id="xcbBytes" type="number" min="64" max="16384" value="1024"></label></div>
<label><input id="xcbLocal" type="checkbox" checked style="width:auto"> Simulate authorized local LAN</label>
<label><input id="xcbSat" type="checkbox" style="width:auto"> Simulate provisioned satellite</label>
<label><input id="xcbCell" type="checkbox" style="width:auto"> Simulate provisioned cellular</label>
<label><input id="xcbSatOut" type="checkbox" style="width:auto"> Simulate satellite outage</label>
<label><input id="xcbCellOut" type="checkbox" style="width:auto"> Simulate cellular outage</label>
<div class="imob-flex"><label>Hypothetical price $/GB<input id="xcbPrice" type="number" min="0" max="100" step=".25" value="2"></label><label>Hypothetical cost $/GB<input id="xcbCost" type="number" min="0" max="100" step=".25" value="1"></label></div>
<button type="button" class="primary" id="xcbRun">Run Both Tests</button><button type="button" id="xcbDownload" disabled>Export 🧾 Evidence</button>
<pre id="xcbResults" role="status" aria-live="polite">Awaiting cross-band route and accounting test.</pre>
`;
const style=document.createElement('style');style.textContent='.imob-crossband{border:1px solid #80f4cc;background:#0b272a;padding:16px;border-radius:18px;margin:14px 0}.imob-crossband label{display:block;margin:10px 0;font-size:13px}.imob-crossband input:not([type=checkbox]){display:block;width:100%;margin-top:6px}.imob-crossband pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 ui-monospace,monospace}.imob-crossband button{min-height:44px;margin:7px}';document.head.append(style);
parent.querySelector('.imob')?.append(card);let last=null;
const $=id=>document.getElementById(id),api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
$('xcbRun').onclick=async()=>{const button=$('xcbRun');button.disabled=true;try{
const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),14000);let response;
try{response=await fetch(api+'/v1/imobile/crossband-rehearsal',{method:'POST',headers:{'Content-Type':'application/json'},signal:ctrl.signal,body:JSON.stringify({packets:Number($('xcbPackets').value),bytes_per_packet:Number($('xcbBytes').value),local_available:$('xcbLocal').checked,satellite_available:$('xcbSat').checked,cellular_available:$('xcbCell').checked,satellite_outage:$('xcbSatOut').checked,cellular_outage:$('xcbCellOut').checked,unit_price_usd_per_gb:Number($('xcbPrice').value),unit_cost_usd_per_gb:Number($('xcbCost').value)})})}finally{clearTimeout(timer)}
if(!response.ok)throw Error('HTTP '+response.status);last=await response.json();
const b=last.receipt.body;$('xcbResults').textContent='SIMULATED ROUTE SCHEDULE\n'+JSON.stringify(last.routes,null,2)+'\nQueued for hypothetical store/forward: '+last.store_and_forward_units+'\nReal deliveries: '+last.actual_deliveries+'\nProjected revenue: $'+b.projected_revenue_usd+'\nActual revenue: $0\nReceipt hash: '+last.receipt.sha256+'\nSignature: none; not certified';
$('xcbDownload').disabled=false;window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:last.receipt.sha256,body:{kind:'imobile-crossband-test',status:'simulated-only'}}}))
}catch(e){$('xcbResults').textContent='Test unavailable: '+e.message}finally{button.disabled=false}};
$('xcbDownload').onclick=()=>{if(!last)return;const u=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='imobile-crossband-test.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1100)};
})();