import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer,digest} from '../src/server.mjs';
const id='123e4567-e89b-12d3-a456-426614174000';
async function withServer(fetchImpl,fn,configured=true) {
  const s=createServer({supabaseUrl:configured?'https://example.supabase.co':undefined,publishableKey:configured?'publishable':undefined,fetchImpl});
  await new Promise(r=>s.listen(0,'127.0.0.1',r));
  try {await fn('http://127.0.0.1:'+s.address().port);}
  finally {await new Promise(r=>s.close(r));}
}
const api=(url,body,headers={authorization:'Bearer abc.def.ghi'})=>fetch(url+'/v1/clock/events',{method:'POST',headers:{'content-type':'application/json',...headers},body:JSON.stringify(body)});
test('sha256 deterministic stable',()=>assert.equal(digest({a:1,b:2}),digest({b:2,a:1})));
test('health claims no hardware precision',()=>withServer(async()=>{},async u=>{
  const r=await (await fetch(u+'/health')).json();
  assert.equal(r.hardwareAttested,false);assert.equal(r.precisionVerified,false);
}));
test('unauthorized request rejected before database',async()=>{
  let calls=0;
  await withServer(async()=>{calls++;},async u=>{
    assert.equal((await api(u,{event:'x',details:''},{authorization:''})).status,401);
    assert.equal(calls,0);
  });
});
test('invalid event rejected',()=>withServer(async()=>{},async u=>assert.equal((await api(u,{event:'',details:''})).status,422)));
test('database failure not success',()=>withServer(async url=>url.includes('/auth/')
  ?new Response(JSON.stringify({id}),{status:200}):new Response('{}',{status:503}),
  async u=>assert.equal((await api(u,{event:'x',details:''})).status,503)));
test('storage acknowledgement required',()=>withServer(async url=>url.includes('/auth/')
  ?new Response(JSON.stringify({id}),{status:200}):new Response('[]',{status:201}),
  async u=>assert.equal((await api(u,{event:'x',details:''})).status,503)));
test('committed event returns matching receipt digest',()=>withServer(async(url,opts)=>{
  if(url.includes('/auth/'))return new Response(JSON.stringify({id}),{status:200});
  const row=JSON.parse(opts.body);assert.equal(row.owner_id,id);
  return new Response(JSON.stringify([{id:'evidence-id',sha256:row.sha256}]),{status:201});
},async u=>{
  const r=await api(u,{event:'Test',details:'measured'});
  assert.equal(r.status,201);
  const item=(await r.json()).receipt;
  assert.equal(item.sha256,digest(item.body));assert.equal(item.body.hardwareAttested,false);
}));