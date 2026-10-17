const test=require('node:test'),assert=require('node:assert/strict');
const {requestAssessment,describeAssessment,baseUrl}=require('../src/vcpClient');
test('HTTPS required, credentials and fragments rejected',()=>{
 for(const url of ['http://127.0.0.1:8795','https://admin:secret@example.com','https://example.com/#bad'])assert.throws(()=>baseUrl(url));
});
test('missing session rejects before network access',async()=>{
 await assert.rejects(()=>requestAssessment({gateway:'https://example.com',prompt:'Mars moons?',token:'',fetcher:()=>{throw Error('should never call')}}),/Sign in/);
});
test('authenticated requests carry exact gateway path and never self-certify',async()=>{
 let actual;
 const obj=await requestAssessment({gateway:'https://example.com/',prompt:'How many moons does Mars have?',token:'test-secret',fetcher:async(url,opts)=>{actual={url,opts};return {ok:true,json:async()=>({status:'EVIDENCE_RETRIEVED',certified:false,verified:false})}}});
 assert.equal(actual.url,'https://example.com/v1/vcp/assess');
 assert.equal(actual.opts.headers.Authorization,'Bearer test-secret');
 assert.equal(obj.badge,'NOT CERTIFIED');
});
test('client refuses a backend asserting unsupported certainty',()=>{
 assert.throws(()=>describeAssessment({certified:true,verified:true}),/independent certificate/);
});
test('server errors not treated as false claims',async()=>{
 await assert.rejects(()=>requestAssessment({gateway:'https://example.com',prompt:'A valid claim',token:'x',fetcher:async()=>({ok:false,status:503})}),/unavailable/);
});
