/* iMobile Live: real browser WebRTC media, manual exchange of session descriptions.
   No telecom/carrier claim; requires two consenting devices and viable network route. */
(()=>{'use strict';const main=document.querySelector('main'),nav=document.querySelector('nav');if(!main||!nav)return;
const pane=document.createElement('section');pane.id='imobile-live';pane.className='view';
pane.innerHTML='<div class="glass" style="background:linear-gradient(140deg,#082d2b,#0b1827);border:1px solid #75e7c1"><small>i™ THE ONE · JUST ASK BUDDY™</small><h1>📞 iMobile Live</h1><p>Real person-to-person audio, video and messaging using WebRTC. Two devices must explicitly exchange invitations and grant microphone/camera permissions. No phone number or carrier call is created.</p><div class="imobile-quick"><h2>Call someone</h2><p>Choose a contact or enter a phone number/email to send an invitation.</p><button type="button" id="ilContacts">👥 Choose contacts</button><label>Import contacts (.vcf)<input id="ilVcf" type="file" accept=".vcf,text/vcard"></label><label>Recipient<input id="ilRecipient" type="text" autocomplete="off" placeholder="Phone, email or contact name" maxlength="150"></label><div id="ilContactsList"></div><button id="ilQuickVideo" class="primary">📹 Video invite</button><button id="ilQuickAudio">📞 Audio invite</button><p id="ilQuickState" role="status">Invitations use the iPhone share sheet; they are not cellular calls.</p></div><details><summary>Advanced connection / troubleshooting</summary><div style="display:flex;flex-wrap:wrap;gap:8px"><button class="primary" id="ilStartVideo">📹 Start video call</button><button id="ilStartAudio">📞 Start audio call</button><button id="ilJoin">Join invitation</button><button id="ilHang">End call</button></div><p id="ilState" role="status">Ready · no connected peer</p><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px"><div><h3>You</h3><video id="ilLocal" autoplay muted playsinline style="width:100%;border-radius:12px;background:#000;min-height:160px"></video></div><div><h3>Other person</h3><video id="ilRemote" autoplay playsinline style="width:100%;border-radius:12px;background:#000;min-height:160px"></video></div></div><h2>Encrypted call invitation</h2><p>Caller: start a call, copy the invitation and send it privately. Recipient: paste it, press Join, then send the resulting answer back. Caller: paste that answer and press Complete connection. Invitations contain WebRTC network metadata; only share them with the intended person. TURN relay credentials are not yet provisioned.</p><label>Your invitation / answer<textarea id="ilOut" readonly rows="6" style="width:100%"></textarea></label><div style="display:flex;gap:8px;flex-wrap:wrap"><button id="ilShare" class="primary">📤 Share invitation · AirDrop / Messages / Mail</button><button id="ilCopy">Copy my code</button></div><p class="fine">The iPhone share sheet lets you choose AirDrop, a phone contact through Messages, or email. On unsupported browsers, copy the invitation instead. The recipient must return their answer.</p><label>Or import a received invitation file<input id="ilFile" type="file" accept=".json,application/json,text/plain"></label><label>Paste their invitation / answer<textarea id="ilIn" rows="6" style="width:100%"></textarea></label><button id="ilComplete">Complete connection</button><h2>💬 Live chat</h2><div id="ilMessages" role="log" style="min-height:80px;max-height:190px;overflow:auto;background:#041b20;padding:12px;border-radius:12px"></div><input id="ilText" aria-label="Chat message" maxlength="1000" placeholder="Message peer"><button id="ilSend">Send message</button></details><p class="fine">Real media and data, not a simulator. This version uses manual signaling, STUN and DTLS-SRTP. Some networks require a configured TURN relay for calls to connect. Not for emergency calling. Browser/PWA cannot dial cellular numbers or automatically discover nearby users.</p></div>';
main.append(pane);const navBtn=document.createElement('button');navBtn.type='button';navBtn.dataset.tab='imobile-live';navBtn.textContent='📞 Calls';navBtn.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v===pane));nav.querySelectorAll('[data-tab]').forEach(v=>v.classList.toggle('active',v===navBtn))};nav.append(navBtn);nav.style.overflowX='auto';nav.style.justifyContent='flex-start';
const $=id=>document.getElementById(id);let pc=null,local=null,channel=null;const state=s=>$('ilState').textContent=s;
const add=(who,msg)=>{const item=document.createElement('p');item.textContent=who+': '+msg;$('ilMessages').append(item);$('ilMessages').scrollTop=$('ilMessages').scrollHeight};
function stop(){if(channel)channel.close();channel=null;if(pc)pc.close();pc=null;if(local)local.getTracks().forEach(t=>t.stop());local=null;$('ilLocal').srcObject=null;$('ilRemote').srcObject=null;state('Call ended');}
function createPeer(){if(!window.RTCPeerConnection)throw Error('WebRTC not supported');const p=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});p.ontrack=e=>{$('ilRemote').srcObject=e.streams[0];state('Remote media received · real WebRTC')};p.onconnectionstatechange=()=>state('Peer connection: '+p.connectionState);p.oniceconnectionstatechange=()=>{if(p.iceConnectionState==='failed')state('Connection failed. Network may require a TURN relay.')};p.ondatachannel=e=>bindChannel(e.channel);return p}
function bindChannel(ch){channel=ch;ch.onopen=()=>state('Connected · encrypted peer chat open');ch.onmessage=e=>add('Peer',String(e.data).slice(0,1000));ch.onclose=()=>state('Peer chat closed')}
async function media(video){if(!navigator.mediaDevices?.getUserMedia)throw Error('Camera/microphone unsupported or insecure origin');try{return await navigator.mediaDevices.getUserMedia({audio:true,video:video?{facingMode:'user'}:false})}catch(e){throw Error('Media permission denied or device unavailable: '+e.name)}}
async function waitIce(p){if(p.iceGatheringState==='complete')return;await new Promise(resolve=>{const timer=setTimeout(done,11000);function done(){clearTimeout(timer);p.removeEventListener('icegatheringstatechange',on);resolve()}function on(){if(p.iceGatheringState==='complete')done()}p.addEventListener('icegatheringstatechange',on)})}
async function start(video){stop();try{local=await media(video);$('ilLocal').srcObject=local;pc=createPeer();local.getTracks().forEach(t=>pc.addTrack(t,local));bindChannel(pc.createDataChannel('iChirp'));await pc.setLocalDescription(await pc.createOffer());await waitIce(pc);$('ilOut').value=JSON.stringify({type:'offer',sdp:pc.localDescription.sdp});state('Share the invitation with the other person. Await their answer.')}catch(e){stop();state('Cannot start: '+e.message)}}
async function join(){stop();try{const data=JSON.parse($('ilIn').value);if(data.type!=='offer'||typeof data.sdp!=='string'||data.sdp.length>150000)throw Error('Invalid invitation');local=await media(data.sdp.includes('m=video'));$('ilLocal').srcObject=local;pc=createPeer();local.getTracks().forEach(t=>pc.addTrack(t,local));await pc.setRemoteDescription({type:'offer',sdp:data.sdp});await pc.setLocalDescription(await pc.createAnswer());await waitIce(pc);$('ilOut').value=JSON.stringify({type:'answer',sdp:pc.localDescription.sdp});state('Send your answer to the caller. The call will connect when their device receives it.')}catch(e){stop();state('Cannot join: '+e.message)}}
const contacts=[];
function drawContacts(){
 const host=$('ilContactsList');host.replaceChildren();
 for(const c of contacts.slice(0,60)){const b=document.createElement('button');b.type='button';b.textContent=c.name+(c.phone?' · '+c.phone:c.email?' · '+c.email:'');b.onclick=()=>{$('ilRecipient').value=c.phone||c.email||c.name;state('Contact selected; choose audio or video invitation.')};host.append(b)}
}
$('ilContacts').onclick=async()=>{
 if(!('contacts' in navigator)&&!navigator.contacts){$('ilQuickState').textContent='Direct contacts access is unavailable in this iPhone PWA. Import a .vcf exported from Contacts or enter an address.';return}
 try{const picked=await navigator.contacts.select(['name','tel','email'],{multiple:true});for(const item of picked){contacts.push({name:item.name?.[0]||'Contact',phone:item.tel?.[0]||'',email:item.email?.[0]||''})}drawContacts();$('ilQuickState').textContent=contacts.length+' contacts loaded locally; not uploaded.'}
 catch(e){$('ilQuickState').textContent='Contact permission unavailable or cancelled.'}
};
$('ilVcf').onchange=async e=>{
 const file=e.target.files?.[0];if(!file)return;
 if(file.size>1048576){$('ilQuickState').textContent='Choose a vCard under 1 MB.';return}
 const raw=await file.text(),cards=raw.split(/BEGIN:VCARD/i).slice(1,101);
 for(const card of cards){const lines=card.replace(/\\r?\\n[ \\t]/g,'').split(/\\r?\\n/),find=prefix=>{const l=lines.find(x=>x.toUpperCase().split(':')[0].startsWith(prefix));return l?l.slice(l.indexOf(':')+1).trim():''};const name=find('FN')||find('N').replace(/;/g,' '),phone=find('TEL'),email=find('EMAIL');if(name&&(phone||email))contacts.push({name,phone,email})}
 drawContacts();$('ilQuickState').textContent=contacts.length+' contacts imported locally. No contact data uploaded.';e.target.value='';
};
async function quick(video){
 const recipient=$('ilRecipient').value.trim();
 if(!recipient){$('ilQuickState').textContent='Choose a contact or type a phone number or email first.';return}
 await start(video);
 if(!pc||!$('ilOut').value){$('ilQuickState').textContent='Camera/microphone or WebRTC unavailable.';return}
 $('ilQuickState').textContent='Choose Messages, Mail or AirDrop to invite '+recipient+'. An answer is still required.';
 $('ilShare').click();
}
$('ilQuickVideo').onclick=()=>quick(true);
$('ilQuickAudio').onclick=()=>quick(false);
$('ilStartVideo').onclick=()=>start(true);$('ilStartAudio').onclick=()=>start(false);$('ilJoin').onclick=join;$('ilHang').onclick=stop;
$('ilComplete').onclick=async()=>{try{if(!pc||pc.signalingState!=='have-local-offer')throw Error('Start a call first');const data=JSON.parse($('ilIn').value);if(data.type!=='answer'||typeof data.sdp!=='string'||data.sdp.length>150000)throw Error('Invalid answer');await pc.setRemoteDescription({type:'answer',sdp:data.sdp});state('Connecting peer…')}catch(e){state('Connection error: '+e.message)}};
$('ilShare').onclick=async()=>{
 const payload=$('ilOut').value.trim();
 if(!payload){state('Start or join a call to generate an invitation first.');return}
 try{
  const parsed=JSON.parse(payload);
  if(!['offer','answer'].includes(parsed.type)||typeof parsed.sdp!=='string')throw Error('Invalid invitation');
  const title=parsed.type==='offer'?'iMobile call invitation':'iMobile call answer';
  const file=new File([payload],'imobile-'+parsed.type+'.json',{type:'application/json'});
  if(navigator.share){
   if(navigator.canShare&&navigator.canShare({files:[file]})){
    await navigator.share({title,text:'iMobile call signaling. Open i™ Calls and import this file. Share privately with your intended caller only.',files:[file]});
   }else{
    await navigator.share({title,text:payload});
   }
   state('Invitation handed to your device share sheet; delivery and call connection not yet verified.');
  }else if(navigator.clipboard){
   await navigator.clipboard.writeText(payload);
   state('Share sheet unavailable; signaling data copied for AirDrop, Messages, or email.');
  }else state('Sharing unavailable. Select and manually copy your invitation.');
 }catch(e){if(e.name==='AbortError'){state('Sharing cancelled.')}else state('Share failed: '+String(e.message).slice(0,150))}
};
$('ilFile').addEventListener('change',async event=>{
 const file=event.target.files?.[0];if(!file)return;
 if(file.size>170000){state('Invitation too large; limit 170 KB.');event.target.value='';return}
 try{
  const raw=await file.text(),data=JSON.parse(raw);
  if(!['offer','answer'].includes(data.type)||typeof data.sdp!=='string'||data.sdp.length>150000)throw Error('Unsupported invitation');
  $('ilIn').value=JSON.stringify({type:data.type,sdp:data.sdp});
  state(data.type==='offer'?'Received an offer. Select Join invitation.':'Received an answer. Select Complete connection.');
 }catch(e){state('Could not load invitation file: '+e.message)}
 event.target.value='';
});
$('ilCopy').onclick=async()=>{try{await navigator.clipboard.writeText($('ilOut').value);state('Invitation copied; share privately')}catch{state('Select the invitation field and copy manually')}};
$('ilSend').onclick=()=>{const msg=$('ilText').value.trim();if(!msg)return;if(!channel||channel.readyState!=='open'){state('No real connected peer to message');return}channel.send(msg);add('You',msg);$('ilText').value=''};
window.addEventListener('pagehide',stop);
})();