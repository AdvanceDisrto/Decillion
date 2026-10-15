/* Render the to3D-exported Buddy GLB. A single mesh is not an articulated skeleton.
   If embedded clips exist, use them; otherwise use honest whole-character animation. */
(()=>{
const MODEL='https://storage.to3d.app/generated-3d/models/2026-10-15/task_fa31ec19-e871-4c57-ae12-24e1c0a79a04_model.glb';
const POSTER='https://storage.to3d.app/generated-3d/images/2026-10-15/task_fa31ec19-e871-4c57-ae12-24e1c0a79a04_image.png';
const box=document.querySelector('.buddy-world'),host=document.getElementById('buddy3d'),status=document.getElementById('buddy3d-status');
if(!box||!host)return;
const poster=document.createElement('div');poster.className='buddy3d-poster';
const img=document.createElement('img');img.src=POSTER;img.alt='Buddy i™ — green and blue luminous robot';img.loading='eager';
poster.append(img);host.append(poster);
const viewer=document.createElement('model-viewer');viewer.className='buddy3d-model';
viewer.setAttribute('src',MODEL);viewer.setAttribute('alt','Buddy i™ 3D character');
viewer.setAttribute('camera-controls','');viewer.setAttribute('auto-rotate','');viewer.setAttribute('rotation-per-second','10deg');
viewer.setAttribute('camera-orbit','0deg 80deg auto');viewer.setAttribute('environment-image','neutral');
viewer.setAttribute('shadow-intensity','1');viewer.setAttribute('exposure','1.1');viewer.setAttribute('interaction-prompt','none');
host.append(viewer);status.textContent='Loading Buddy 3D…';
let loaded=false;
viewer.addEventListener('load',()=>{
 loaded=true;host.classList.add('loaded');
 const names=viewer.availableAnimations||[];viewer.dataset.clips=names.join(',');
 const idle=names.find(a=>/idle|breath|stand/i.test(a));
 if(idle){viewer.animationName=idle;viewer.play()}status.textContent='Buddy 3D ready'+(names.length?' · animated':' · static mesh');
});
viewer.addEventListener('error',()=>{status.textContent='3D unavailable · showing character image';host.classList.remove('loaded')});
img.onerror=()=>{poster.textContent='Buddy 3D · connection required';poster.style.color='#a5ffe2'};
const previous=window.buddyCompanion;
function setMode(mode){
 box.dataset.buddyMode=mode||'idle';
 if(!loaded)return;
 const names=viewer.availableAnimations||[];
 const pattern=mode==='walking'?/walk|run|step/i:mode==='talking'?/talk|speak|mouth/i:mode==='listening'?/listen|head|nod/i:mode==='thinking'?/think|idle/i:/idle|breath|stand/i;
 const match=names.find(s=>pattern.test(s));
 if(match){viewer.animationName=match;viewer.play()}
}
function bridge(){if(!window.buddyCompanion)return false;const oldMode=window.buddyCompanion.mode;window.buddyCompanion.mode=(m)=>{oldMode(m);setMode(m)};return true}
if(!bridge()){let count=0;const t=setInterval(()=>{if(bridge()||++count>30)clearInterval(t)},100)}
window.buddy3D={model:MODEL,get loaded(){return loaded},setMode};
document.addEventListener('visibilitychange',()=>{if(document.hidden){viewer.pause?.()}else if(loaded&&viewer.animationName){viewer.play?.()}});
})();
