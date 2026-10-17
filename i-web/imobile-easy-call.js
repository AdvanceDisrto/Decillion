/* iMobile Easy Call: real authenticated WebRTC signaling, no invitation JSON.
   Requires working i account, reachable backend, microphone permission, STUN/TURN. */
(()=>{'use strict';const main=document.querySelector('main'),nav=document.querySelector('nav');if(!main||!nav)return;
const page=document.createElement('section');page.className='view';page.id='imobile-easy';
page.innerHTML='<div class="glass" style="border:1px solid #74ebc2;background:linear-gradient(145deg,#052f2a,#0c1428)"><small>i™ · JUST ASK BUDDY™</small><h1>📞 iMobile</h1><p>Call someone in two taps. Share an invitation through Messages, AirDrop or Mail. Both people sign in to i™.</p><div style="display:flex;flex-wrap:wrap;gap:9px"><button id="ieAudio" class="primary">📞 Audio Call</button><button id="ieVideo" class="primary">📹 Video Call</button><button id="ieEnd">End</button></div><p id="ieStatus" role="status">Ready. Sign in before calling.</p><button id="ieEnableAlerts" type="button">🔔 Enable iChirp sounds</button><span id="ieAlertInfo" role="status">Sounds off until enabled</span><div id="ieIncoming" hidden><h2>📲 Incoming iMobile call</h2><button id="ieAccept" class="primary">Accept & Connect</button><button id="ieDecline">Decline</button></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:16px"><div><h3>You</h3><video autoplay muted playsinline id="ieSelf" style="width:100%;background:#000;border-radius:14px;min-height:130px"></video></div><div><h3>Other person</h3><video autoplay playsinline id="iePeer" style="width:100%;background:#000;border-radius:14px;min-height:130px"></video></div></div><div style="margin:12px 0;padding:14px;border:1px solid #398d82;border-radius:18px"><h2>📻 iChirp Walkie-Talkie</h2><p>While a WebRTC call is connected, hold the button to speak. Releasing mutes your microphone.</p><button type="button" id="iePTTMode">Enable PTT mode</button><button type="button" id="ieTalk" disabled style="touch-action:none;user-select:none;min-height:72px;width:100%;border-radius:26px;background:#006e68;color:#fff;font-size:1.3em">🎙️ Hold to talk</button><span id="iePTTState" role="status">PTT off</span></div><button id="ieShare" hidden>📤 Share invitation again</button><p class="fine">Internet calling only; cannot dial the telephone network or receive background ringing yet. Calls require a working i™ account and compatible network. No TURN relay provisioned: some carrier/NAT combinations cannot connect. Not for emergencies.</p></div>';
main.append(page);const tab=document.createElement('button');tab.dataset.tab='imobile-easy';tab.type='button';tab.textContent='📞 Easy Call';tab.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v===page));nav.querySelectorAll('[data-tab]').forEach(v=>v.classList.toggle('active',v===tab))};nav.append(tab);nav.style.overflowX='auto';nav.style.justifyContent='flex-start';
const $=id=>document.getElementById(id),status=text=>$('ieStatus').textContent=text;
let conn=null,media=null,room=null,mode='audio',caller=false,seen=0,timer=null,live=false;
let chirpEnabled=false,chirpAudio=null;
let pttMode=false;
function talk(active){
 if(!pttMode||!media||conn?.connectionState!=='connected'){if(active)status('Start and connect a real call first.');return}
 for(const track of media.getAudioTracks())track.enabled=!!active;
 $('iePTTState').textContent=active?'🔴 Transmitting microphone':'🟢 Listening · microphone muted';
 $('ieTalk').textContent=active?'🔴 Speaking · release to listen':'🎙️ Hold to talk';
}
function resetPtt(){
 pttMode=false;$('iePTTMode').textContent='Enable PTT mode';$('ieTalk').disabled=true;
 $('ieTalk').textContent='🎙️ Hold to talk';$('iePTTState').textContent='PTT off';
}
$('iePTTMode').onclick=()=>{
 if(!media||conn?.connectionState!=='connected'){status('Establish a real audio/video call before enabling walkie-talkie mode.');return}
 pttMode=!pttMode;
 for(const t of media.getAudioTracks())t.enabled=!pttMode;
 $('ieTalk').disabled=!pttMode;
 $('iePTTMode').textContent=pttMode?'Disable PTT mode':'Enable PTT mode';
 $('iePTTState').textContent=pttMode?'🟢 Listening · hold to transmit':'PTT off · open microphone';
};
$('ieTalk').addEventListener('pointerdown',e=>{e.preventDefault();try{$('ieTalk').setPointerCapture(e.pointerId)}catch{}talk(true)});
for(const event of ['pointerup','pointercancel','lostpointercapture'])$('ieTalk').addEventListener(event,()=>talk(false));
window.addEventListener('blur',()=>talk(false));
document.addEventListener('visibilitychange',()=>{if(document.hidden)talk(false)});

async function chirp(){
 if(!chirpEnabled)return;
 try{
  const AudioCtx=window.AudioContext||window.webkitAudioContext;
  if(!AudioCtx)return;
  chirpAudio=chirpAudio||new AudioCtx();
  if(chirpAudio.state==='suspended')await chirpAudio.resume();
  const t=chirpAudio.currentTime;
  for(const [offset,freq] of [[0,960],[0.11,1240],[0.24,1040]]){
   const osc=chirpAudio.createOscillator(),gain=chirpAudio.createGain();
   osc.type='sine';osc.frequency.setValueAtTime(freq,t+offset);
   gain.gain.setValueAtTime(0.001,t+offset);
   gain.gain.exponentialRampToValueAtTime(0.12,t+offset+0.018);
   gain.gain.exponentialRampToValueAtTime(0.001,t+offset+0.10);
   osc.connect(gain);gain.connect(chirpAudio.destination);
   osc.start(t+offset);osc.stop(t+offset+0.11);
  }
 }catch{}
}
$('ieEnableAlerts').onclick=async()=>{
 chirpEnabled=true;await chirp();$('ieAlertInfo').textContent='iChirp enabled while this page is active. Background ringing needs native push/CallKit.';
};

