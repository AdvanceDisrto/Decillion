'use strict';const $=x=>document.getElementById(x),KEY='i-the-one-receipts-v02';let receipts=[],installPrompt,activeReceipt=null,returnFocus=null;const canon=x=>JSON.stringify(x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canon(x[k]))])):Array.isArray(x)?x.map(v=>JSON.parse(canon(v))):x);async function hash(s){const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s));return 'sha256:'+Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('')}async function verify(r){return !!(r&&r.body&&typeof r.id==='string')&&r.id===await hash(canon(r.body))}function notice(s){const t=$('toast');t.textContent=s;t.style.display='block';setTimeout(()=>t.style.display='none',3000)}function save(){localStorage.setItem(KEY,JSON.stringify(receipts));render()}async function create(text){const body={protocol:'i-receipt/0.1',action:'user-note',issuer:'browser-unverified',payload:{text,createdAt:new Date().toISOString()},parents:receipts.length?[receipts[receipts.length-1].id]:[],evidence:[],verification:{integrity:'sha256-only',authenticity:'not-established',truth:'not-established'}};const r={id:await hash(canon(body)),body};receipts.push(r);save();eject(r);return r}function download(name,data){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)}function message(t,who){const e=document.createElement('div');e.className='bubble'+(who==='me'?' me':'');e.textContent=t;$('messages').append(e);$('messages').scrollTop=$('messages').scrollHeight}function say(s){if(window.buddyCompanion)window.buddyCompanion.mode('talking');if($('speak').checked&&'speechSynthesis'in window){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(s.slice(0,400)))}}async function ask(q){q=q.trim();if(!q)return;if(window.buddyCompanion)window.buddyCompanion.mode('thinking');message(q,'me');$('prompt').value='';let s;if(/verif/i.test(q)){const n=(await Promise.all(receipts.map(verify))).filter(Boolean).length;s='Verified '+n+' of '+receipts.length+' local integrity hashes. This does not prove real-world truth.'}else if(/receipt|record|note/i.test(q)){const r=await create(q);s='Created local receipt: '+r.id}else if(/device|capabilit|system/i.test(q)){s='Online: '+navigator.onLine+'; secure: '+isSecureContext+'; voice recognition: '+!!(window.SpeechRecognition||window.webkitSpeechRecognition)}else {const remote=await window.buddyRemote(q);s=remote||'I am Buddy’s local interface. I can create or verify receipts and inspect this device. Sign in and connect the model service for AI responses.'}message(s);say(s);if(window.buddyCompanion&&!$('speak').checked)window.buddyCompanion.mode('')}function eject(r){activeReceipt=r;returnFocus=document.activeElement;const stage=$('receiptStage'),paper=$('receiptPaper');$('receiptStatus').textContent='● ACTION RECORDED — LOCAL INTEGRITY';$('receiptAction').textContent=r.body?.payload?.text||'Action recorded';$('receiptDate').textContent=r.body?.payload?.createdAt||'';$('receiptId').textContent=r.id;$('receiptDisclaimer').textContent='SHA-256 checks data integrity only. Identity, truth and remote execution are not certified.';stage.style.display='flex';stage.classList.add('show');stage.setAttribute('aria-hidden','false');paper.classList.remove('eject');void paper.offsetWidth;paper.classList.add('eject');$('receiptClose').focus()}function closeReceipt(){const stage=$('receiptStage');stage.classList.remove('show');stage.style.display='none';stage.setAttribute('aria-hidden','true');if(returnFocus&&returnFocus.focus)returnFocus.focus()}function render(){const e=$('receiptList');e.replaceChildren();receipts.slice().reverse().forEach(r=>{const box=document.createElement('div');box.className='glass stack';const label=document.createElement('div');label.textContent=(r.body?.payload?.text||'Receipt').slice(0,140);const id=document.createElement('small');id.textContent=r.id;const b=document.createElement('button');b.textContent='Verify integrity';b.onclick=async()=>{eject(r);$('receiptStatus').textContent=await verify(r)?'● INTEGRITY VERIFIED':'● INTEGRITY FAILED'};box.append(label,id,b);e.append(box)})}try{const x=JSON.parse(localStorage.getItem(KEY)||'[]');receipts=Array.isArray(x)?x.slice(0,1000):[]}catch{}render();document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===b.dataset.tab));document.querySelectorAll('[data-tab]').forEach(v=>v.classList.toggle('active',v===b))});$('askform').onsubmit=e=>{e.preventDefault();ask($('prompt').value)};$('create').onclick=async()=>{const s=$('note').value.trim();if(!s)return notice('Enter a note');await create(s);$('note').value='';notice('Receipt saved locally')};$('export').onclick=()=>download('i-the-one-receipts.json',receipts);$('import').onchange=async e=>{const f=e.target.files[0];if(!f||f.size>5e6)return notice('File too large');try{const arr=JSON.parse(await f.text());const items=Array.isArray(arr)?arr:[arr];if(items.length>500)throw Error('Too many records');for(const r of items)if(!(await verify(r)))throw Error('Invalid receipt');const ids=new Set(receipts.map(r=>r.id));for(const r of items)if(!ids.has(r.id)){receipts.push(r);ids.add(r.id)}save();notice('Imported '+items.length+' receipts')}catch(err){notice(err.message)}};$('mic').onclick=()=>{const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return notice('Speech input unavailable');const r=new SR();r.onresult=e=>ask(e.results[0][0].transcript);r.onerror=e=>notice(e.error);r.start()};$('capabilities').textContent='Online: '+navigator.onLine+' · Secure context: '+isSecureContext;$('connection').textContent=navigator.onLine?'Local core · online':'Local core · offline';window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installPrompt=e});$('install').onclick=async()=>installPrompt?installPrompt.prompt():notice('Use browser Share → Add to Home Screen');if('serviceWorker'in navigator&&isSecureContext)navigator.serviceWorker.register('sw.js').catch(()=>{});
$('receiptClose').onclick=closeReceipt;$('receiptStage').addEventListener('click',e=>{if(e.target===$('receiptStage'))closeReceipt()});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('receiptStage').classList.contains('show'))closeReceipt()});$('receiptVerify').onclick=async()=>{if(!activeReceipt)return;const ok=await verify(activeReceipt);$('receiptStatus').textContent=ok?'● INTEGRITY VERIFIED':'● INTEGRITY FAILED';notice(ok?'Receipt hash matches':'Receipt hash mismatch')};$('receiptSave').onclick=()=>{if(activeReceipt)download('i-receipt-'+activeReceipt.id.slice(7,19)+'.json',activeReceipt)};$('receiptShare').onclick=async()=>{if(!activeReceipt)return;const content=JSON.stringify(activeReceipt,null,2);if(navigator.share){try{await navigator.share({title:'i™ THE ONE receipt',text:content})}catch(e){if(e.name!=='AbortError')notice('Share unavailable')}}else if(navigator.clipboard&&isSecureContext){try{await navigator.clipboard.writeText(content);notice('Receipt copied')}catch{notice('Copy unavailable')}}else notice('Use Save JSON')};

