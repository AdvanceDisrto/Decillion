/** i™ Provider Registry (catalog only).
 * Supplied model names, contexts and prices are illustrative / unverified.
 * Not a credential vault. Routing policy still permits ONLY verified Apache-2.0
 * licensed self-hosted iModels; cloud-provider entries are DISABLED by default.
 * Local endpoint is server-loopback, never the user's phone from hosted web.
 */
export type ProviderId = 'openai'|'anthropic'|'deepseek'|'google'|'mistral'|'cohere'|'local';
export type Task = 'chat'|'completion'|'reasoning'|'vision'|'code'|'embedding';
export type Tier = 'FRONTIER_TOP_TIER'|'MID_TIER_BALANCED'|'LOW_COST_EDGE';
export interface ProviderCapability {
  taskTypes: Task[];
  maxContextTokens: number;
  supportsStreaming: boolean;
  supportsFunctionCalling: boolean;
  supportsVision: boolean;
}
export interface ProviderPricing {
  inputCostPer1kTokens: number;
  outputCostPer1kTokens: number;
  verifiedAt: string | null; // null means NOT current price
}
export interface ProviderModel {
  modelId: string;
  displayName: string;
  tier: Tier;
  capability: ProviderCapability;
  pricing: ProviderPricing;
  availabilityVerified: false;
}
export interface ProviderDefinition {
  providerId: ProviderId;
  baseUrl: string;
  apiKeyEnvVar: string;
  models: ProviderModel[];
  healthCheckPath: string;
  connectionVerified: false;
  enabledByPolicy: boolean;
}
const model = (modelId:string,displayName:string,tier:Tier,taskTypes:Task[],ctx:number,input:number,output:number,
  supportsVision:boolean=false,supportsFunctionCalling:boolean=true): ProviderModel=>({
  modelId,displayName,tier,
  capability:{taskTypes,maxContextTokens:ctx,supportsStreaming:true,supportsFunctionCalling,supportsVision},
  pricing:{inputCostPer1kTokens:input,outputCostPer1kTokens:output,verifiedAt:null},
  availabilityVerified:false
});
const entry=(providerId:ProviderId,baseUrl:string,apiKeyEnvVar:string,models:ProviderModel[]):ProviderDefinition=>({
  providerId,baseUrl,apiKeyEnvVar,models,healthCheckPath:'/models',connectionVerified:false,
  enabledByPolicy:false
});
export const PROVIDER_REGISTRY: Record<ProviderId,ProviderDefinition> = {
  openai:entry('openai','https://api.openai.com/v1','OPENAI_API_KEY',[
    model('gpt-4o','GPT-4o','FRONTIER_TOP_TIER',['chat','reasoning','vision','code'],128000,.0025,.01,true),
    model('gpt-4o-mini','GPT-4o mini','LOW_COST_EDGE',['chat','vision'],128000,.00015,.0006,true)]),
  anthropic:entry('anthropic','https://api.anthropic.com/v1','ANTHROPIC_API_KEY',[
    model('claude-sonnet-4-5-20250929','Claude Sonnet 4.5','FRONTIER_TOP_TIER',['chat','reasoning','code','vision'],200000,.003,.015,true),
    model('claude-haiku-4-5-20251001','Claude Haiku 4.5','LOW_COST_EDGE',['chat','code'],200000,.001,.005,false)]),
  deepseek:entry('deepseek','https://api.deepseek.com/v1','DEEPSEEK_API_KEY',[
    model('deepseek-chat','DeepSeek Chat','MID_TIER_BALANCED',['chat','code'],64000,.00027,.0011),
    model('deepseek-reasoner','DeepSeek Reasoner','FRONTIER_TOP_TIER',['chat','reasoning'],64000,.00055,.0022,false,false)]),
  google:entry('google','https://generativelanguage.googleapis.com/v1beta/openai','GOOGLE_API_KEY',[
    model('gemini-2.0-flash','Gemini 2.0 Flash','MID_TIER_BALANCED',['chat','vision','code'],1000000,.0001,.0004,true)]),
  mistral:entry('mistral','https://api.mistral.ai/v1','MISTRAL_API_KEY',[
    model('mistral-large-latest','Mistral Large','MID_TIER_BALANCED',['chat','code'],128000,.002,.006)]),
  cohere:entry('cohere','https://api.cohere.com/v2','COHERE_API_KEY',[
    model('command-r-plus-08-2024','Command R+','MID_TIER_BALANCED',['chat','code'],128000,.0025,.01)]),
  local:entry('local','http://127.0.0.1:11434/v1','LOCAL_API_KEY',[
    model('llama3.3:70b','Llama 3.3 70B','MID_TIER_BALANCED',['chat','code'],128000,0,0,false,false)])
};
export const REGISTRY_STATUS = 'REFERENCE_ONLY_UNVERIFIED' as const;
export const ROUTING_POLICY = 'APACHE_2_0_ONLY' as const;
