'use strict';
// A signed certificate is not a fact: this module only validates schema/shape.
// Cryptographic certificate verification is performed by separately keyed ICE verifier.
function classifyCertificate(response){
 if(!response||typeof response!=='object')return {state:'UNAVAILABLE',message:'No ICE validation response'};
 if(response.signature_valid===true&&response.currently_valid===true){
  return {state:'EVIDENCE_INTEGRITY_ONLY',message:'ICE signature/current status validated; factual truth not certified'};
 }
 if(response.signature_valid===true)return {state:'NOT_CURRENTLY_VALID',message:'Certificate signature valid, but current validity failed'};
 return {state:'UNVERIFIED',message:'No valid independently checked ICE certificate'};
}
async function validateCertificate({url,certificate,fetcher=fetch}){
 if(!/^https:\/\//.test(url))throw Error('HTTPS verifier required');
 const response=await fetcher(url.replace(/\/$/,'')+'/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({certificate})});
 if(!response.ok)throw Error('Independent certificate verifier unavailable');
 return classifyCertificate(await response.json());
}
module.exports={classifyCertificate,validateCertificate};
