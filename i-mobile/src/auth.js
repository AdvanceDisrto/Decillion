'use strict';
// Supabase Auth REST gateway with short-lived access token + rotating refresh token.
// Public publishable key only. Secrets must remain on the server.
function config(url,key){
 if(typeof url!=='string'||!/^https:\/\//.test(url))throw Error('HTTPS authentication endpoint required');
 const u=new URL(url);if(u.username||u.password||u.hash||u.search)throw Error('Unsafe authentication URL');
 if(typeof key!=='string'||key.length<10)throw Error('Missing Supabase publishable key');
 return {base:u.origin,key};
}
async function authRequest({url,key,method='POST',route,payload,fetcher=fetch}){
 const c=config(url,key);
 const response=await fetcher(c.base+'/auth/v1/'+route,{method,headers:{'apikey':c.key,'Content-Type':'application/json'},body:payload?JSON.stringify(payload):undefined});
 const obj=await response.json();
 if(!response.ok||obj.error||obj.error_code)throw Error('Buddy sign-in unavailable: '+(obj.msg||obj.error_description||obj.message||response.status));
 return obj;
}
async function signIn(args){
 const body=await authRequest({...args,route:'token?grant_type=password',payload:{email:args.email,password:args.password}});
 if(!body.access_token||!body.refresh_token)throw Error('Incomplete authenticated session');
 return body;
}
async function refresh(args){
 const body=await authRequest({...args,route:'token?grant_type=refresh_token',payload:{refresh_token:args.refresh_token}});
 if(!body.access_token||!body.refresh_token)throw Error('Incomplete refreshed session');
 return body;
}
async function signOut(args){
 if(!args.access_token)throw Error('No active session');
 const c=config(args.url,args.key);
 await args.fetcher?.(c.base+'/auth/v1/logout',{method:'POST',headers:{apikey:c.key,Authorization:'Bearer '+args.access_token}})
 || await fetch(c.base+'/auth/v1/logout',{method:'POST',headers:{apikey:c.key,Authorization:'Bearer '+args.access_token}});
}
module.exports={config,authRequest,signIn,refresh,signOut};
