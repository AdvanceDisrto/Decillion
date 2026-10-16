/* i™ Buddy character asset gate. The rejected legacy mesh is deliberately retired.
   Never display an unapproved external model or silently fall back to that asset. */
(()=>{
const host=document.getElementById('buddy3d'),stage=document.querySelector('.buddy-world'),status=document.getElementById('buddy3d-status'),character=document.getElementById('buddyCharacter');
if(!host||!stage)return;
host.replaceChildren();
host.setAttribute('aria-hidden','true');
stage.classList.add('buddy-native-mode');
if(character){character.style.setProperty('display','block','important');character.setAttribute('aria-label','Buddy i companion with two lowercase i eyes');}
if(status)status.textContent='Buddy i™ · native character preview';
const sync=()=>{if(!window.buddyCompanion)return false;const old=window.buddyCompanion.mode;if(old.__nativeBridge)return true;const bridge=(mode)=>{old(mode);stage.dataset.buddyMode=mode||'idle';};bridge.__nativeBridge=true;window.buddyCompanion.mode=bridge;return true;};
if(!sync()){let n=0;const timer=setInterval(()=>{if(sync()||++n>30)clearInterval(timer)},100);}
window.buddy3D={loaded:false,retiredLegacyMesh:true,setMode(mode){stage.dataset.buddyMode=mode||'idle';}};
})();