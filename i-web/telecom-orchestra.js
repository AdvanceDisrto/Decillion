/* i™ Telecom Symphony — real result driven dashboard. Animations are illustrative.
 * Radio/carrier access must be licensed/provisioned; no fabricated KPI is shown. */
(()=>{'use strict';
const page=document.createElement('section');
page.id='telecom-orchestra';page.className='view';
page.innerHTML=`<div class="glass ito-wrap">
<div class="ito-header"><div><p class="ito-eyebrow">i™ TELECOMMUNICATION MATRIX / INSTRUMENTS</p><h1>🎼 Telecom Symphony Orchestra</h1><p class="fine">Conductor laboratory for satellite, terrestrial, radio, fiber and Apache-2.0 iModels. These are simulated routing scores—not real carrier-frequency switching.</p></div><span class="ito-pill" id="itoState">Verification pending</span></div>
<canvas id="itoCanvas" width="900" height="250" aria-label="Animated illustrative network-wave composition"></canvas>
<div class="ito-grid">
 <article class="ito-panel"><h3>🎺 Instrument Matrix</h3><div id="itoInstruments">Checking real connection status…</div></article>
 <article class="ito-panel"><h3>⚙ Conductors / Node Failure Lab</h3>
  <div class="ito-form"><label>Logical nodes<input id="itoNodes" type="number" min="2" max="256" value="32"></label><label>Work units<input id="itoJobs" type="number" min="1" max="10000" value="10000"></label><label>Node dropout <output id="itoPercent">50%</output><input id="itoDrop" type="range" min="0" max="95" step="5" value="50"></label><label>Seed<input id="itoSeed" type="number" min="0" max="1000000" value="42"></label></div>
  <button class="primary" id="itoRun">▶ Run Fault Simulation</button><button id="itoAudio">♫ Play Sonification</button><button id="itoStopAudio">■ Stop</button><div class="fine">Audio is generated from mathematics, not intercepted telecommunications or private traffic.</div>
 </article>
</div>
<div class="ito-grid">
<article class="ito-panel"><h3>💰 Revenue Sensitivity — NOT actual billing</h3>
<div class="ito-form"><label>Modeled selling price / GB ($)<input type="number" id="itoPrice" min="0" max="100" step=".5" value="5"></label>
<label>Modeled cost / GB ($)<input type="number" id="itoCost" min="0" max="100" step=".5" value="2"></label>
<label>Work unit payload (KiB)<input type="number" id="itoKiB" min="1" max="16384" value="16"></label></div>
<p class="fine">The numbers below are a what-if projection. No credits issued, no customers billed, no money earned.</p>
<div id="itoFinance" class="ito-finance">No simulation executed.</div></article>
<article class="ito-panel"><h3>🧾 i™ Master Orchestral Score</h3>
<div id="itoReceipt" class="ito-receipt"><strong>UNVERIFIED</strong><p>Execute a test to generate an unsigned SHA-256 integrity record.</p></div>
<button id="itoDownload" disabled>⇩ Export test receipt JSON</button>
<button id="itoGetAudio">⇩ Download audio WAV</button></article></div>
<article class="ito-panel"><h3>⌘ iShell / Orchestration Event Log</h3><pre id="itoConsole" role="log" aria-live="polite">i™ Orchestrator initialized in educational simulation mode.\nNo cellular, satellite, P2P radios, fiber backhaul or physical cluster have been bound.\n</pre></article>
<p class="fine">Production gate: authorized network agreements, verifiable nodes, signal telemetry, authenticated transport, production billing, measured fault recovery, and independently signed receipts. Neither zero latency nor unlimited storage/VRAM is asserted.</p></div>`;
const css=document.createElement('style');css.textContent=`
.ito-wrap{max-width:1140px;margin-inline:auto;border:1px solid #7ff6d58e;background:radial-gradient(circle at 20% -10%,#17625478,transparent 55%),linear-gradient(150deg,#071d24,#052c29 65%,#051921)}
.ito-header{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;flex-wrap:wrap}
.ito-eyebrow{letter-spacing:.17em;font-size:11px;color:#8eefd0;font-weight:700}
.ito-pill{padding:8px 12px;border:1px solid #d4b57a;border-radius:100px;color:#f5dc9e;background:#433d2350;font-size:12px;font-weight:700}
.ito-wrap h1{font-size:clamp(27px,5vw,40px)}.ito-wrap h3{margin:0 0 12px;color:#d6ffed;font-size:18px}
#itoCanvas{display:block;max-width:100%;width:100%;height:auto;aspect-ratio:18/5;border-radius:16px;background:radial-gradient(circle at 50% 80%,#174644,#021719);border:1px solid #72dabb5c;margin:12px 0}
.ito-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;margin:13px 0}
.ito-panel{min-width:0;padding:16px;border:1px solid #76e6bb59;border-radius:18px;background:linear-gradient(160deg,#102f32d0,#061b23e8)}
.ito-instrument{display:flex;gap:11px;align-items:center;padding:9px;margin:7px 0;border:1px solid #92e3cf36;border-radius:9px;background:#153c394f}
.ito-instrument strong,.ito-instrument small{display:block}.ito-instrument small{font-size:11px;opacity:.75}
.ito-led{width:9px;height:9px;background:#e8bb73;border-radius:50%;box-shadow:0 0 9px #debf7180;flex-shrink:0}
.ito-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.ito-form label{font-size:12px;display:block}.ito-form input{margin-top:6px}
.ito-form input[type=range]{accent-color:#81fad1}
.ito-panel button{margin:11px 6px 0 0;min-height:44px}
.ito-finance,.ito-receipt{border:1px solid #82efcd77;padding:12px;overflow-wrap:anywhere;border-radius:10px;margin-top:10px;font-size:13px;line-height:1.6}
.ito-receipt{background:linear-gradient(120deg,#b5cfdd1c,#f7d48c1a);border:1px solid #c5dddc}
#itoConsole{max-height:250px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.65 ui-monospace,SFMono-Regular,monospace;background:#020e15;color:#9af7cf;border-radius:10px;padding:12px}
@media(max-width:740px){.ito-grid{grid-template-columns:1fr}.ito-panel{padding:12px}}
`;document.head.append(css);document.querySelector('main')?.append(page);
const nav=document.querySelector('nav');if(nav){const b=document.createElement('button');b.type='button';b.dataset.tab='telecom-orchestra';b.textContent='🎼 Orchestra';b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v===page));document.querySelectorAll('nav [data-tab]').forEach(v=>v.classList.toggle('active',v===b))};nav.append(b)}
const $=id=>document.getElementById(id);
const api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
let latest=null, audio=null,playing=false;
const log=text=>{const out=$('itoConsole');const val=new Date().toISOString().slice(11,19)+' '+text;out.textContent=(out.textContent+'\n'+val).slice(-7500);out.scrollTop=out.scrollHeight};
async function request(path,method='GET',data){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),13000);try{const r=await fetch(api+path,{method,signal:controller.signal,cache:'no-store',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(timer)}}
async function init(){try{const d=await request('/v1/orchestra/capabilities');$('itoState').textContent='Software lab · no uplinks';$('itoInstruments').replaceChildren();for(const x of d.instruments){const row=document.createElement('div');row.className='ito-instrument';const icon=document.createElement('span');icon.className='ito-led';const body=document.createElement('div');const title=document.createElement('strong');title.textContent=x.label;const small=document.createElement('small');small.textContent=x.path+' — '+(x.connected?'Connected':'NOT connected');body.append(title,small);row.append(icon,body);$('itoInstruments').append(row)}log('[CONNECTIVITY] '+d.instruments.length+' instrument labels, 0 authenticated carrier links.')}catch(e){$('itoState').textContent='Gateway unavailable';$('itoInstruments').textContent='Connection status unavailable: '+e.message;log('[ERROR] no gateway proof: '+e.message)}}
$('itoDrop').oninput=()=>{$('itoPercent').textContent=$('itoDrop').value+'%'};
$('itoRun').onclick=async()=>{const btn=$('itoRun');btn.disabled=true;try{const d=await request('/v1/orchestra/simulate','POST',{
nodes:Number($('itoNodes').value),jobs:Number($('itoJobs').value),
dropout_fraction:Number($('itoDrop').value)/100,seed:Number($('itoSeed').value),
proposed_price_usd_per_gb:Number($('itoPrice').value),
proposed_cost_usd_per_gb:Number($('itoCost').value),
assumed_kib_per_job:Number($('itoKiB').value)});
latest=d.receipt;const m=d.metrics;
$('itoFinance').textContent='Modeled volume: '+m.gigabytes_assumed+' GB · Hypothetical revenue $'+m.hypothetical_revenue_usd.toFixed(6)+' · Hypothetical costs $'+m.hypothetical_cost_usd.toFixed(6)+' · Actual revenue $0.00';
$('itoReceipt').replaceChildren();const strong=document.createElement('strong');strong.textContent='🧾 SIMULATED · NOT CERTIFIED';const pre=document.createElement('pre');pre.style.cssText='white-space:pre-wrap;word-break:break-all;font-size:12px';pre.textContent='SHA-256 '+latest.sha256+'\n'+m.completed_in_memory+'/'+m.simulated_jobs+' in-memory units assigned\n'+m.dropped_nodes+'/'+m.simulated_nodes+' logical nodes dropped\n'+m.reassigned_jobs+' units rerouted\nActual radio packets sent: 0\nSignature: NONE';$('itoReceipt').append(strong,pre);
$('itoDownload').disabled=false;log('[FAULT TEST] Dropped '+m.dropped_nodes+'/'+m.simulated_nodes+' synthetic nodes; reassigned '+m.reassigned_jobs+' work units');log('[ACCOUNTING] '+m.gigabytes_assumed+' GB assumed; revenue purely hypothetical, $0 realized');log('[EVIDENCE] integrity sha256='+latest.sha256);
window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:{sha256:latest.sha256,body:{kind:'telecom-orchestra-mock',status:'simulated; not certified'}}}));
}catch(e){log('[ERROR] '+e.message)}finally{btn.disabled=false}};
$('itoAudio').onclick=()=>{if(audio){audio.pause();audio=null}audio=new Audio(api+'/v1/orchestra/audio.wav');audio.play().then(()=>{playing=true;log('[SONIFICATION] playing 2-second synthetic WAV; not live radio signal')}).catch(e=>log('[AUDIO] '+e.message));audio.onended=()=>playing=false};
$('itoStopAudio').onclick=()=>{if(audio){audio.pause();audio.currentTime=0;playing=false;log('[AUDIO] stopped')}};
$('itoGetAudio').onclick=()=>{const a=document.createElement('a');a.href=api+'/v1/orchestra/audio.wav';a.download='i-orchestra-sonification.wav';a.rel='noopener';a.click()};
$('itoDownload').onclick=()=>{if(!latest)return;const u=URL.createObjectURL(new Blob([JSON.stringify(latest,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='i-orchestra-score-'+latest.sha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1200)};
const canvas=$('itoCanvas'),ctx=canvas.getContext('2d');let frame=0;
function render(){if(!ctx)return;const w=canvas.width,h=canvas.height;ctx.clearRect(0,0,w,h);ctx.lineWidth=2;
const hues=[165,190,45,300,118];for(let i=0;i<5;i++){const y=30+i*47;ctx.strokeStyle='hsl('+hues[i]+' 80% 62%)';ctx.globalAlpha=.78;ctx.beginPath();for(let x=0;x<=w;x+=5){const phase=frame*.028+i*1.3;const yy=y+Math.sin(x*.021+phase)*(6+i*1.6)+Math.sin(x*.057-phase)*2; x?ctx.lineTo(x,yy):ctx.moveTo(x,yy)}ctx.stroke()}ctx.globalAlpha=1;frame++;if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)requestAnimationFrame(render)}
render();init();
window.iOrchestra={run:()=>$('itoRun').click(),refresh:init};
})();
