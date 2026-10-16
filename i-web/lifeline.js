/* i™ Lifeline — real capability probe and non-emergency telecom laboratory.
   NO carrier bypass, satellite access, guaranteed emergency delivery or actual mesh.
*/
(()=>{'use strict';
const sec=document.createElement('section');sec.id='lifeline';sec.className='view';sec.innerHTML=`
<div class="glass ilf">
<h1>📡 i™ Lifeline · Public Assistance Network</h1>
<p class="fine" role="alert"><strong>Network laboratory — not an emergency communications service.</strong> No Starlink, AT&T, Verizon, T-Mobile or solar satellite uplink is provisioned. For emergencies, use the device's available emergency call service (in the U.S., dial 911).</p>
<div class="ilf-grid"><article><h2>🌐 Network Topology</h2><div id="ilfCarriers">Checking gateway…</div><button type="button" id="ilfRefresh">↻ Verify connections</button></article>
<article><h2>@username · Packet test</h2><p class="fine">A handle identifies a simulated destination; it is not yet a verified directory or real recipient.</p>
<label>Destination <input id="ilfHandle" value="@buddy" maxlength="41" autocomplete="off"></label>
<label>Test message <textarea id="ilfMessage" rows="3" maxlength="1024" placeholder="Write non-sensitive test text"></textarea></label>
<label>Proposed route<select id="ilfRoute"><option value="solar-wifi-local">Solar Wi-Fi local</option><option value="starlink-direct-to-cell">Starlink Direct-to-Cell</option><option value="att">AT&amp;T</option><option value="verizon">Verizon</option><option value="t-mobile">T-Mobile</option></select></label>
<label><input type="checkbox" id="ilfOutage" style="width:auto"> Simulate internet outage</label>
<button type="button" id="ilfSend" class="primary">Run simulated packet</button>
<p id="ilfSendStatus" class="fine" role="status">No packet transmitted.</p></article></div>
<article class="ilf-energy"><h2>☀ Solar Relay Energy Budget</h2><p class="fine">Engineering estimate using entered values. Not measured sunlight or battery telemetry.</p>
<div class="ilf-controls"><label>Battery Wh<input id="ilfBattery" type="number" min="0.1" value="250"></label><label>Solar W<input id="ilfSolar" type="number" min="0" value="35"></label><label>Base draw W<input id="ilfBase" type="number" min="0.1" value="8"></label><label>Radio draw W<input id="ilfRadio" type="number" min="0" value="10"></label><label>Duty 0–1<input id="ilfDuty" type="number" min="0" max="1" step="0.1" value="0.3"></label></div>
<button id="ilfPower">Calculate power budget</button><pre id="ilfEnergyResult">Not calculated</pre></article>
<div class="ilf-grid"><article><h2>🧾 i™ Lifeline Receipt</h2><pre id="ilfReceipt">No demonstration executed. Verified delivery: NONE.</pre><button id="ilfExport" disabled>Export test receipt</button></article>
<article><h2>Connections require provisioning</h2><p class="fine">Satellite and cellular service require compatible radios, carrier authorization, network coverage and an active supported service where applicable. A PWA cannot override SIM/eSIM or radio restrictions.</p><p class="fine">BLE, LAN and Wi-Fi Direct require real nearby hardware and native device permission. Offline packets cannot reach distant people without an operating communications path.</p></article></div>
</div>`;
const css=document.createElement('style');css.textContent=`
.ilf{border:1px solid #83eac1;background:linear-gradient(125deg,#0d3938,#091621)}
.ilf .ilf-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.ilf article{min-width:0;border:1px solid #55dfaf58;background:#041e22b5;padding:15px;border-radius:16px;margin:9px 0}
.ilf h2{font-size:18px;margin:0 0 10px}
.ilf label{display:block;font-size:13px;margin:9px 0}
.ilf label input,.ilf label textarea,.ilf label select{display:block;width:100%;margin-top:5px;color:#edfff7}
.ilf select{padding:10px;background:#082c2a;border:1px solid #5fd8b27a;border-radius:12px}
.ilf .ilf-controls{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px}
.ilf .ilf-carrier{border-left:3px solid #dab879;background:#15342d;padding:8px 10px;margin:7px 0}
.ilf .ilf-carrier small{display:block;opacity:.8}
.ilf pre{white-space:pre-wrap;word-break:break-word;line-height:1.5;font:12px ui-monospace,monospace}
@media(max-width:700px){.ilf .ilf-grid{grid-template-columns:1fr}.ilf .ilf-controls{grid-template-columns:repeat(2,minmax(0,1fr))}.ilf article{padding:11px}}
`;document.head.append(css);document.querySelector('main')?.append(sec);
const nav=document.querySelector('nav');if(nav){const button=document.createElement('button');button.type='button';button.textContent='📡 Lifeline';button.dataset.tab='lifeline';button.onclick=()=>{document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x===sec));document.querySelectorAll('nav [data-tab]').forEach(x=>x.classList.toggle('active',x===button))};nav.append(button)}
const $=id=>document.getElementById(id),api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
let last=null;
async function request(path,method='GET',data){const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);try{const r=await fetch(api+path,{method,cache:'no-store',signal:controller.signal,headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(timeout)}}
async function refresh(){const elem=$('ilfCarriers');elem.textContent='Probing gateway…';try{const d=await request('/v1/lifeline/capabilities');elem.replaceChildren();for(const c of d.carriers){const row=document.createElement('div');row.className='ilf-carrier';const title=document.createElement('strong');title.textContent=c.id;const small=document.createElement('small');small.textContent=c.connected?'Connected and provisioned':'NOT CONNECTED · not provisioned';row.append(title,small);elem.append(row)}}catch(e){elem.textContent='Carrier status unavailable: '+e.message+' · no verified uplinks.'}}
$('ilfRefresh').onclick=refresh;
$('ilfSend').onclick=async()=>{let button=$('ilfSend');button.disabled=true;$('ilfSendStatus').textContent='Running local route simulation…';try{const d=await request('/v1/lifeline/mock-packet','POST',{handle:$('ilfHandle').value.trim(),message:$('ilfMessage').value,route:$('ilfRoute').value,simulate_outage:$('ilfOutage').checked});last=d.receipt;$('ilfReceipt').textContent='SHA-256: '+last.sha256+'\nTransmission: '+d.status+'\nSignature: none\nCertified: NO';$('ilfSendStatus').textContent='Simulation completed. Message was NOT delivered to any recipient.';$('ilfExport').disabled=false;window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:last.sha256,body:{kind:'lifeline-mock-packet',status:'simulated; not delivered'}}}))}catch(e){$('ilfSendStatus').textContent='Simulation failed: '+e.message}finally{button.disabled=false}};
$('ilfPower').onclick=async()=>{try{const d=await request('/v1/lifeline/power-budget','POST',{battery_wh:Number($('ilfBattery').value),solar_w:Number($('ilfSolar').value),base_w:Number($('ilfBase').value),radio_w:Number($('ilfRadio').value),duty_cycle:Number($('ilfDuty').value)});$('ilfEnergyResult').textContent=JSON.stringify(d,null,2)}catch(e){$('ilfEnergyResult').textContent='Budget unavailable: '+e.message}};
$('ilfExport').onclick=()=>{if(!last)return;const b=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download='i-lifeline-mock-receipt-'+last.sha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1200)};
refresh();
})();
