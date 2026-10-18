// iClock Evidence Lab: timestamps are host measurements, not picosecond hardware.
const text=new TextEncoder();
export const scales=[["Picosecond","ps","10⁻¹²"],["Femtosecond","fs","10⁻¹⁵"],["Attosecond","as","10⁻¹⁸"],["Zeptosecond","zs","10⁻²¹"],["Yoctosecond","ys","10⁻²⁴"]];
export const unitMultipliers={ps:1000n,fs:1000000n,as:1000000000n,zs:1000000000000n,ys:1000000000000000n};
export function convertNanoseconds(ns,unit){if(!(unit in unitMultipliers))throw Error("Unknown time unit");return (BigInt(ns)*unitMultipliers[unit]).toString();}
export function canonical(v){if(Array.isArray(v))return "["+v.map(canonical).join(",")+"]";if(v&&typeof v==="object")return "{"+Object.keys(v).sort().map(k=>JSON.stringify(k)+":"+canonical(v[k])).join(",")+"}";return JSON.stringify(v);}
export async function sha256(value){const b=await crypto.subtle.digest("SHA-256",text.encode(value));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("");}
export class ClockLab {
 constructor(){this.receipts=[];this.lastMonotonic=null;}
 async record(label,detail){
   if(typeof label!=="string"||!label.trim()||label.length>160)throw Error("Event name required (max 160)");
   if(typeof detail!=="string"||detail.length>8000)throw Error("Details must be text (max 8000)");
   const now=performance.now();
   if(this.lastMonotonic!==null&&now<this.lastMonotonic)throw Error("Monotonic clock reversed");
   this.lastMonotonic=now;
   const body={schema:"iclock-evidence/1",sequence:this.receipts.length+1,event:label.trim(),details:detail,wallTimestamp:new Date().toISOString(),monotonicMilliseconds:now,previousHash:this.receipts.at(-1)?.sha256||null,clockSource:"Browser wall clock and performance.now()",precisionClaim:"none",hardwareAttested:false,independentlyCertified:false};
   const receipt={body,sha256:await sha256(canonical(body))};this.receipts.push(receipt);return receipt;
 }
 async verify(){let previous=null;for(let i=0;i<this.receipts.length;i++){const r=this.receipts[i];if(r.body.sequence!==i+1||r.body.previousHash!==previous||r.sha256!==await sha256(canonical(r.body)))return {ok:false,index:i};previous=r.sha256;}return {ok:true,count:this.receipts.length};}
 export(){return JSON.stringify({schema:"iclock-export/1",receipts:this.receipts},null,2);}
}