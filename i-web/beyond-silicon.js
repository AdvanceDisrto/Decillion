/* i™ Beyond-Silicon Research Lab: bounded backend CPU demonstrations.
No connected photonic, organoid or quantum hardware is claimed. */
(()=>{
'use strict';
const host=document.getElementById('explore');
if(!host)return;
const api=((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com').replace(/\/$/,'');
const root=document.createElement('section');root.className='glass';root.id='beyondSilicon';
root.innerHTML=`<h2>✧ i™ Beyond-Silicon Research Lab</h2>
<p class="fine">Explore three experimental architectures with real <b>CPU reference simulations</b>. No physical photonic chip, biological organoid or quantum device is connected.</p>
<div class="research-grid">
 <button type="button" data-engine="photonic"><strong>◈ iOPU™ · Photonic</strong><small>Ideal 2-port light interference model</small></button>
 <button type="button" data-engine="neuromorphic"><strong>⌁ iNeuro™ · Neuromorphic</strong><small>Digital spiking neuron model — no tissue</small></button>
 <button type="button" data-engine="quantum"><strong>◇ iQuantum™ · Analog Quantum</strong><small>2-qubit classical statevector model</small></button>
</div><div class="research-controls">
<label>Input A <input id="researchA" type="number" step="0.1" value="0.7"></label>
<label>Input B <input id="researchB" type="number" step="0.1" value="-0.3"></label>
<label>Phase <input id="researchPhase" type="number" step="0.1" value="0.4"></label>
<label>Steps <input id="researchSteps" type="number" min="1" max="64" value="12"></label>
</div><div class="research-actions"><button type="button" class="primary" id="researchRun">Run photonic reference</button><button type="button" id="researchReceipt" disabled>🧾 Export receipt</button></div>
<pre id="researchResult" role="status" aria-live="polite">Select an engine to run an independently checkable software demonstration.</pre>
<p class="fine">Reference calculations are not a benchmark of photonic speed, neural learning, quantum advantage, or hardware receipts. Browser UI and backend do not provide laboratory instrumentation or biological materials.</p>`;
const css=document.createElement('style');
css.textContent=`
#beyondSilicon{border:1px solid #65e7b994;background:linear-gradient(130deg,#063931e8,#04191fdf)}
#beyondSilicon .research-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
#beyondSilicon .research-grid button{padding:13px 9px;min-height:95px;text-align:left;line-height:1.4}
#beyondSilicon .research-grid button.selected{background:#78e9c8;color:#03251e}
#beyondSilicon .research-grid button strong{display:block;font-size:14px}
#beyondSilicon .research-grid button small{display:block;margin-top:5px;font-size:11px;color:inherit;opacity:.8}
#beyondSilicon .research-controls{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:15px}
#beyondSilicon .research-controls label{font-size:12px}
#beyondSilicon .research-controls input{margin-top:5px;padding:10px;width:100%}
#beyondSilicon .research-actions{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
#beyondSilicon pre{background:#021d1a;border-radius:12px;padding:13px;white-space:pre-wrap;overflow-wrap:anywhere;max-height:300px;overflow:auto;font-size:12px;line-height:1.55}
@media(max-width:680px){#beyondSilicon .research-grid{grid-template-columns:1fr}#beyondSilicon .research-grid button{min-height:0}#beyondSilicon .research-controls{grid-template-columns:repeat(2,minmax(0,1fr))}}
`;document.head.append(css);host.append(root);
let selection='photonic',last=null;
const $=id=>document.getElementById(id);
for(const button of root.querySelectorAll('[data-engine]')){
 button.addEventListener('click',()=>{
 selection=button.dataset.engine;
 for(const x of root.querySelectorAll('[data-engine]'))x.classList.toggle('selected',x===button);
 $('researchRun').textContent='Run '+selection+' reference';
 });
}
root.querySelector('[data-engine="photonic"]').classList.add('selected');
$('researchRun').addEventListener('click',async()=>{
 const button=$('researchRun');button.disabled=true;$('researchResult').textContent='Running bounded reference calculation…';
 try{
  const values=[Number($('researchA').value),Number($('researchB').value)];
  const phase=Number($('researchPhase').value),steps=Number($('researchSteps').value);
  if(!values.every(Number.isFinite)||!Number.isFinite(phase)||!Number.isInteger(steps)||steps<1||steps>64||Math.abs(phase)>6.283185307179586)throw Error('Enter finite inputs, phase between ±6.28, steps 1–64.');
  const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),12000);
  let response;
  try{response=await fetch(api+'/v1/alternative-compute/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({engine:selection,values,phase,steps}),signal:ctrl.signal})}finally{clearTimeout(timer)}
  if(!response.ok)throw Error('Research API: HTTP '+response.status);
  const payload=await response.json();last=payload.receipt;
  $('researchResult').textContent=JSON.stringify({simulation:payload.result,receipt_hash:last.sha256,signature:last.signature,hardware_verified:last.body.verified_hardware},null,2);
  $('researchReceipt').disabled=false;
 }catch(e){$('researchResult').textContent='Research service unavailable: '+String(e.message||e);last=null;$('researchReceipt').disabled=true}
 finally{button.disabled=false}
});
$('researchReceipt').addEventListener('click',()=>{
 if(!last)return;
 const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='i-research-'+last.body.engine+'-'+last.sha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
})();
