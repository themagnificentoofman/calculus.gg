import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,mkdtempSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openDatabase,insertProblem,hash } from '../scripts/bank/admin.mjs';
import { openCompact,syncCompact,verifyCompact,activateCompact } from '../scripts/bank/compact.mjs';
import { exportCompact,loadPlan,runImport,localImportAdapter,verifyImported,activateVerified,collectMeta } from '../scripts/bank/compact-import.mjs';
import { sqliteD1 } from '../scripts/bank/sqlite-d1.mjs';
import { selectBankQuestions,assertBankSetPlayable,POOL_SQL,SLOT_SQL } from '../lib/server/compact-bank-selection.ts';
import { BankUnavailableError } from '../lib/server/bank-selection.ts';
import { decodeCompact,canonical } from '../lib/bank/compact-codec.mjs';
import { createGameApi } from '../lib/server/game-api.ts';
import { createProblemReport } from '../lib/server/problem-report.ts';
const samples=JSON.parse(readFileSync(new URL('./fixtures/bank/review-samples.json',import.meta.url),'utf8'));
function fixture(){
  const source=openDatabase(':memory:'),target=openCompact(':memory:');
  source.prepare("INSERT INTO bank_releases VALUES ('test-release','{}',?,'published')").run(samples.length);
  for(const p of samples){insertProblem(source,p);for(const tag of ['*',...p.techniqueTags]){source.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?)').run('test-release',p.topic,p.difficulty,tag,p.familyId,1);source.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run('test-release',p.topic,p.difficulty,tag,p.familyId,0,p.problemId,1);}}
  syncCompact(source,target,'test-release');activateCompact(target,'test-release');
  return {source,target,db:sqliteD1(target),close(){source.close();target.close();}};
}
test('compact conversion reconstructs canonical evidence, preserves immutable revisions and never revives retirement',async()=>{
  const f=fixture();try{
    assert.equal(verifyCompact(f.target,f.source).verified,72);
    syncCompact(f.source,f.target,'test-release');assert.equal(verifyCompact(f.target,f.source).verified,72);
    const p=samples[0],before=f.target.prepare('SELECT problem_ref FROM cbank_problems WHERE problem_id=?').get(p.problemId).problem_ref;
    const revision={...p,problemRevision:2,solutionSteps:[...p.solutionSteps,String.raw`\textnormal{An additional check.}`]};delete revision.contentHash;revision.contentHash=hash(revision);
    insertProblem(f.source,revision);f.source.prepare("UPDATE bank_publication SET state='retired',retirement_reason='Verified correction' WHERE problem_id=? AND revision=1").run(p.problemId);
    syncCompact(f.source,f.target,'test-release');assert.equal(verifyCompact(f.target,f.source).verified,73);
    assert.equal(f.target.prepare('SELECT problem_ref FROM cbank_problems WHERE problem_id=? AND revision=1').get(p.problemId).problem_ref,before);
    assert.equal(f.target.prepare('SELECT count(*) AS n FROM cbank_problems WHERE problem_id=?').get(p.problemId).n,2);
    assert.throws(()=>activateCompact(f.target,'test-release'),/Incomplete/);
    assert.throws(()=>f.target.exec("UPDATE cbank_problems SET payload_gzip=X'00'"),/new problem revision/);
    assert.throws(()=>f.target.exec('DELETE FROM cbank_problems'),/historical/);
    assert.throws(()=>f.target.exec("UPDATE cbank_shared SET metadata_json='{}'"),/immutable metadata/);
    assert.throws(()=>f.target.exec('DELETE FROM cbank_slots'),/membership/);
    f.source.prepare("INSERT INTO bank_releases VALUES ('corrected-release','{}',?,'published')").run(samples.length);
    f.source.exec("INSERT INTO bank_pools SELECT 'corrected-release',topic,difficulty,tag,family_id,item_count FROM bank_pools WHERE release_id='test-release'");
    f.source.prepare("INSERT INTO bank_slots SELECT 'corrected-release',topic,difficulty,tag,family_id,slot,problem_id,CASE WHEN problem_id=? THEN 2 ELSE revision END FROM bank_slots WHERE release_id='test-release'").run(p.problemId);
    syncCompact(f.source,f.target,'corrected-release');activateCompact(f.target,'corrected-release');
    const corrected=await selectBankQuestions(f.db,{category:p.topic,difficulty:p.difficulty,tag:p.techniqueTags[0],count:1});
    assert.equal(corrected.questions[0].problemId,p.problemId);assert.equal(corrected.questions[0].problemRevision,2);
    f.source.prepare("UPDATE bank_publication SET state='approved',retirement_reason=NULL WHERE problem_id=? AND revision=1").run(p.problemId);
    syncCompact(f.source,f.target,'test-release');assert.equal(f.target.prepare('SELECT state FROM cbank_publication WHERE problem_ref=?').get(before).state,'retired');
    const row=f.target.prepare('SELECT b.*,m.metadata_json FROM cbank_problems b JOIN cbank_shared m USING(shared_id) WHERE problem_id=? AND revision=1').get(p.problemId);
    assert.equal(canonical(await decodeCompact(row)),canonical(p));
    await assert.rejects(decodeCompact({...row,content_hash:new Uint8Array(32)}),/hash mismatch/);
    await assert.rejects(decodeCompact({...row,payload_gzip:new Uint8Array([0,1,2])}));
  }finally{f.close();}
});
test('compact indexed sampler respects filters/recency, bounds decompressions and rechecks retirement',async()=>{
  const f=fixture(),Original=globalThis.DecompressionStream;let decompressions=0;
  globalThis.DecompressionStream=class extends Original{constructor(...args){super(...args);decompressions++;}};
  try{
    const input={category:'integration',difficulty:'medium',count:3},selected=await selectBankQuestions(f.db,input);
    assert.equal(decompressions,3);assert.equal(new Set(selected.questions.map(p=>p.problemId)).size,3);
    assert.ok(selected.questions.every(p=>p.topic===input.category&&p.difficulty===input.difficulty));
    const repeated=await selectBankQuestions(f.db,input,{problems:selected.questions.map(p=>p.problemId),families:selected.questions.map(p=>p.familyId)});assert.equal(repeated.relaxation,'recent-problems');
    const tagged=await selectBankQuestions(f.db,{...input,count:1,tag:'substitution'});assert.equal(tagged.questions[0].familyId,'quadratic-substitution');
    await assert.rejects(selectBankQuestions(f.db,{...input,count:4}),BankUnavailableError);
    await assertBankSetPlayable(f.db,selected.questions);
    f.target.prepare("UPDATE cbank_publication SET state='retired' WHERE problem_ref=(SELECT problem_ref FROM cbank_problems WHERE problem_id=?)").run(selected.questions[0].problemId);
    await assert.rejects(selectBankQuestions(f.db,input),BankUnavailableError);await assert.rejects(assertBankSetPlayable(f.db,selected.questions),BankUnavailableError);
    for(const [sql,args] of [[POOL_SQL,['medium','*','integration','integration']],[SLOT_SQL,[1,0]]]){
      const plans=f.target.prepare('EXPLAIN QUERY PLAN '+sql).all(...args).map(r=>r.detail);
      assert.ok(plans.some(p=>/SEARCH/.test(p)));assert.ok(!plans.some(p=>/^SCAN (cbank|b\b|s\b|u\b)/.test(p)),plans.join('\n'));
    }
  }finally{globalThis.DecompressionStream=Original;f.close();}
});
test('compact import checksums, atomic receipts, interruption resume, immutable conflicts, verification and activation',async()=>{
  const f=fixture(),dir=mkdtempSync(join(tmpdir(),'compact-import-')),target=openCompact(':memory:');
  try{
    const folder=join(dir,'initial'),plan=exportCompact(f.target,folder,{rowsPerBatch:30}),db=localImportAdapter(target);
    await assert.rejects(runImport(db,folder),/Explicit positive tranche/);
    await assert.rejects(runImport(db,folder,{maxBatches:1}),/Supported Sites method/);
    let calls=0;const interrupted={...db,batch:async s=>{if(++calls===3)throw Error('Connection lost before commit');return db.batch(s);}};
    await assert.rejects(runImport(interrupted,folder,{local:true}),/Connection lost/);
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_import_receipts').get().n,2);
    const resumed=await runImport(db,folder,{local:true});assert.equal(resumed.skipped,2);
    const replay=await runImport(db,folder,{local:true});assert.equal(replay.skipped,plan.batches.length);assert.equal(replay.completed,0);
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_config').get().n,0);
    await assert.rejects(activateVerified(db,plan,{},'test-release'),/verification/);
    const verified=await verifyImported(db,plan);assert.equal(verified.verified,72);assert.equal(verified.metadata[0].rowsWritten,null);
    await activateVerified(db,plan,verified,'test-release');assert.equal(target.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,'test-release');
    // Lost response after commit is also resumable via the atomically committed receipt.
    const another=openCompact(':memory:');try{const d=localImportAdapter(another);let once=true;await assert.rejects(runImport({...d,batch:async s=>{const r=await d.batch(s);if(once){once=false;throw Error('Lost response');}return r;}},folder,{local:true}),/Lost response/);assert.equal((await runImport(d,folder,{local:true})).skipped,1);}finally{another.close();}
    const publication=f.target.prepare('SELECT problem_ref FROM cbank_problems LIMIT 1').get().problem_ref;
    f.target.prepare("UPDATE cbank_publication SET state='retired',retirement_reason='Correction' WHERE problem_ref=?").run(publication);
    const retiredDir=join(dir,'retired'),retiredPlan=exportCompact(f.target,retiredDir,{rowsPerBatch:30});await runImport(db,retiredDir,{local:true});
    // Re-executing stale approval statements cannot revive a retired revision, even without receipts.
    for(const b of plan.batches){const statements=JSON.parse(readFileSync(join(folder,b.file),'utf8')).filter(s=>s.startsWith('INSERT INTO cbank_publication'));if(statements.length)await db.batch(statements.map(s=>db.prepare(s)));}
    assert.equal(target.prepare('SELECT state FROM cbank_publication WHERE problem_ref=?').get(publication).state,'retired');
    await assert.rejects(verifyImported(db,plan),/mismatch/);
    const retiredVerification=await verifyImported(db,retiredPlan);await assert.rejects(activateVerified(db,retiredPlan,retiredVerification,'test-release'),/CHECK constraint/);
    const dataBatch=plan.batches.find(b=>JSON.parse(readFileSync(join(folder,b.file),'utf8')).some(s=>s.startsWith('INSERT INTO cbank_problems')));
    const statement=JSON.parse(readFileSync(join(folder,dataBatch.file),'utf8')).find(s=>s.startsWith('INSERT INTO cbank_problems'));
    await assert.rejects(db.batch([db.prepare(statement.replace(/X'[a-f0-9]{64}'/,"X'"+'0'.repeat(64)+"'"))]),/new problem revision/);
    writeFileSync(join(folder,plan.batches[0].file),'[]');assert.throws(()=>loadPlan(folder),/checksum/);
  }finally{target.close();f.close();rmSync(dir,{recursive:true,force:true});}
});
test('resource counters remain unknown locally and preserve actual provider metadata',()=>{
  assert.deepEqual(collectMeta([{meta:{rows_read:2,rows_written:3,size_after:99,duration:1}},{meta:{rows_read:4,rows_written:5,size_after:123,duration:2}}]),{rowsRead:6,rowsWritten:8,sizeAfter:123,sqlDurationMs:3});
  assert.equal(collectMeta({results:[]}).rowsWritten,null);
});
test('tranches enforce exact boundaries and reconcile every previous receipt before writing',async()=>{
  const f=fixture(),dir=mkdtempSync(join(tmpdir(),'compact-tranche-')),target=openCompact(':memory:');
  try{
    const folder=join(dir,'plan'),plan=exportCompact(f.target,folder,{rowsPerBatch:30}),db=localImportAdapter(target);
    const first=await runImport(db,folder,{local:true,maxBatches:2});
    assert.equal(first.completed,2);assert.equal(first.nextIndex,2);assert.equal(first.hasMore,true);
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_import_receipts').get().n,2);
    await assert.rejects(runImport(db,folder,{local:true,startIndex:3,maxBatches:1}),/Missing earlier receipt at sequence 2/);
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_import_receipts').get().n,2);
    const second=await runImport(db,folder,{local:true,startIndex:2,maxBatches:1});
    assert.equal(second.completed,1);assert.equal(second.skipped,2);assert.equal(second.nextIndex,3);
    const retry=await runImport(db,folder,{local:true,startIndex:2,maxBatches:1});
    assert.equal(retry.completed,0);assert.equal(retry.skipped,3);
    const last=await runImport(db,folder,{local:true,startIndex:3,maxBatches:plan.batches.length});
    assert.equal(last.hasMore,false);assert.equal(last.nextIndex,plan.batches.length);
    assert.equal((await verifyImported(db,plan)).verified,72);
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_config').get().n,0);
  }finally{target.close();f.close();rmSync(dir,{recursive:true,force:true});}
});
test('remote tranches fail closed on absent, stale, mismatched or exhausted allowances and missing counters',async()=>{
  // Synthetic counters exercise guard logic only. They are not production quota evidence.
  const f=fixture(),dir=mkdtempSync(join(tmpdir(),'compact-allowance-')),target=openCompact(':memory:');
  try{
    const folder=join(dir,'plan'),plan=exportCompact(f.target,folder,{rowsPerBatch:30}),base=localImportAdapter(target);
    let reads=0,writes=0,omitLookup=false,expireAfterLookup=false,omitWrite=false,current;
    const db={
      // Preserve real prepared statements for execution; attach synthetic test counters.
      prepare(text){const create=stmt=>({...stmt,bind:(...v)=>create(stmt.bind(...v)),all:async()=>{reads++;const result=await stmt.all();if(expireAfterLookup)current.validUntil=new Date(Date.now()-1).toISOString();return {...result,...(omitLookup?{}:{meta:{rows_read:1,rows_written:0,size_after:4096,duration:1}})};}});return create(base.prepare(text));},
      batch:async statements=>{writes++;const result=await base.batch(statements);return result.map(r=>({...r,...(omitWrite?{}:{meta:{rows_read:1,rows_written:2,size_after:8192,duration:1}})}));}
    };
    const grant=overrides=>({method:'synthetic-test-only',projectId:'appgprj_6ad91db3d4788191b3e73074e27447f5',binding:'DB',bundleId:plan.bundleId,startIndex:0,endIndexExclusive:1,remainingReads:10000,readReserve:100,remainingWrites:10000,writeReserve:100,currentSizeBytes:4096,estimatedImportBytes:100000,storageCeilingBytes:10000000,storageHeadroomBytes:4096,checkedAt:new Date().toISOString(),validUntil:new Date(Date.now()+60000).toISOString(),sharedUsageReservation:'synthetic-test-only',...overrides});
    const run=overrides=>runImport(db,folder,{maxBatches:1,refreshAllowance:async()=>current=grant(overrides)});
    await assert.rejects(runImport(db,folder,{maxBatches:1}),/Supported Sites method/);
    await assert.rejects(run({remainingReads:undefined}),/Fresh read\/write/);
    await assert.rejects(run({checkedAt:new Date(Date.now()-60000).toISOString()}),/Fresh read\/write/);
    await assert.rejects(run({endIndexExclusive:2}),/exact tranche/);
    await assert.rejects(run({remainingWrites:-1}),/Invalid resource/);
    assert.equal(reads,0);assert.equal(writes,0);
    await assert.rejects(run({remainingReads:100}),/next indexed receipt/);assert.equal(reads,0);
    await assert.rejects(run({remainingWrites:100}),/Write allowance/);assert.equal(writes,0);
    omitLookup=true;await assert.rejects(run({}),/Receipt-read allowance/);omitLookup=false;assert.equal(writes,0);
    expireAfterLookup=true;await assert.rejects(run({}),/expired during receipt lookup/);expireAfterLookup=false;assert.equal(writes,0);
    omitWrite=true;await assert.rejects(run({}),/Committed batch has no resource metadata/);omitWrite=false;
    assert.equal(target.prepare('SELECT count(*) AS n FROM cbank_import_receipts').get().n,1);
    const resumed=await run({});assert.equal(resumed.completed,0);assert.equal(resumed.skipped,1);assert.equal(writes,1);
    assert.equal(resumed.remainingAllowance.reads,9999);assert.equal(resumed.remainingAllowance.writes,10000);
  }finally{target.close();f.close();rmSync(dir,{recursive:true,force:true});}
});
test('compact gameplay preserves private snapshots, shared answer order, server XP and reports with no model calls',async()=>{
  const f=fixture(),data=new Map();let now=100000,queue=Promise.resolve();
  const tx={get:async key=>structuredClone(data.get(key)||null),set:(key,value)=>data.set(key,structuredClone(value)),delete:key=>data.delete(key)};
  const store={data,get:tx.get,find:async()=>[],transaction:fn=>{const r=queue.then(()=>fn(tx));queue=r.catch(()=>{});return r;}};
  const originalFetch=globalThis.fetch;globalThis.fetch=async()=>{throw Error('Network/model call forbidden');};
  const request=(resource,body,uid)=>new Request('https://test.invalid/api/'+resource,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+uid},body:JSON.stringify(body)});
  try{
    const api=createGameApi({store,now:()=>now,verify:async sub=>({sub}),select:(input,recent)=>selectBankQuestions(f.db,input,recent),checkPlayable:q=>assertBankSetPlayable(f.db,q),quota:async()=>true});
    const call=async(uid,resource,body,status=200)=>{const r=await api(resource,request(resource,body,uid)),v=await r.json();assert.equal(r.status,status,JSON.stringify(v));return v;};
    for(const uid of ['player-one','player-two'])await call(uid,'profile',{});
    const set=await call('player-one','questions',{category:'integration',difficulty:'easy',count:3,mode:'pvp'});
    await call('player-two','games',{action:'create',questionSetId:set.questionSetId,mode:'pvp',options:{}},403);
    const created=await call('player-one','games',{action:'create',questionSetId:set.questionSetId,mode:'pvp',options:{}});await call('player-two','games',{action:'join',gameId:created.id,mode:'pvp'});now+=4000;
    const secret=data.get('gameSecrets/'+created.id),snapshot=JSON.stringify(secret.roundSnapshot);
    assert.equal(secret.roundSnapshot.questions.length,3);assert.ok(secret.roundSnapshot.questions.every(q=>q.contentHash&&q.problemId&&q.bankRelease==='test-release'));
    const a=await call('player-one','games',{action:'view',gameId:created.id}),b=await call('player-two','games',{action:'view',gameId:created.id});assert.deepEqual(a.game.questions,b.game.questions);
    for(const key of ['correctIndex','explanation','answerChoiceId','roundSnapshot','payload_gzip','metadata_json'])assert.ok(!JSON.stringify(a).includes(key));
    f.target.exec("UPDATE cbank_publication SET state='retired',retirement_reason='Review'");
    for(let i=0;i<3;i++)for(const uid of ['player-one','player-two'])await call(uid,'games',{action:'answer',gameId:created.id,index:i,selectedOption:secret.questions[i].correctIndex});
    assert.equal(data.get('users/player-one').xp,30);assert.equal(JSON.stringify(data.get('gameSecrets/'+created.id).roundSnapshot),snapshot);
    const before=structuredClone(data.get('users/player-one'));await call('player-one','games',{action:'claim',gameId:created.id});assert.deepEqual(data.get('users/player-one'),before);
    await call('player-one','questions',{category:'integration',difficulty:'easy',count:3,mode:'test'},409);
    const report=createProblemReport({db:f.db,verify:async()=>({sub:'player-one'}),quota:async()=>true});
    const response=await report(request('problems/report',{problemId:samples[0].problemId,problemRevision:1,reason:'Please check this solution.'},'player-one'));assert.deepEqual(await response.json(),{ok:true});assert.equal(f.target.prepare('SELECT count(*) AS n FROM bank_reports').get().n,1);
  }finally{globalThis.fetch=originalFetch;f.close();}
});
