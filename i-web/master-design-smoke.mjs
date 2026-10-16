/* Static acceptance checks for the shipped exact-reference package.
   Run with: node i-web/master-design-smoke.mjs <extracted-package-directory> */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.argv[2]||process.cwd();
for(const name of ['index.html','style.css','app.js','sw.js','manifest.webmanifest','icon.svg','i-master-artwork.jpg']){
 const file=path.join(root,name);assert.ok(fs.existsSync(file),'Missing file '+name);
 assert.ok(fs.statSync(file).size>0,'Empty file '+name);
}
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const js=fs.readFileSync(path.join(root,'app.js'),'utf8');
const css=fs.readFileSync(path.join(root,'style.css'),'utf8');
assert.ok(html.includes('i-master-artwork.jpg'),'Exact reference scene not loaded');
for(const section of ['buddy','discover','create','hubs','stream','wallet','build','find','control','receipts']){
 assert.ok(html.includes('data-open="'+section+'"'),section+' not accessible');
}
assert.ok(js.includes('crypto.subtle.digest'),'No cryptographic receipt hash');
assert.ok(css.includes('safe-area-inset-bottom'),'Missing mobile safe-area controls');
assert.ok(!js.includes('gen_token_data'),'Fake inference placeholder found');
console.log('i™ master portal static acceptance: PASS');
