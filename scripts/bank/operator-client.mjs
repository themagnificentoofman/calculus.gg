import {readFileSync,writeFileSync,appendFileSync,existsSync,mkdirSync,rmSync,renameSync} from 'node:fs';
import {createHash,sign,randomUUID} from 'node:crypto';
import {join,resolve} from 'node:path';
import {runImport,loadPlan} from './compact-import.mjs';
const [mode,keyPath,importDirectory,stateDirectory]=process.argv.slice(2);
if(!['init','import','verify','activate','status'].includes(mode))throw Error('Use init|import|verify|activate|status');
const dir=resolve(stateDirectory);mkdirSync(dir,{recursive:true,mode:0o700});
const lock=join(dir,'client.lock');
if(existsSync(lock)){
  const previous=Number(readFileSync(join(lock,'pid'),'utf8'));
  try{process.kill(previous,0);throw Error('Another importer process is running');}
  catch(error){if(error.code!=='ESRCH')throw error;rmSync(lock,{recursive:true});}
}
mkdirSync(lock);writeFileSync(join(lock,'pid'),String(process.pid));
const statePath=join(dir,'state.json'),pendingPath=join(dir,'pending.json'),eventsPath=join(dir,'events.jsonl');
const plan=loadPlan(importDirectory),key=readFileSync(keyPath),origin='https://calculus.ninja';
let state=existsSync(statePath)?JSON.parse(readFileSync(statePath,'utf8')):{bundleId:plan.bundleId,measuredReads:7431,measuredWrites:3860,events:0,settlementCountersUnavailable:0};
if(state.bundleId!==plan.bundleId)throw Error('Client ledger bundle mismatch');
const atomic=(path,value)=>{writeFileSync(path+'.tmp',value,{mode:0o600});renameSync(path+'.tmp',path);};
const save=()=>atomic(statePath,JSON.stringify(state,null,2)+'\n');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function record(input,result,status,ms){
  const measurements=[...(result.measurements||[]),...(result.recoveryMeasurements||[]),...(result.settlement?[result.settlement]:[])];
  // A recovered response repeats already-accounted operation measurements. Only
  // its recovery lookup is new if that operation was recorded by this client.
  const isKnown=state.lastRecordedId===input.id;
  const fresh=isKnown?(result.recoveryMeasurements||[]):measurements;
  for(const m of fresh){if(!Number.isSafeInteger(m.rowsRead)||!Number.isSafeInteger(m.rowsWritten)||!Number.isSafeInteger(m.sizeAfter))throw Error('Missing client consumption measurements');state.measuredReads+=m.rowsRead;state.measuredWrites+=m.rowsWritten;state.databaseBytes=m.sizeAfter;}
  if(result.replayed&&!isKnown&&!result.settlement)state.settlementCountersUnavailable++;
  state.events++;state.lastRecordedId=input.id;state.last=result;
  const entry={at:new Date().toISOString(),id:input.id,op:input.op,index:input.index,page:input.page,cell:input.cell,status,roundTripMs:ms,serverMs:result.serverMs,measurements:fresh,budget:result.budget,nextSequence:result.nextSequence,error:result.error,halted:result.halted,replayed:result.replayed};
  appendFileSync(eventsPath,JSON.stringify(entry)+'\n',{mode:0o600});save();
  if(input.op!=='import'||input.index%25===0||status!==200)console.log(JSON.stringify({...entry,measurements:undefined,budget:result.budget?{chargedReads:result.budget.chargedReads,chargedWrites:result.budget.chargedWrites,databaseBytes:result.budget.databaseBytes}:undefined}));
}
async function execute(input){
  atomic(pendingPath,JSON.stringify(input));
  const body=JSON.stringify(input),hash=createHash('sha256').update(body).digest('hex');
  for(let attempt=0;attempt<3;attempt++){
    const time=String(Date.now()),message=`calculus-ninja-operator-v1\nappgprj_6ad91db3d4788191b3e73074e27447f5\nPOST\n/api/bank-import\n${time}\n${hash}`,started=performance.now();
    let response;
    try{response=await fetch(origin+'/api/bank-import',{method:'POST',body,redirect:'error',signal:AbortSignal.timeout(45000),headers:{'Content-Type':'application/json','x-bank-time':time,'x-bank-body-sha256':hash,'x-bank-signature':sign(null,Buffer.from(message),key).toString('base64')}});}
    catch(error){appendFileSync(eventsPath,JSON.stringify({at:new Date().toISOString(),op:input.op,id:input.id,transport:error.name,attempt,reconcile:true})+'\n');if(attempt===2)throw Error('Ambiguous response; pending operation retained for reconciliation');await sleep(2000*(attempt+1));continue;}
    if(response.status===429){const seconds=Number(response.headers.get('retry-after'));appendFileSync(eventsPath,JSON.stringify({at:new Date().toISOString(),status:429,id:input.id,retryAfter:response.headers.get('retry-after')})+'\n');if(attempt===2)throw Error('Repeated provider rate limit');await sleep(Number.isFinite(seconds)?Math.max(1000,seconds*1000):2000*(attempt+1));continue;}
    let result;try{result=await response.json();}catch{throw Error('Invalid provider response; reconcile pending operation');}
    record(input,result,response.status,Math.round(performance.now()-started));
    if(!response.ok||result.halted)throw Error(result.error||result.halted||'Provider denied operation');
    if(result.id!==input.id||result.bundleId!==plan.bundleId||!result.budget)throw Error('Operator response integrity mismatch');
    rmSync(pendingPath);state.last=result;save();
    if(result.serverMs>5000||performance.now()-started>15000)throw Error('Operation latency threshold exceeded after accounted completion');
    return result;
  }
}
const call=input=>execute({...input,id:randomUUID()});
async function health(){
  const started=performance.now(),response=await fetch(origin+'/api/health',{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(10000)}),body=await response.json(),ms=Math.round(performance.now()-started);
  appendFileSync(eventsPath,JSON.stringify({at:new Date().toISOString(),op:'health',status:response.status,ms,body})+'\n');
  if(response.status!==200||body.status!=='ok'||!body.secureGameplayConfigured||ms>2000)throw Error('Production health threshold failed');
}
try{
  // A prior invocation can finish a persisted operation but must never invent a new ID for it.
  if(existsSync(pendingPath))await execute(JSON.parse(readFileSync(pendingPath,'utf8')));
  await health();let current=await call({op:mode==='init'?'init':'status'});
  if(mode==='import'){
    while(current.nextSequence<1850){
      if(current.nextSequence===8&&current.pilotVerified<1000){for(let page=current.pilotVerified/100;page<10;page++)current=await call({op:'pilot',page});await health();}
      const start=current.nextSequence,end=start<current.trancheEnd?current.trancheEnd:Math.min(1850,start+25);
      await runImport(null,importDirectory,{mode:'operator-budget',operator:call,startIndex:start,maxBatches:end-start,checkpointPath:join(dir,'tranches.jsonl'),onProgress:async()=>sleep(150)});
      await health();current=await call({op:'status'});
      console.log(JSON.stringify({trancheCompleted:true,nextSequence:current.nextSequence,budget:current.budget,clientMeasuredReads:state.measuredReads,clientMeasuredWrites:state.measuredWrites}));
    }
  }
  if(mode==='verify'){
    if(current.nextSequence!==1850)throw Error('Import incomplete');
    for(let page=current.problemPages;page<1008;page++){current=await call({op:'problems',page});if(page%25===0)await health();}
    for(let page=current.membershipPages;page<261;page++){current=await call({op:'memberships',page});if(page%25===0)await health();}
    if(!current.metadataVerified)current=await call({op:'metadata'});
    for(let cell=current.selectionCells;cell<24;cell++)current=await call({op:'selection',cell});
  }
  if(mode==='activate')current=await call({op:'activate'});
  await health();state.last=current;save();console.log(JSON.stringify({mode,finished:true,nextSequence:current.nextSequence,problemPages:current.problemPages,membershipPages:current.membershipPages,selectionCells:current.selectionCells,activated:current.activated,budget:current.budget,clientMeasuredReads:state.measuredReads,clientMeasuredWrites:state.measuredWrites}));
}catch(error){state.stopped={at:new Date().toISOString(),reason:error.message};save();console.error(error.message);process.exitCode=1;}
finally{rmSync(lock,{recursive:true,force:true});}
