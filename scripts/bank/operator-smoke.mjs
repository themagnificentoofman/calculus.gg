import {Miniflare} from 'miniflare';
import {stripTypeScriptTypes} from 'node:module';
import {readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {generateKeyPairSync,sign,createHash,randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {runImport} from './compact-import.mjs';
const directory=resolve(process.argv[2]),plan=JSON.parse(readFileSync('lib/server/operator-plan.json','utf8'));
const {publicKey,privateKey}=generateKeyPairSync('ed25519'),persist=mkdtempSync(join(tmpdir(),'operator-smoke-'));
const paths=['lib/server/bank-operator.mjs','lib/server/bank-pilot.mjs','lib/server/bank-pilot-plan.mjs','lib/server/operator-budget.mjs','lib/bank/compact-codec.mjs','lib/server/compact-bank-selection.ts','lib/server/bank-selection.ts'];
const modules=paths.map(path=>({type:'ESModule',path,contents:path.endsWith('.ts')?stripTypeScriptTypes(readFileSync(path,'utf8')):readFileSync(path,'utf8').replace("import PLAN from './operator-plan.json' with {type:'json'};","import PLAN from './operator-plan.mjs';")}));
modules.push({type:'ESModule',path:'lib/server/operator-plan.mjs',contents:'export default '+JSON.stringify(plan)});
modules.unshift({type:'ESModule',path:'test.mjs',contents:`import {bankOperator} from './lib/server/bank-operator.mjs'; export default {fetch(request,env){let n=0;const fault=request.headers.get('x-test-fault');const wrap=s=>({bind:(...v)=>wrap(s.bind(...v)),all:async()=>{const r=await s.all();return fault==='missing-meta'?{...r,meta:undefined}:r;},run:()=>s.run(),raw:s});const db={prepare:s=>wrap(env.DB.prepare(s)),batch:async s=>{if(fault==='provider-quota'&&++n===2)throw Error('D1 exceeded daily write limit');return env.DB.batch(s.map(x=>x.raw));}};return bankOperator(request,db,env.KEY,env.EXPIRES)}};`});
const create=()=>new Miniflare({modules,modulesRoot:process.cwd(),compatibilityDate:'2026-04-01',d1Databases:{DB:'operator-test'},d1Persist:persist,bindings:{KEY:publicKey.export({type:'spki',format:'der'}).toString('base64'),EXPIRES:String(Date.now()+3600000)}});
let mf=create();
async function call(input,status=200,fault=''){
  input={id:randomUUID(),...input};const body=JSON.stringify(input),time=String(Date.now()),hash=createHash('sha256').update(body).digest('hex');
  const message=`calculus-ninja-operator-v1\n${plan.projectId}\nPOST\n/api/bank-import\n${time}\n${hash}`;
  const response=await mf.dispatchFetch('http://localhost/api/bank-import',{method:'POST',body,headers:{'x-bank-time':time,'x-bank-body-sha256':hash,'x-bank-signature':sign(null,Buffer.from(message),privateKey).toString('base64'),'x-test-fault':fault}});
  const result=await response.json();if(status!==null)assert.equal(response.status,status,JSON.stringify(result));return {input,result,status:response.status};
}
const batch=index=>({op:'import',index,text:readFileSync(join(directory,`batch-${String(index).padStart(5,'0')}.json`),'utf8')});
try{
  let db=await mf.getD1Database('DB');
  for(const name of ['0000_dazzling_tenebrous','0001_problem_bank','0002_compact_bank','0003_operator_ledger'])await db.exec(readFileSync('drizzle/'+name+'.sql','utf8').split('\n').filter(l=>!l.trim().startsWith('--')).join(' '));
  for(let i=0;i<4;i++)await db.batch([...JSON.parse(batch(i).text).map(s=>db.prepare(s)),db.prepare('INSERT INTO cbank_import_receipts VALUES (?,?)').bind(plan.bundleId+'/'+i,plan.batches[i].sha256)]);
  const initial=(await call({op:'init'})).result;assert.equal(initial.budget.provider.remainingReads,null);assert.ok(initial.budget.measuredWrites>=3860);
  const first=await call(batch(4));assert.equal(first.result.nextSequence,5);
  await mf.dispose();mf=create();db=await mf.getD1Database('DB');
  const replay=(await call(first.input)).result;assert.equal(replay.replayed,true);assert.equal(replay.budget.measuredWrites,first.result.budget.measuredWrites);
  await assert.rejects(runImport(null,directory,{mode:'operator-budget',local:true,startIndex:5,maxBatches:3,operator:async input=>(await call(input)).result}),/authenticated hosted/);
  const resumed=await runImport(null,directory,{mode:'operator-budget',startIndex:5,maxBatches:3,operator:async input=>(await call(input)).result});
  assert.equal(resumed.nextIndex,8);assert.equal(resumed.provider.remainingWrites,null);await call(batch(8),409);
  await call({op:'open',start:8,end:33},409);
  for(let page=0;page<10;page++)await call({op:'pilot',page});
  await call({op:'open',start:8,end:34},409);await call({op:'open',start:8,end:33});
  const before=(await call({op:'status'})).result;
  await db.prepare('UPDATE cbank_operator_ledger SET measured_writes=1299999').run();
  const exhausted=(await call(batch(8),503)).result;assert.match(exhausted.error,/write budget/);
  await db.prepare('UPDATE cbank_operator_ledger SET measured_writes=?').bind(before.budget.measuredWrites).run();
  await call({op:'status'},503,'missing-meta');
  const concurrent=await Promise.all([call(batch(8),null),call(batch(8),null)]);assert.equal(concurrent.filter(x=>x.status===200).length,1);assert.ok(concurrent.some(x=>[409,423].includes(x.status)));
  const denial=(await call(batch(9),503,'provider-quota')).result;assert.equal(denial.error,'provider-quota-or-limit');assert.equal(denial.pending,true);
  const recovery=(await call(batch(9),409)).result;assert.equal(recovery.committedReceipt,null);assert.equal(recovery.nextSequence,9);
  assert.equal((await db.prepare('SELECT count(*) AS n FROM cbank_import_receipts').all()).results[0].n,9);
  assert.equal((await db.prepare('SELECT count(*) AS n FROM cbank_config').all()).results[0].n,0);
  console.log(JSON.stringify({passed:true,scope:'local authenticated Worker/D1',providerTelemetry:null,tested:['operator mode','persistent accounting','lost response/restart replay','four-batch validation','25-batch cap','cumulative budget','missing counters','single in-flight lock','provider denial preserves checkpoint'],active:false}));
}finally{await mf.dispose();rmSync(persist,{recursive:true,force:true});}
