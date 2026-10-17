const test=require('node:test'),assert=require('node:assert/strict');
const {signIn,refresh,config}=require('../src/auth');
const {classifyCertificate}=require('../src/certificate');
test('rejects insecure Supabase authentication URL',()=>assert.throws(()=>config('http://example.com','publishable-123456'),/HTTPS/));
test('password sign in obtains access and refresh tokens',async()=>{
 let req;const got=await signIn({url:'https://demo.supabase.co',key:'publishable-123456',email:'u@example.com',password:'secret',fetcher:async(u,opts)=>{req={u,opts};return {ok:true,json:async()=>({access_token:'token',refresh_token:'rotate'})}}});
 assert.equal(got.access_token,'token');assert.equal(JSON.parse(req.opts.body).email,'u@example.com');
 assert.equal(req.u,'https://demo.supabase.co/auth/v1/token?grant_type=password');
});
test('refresh updates rotating session',async()=>{
 const got=await refresh({url:'https://demo.supabase.co',key:'publishable-123456',refresh_token:'old',fetcher:async()=>({ok:true,json:async()=>({access_token:'new',refresh_token:'rotated'})})});
 assert.equal(got.refresh_token,'rotated');
});
test('certificate classification is evidence only',()=>{
 assert.equal(classifyCertificate({signature_valid:true,currently_valid:true}).state,'EVIDENCE_INTEGRITY_ONLY');
 assert.equal(classifyCertificate({signature_valid:true,currently_valid:false}).state,'NOT_CURRENTLY_VALID');
 assert.equal(classifyCertificate({signature_valid:false}).state,'UNVERIFIED');
});