const api=(path,method='GET',body=null)=>{if(!window.iMobileCallApi)throw Error('i™ sign-in not initialized');return window.iMobileCallApi(path,method,body)};
function clear(){resetPtt();live=false;if(timer){clearInterval(timer);timer=null}if(conn){conn.close();conn=null}if(media){media.getTracks().forEach(t=>t.stop());media=null}$('ieSelf').srcObject=null;$('iePeer').srcObject=null;$('ieIncoming').hidden=true;$('ieShare').hidden=true;}
async function end(){if(room){try{await api('rooms/'+room+'/signal','POST',{type:'hangup'})}catch{}}clear();room=null;history.replaceState(null,'',location.pathname+location.search);status('Call ended');}
function rtc(){if(!window.RTCPeerConnection)throw Error('WebRTC unavailable');const p=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});p.ontrack=e=>{$('iePeer').srcObject=e.streams[0];status('Peer media received')};p.onconnectionstatechange=()=>{if(p.connectionState==='connected')status('🟢 Connected — real encrypted call');else if(p.connectionState==='failed'||p.connectionState==='disconnected')status('Network connection '+p.connectionState)};p.oniceconnectionstatechange=()=>{if(p.iceConnectionState==='failed')status('Network cannot connect directly; TURN relay needed.')};return p}
async function capture(video){if(!navigator.mediaDevices?.getUserMedia)throw Error('Media not available in this browser');media=await navigator.mediaDevices.getUserMedia({audio:true,video:video?{facingMode:'user'}:false});$('ieSelf').srcObject=media}
async function ice(p){if(p.iceGatheringState==='complete')return;await new Promise(resolve=>{const timeout=setTimeout(done,8000);function done(){clearTimeout(timeout);p.removeEventListener('icegatheringstatechange',check);resolve()}function check(){if(p.iceGatheringState==='complete')done()}p.addEventListener('icegatheringstatechange',check)})}
async function signal(type,sdp){return api('rooms/'+room+'/signal','POST',{type,sdp})}
function poll(){if(timer)clearInterval(timer);timer=setInterval(async()=>{if(!room||!live)return;try{const result=await api('rooms/'+room+'/events?after='+seen);for(const e of result.events){seen=Math.max(seen,e.seq);if(e.type==='answer'&&caller&&conn?.signalingState==='have-local-offer'){await conn.setRemoteDescription({type:'answer',sdp:e.sdp});status('Connecting…')}if(e.type==='offer'&&!caller&&conn?.signalingState==='stable'){await conn.setRemoteDescription({type:'offer',sdp:e.sdp});await conn.setLocalDescription(await conn.createAnswer());await ice(conn);await signal('answer',conn.localDescription.sdp);status('Answer sent, connecting…')}if(e.type==='hangup'){clear();room=null;status('Other person ended call');return}}seen=Math.max(seen,result.last_sequence)}catch(e){status('Connection check: '+String(e.message).slice(0,140))}},1600)}
async function share(){if(!room)return;const url=location.origin+location.pathname+'#icall='+encodeURIComponent(room)+'&kind='+mode;try{if(navigator.share){await navigator.share({title:'iMobile call',text:'Open i™ and sign in to answer my '+mode+' call.',url});status('Invitation shared. Waiting for person to answer.')}else{await navigator.clipboard.writeText(url);status('Invitation link copied. Send it privately via Messages or email.')}}catch(e){if(e.name!=='AbortError')status('Share unavailable: '+e.message)}}
async function start(video){clear();room=null;seen=0;mode=video?'video':'audio';caller=true;try{status('Preparing microphone…');await capture(video);conn=rtc();media.getTracks().forEach(t=>conn.addTrack(t,media));const response=await api('rooms','POST');room=response.room_id;await conn.setLocalDescription(await conn.createOffer());await ice(conn);await signal('offer',conn.localDescription.sdp);live=true;poll();$('ieShare').hidden=false;await share()}catch(e){clear();room=null;status('Cannot place call: '+e.message)}}
async function accept(){if(!room)return;$('ieIncoming').hidden=true;try{status('Connecting…');await capture(mode==='video');conn=rtc();media.getTracks().forEach(t=>conn.addTrack(t,media));await api('rooms/'+room+'/join','POST');live=true;poll();status('Answering call…')}catch(e){clear();status('Unable to answer: '+e.message)}}
$('ieAudio').onclick=()=>start(false);$('ieVideo').onclick=()=>start(true);$('ieEnd').onclick=end;$('ieShare').onclick=share;$('ieAccept').onclick=accept;$('ieDecline').onclick=()=>{clear();room=null;history.replaceState(null,'',location.pathname+location.search);status('Call declined')};
function incoming(){const hash=location.hash.match(/(?:^#|&)icall=([A-Za-z0-9_-]{16,80})/);if(!hash)return;clear();room=decodeURIComponent(hash[1]);mode=/[&]kind=video(?:&|$)/.test(location.hash)?'video':'audio';caller=false;seen=0;$('ieIncoming').hidden=false;chirp();tab.click();status('Invitation received. Tap Accept to request microphone/camera permission.')}
window.addEventListener('hashchange',incoming);window.addEventListener('pagehide',clear);incoming();
})();