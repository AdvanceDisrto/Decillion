/* Buddy i™ visual companion: progressive enhancement, no remote assets. */
(()=>{
const $=id=>document.getElementById(id), buddy=$('buddyCharacter'), intro=$('buddyIntro'), state=$('buddyState');
if(!buddy)return;
const greeting="Hey there! I'm Buddy. Welcome to i™. What can I do for you today?";
let speaking=false;
function status(s){if(state)state.textContent=s}
function mode(name){buddy.classList.remove('talking','listening','thinking','walking');if(name)buddy.classList.add(name);status(name==='talking'?'Buddy is speaking':name==='listening'?'Buddy is listening':name==='thinking'?'Buddy is working':'Buddy is here')}
function speak(text){if(!('speechSynthesis' in window)){status('Voice playback unavailable');return}try{speechSynthesis.cancel();const utter=new SpeechSynthesisUtterance(text);utter.rate=.96;utter.pitch=1.08;utter.onstart=()=>{speaking=true;mode('talking')};utter.onend=()=>{speaking=false;mode('')};utter.onerror=()=>{speaking=false;mode('')};speechSynthesis.speak(utter)}catch{status('Voice playback unavailable')}}
window.buddyCompanion={speak,mode,greet:()=>speak(greeting)};
$('buddyGreet')?.addEventListener('click',()=>speak(greeting));
$('buddyListen')?.addEventListener('click',()=>{mode('listening');$('mic')?.click();setTimeout(()=>{if(!speaking)mode('')},9000)});
$('buddyAsk')?.addEventListener('click',()=>{$('prompt')?.focus();document.querySelector('[data-tab="buddy"]')?.click()});
const shouldGreet=!sessionStorage.getItem('buddy-welcomed');
if(shouldGreet){sessionStorage.setItem('buddy-welcomed','1');setTimeout(()=>{intro?.classList.add('show');status('Tap Say hello to hear Buddy')},1700)}
document.addEventListener('visibilitychange',()=>{if(document.hidden&&speaking){speechSynthesis.cancel();mode('')}});
})();
