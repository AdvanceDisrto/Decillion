/* i™ Mini Buddy: on-page, draggable, touch friendly. Not an OS-wide overlay. */
(()=>{'use strict';const root=document.createElement('aside');root.id='miniBuddy';root.setAttribute('aria-label','Mini Buddy companion');root.innerHTML='<div class="mini-speech" hidden aria-live="polite"></div><button class="mini-avatar" type="button" aria-label="Ask Mini Buddy"><span class="mini-arm left"></span><span class="mini-arm right"></span><span class="mini-body">i</span><span class="mini-feet"><span></span><span></span></span><span class="mini-head"><span class="mini-face"><span class="mini-eye">i</span><span class="mini-eye">i</span><span class="mini-mouth"></span></span></span></button><div class="mini-controls"><button type="button" class="mini-close" aria-label="Hide Mini Buddy">×</button></div>';document.body.append(root);
const toggle=document.createElement('button');toggle.id='miniBuddyToggle';toggle.type='button';toggle.textContent='✦ Mini Buddy';toggle.setAttribute('aria-label','Show or hide Mini Buddy');document.body.append(toggle);
const avatar=root.querySelector('.mini-avatar'),speech=root.querySelector('.mini-speech');let visible=true,moving=false,start=null,dragged=false;
function position(x,y){const w=root.offsetWidth||90,h=root.offsetHeight||115;root.style.left=Math.max(4,Math.min(window.innerWidth-w-4,x))+'px';root.style.top=Math.max(65,Math.min(window.innerHeight-h-155,y))+'px'}
function show(v){visible=v;root.hidden=!v;toggle.textContent=v?'✕ Hide Mini Buddy':'✦ Mini Buddy';try{localStorage.setItem('i-mini-buddy-visible',v?'1':'0')}catch{}}
function say(text,mode='greeting'){speech.textContent=text;speech.hidden=false;root.dataset.mode=mode;clearTimeout(say.timer);say.timer=setTimeout(()=>{speech.hidden=true;root.dataset.mode='idle'},3300)}
avatar.addEventListener('pointerdown',e=>{if(e.button!==0)return;start={x:e.clientX,y:e.clientY,left:root.offsetLeft,top:root.offsetTop};dragged=false;moving=true;avatar.setPointerCapture(e.pointerId)});
avatar.addEventListener('pointermove',e=>{if(!moving||!start)return;const dx=e.clientX-start.x,dy=e.clientY-start.y;if(Math.abs(dx)+Math.abs(dy)>7)dragged=true;if(dragged)position(start.left+dx,start.top+dy)});
avatar.addEventListener('pointerup',()=>{moving=false;start=null});
avatar.addEventListener('click',()=>{if(dragged){dragged=false;return}say('Hey there! Just ask Buddy.','greeting');document.querySelector('[data-tab="buddy"]')?.click();document.querySelector('#buddy input[type="text"],#buddy .compose input')?.focus({preventScroll:true})});
root.querySelector('.mini-close').addEventListener('click',()=>show(false));toggle.addEventListener('click',()=>{show(!visible);if(visible)say('I’m right here!','greeting')});
try{if(localStorage.getItem('i-mini-buddy-visible')==='0')show(false)}catch{}
position(window.innerWidth-112,Math.max(90,window.innerHeight-350));window.addEventListener('resize',()=>position(root.offsetLeft,root.offsetTop));
const previous=window.buddyMini;window.buddyMini={say,setMode(mode){root.dataset.mode=mode},show,previous};
window.addEventListener('buddy:mode',e=>{if(e.detail?.mode)root.dataset.mode=e.detail.mode});
document.addEventListener('visibilitychange',()=>{if(document.hidden)root.dataset.mode='idle'});
/* Quiet by default: no overlay speech bubble obscuring the hero or input controls. */
})();