/* i™ Live Update Mode v1: version polling + safe service worker activation. */
(()=>{
const UPDATE_PREF='i-auto-update-v1', VERSION_URL='./version.json';
let registration=null,waiting=false,updating=false,lastVersion='2026.10.15.4';
const banner=$('updateBanner'),info=$('updateInfo'),pref=$('autoUpdate');
localStorage.setItem('i-version-last-seen',lastVersion);pref.checked=localStorage.getItem(UPDATE_PREF)!=='off';
pref.onchange=()=>{localStorage.setItem(UPDATE_PREF,pref.checked?'on':'off');if(pref.checked)checkUpdates(true)};
const showUpdate=()=>{waiting=true;banner.classList.add('show');$('updateState').textContent='🧾 New i™ version is ready to install';info.textContent='Update available · Your local receipts remain on this device'};
const checkUpdates=async(manual=false)=>{
 if(!navigator.onLine){if(manual)notice('Offline · update will check when connected');return}
 try{
  const response=await fetch(VERSION_URL+'?t='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('Version endpoint unavailable');
  const data=await response.json();
  if(typeof data.version!=='string')throw Error('Invalid version');
  const stored=localStorage.getItem('i-version-last-seen')||lastVersion;
  info.textContent='Installed version: '+stored+' · Latest: '+data.version;
  if(data.version!==stored){showUpdate();}else if(manual)notice('i™ is up to date');
  if(registration){await registration.update();if(registration.waiting)showUpdate()}
 }catch(e){info.textContent='Update check unavailable · offline app remains usable';if(manual)notice('Could not check updates')}
};
$('checkUpdates').onclick=()=>checkUpdates(true);
$('laterUpdate').onclick=()=>banner.classList.remove('show');
$('applyUpdate').onclick=async()=>{
 if(updating)return;updating=true;
 $('applyUpdate').disabled=true;$('updateState').textContent='Preparing update…';
 if(registration){await registration.update().catch(()=>{});if(registration.waiting){registration.waiting.postMessage({type:'SKIP_WAITING'});return}}
 // No SW waiting: navigate to newest network version, preserving localStorage.
 location.reload();
};
let controlled=Boolean(navigator.serviceWorker?.controller);
navigator.serviceWorker?.addEventListener('controllerchange',()=>{if(controlled&&updating){location.reload()}controlled=true});
if('serviceWorker' in navigator&&isSecureContext){
 navigator.serviceWorker.ready.then(reg=>{
  registration=reg;
  if(reg.waiting)showUpdate();
  reg.addEventListener('updatefound',()=>{
   const worker=reg.installing;
   worker?.addEventListener('statechange',()=>{if(worker.state==='installed'&&navigator.serviceWorker.controller)showUpdate()});
  });
  checkUpdates(false);
 }).catch(()=>{info.textContent='Update service unavailable'});
}else info.textContent='Automatic updates require HTTPS and service worker support';
window.addEventListener('online',()=>{if(pref.checked)checkUpdates(false)});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&pref.checked)checkUpdates(false)});
setInterval(()=>{if(pref.checked&&!document.hidden)checkUpdates(false)},5*60*1000);
})();
/* Free accounts, authenticated Buddy and local-first community preview */
(()=>{
const cfg=window.I_CONFIG||{}, key='i-community-local-v1';
let token='',refresh='',expires=0,posts=[];
try{posts=JSON.parse(localStorage.getItem(key)||'[]');if(!Array.isArray(posts))posts=[]}catch{posts=[]}
const status=$('accountStatus');
const configured=Boolean(cfg.supabaseUrl&&cfg.supabasePublishableKey);
const setStatus=()=>{status.textContent=!configured?'Free account service not configured yet':token?'Signed in · Free account':'Free account service available · Sign in or register'};
const renderPosts=()=>{const feed=$('communityFeed');feed.replaceChildren();posts.slice().reverse().forEach(post=>{const card=document.createElement('article');card.className='glass stack';const meta=document.createElement('div');meta.className='community-meta';meta.textContent='My device · '+new Date(post.created).toLocaleString();const content=document.createElement('div');content.className='community-post';content.textContent=post.text;card.append(meta,content);feed.append(card)})};
renderPosts();setStatus();
$('publishPost').onclick=()=>{const text=$('postText').value.trim();if(!text)return notice('Write something first');posts.push({text:text.slice(0,1200),created:new Date().toISOString()});posts=posts.slice(-200);try{localStorage.setItem(key,JSON.stringify(posts))}catch{return notice('Device storage unavailable')}renderPosts();$('postText').value='';notice('Saved on this device · Not published publicly')};
async function auth(path,body){
 if(!configured){notice('Account service not configured');return}
 try{
  const res=await fetch(cfg.supabaseUrl.replace(/\/$/,'')+'/auth/v1/'+path,{method:'POST',headers:{'apikey':cfg.supabasePublishableKey,'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await res.json();if(!res.ok)throw Error(data.msg||data.error_description||data.message||'Authentication failed');
  if(data.access_token){token=data.access_token;refresh=data.refresh_token||'';expires=Date.now()+(data.expires_in||3600)*1000;notice('Signed in successfully')}
  else notice('Check your email to confirm your free account');
  setStatus()
 }catch(e){notice(String(e.message).slice(0,130))}
}
$('createAccount').onclick=()=>{const email=$('accountEmail').value.trim(),password=$('accountPassword').value;if(!email.includes('@')||password.length<8)return notice('Enter valid email and password (8+ characters)');auth('signup',{email,password})};
$('signIn').onclick=()=>auth('token?grant_type=password',{email:$('accountEmail').value.trim(),password:$('accountPassword').value});
$('signOut').onclick=async()=>{if(token&&configured){await fetch(cfg.supabaseUrl.replace(/\/$/,'')+'/auth/v1/logout',{method:'POST',headers:{apikey:cfg.supabasePublishableKey,Authorization:'Bearer '+token}}).catch(()=>{})}token='';refresh='';expires=0;setStatus();notice('Signed out')};
window.buddyRemote=async(q)=>{
 if(!token||!cfg.buddyApiUrl||Date.now()>expires){if(token&&Date.now()>expires){token='';setStatus()}return null}
 try{
  const res=await fetch(cfg.buddyApiUrl.replace(/\/$/,'')+'/v1/actions',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({request:q})});
  if(!res.ok){notice('Buddy API unavailable ('+res.status+')');return null}
  const data=await res.json();if(data.receipt){notice('Signed receipt saved remotely · '+data.receipt.id.slice(0,12))}
  return typeof data.answer==='string'?data.answer:null
 }catch{return null}
};
})();
