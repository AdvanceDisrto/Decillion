'use strict';
function baseUrl(value) {
 if(typeof value!=='string'||!/^https:\/\//.test(value)) throw Error('HTTPS VCP gateway required');
 const url=new URL(value);
 if(url.username||url.password||url.hash)throw Error('Unsafe gateway URL');
 return url.origin+url.pathname.replace(/\/$/,'');
}
function describeAssessment(data){
 if(!data||typeof data!=='object')throw Error('Malformed assessment');
 if(data.certified===true || data.verified===true)throw Error('Unsupported client certification assertion; independent certificate verification required');
 return {status:typeof data.status==='string'?data.status:'INCONCLUSIVE',badge:'NOT CERTIFIED',claim:data.claim||null,source:data.source||null,checks:data.checks||{},record:data};
}
async function requestAssessment({gateway,prompt,token,fetcher=fetch,signal}){
 const endpoint=baseUrl(gateway);
 if(typeof prompt!=='string'||prompt.trim().length<3||prompt.length>1600)throw Error('Enter a claim (3–1600 characters)');
 if(typeof token!=='string'||!token)throw Error('Sign in to Buddy before assessing');
 const result=await fetcher(endpoint+'/v1/vcp/assess',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},body:JSON.stringify({prompt:prompt.trim()}),signal});
 if(!result.ok)throw Error('VCP assessment unavailable (HTTP '+result.status+')');
 return describeAssessment(await result.json());
}
module.exports={requestAssessment,describeAssessment,baseUrl};
