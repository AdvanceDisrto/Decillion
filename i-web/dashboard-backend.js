/* i™ THE ONE dashboard real backend bridge. Session kept in memory only.
 * Generated action receipts prove execution metadata/integrity, NOT factual truth.
 */
(()=>{'use strict';
const cfg=window.I_CONFIG||{};
const $=id=>document.getElementById(id);
let token='',refreshToken='',expiry=0,last=null;
const el=(tag,attributes={},text='')=>{const n=document.createElement(tag);for(const [k,v] of Object.entries(attributes))n.setAttribute(k,v);n.textContent=text;return n};
const api=(cfg.buddyApiUrl||'').replace(/\/$/,'');
const authHost=(cfg.supabaseUrl||'').replace(/\/$/,'');
const pub=cfg.supabasePublishableKey||'';
const modal=el('dialog',{id:'buddyLoginDialog','aria-label':'Buddy secure sign-in'});
modal.innerHTML='<form method="dialog" style="display:grid;gap:12px;min-width:min(340px,80vw)"><h2>🔐 Buddy Identity</h2><p>Sign in with your existing Buddy account. No credentials are saved in this dashboard.</p><label>Email <input id="dashEmail" type="email" autocomplete="email" required></label><label>Password <input id="dashPassword" type="password" autocomplete="current-password" required></label><p id="dashAuthStatus" role="status"></p><button id="dashLogin" type="button">SIGN IN</button><button type="submit">Cancel</button></form>';
document.body.appendChild(modal);
const style=el('style');style.textContent='#buddyLoginDialog{border:1px solid #77ffc6;background:#061f21;color:#e0ffec;border-radius:20px;box-shadow:0 0 40px #3dffcf80;max-width:min(94vw,460px)}#buddyLoginDialog::backdrop{background:#010906cc;backdrop-filter:blur(9px)}#buddyLoginDialog input{display:block;width:100%;padding:12px;margin-top:6px;border-radius:9px;border:1px solid #50bba0;background:#021110;color:white}#buddyLoginDialog button{background:#13513f;color:#eaffef;border:1px solid #70fcae;padding:12px;border-radius:9px}.backend-pill{display:block;margin-top:9px;color:#ffca78;font-size:11px}.backend-answer{position:relative;padding:16px;margin-top:13px;background:#061d1ae8;border:1px solid #6dfcc3;border-radius:15px;max-height:225px;overflow:auto;white-space:pre-wrap;font-size:13px;line-height:1.45}';document.head.appendChild(style);
const badge=el('p',{class:'backend-pill',id:'backendConnection'},'● Checking Buddy backend...');
document.querySelector('.status .checks')?.after(badge);
const reply=el('div',{class:'backend-answer',id:'backendReply','aria-live':'polite'},'Buddy responses will appear here after you sign in.');document.querySelector('.buddy-actions')?.after(reply);
const status=(value)=>{if($('backendConnection'))$('backendConnection').textContent=value};
const show=(s)=>{if($('backendReply'))$('backendReply').textContent=s};
const showLogin=()=>{if(!authHost||!pub){show('Buddy sign-in is not configured. Open the Buddy app to review account setup.');return}modal.showModal()};
function assign(r){
 last=r;
 const body=r.body||{};
 if($('actionText'))$('actionText').textContent=(body.request||'Authenticated model response').slice(0,55);
 if($('receiptId'))$('receiptId').textContent=r.id?'#'+r.id.slice(0,18):'NO RECEIPT ID';
 if($('receiptTime'))$('receiptTime').textContent=body.created_at||new Date().toISOString();
 if($('rstatus'))$('rstatus').textContent='SIGNED ACTION RECORD · NOT FACT CERTIFIED';
 status('● Backend response returned an Ed25519-signed action record (signature not verified here).');
}
async function authenticate(){
 const email=$('dashEmail').value.trim(),password=$('dashPassword').value;
 if(!email||!password)return;
 $('dashAuthStatus').textContent='Authenticating...';
 try{
  const r=await fetch(authHost+'/auth/v1/token?grant_type=password',{method:'POST',headers:{apikey:pub,'Content-Type':'application/json'},body:JSON.stringify({email,password})});
  const d=await r.json();if(!r.ok||!d.access_token)throw Error('Sign-in failed. Verify your Buddy credentials.');
  token=d.access_token;refreshToken=d.refresh_token||'';expiry=Date.now()+Math.max(30,(d.expires_in||300)-45)*1000;
  $('dashPassword').value='';modal.close();status('● Buddy identity authenticated.');show('Signed in as '+email+'. Ask Buddy a question.');
 }catch(e){$('dashAuthStatus').textContent=e.message}
}
$('dashLogin').addEventListener('click',authenticate);
async function currentToken(){
 if(!token)return null;
 if(Date.now()<expiry)return token;
 if(!refreshToken)return null;
 try{
  const r=await fetch(authHost+'/auth/v1/token?grant_type=refresh_token',{method:'POST',headers:{apikey:pub,'Content-Type':'application/json'},body:JSON.stringify({refresh_token:refreshToken})});
  const d=await r.json();if(!r.ok||!d.access_token)throw Error('session expired');
  token=d.access_token;refreshToken=d.refresh_token||'';expiry=Date.now()+Math.max(30,(d.expires_in||300)-45)*1000;return token;
 }catch{token='';refreshToken='';return null}
}
async function askReal(q){
 if(!api){show('Buddy API URL is not configured in config.js.');return}
 const current=await currentToken();if(!current){showLogin();return}
 const form=$('askform');const button=form?.querySelector('[type="submit"]');if(button)button.disabled=true;
 show('Connecting to Buddy...');status('● Sending authenticated request to Buddy API');
 try{
  const r=await fetch(api+'/v1/actions',{method:'POST',headers:{Authorization:'Bearer '+current,'Content-Type':'application/json'},body:JSON.stringify({request:q.slice(0,3500),model:'buddy'})});
  const d=await r.json().catch(()=>({}));
  if(!r.ok)throw Error('Buddy API returned HTTP '+r.status+' · '+String(d.detail||'Service unavailable'));
  show(typeof d.answer==='string'?d.answer:'Buddy returned no text.');
  if(d.receipt)assign(d.receipt);else status('● Model returned output without a signed receipt.');
 }catch(e){show(String(e.message));status('● Buddy request failed or provider not configured. No receipt issued.')}
 finally{if(button)button.disabled=false}
}
async function health(){
 if(!api)return status('● Buddy backend URL not configured');
 try{
  const r=await fetch(api+'/health',{signal:AbortSignal.timeout(7500)});
  if(!r.ok)throw Error('HTTP '+r.status);
  const d=await r.json();
  status('● API '+(d.status==='ok'?'reachable':'unready')+' · model '+(d.model_configured?'configured':'not configured')+' · signing '+(d.storage_auth_signing_configured?'configured':'not configured'));
 }catch{status('● Backend not reachable from this browser')}
}
const form=$('askform');
if(form){const replacement=form.cloneNode(true);form.replaceWith(replacement);replacement.addEventListener('submit',e=>{e.preventDefault();const text=$('ask').value.trim();if(text)askReal(text)})}
const talk=$('talk');if(talk)talk.onclick=()=>{if(!token)showLogin();else $('ask')?.focus()};
document.querySelectorAll('.action-dock a').forEach(a=>{if(a.textContent.includes('Ask me anything'))a.onclick=e=>{e.preventDefault();if(!token)showLogin();else $('ask')?.focus()}});
const showReceipt=()=>{if(last)show(JSON.stringify(last,null,2));else show('No signed API receipt yet. Sign in and ask Buddy first.')};
document.querySelectorAll('.receipt-controls a').forEach(a=>{a.addEventListener('click',e=>{if(last){e.preventDefault();showReceipt()}})});
health();setInterval(()=>{if(!document.hidden)health()},120000);
})();
