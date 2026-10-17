/* iChirp notes: actual microphone/camera capture and local playback.
   Native share sheet transfers recorded file; no claim of in-app delivery. */
(()=>{'use strict';
const main=document.querySelector('main'),nav=document.querySelector('nav');if(!main||!nav)return;
const panel=document.createElement('section');panel.className='view';panel.id='ichirp-notes';
panel.innerHTML='<div class="glass" style="background:linear-gradient(155deg,#071c25,#093b34);border:1px solid #18bfa9"><small>i™ THE ONE · JUST ASK BUDDY™</small><h1>🐦 iChirp</h1><p>Voice notes and video chirps. Record, listen, and share with a contact via Messages, Mail or AirDrop.</p><div style="display:flex;gap:10px;flex-wrap:wrap"><button id="icVoice" class="primary">🎙️ Voice chirp</button><button id="icVideo">📹 Video chirp</button><button id="icStop" disabled>⏹ Stop</button></div><p id="icStatus" role="status">Ready · no recording</p><video id="icPreview" controls playsinline style="width:100%;max-height:340px;background:#000;border-radius:20px" hidden></video><audio id="icAudio" controls hidden style="width:100%"></audio><p id="icInfo"></p><button id="icShare" disabled>📤 Share recording</button><button id="icSave" disabled>Save recording</button><p class="fine">Requires permission to access microphone, and camera for video. Recordings remain on your device until you explicitly share or save them. Sharing availability and file size restrictions depend on the receiving app. Native call/telecom number service and background PTT are separate integrations.</p></div>';
main.append(panel);
const navButton=document.createElement('button');navButton.type='button';navButton.dataset.tab='ichirp-notes';navButton.textContent='🐦 Chirp';navButton.onclick=()=>{document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x===panel));nav.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===navButton))};nav.append(navButton);nav.style.overflowX='auto';nav.style.justifyContent='flex-start';
const $=id=>document.getElementById(id),status=s=>$('icStatus').textContent=s;
let recorder=null,stream=null,chunks=[],recording=null,objectURL=null,started=0,clipKind='voice';
function release(){if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}}
function resetClip(){recording=null;if(objectURL){URL.revokeObjectURL(objectURL);objectURL=null}$('icAudio').hidden=true;$('icPreview').hidden=true;$('icAudio').removeAttribute('src');$('icPreview').removeAttribute('src');$('icPreview').srcObject=null;$('icShare').disabled=true;$('icSave').disabled=true}
async function begin(video){if(recorder?.state==='recording')return;resetClip();release();if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){status('Recording unavailable in this browser or insecure context.');return}try{
clipKind=video?'video':'voice';stream=await navigator.mediaDevices.getUserMedia({audio:true,video:video?{facingMode:'user'}:false});
const candidates=video?['video/mp4','video/webm;codecs=vp8,opus','video/webm']:['audio/mp4','audio/webm;codecs=opus','audio/webm'];
const mime=candidates.find(t=>MediaRecorder.isTypeSupported(t));if(!mime)throw new Error('No supported recording format');
recorder=new MediaRecorder(stream,{mimeType:mime});chunks=[];started=Date.now();
recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
recorder.onerror=()=>{release();status('Recorder error; please retry')};
recorder.onstop=()=>{const duration=Math.round((Date.now()-started)/1000);recording=new Blob(chunks,{type:mime});release();recorder=null;chunks=[];
if(!recording.size){status('No media captured');return}objectURL=URL.createObjectURL(recording);
const player=video?$('icPreview'):$('icAudio');player.src=objectURL;player.hidden=false;player.controls=true;
$('icInfo').textContent=duration+' seconds · '+Math.round(recording.size/1024)+' KB · '+mime;
$('icShare').disabled=false;$('icSave').disabled=false;$('icStop').disabled=true;status('Recording complete. Review before sharing.')};
recorder.start(1000);$('icStop').disabled=false;status('🔴 Recording '+clipKind+' · tap Stop to finish');
if(video){$('icPreview').hidden=false;$('icPreview').muted=true;$('icPreview').srcObject=stream;$('icPreview').play().catch(()=>{})}
}catch(e){release();status('Cannot record: '+e.name+' '+e.message)}
}
$('icVoice').onclick=()=>begin(false);$('icVideo').onclick=()=>begin(true);
$('icStop').onclick=()=>{if(recorder?.state==='recording')recorder.stop()};
function getFile(){const ext=recording.type.includes('mp4')?'mp4':'webm';return new File([recording],'iChirp-'+clipKind+'-'+Date.now()+'.'+ext,{type:recording.type})}
$('icShare').onclick=async()=>{if(!recording)return;const file=getFile();try{if(navigator.canShare?.({files:[file]})&&navigator.share){await navigator.share({title:'iChirp '+clipKind,text:'iChirp from i™',files:[file]});status('Shared using device sheet; recipient delivery not verified.')}else status('File sharing unavailable here. Use Save recording and attach it to a message.')}catch(e){if(e.name!=='AbortError')status('Share failed: '+e.message)}};
$('icSave').onclick=()=>{if(!recording)return;const a=document.createElement('a');a.href=objectURL;a.download=getFile().name;a.click();status('Save requested')};
window.addEventListener('pagehide',()=>{if(recorder?.state==='recording')recorder.stop();release()});
})();