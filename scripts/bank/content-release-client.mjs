#!/usr/bin/env node
// Serial, resumable client. Keys, pending bodies and logs stay in ignored files.
import { readFileSync,writeFileSync,mkdirSync,existsSync,renameSync,appendFileSync,rmSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { createHash,sign } from 'node:crypto';
import { message,steps } from '../../lib/server/content-release.mjs';
const [mode,planDirectory,keyPath,maximum='25']=process.argv.slice(2),max=Number(maximum);
if(!['init','status','continue','activate','rollback'].includes(mode)||!Number.isSafeInteger(max)||max<1||max>25)throw Error('Usage: content-release-client.mjs init|status|continue|activate|rollback PLAN_DIRECTORY PRIVATE_KEY [MAX_STEPS<=25]');
const dir=resolve(planDirectory),plan=JSON.parse(readFileSync(join(dir,'plan.json'),'utf8')),program=steps(plan),key=readFileSync(keyPath),stateDir=join(dir,'hosted');mkdirSync(stateDir,{recursive:true,mode:0o700});
const pending=join(stateDir,'pending.json'),events=join(stateDir,'events.jsonl'),statePath=join(stateDir,'state.json'),lock=join(stateDir,'client.lock');
if(existsSync(lock)){const pid=Number(readFileSync(join(lock,'pid'),'utf8'));try{process.kill(pid,0);throw Error('Another release client is running');}catch(e){if(e.code!=='ESRCH')throw e;rmSync(lock,{recursive:true});}}
mkdirSync(lock);writeFileSync(join(lock,'pid'),String(process.pid));
const atomic=(file,value)=>{writeFileSync(file+'.tmp',JSON.stringify(value,null,2)+'\n',{mode:0o600});renameSync(file+'.tmp',file);};
const sha=text=>createHash('sha256').update(text).digest('hex');
async function execute(input){
 atomic(pending,input);const body=JSON.stringify(input),hash=sha(body),time=String(Date.now()),start=performance.now();
 // No blind network retry: pending exact bytes survive a lost response.
 const r=await fetch('https://calculus.ninja/api/content-release',{method:'POST',redirect:'error',body,signal:AbortSignal.timeout(45000),headers:{'Content-Type':'application/json','x-bank-time':time,'x-bank-body-sha256':hash,'x-bank-signature':sign(null,Buffer.from(message(plan,time,hash)),key).toString('base64')}});
 const result=await r.json();appendFileSync(events,JSON.stringify({at:new Date().toISOString(),op:input.op,step:input.step,status:r.status,roundTripMs:performance.now()-start,...result})+'\n',{mode:0o600});
 if(!r.ok||result.halted)throw Error(result.error||result.halted||'Release operation failed; inspect pending request and receipts');
 if(result.bundleId!==plan.bundleId)throw Error('Response bundle mismatch');atomic(statePath,result);rmSync(pending);return result;
}
async function health(){const r=await fetch('https://calculus.ninja/api/health',{redirect:'error',signal:AbortSignal.timeout(10000)});const b=await r.json();if(!r.ok||b.status!=='ok'||!b.secureGameplayConfigured)throw Error('Production health failed');}
try{
 await health();if(existsSync(pending))await execute(JSON.parse(readFileSync(pending,'utf8')));
 let state=await execute({op:mode==='init'?'init':'status'});
 if(mode==='continue'){
  const end=Math.min(program.length,state.nextSequence+max);
  for(let index=state.nextSequence;index<end;index++){
   const step=program[index],input={op:'step',step:index};
   if(step.kind==='import'){if(!/^batch-\d{5}\.json$/.test(step.file))throw Error('Invalid compiled batch path');input.text=readFileSync(join(dir,step.file),'utf8');if(sha(input.text)!==step.sha256)throw Error('Local batch changed');}
   state=await execute(input);if(state.nextSequence!==index+1)throw Error('Checkpoint mismatch');
  }
 }else if(['activate','rollback'].includes(mode))state=await execute({op:mode});
 await health();console.log(JSON.stringify({mode,...state,measurements:undefined,more:state.nextSequence<program.length}));
}catch(e){console.error(e.message);process.exitCode=1;}finally{rmSync(lock,{recursive:true,force:true});}
