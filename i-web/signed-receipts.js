/* Signed i™ receipt viewer — verify local hash and Ed25519 signature without promoting a public key to trusted identity. */
(()=>{
const $=id=>document.getElementById(id),KEY='i-signed-receipts-v1';
let signed=[];
try{const arr=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(arr))signed=arr}catch{}
function bytesFromHex(hex){const out=new Uint8Array(hex.length/2);for(let i=0;i<out.length;i++)out[i]=parseInt(hex.slice(i*2,i*2+2),16);return out}
function fromB64(v){return Uint8Array.from(atob(v),c=>c.charCodeAt(0))}
function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v)}
async function verifyReceipt(r){
 if(!r||!r.body||typeof r.id!=='string'||!r.signature||!r.public_key)return false;
 const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(r.body))));
 const hex=Array.from(digest,b=>b.toString(16).padStart(2,'0')).join('');
 if(hex!==r.id)return false;
 const key=await crypto.subtle.importKey('raw',fromB64(r.public_key),{name:'Ed25519'},false,['verify']);
 return crypto.subtle.verify({name:'Ed25519'},key,fromB64(r.signature),digest)
}
function show(r){
 if(!r?.body)return;
 signed=signed.filter(v=>v.id!==r.id);signed.push(r);signed=signed.slice(-100);
 try{localStorage.setItem(KEY,JSON.stringify(signed))}catch{}
 const stage=$('receiptStage'),paper=$('receiptPaper');
 if(!stage||!paper)return;
 $('receiptStatus').textContent='● SERVER SIGNATURE PRESENT — VERIFY TO CHECK';
 $('receiptAction').textContent=(r.body.request||'Model response')+'\n\n'+String(r.body.result||'').slice(0,1400);
 $('receiptDate').textContent=r.body.created_at||'';
 $('receiptId').textContent='sha256:'+r.id;
 $('receiptDisclaimer').textContent='Ed25519 verifies integrity against the embedded public key; independently validating the issuer key and real-world execution still requires external evidence.';
 stage.classList.add('show');stage.style.display='flex';stage.setAttribute('aria-hidden','false');
 paper.classList.remove('eject');void paper.offsetWidth;paper.classList.add('eject');$('receiptClose')?.focus();
 $('receiptVerify').onclick=async()=>{try{const valid=await verifyReceipt(r);$('receiptStatus').textContent=valid?'● SIGNATURE VALID — KEY IDENTITY UNCONFIRMED':'● SIGNATURE OR CONTENT INVALID'}catch{$('receiptStatus').textContent='● SIGNATURE CHECK NOT SUPPORTED ON THIS DEVICE'}};
 $('receiptSave').onclick=()=>{const blob=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='i-signed-'+r.id.slice(0,14)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)};
 $('receiptShare').onclick=async()=>{if(navigator.share){try{await navigator.share({title:'i™ signed receipt',text:JSON.stringify(r)})}catch{}}};
}
const localHandlers={verify:$('receiptVerify')?.onclick,save:$('receiptSave')?.onclick,share:$('receiptShare')?.onclick};
window.addEventListener('i-local-receipt-open',()=>{for(const [name,el] of [['verify','receiptVerify'],['save','receiptSave'],['share','receiptShare']]){if($(el))$(el).onclick=localHandlers[name]}});
window.showSignedReceipt=show;
const holder=document.getElementById('signedReceiptList');
function render(){
 if(!holder)return;holder.replaceChildren();
 const title=document.createElement('h2');title.textContent='My signed Buddy receipts';holder.append(title);
 if(!signed.length){const info=document.createElement('p');info.className='fine';info.textContent='No server-signed receipts on this device yet.';holder.append(info);return}
 for(const r of signed.slice().reverse()){
  const card=document.createElement('div');card.className='glass stack';
  const line=document.createElement('span');line.textContent=(r.body?.request||'AI action').slice(0,140);
  const b=document.createElement('button');b.textContent='Inspect signature';b.onclick=()=>show(r);
  card.append(line,b);holder.append(card)
 }
}
render();
const previous=window.showSignedReceipt;
window.showSignedReceipt=r=>{previous(r);render()};
})();
