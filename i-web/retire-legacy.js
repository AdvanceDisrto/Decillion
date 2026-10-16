/* Suppress retired legacy character regardless of historic inline display rules. */
(()=>{'use strict';function retire(){
 document.getElementById('buddyCharacter')?.remove();
 const old=document.getElementById('buddy3d');if(old){old.replaceChildren();old.remove()}
 document.getElementById('buddy3d-status')?.remove();
 document.querySelector('.buddy-world')?.classList.remove('buddy-native-mode');
}
retire();addEventListener('pageshow',retire);
})();