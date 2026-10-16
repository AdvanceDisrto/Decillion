/* i™ IDE | browser-only source execution. Executes user-supplied JavaScript in an
   opaque-origin CSP-restricted sandbox iframe. This is not PowerShell or native OS access. */
(()=>{'use strict';
const src='console.log("Hello from i™.");\nconsole.log("Compute:", 6*7);';
const css=document.createElement('style');css.textContent=`
#iIDE{background:linear-gradient(140deg,#082d2d,#061a28);border:1px solid #75f8d188;border-radius:18px;padding:16px;margin:15px 0}
#iIDE .ide-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#iIDE .ide-row>*{flex:1}#iIDE select{background:#092e2b;border:1px solid #67dabc;color:white;border-radius:10px;padding:10px}
#iIDE .ide-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;margin:12px 0}
#iIDE .ide-edit,#iIDE .ide-term{width:100%;min-height:230px;background:#061315;color:#bfffe1;border:1px solid #41c69988;border-radius:12px;padding:13px;font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}
#iIDE .ide-edit{resize:vertical;tab-size:2}
#iIDE .ide-term{margin:0;color:#b1d4ca}
#iIDE .ide-prompt{display:flex;gap:7px}#iIDE .ide-prompt input{flex:1;min-width:0}
#iIDE .ide-info{font-size:12px;color:#bbddce}
#iIDE button{min-height:42px}
#iIDE .ide-cert{border:1px solid #7dffe1;border-radius:13px;padding:14px;background:#042c25;margin:10px 0;overflow-wrap:anywhere}
#iIDE .ide-cert h3{margin:0 0 6px}#iIDE .ide-cert pre{white-space:pre-wrap;font:12px ui-monospace,monospace;line-height:1.5}
#iIDE .ide-cert .badge{display:inline-block;border:1px solid #55dfba;padding:4px 8px;border-radius:99px;font-size:11px}
#iIDE .ide-footnote{font-size:12px;color:#b7cdbf}
#iIDE .ide-tooltabs button{flex:0 0 auto}
@media(max-width:700px){#iIDE .ide-layout{grid-template-columns:1fr}#iIDE .ide-edit,#iIDE .ide-term{min-height:180px}#iIDE{padding:12px}}
`;document.head.append(css);
const view=document.createElement('section');view.id='ide';view.className='view';view.innerHTML=`
<h1>⌘ i™ Developer Studio</h1><p class="fine">Edit, run and test JavaScript inside i™. Built-in iShell commands stay inside this PWA. Native PowerShell, compilers and external devices require a separately authenticated host adapter.</p>
<div id="iIDE">
<div class="ide-row"><label>Target <select id="ideTarget"><option value="pwa">PWA · This device</option><option value="mobile">Mobile · Profile</option><option value="tablet">Tablet · Profile</option><option value="pc">PC · Profile</option><option value="smart">Smart device · Profile</option></select></label><span class="ide-info" id="ideDevice">Browser sandbox</span></div>
<div class="ide-row ide-tooltabs"><button id="ideRun" class="primary">▶ Run JS</button><button id="ideStop">■ Stop</button><button id="ideNet">⇄ Network probe</button><button id="ideVerify">✓ Verify receipt</button><button id="ideExport">↓ Save evidence</button></div>
<div class="ide-layout"><div><h3>Source · main.js</h3><textarea id="ideSource" class="ide-edit" spellcheck="false" aria-label="Editable JavaScript source"></textarea></div><div><h3>iShell · Terminal</h3><pre class="ide-term" id="ideOutput" role="log" aria-live="polite"></pre><form class="ide-prompt" id="ideForm"><input id="ideCommand" placeholder="help, run, status, debug --gpu" aria-label="iShell command"><button type="submit">↵</button></form></div></div>
<div class="ide-cert" id="ideCert"><h3>🧾 i™ Verified Receipt</h3><span class="badge" id="ideBadge">Awaiting execution</span><pre id="ideReceiptInfo">Execute source to issue a SHA-256 integrity receipt.</pre><small>Certification status: NOT ISSUED. A hash proves content integrity, not hardware execution, identity, or a global ledger seal.</small></div>
<p class="ide-footnote">JavaScript executes in an opaque-origin sandbox with a restrictive Content Security Policy, no same-origin access and no permitted network connection. CPU time is limited by removing the sandbox after a timeout. This is a browser IDE, not unrestricted operating-system PowerShell or VS Code.</p>
</div>`;
document.querySelector('main')?.append(view);
const nav=document.querySelector('nav');if(nav){const b=document.createElement('button');b.type='button';b.textContent='IDE';b.dataset.tab='ide';b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id==='ide'));document.querySelectorAll('[data-tab]').forEach(v=>v.classList.toggle('active',v===b))};nav.append(b)}
const $=id=>document.getElementById(id),LOG=$('ideOutput');$('ideSource').value=src;
let active=null,last=null,index=0;const entries=[];const log=s=>{entries.push(String(s));if(entries.length>160)entries.shift();LOG.textContent=entries.join('\n');LOG.scrollTop=LOG.scrollHeight};
const ready=()=>({online:navigator.onLine,secure:isSecureContext,webgpu:!!navigator.gpu,logicalCores:navigator.hardwareConcurrency||null,memoryHintGiB:navigator.deviceMemory||null,origin:location.origin});
const canonical=obj=>JSON.stringify(obj&&typeof obj==='object'?(Array.isArray(obj)?obj.map(x=>JSON.parse(canonical(x))):Object.fromEntries(Object.keys(obj).sort().map(k=>[k,JSON.parse(canonical(obj[k]))]))):obj);
const hash=async obj=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(obj)))),x=>x.toString(16).padStart(2,'0')).join('');
function stop(){if(active){active.frame.remove();clearTimeout(active.timeout);active=null;log('[iShell] Execution sandbox stopped.')}}
async function receipt(type,detail,status='completed'){
 const body={schema:'i-ide-receipt/1',kind:type,status,target:$('ideTarget').value,time:new Date().toISOString(),detail,
  verification:{integrity:'sha256',authenticity:'not-verified',certification:'not-issued',hardware_attestation:false}};
 const r={body,sha256:await hash(body)};last=r;try{localStorage.setItem('i-ide-receipt-last',JSON.stringify(r))}catch{}
 $('ideBadge').textContent='SHA-256 integrity recorded · '+status;
 $('ideReceiptInfo').textContent='SHA-256: '+r.sha256+'\nTarget: '+r.body.target+'\nAction: '+type+'\nResult: '+status+'\nTimestamp: '+body.time;
 window.dispatchEvent(new CustomEvent('i:ide-receipt',{detail:r}));return r;
}
async function run(){
 stop();const code=$('ideSource').value;if(code.length>24000){log('[error] Source limit is 24KB.');return}
 const id='im-exec-'+(++index);const frame=document.createElement('iframe');
 frame.setAttribute('sandbox','allow-scripts');frame.setAttribute('aria-hidden','true');
 frame.style.cssText='position:absolute;width:0;height:0;border:0;opacity:0';
 const script=JSON.stringify(code).replace(/</g,'\\u003c');
 const inner=`<!doctype html><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; connect-src 'none'; img-src 'none'; form-action 'none'; base-uri 'none'"><script>
 const id=${JSON.stringify(id)};
 const send=(type,value)=>parent.postMessage({channel:'i-ide-sandbox',id,type,value},'*');
 const console={log:(...x)=>send('stdout',x.map(String).join(' ')),error:(...x)=>send('stderr',x.map(String).join(' ')),warn:(...x)=>send('stdout',x.map(String).join(' '))};
 addEventListener('error',e=>{send('stderr',e.message);e.preventDefault()});
 (async()=>{try{const fn=new Function('console',${script});await fn(console);send('done','ok')}catch(e){send('stderr',String(e));send('done','failed')}})();
 <\/script>`;
 frame.srcdoc=inner;document.body.append(frame);log('iShell> run main.js ['+$('ideTarget').value+']');
 active={id,frame,logs:[],timeout:setTimeout(()=>{if(active?.id===id){const a=active;active=null;a.frame.remove();log('[timeout] execution stopped after 3 seconds');receipt('javascript-run',{sourceSha256:'not-recorded',logs:a.logs,error:'timeout'},'timed-out')}},3000)};
}
window.addEventListener('message',async e=>{
 const m=e.data;if(!active||e.source!==active.frame.contentWindow||m?.channel!=='i-ide-sandbox'||m.id!==active.id)return;
 if(m.type==='stdout'||m.type==='stderr'){const line=(m.type==='stderr'?'ERR ':'')+String(m.value).slice(0,2000);active.logs.push(line);log(line)}
 if(m.type==='done'){const a=active;active=null;clearTimeout(a.timeout);a.frame.remove();const sourceHash=await hash({source:$('ideSource').value});await receipt('javascript-run',{sourceSha256:sourceHash,logs:a.logs.slice(-80)},m.value==='ok'?'completed':'failed');log('[iShell] '+m.value)}
});
async function probe(){
 log('iShell> sync status');const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),6000);
 try{const res=await fetch(((window.I_CONFIG||{}).buddyApiUrl||'https://i-the-one-buddy-api.onrender.com')+'/health',{cache:'no-store',signal:ctrl.signal});
 if(!res.ok)throw Error('HTTP '+res.status);const data=await res.json();const results={reachable:true,status:data.status||'unknown',modelConfigured:!!data.model_configured,storageSigningConfigured:!!data.storage_auth_signing_configured};log(JSON.stringify(results));await receipt('network-probe',results)}
 catch(e){log('[network] Remote API unavailable: '+String(e.message||e));await receipt('network-probe',{reachable:false,error:String(e.message||e)},'unavailable')}
 finally{clearTimeout(timer)}
}
async function verify(){
 if(!last){log('No receipt generated.');return}const ok=last.sha256===await hash(last.body);
 $('ideBadge').textContent=ok?'✓ Integrity verified · certification not issued':'✗ Integrity failed';
 log('[receipt] '+(ok?'SHA-256 content matches':'TAMPER DETECTED'));
}
function cmd(input){
 const text=input.trim(),[verb,...args]=text.split(/\s+/);if(!verb)return;
 log('iShell> '+text);
 switch(verb.toLowerCase()){
 case 'help':log('Commands: help, pwd, ls, cat main.js, run, stop, clear, status, targets, target <name>, debug --gpu|--memory|--network, sync, receipt, verify');break;
 case 'pwd':log('/i/workspace (virtual browser workspace)');break;
 case 'ls':log('main.js   receipts/   device/');break;
 case 'cat':log(args[0]==='main.js'?$('ideSource').value.slice(0,8000):'Only main.js is available in this browser workspace.');break;
 case 'run':run();break;
 case 'stop':stop();break;
 case 'clear':entries.length=0;LOG.textContent='';break;
 case 'status':log(JSON.stringify(ready()));break;
 case 'targets':log('pwa, mobile, tablet, pc, smart (profiles; only pwa executes locally)');break;
 case 'target':if(['pwa','mobile','tablet','pc','smart'].includes(args[0])){$('ideTarget').value=args[0];log('Target profile: '+args[0]+' (local browser still executes)')}else log('Unknown target');break;
 case 'debug':if(args[0]==='--gpu')log(JSON.stringify({webgpuExposed:!!navigator.gpu,hardwareVerified:false}));else if(args[0]==='--memory')log(JSON.stringify({deviceMemoryGiB:navigator.deviceMemory||'not disclosed',unlimited:false}));else if(args[0]==='--network')log(JSON.stringify({online:navigator.onLine,api:'use sync for probe'}));else log('Supported flags: --gpu, --memory, --network');break;
 case 'sync':probe();break;
 case 'receipt':log(last?JSON.stringify(last,null,2):'No receipt');break;
 case 'verify':verify();break;
 default:log('Unknown command. Type help. No arbitrary host commands are executed.');
 }
}
$('ideRun').onclick=run;$('ideStop').onclick=stop;$('ideNet').onclick=probe;$('ideVerify').onclick=verify;
$('ideExport').onclick=()=>{if(!last)return log('No receipt to export');const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='i-ide-receipt-'+last.sha256.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('ideForm').onsubmit=e=>{e.preventDefault();const input=$('ideCommand');cmd(input.value);input.value=''};
$('ideTarget').onchange=()=>{$('ideDevice').textContent='Target profile: '+$('ideTarget').value+' · browser sandbox only'};
window.iIDE={run,stop,probe,verify,command:cmd};
log('i™ iNtelligentShell / browser runtime');log('Type help. Native PowerShell requires an authorized local agent.');
// Place a compact live receipt artifact inside previously empty Buddy stage.
const stage=document.querySelector('.buddy-world');if(stage){
 const slot=document.createElement('aside');slot.id='buddyReceiptDock';
 slot.style.cssText='position:absolute;inset:28% 12% 24%;z-index:5;display:grid;place-items:center;pointer-events:none';
 const paper=document.createElement('article');paper.style.cssText='background:linear-gradient(#fafff7,#e4fff0);color:#063326;border:2px solid #81ffe0;border-radius:6px 6px 16px 16px;box-shadow:0 0 40px #20ffd073;padding:17px;width:min(250px,90%);min-height:200px;text-align:center;font:13px ui-monospace,monospace;overflow-wrap:anywhere;transform:translateY(0);transition:transform .55s';
 paper.innerHTML='<strong style="font-size:32px">i™</strong><h3>THE RECEIPT 🧾</h3><p id="buddyDockStatus">Ready for verified integrity records</p><small id="buddyDockHash">No execution recorded</small><p style="font-size:10px;margin-top:16px">POWERED BY THE i™ ECOSYSTEM</p>';
 slot.append(paper);stage.append(slot);
 const style=document.createElement('style');style.textContent='#buddyReceiptDock{max-height:370px}#buddyReceiptDock article{max-height:100%;overflow:auto}@media(max-width:550px){#buddyReceiptDock{inset:28% 14% 25%!important}#buddyReceiptDock article{min-height:160px!important;padding:12px!important}#buddyReceiptDock h3{font-size:15px}}';document.head.append(style);
 window.addEventListener('i:ide-receipt',e=>{const r=e.detail;document.getElementById('buddyDockStatus').textContent=r.body.kind+' · '+r.body.status;document.getElementById('buddyDockHash').textContent=r.sha256.slice(0,24)+'…';paper.style.transform='translateY(-13px)';setTimeout(()=>paper.style.transform='',500)});
}
})();
