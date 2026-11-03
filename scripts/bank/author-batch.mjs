#!/usr/bin/env node
// Offline operator workflow. Responses are proposals, never approved bank rows.
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, existsSync, renameSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { topics,difficulties } from '../../lib/server/questions-policy.mjs';
export const PRICE={model:'gpt-6-luna',inputPerMillion:0.05,outputPerMillion:0.25,checked:'2026-11-02',source:'https://developers.openai.com/api/docs/pricing',surchargeReserve:1.1};
export const LIMITS={inputTokens:8000,outputTokens:8000,maxAttempts:2,count:100};
const hash=s=>createHash('sha256').update(s).digest('hex');
const schema={type:'object',additionalProperties:false,required:['family','topic','difficulty','techniques','mathematicalSpecification','domainProof','independentVerificationPlan','distractorRationale'],properties:{family:{type:'string'},topic:{type:'string',enum:topics},difficulty:{type:'string',enum:difficulties},techniques:{type:'array',items:{type:'string'}},mathematicalSpecification:{type:'string'},domainProof:{type:'string'},independentVerificationPlan:{type:'string'},distractorRationale:{type:'string'}}};
export function makePlan(count=100){
  if(!Number.isInteger(count)||count<1||count>LIMITS.count)throw Error('Use 1–100 family proposals per job');
  const requests=Array.from({length:count},(_,i)=>{
    const topic=topics[i%topics.length],difficulty=difficulties[Math.floor(i/topics.length)%difficulties.length];
    const body={model:PRICE.model,store:false,max_output_tokens:LIMITS.outputTokens,
      instructions:'Propose an original calculus problem family, not copied source text. This is an offline authoring proposal. Explain the mathematical method, bounded parameters, domains, exact independent verifier, and plausible distinct distractors. Do not assert approval, human review, or publishability. Never output executable code.',
      input:`Family request ${i+1}. Topic: ${topic}. Difficulty rubric: ${difficulty}. Seek a distinct technique or reasoning pattern, not a coefficient or wording variant. Easy: one fundamental rule. Medium: choose and combine standard rules. Hard: several coupled steps or domain/convergence analysis. Olympiad: discover a concealed identity or transformation. Include assumptions and an exact proof that exactly one answer is correct.`,
      text:{format:{type:'json_schema',name:'family_proposal',strict:true,schema}}};
    // UTF-8 bytes + an explicit protocol allowance is a conservative token bound,
    // including schema/instructions. No tools, images, external files, or histories.
    if(Buffer.byteLength(JSON.stringify(body))+512>LIMITS.inputTokens)throw Error('Input token bound exceeded');
    return {custom_id:'family-'+hash(JSON.stringify(body)).slice(0,24)+'-attempt-1',method:'POST',url:'/v1/responses',body};
  });
  const worstUSD=count*LIMITS.maxAttempts*(LIMITS.inputTokens*PRICE.inputPerMillion+LIMITS.outputTokens*PRICE.outputPerMillion)/1e6*PRICE.surchargeReserve;
  return {jobId:'bank-author-'+hash(JSON.stringify(requests)).slice(0,24),promptVersion:'families-v1',price:PRICE,limits:LIMITS,worstUSD,authorizedUSD:0,requests,status:'dry-run',attempts:[],counts:{generated:0,rejected:0,duplicate:0,approved:0,published:0},actualUSD:0,costPerApprovedProblemUSD:null};
}
function save(path,value){writeFileSync(path+'.tmp',JSON.stringify(value,null,2)+'\n',{mode:0o600});renameSync(path+'.tmp',path);}
export function validateSubmission(job,requestText,cap){
  const expected=makePlan(job.requests?.length);
  if(job.jobId!==expected.jobId||job.worstUSD!==expected.worstUSD||JSON.stringify(job.requests)!==JSON.stringify(expected.requests)||requestText!==expected.requests.map(r=>JSON.stringify(r)).join('\n')+'\n')throw Error('Authoring plan or payload changed; create a new bounded plan');
  if(!Number.isFinite(cap)||cap<expected.worstUSD||cap>5)throw Error(`Explicit cap must cover the reserved maximum ${expected.worstUSD} USD (operator ceiling $5)`);
  if(job.status!=='dry-run')throw Error('Already submitted or ambiguous submission. Reconcile checkpoint; never blindly retry.');
}
export function consumeResults(job,text){
  const known=new Map(job.requests.map(r=>[r.custom_id,r])),seen=new Set(job.results?.map(r=>r.custom_id)||[]);job.results ||= [];
  for(const line of text.split('\n').filter(Boolean)){
    const row=JSON.parse(line);if(!known.has(row.custom_id))throw Error('Unknown batch request ID');
    if(seen.has(row.custom_id)){job.counts.duplicate++;continue;}seen.add(row.custom_id);
    const body=row.response?.body,usage=body?.usage;
    if(usage){
      if(!Number.isFinite(usage.input_tokens)||!Number.isFinite(usage.output_tokens)||usage.input_tokens<0||usage.output_tokens<0)throw Error('Invalid usage');
      job.actualUSD+=(usage.input_tokens*PRICE.inputPerMillion+usage.output_tokens*PRICE.outputPerMillion)/1e6;
    }else if(row.response)job.unreconciledUsage=true;
    let proposal=null;
    try{
      if(row.error||row.response?.status_code!==200||body?.status!=='completed')throw Error();
      const parts=body.output.filter(o=>o.type==='message').flatMap(o=>o.content||[]);
      if(parts.some(p=>p.type==='refusal'))throw Error();
      proposal=JSON.parse(parts.filter(p=>p.type==='output_text').map(p=>p.text).join(''));
      if(Object.keys(proposal).some(k=>!schema.required.includes(k))||schema.required.some(k=>!(k in proposal))||!topics.includes(proposal.topic)||!difficulties.includes(proposal.difficulty))throw Error();
      job.counts.generated++;
    }catch{job.counts.rejected++;}
    job.results.push({custom_id:row.custom_id,state:proposal?'quarantined-proposal':'failed',proposal,usage:usage||null});
  }
  job.costPerApprovedProblemUSD=job.counts.approved?job.actualUSD/job.counts.approved:null;
  return job;
}
async function main(){
  const [action,dirArg,countOrCap]=process.argv.slice(2),dir=resolve(dirArg||'.bank-data/authoring');mkdirSync(dir,{recursive:true,mode:0o700});const path=resolve(dir,'job.json');
  if(action==='plan'){
    const job=makePlan(Number(countOrCap||100));if(existsSync(path)){const old=JSON.parse(readFileSync(path,'utf8'));if(old.jobId!==job.jobId||old.status!=='dry-run')throw Error('Preserve existing checkpoint; choose a new job directory');}
    save(path,job);writeFileSync(resolve(dir,'requests.jsonl'),job.requests.map(r=>JSON.stringify(r)).join('\n')+'\n',{mode:0o600});
    console.log(JSON.stringify({jobId:job.jobId,requests:job.requests.length,maximumAttempts:2,maximumUSD:job.worstUSD,authorizedUSD:0,model:PRICE.model,actualUSD:0,status:'dry-run'},null,2));return;
  }
  const job=JSON.parse(readFileSync(path,'utf8'));const key=process.env.OPENAI_API_KEY;if(!key)throw Error('No operator OpenAI credential is configured');
  const call=async(url,options={})=>{const response=await fetch('https://api.openai.com/v1/'+url,{...options,headers:{Authorization:`Bearer ${key}`,...options.headers},signal:AbortSignal.timeout(60000)});if(!response.ok)throw Error('OpenAI request failed; inspect job checkpoint before retrying');return response;};
  if(action==='submit'){
    const cap=Number(countOrCap),requestText=readFileSync(resolve(dir,'requests.jsonl'),'utf8');validateSubmission(job,requestText,cap);
    job.authorizedUSD=cap;job.reservedUSD=job.worstUSD;job.status='uploading';save(path,job);
    const form=new FormData();form.set('purpose','batch');form.set('file',new Blob([requestText],{type:'application/jsonl'}),'requests.jsonl');
    const file=await(await call('files',{method:'POST',body:form})).json();job.inputFileId=file.id;job.status='submitting';save(path,job);
    const batch=await(await call('batches',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input_file_id:file.id,endpoint:'/v1/responses',completion_window:'24h',metadata:{job_id:job.jobId,prompt_version:job.promptVersion}})})).json();
    job.batchId=batch.id;job.status=batch.status;job.attempts.push({batchId:batch.id,reservedUSD:job.worstUSD/2});save(path,job);console.log(JSON.stringify({batchId:job.batchId,status:job.status}));
  }else if(action==='collect'){
    if(!job.batchId)throw Error('No known batch ID; reconcile an ambiguous submission with the OpenAI Batch dashboard using job_id metadata');
    const batch=await(await call('batches/'+encodeURIComponent(job.batchId))).json();job.status=batch.status;save(path,job);
    for(const [kind,id] of [['output',batch.output_file_id],['errors',batch.error_file_id]])if(id){
      const text=await(await call('files/'+encodeURIComponent(id)+'/content')).text();writeFileSync(resolve(dir,kind+'.jsonl'),text,{mode:0o600});consumeResults(job,text);save(path,job);
    }
    console.log(JSON.stringify({status:job.status,counts:job.counts,actualUSD:job.actualUSD,unreconciledUsage:!!job.unreconciledUsage,costPerApprovedProblemUSD:job.costPerApprovedProblemUSD}));
  }else throw Error('Use plan, submit, or collect. Failed items require a new reviewed plan; automatic paid retries are disabled.');
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(e=>{console.error(e.message);process.exitCode=1;});
