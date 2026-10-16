/* i™ on-device LLM inference worker. Requires real, cached ONNX model weights.
   Never substitutes template responses for model generation. */
let session=null, tokenizer=null, modelId=null;
const tell=(type,value)=>postMessage({type,...value});
async function load(body){
 const manifest=body.manifest;
 if(!manifest||!Array.isArray(manifest.files)||!manifest.files.length||!manifest.modelUrl)throw Error("Select a verified model manifest with weights");
 const {pipeline,env}=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2');
 env.allowLocalModels=false;
 env.allowRemoteModels=true;
 if(body.offlineOnly)env.allowRemoteModels=false;
 // The library downloads and stores model files in persistent browser cache where supported.
 // Device selection is capability-based. WebGPU does not guarantee acceleration on every iPhone.
 const device=(navigator.gpu && body.preferGPU)?'webgpu':'wasm';
 tell('loading',{status:'loading-model',device});
 tokenizer=await pipeline('text-generation',manifest.modelUrl,{device,dtype:manifest.dtype||'q4',progress_callback:p=>{if(p.status==='progress')tell('progress',{file:p.file,progress:p.progress})}});
 session=tokenizer;modelId=manifest.id;return {model:manifest.id,device}
}
self.onmessage=async e=>{
 const {type,requestId}=e.data||{};
 try {
 if(type==='load'){const result=await load(e.data);tell('ready',{requestId,...result});return}
 if(type==='generate'){
   if(!session)throw Error('No locally loaded weights. Download a real edge model first.');
   const prompt=String(e.data.prompt||'').slice(0,4000);
   if(!prompt.trim())throw Error('Prompt required');
   const output=await session([{role:'system',content:'You are Buddy i™, a helpful local-first assistant. State when actions require external services.'},{role:'user',content:prompt}],{max_new_tokens:Math.max(1,Math.min(192,Number(e.data.maxTokens||96))),do_sample:false});
   const message=output?.[0]?.generated_text;
   const answer=Array.isArray(message)?(message.at(-1)?.content||''):String(message||'');
   if(!answer.trim())throw Error('Model generated no response');
   tell('answer',{requestId,answer,modelId,device:'local-edge'});
 }
 }catch(err){tell('error',{requestId,error:String(err.message||err)})}
};