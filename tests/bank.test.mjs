import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,mkdtempSync,rmSync,readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { openDatabase,insertProblem,validateRecord,hash,releaseContract,importRelease } from '../scripts/bank/admin.mjs';
import { sqliteD1 } from '../scripts/bank/sqlite-d1.mjs';
import { selectBankQuestions,BankUnavailableError,assertBankSetPlayable } from '../lib/server/bank-selection.ts';
import { createGameApi } from '../lib/server/game-api.ts';
import { createServerGames,publicGame } from '../lib/server/game-engine.ts';
import { consumeBankReadQuota } from '../lib/server/quota.ts';
import { createProblemReport } from '../lib/server/problem-report.ts';
import { makePlan,consumeResults,validateSubmission } from '../scripts/bank/author-batch.mjs';
const samples=JSON.parse(readFileSync(new URL('./fixtures/bank/review-samples.json',import.meta.url),'utf8'));
function fixture(){
 const sql=openDatabase(':memory:');
 sql.exec("CREATE TABLE ai_quota (key TEXT PRIMARY KEY,count INTEGER NOT NULL,expires_at INTEGER NOT NULL)");
 sql.prepare('INSERT INTO bank_releases VALUES (?,?,?,?)').run('test-release','{}',samples.length,'published');
 sql.prepare('INSERT INTO bank_config VALUES (?,?)').run('active_release','test-release');
 for(const p of samples){insertProblem(sql,p);for(const tag of ['*',...p.techniqueTags]){sql.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?)').run('test-release',p.topic,p.difficulty,tag,p.familyId,1);sql.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run('test-release',p.topic,p.difficulty,tag,p.familyId,0,p.problemId,p.problemRevision);}}
 return {sql,db:sqliteD1(sql)};
}
function memoryStore(){
 const data=new Map();let queue=Promise.resolve();const tx={get:async key=>structuredClone(data.get(key)||null),set:(key,value)=>data.set(key,structuredClone(value)),delete:key=>data.delete(key)};
 return {data,get:tx.get,find:async()=>[],transaction:fn=>{const result=queue.then(()=>fn(tx));queue=result.catch(()=>{});return result;}};
}
const request=(resource,body,uid='player-123')=>new Request('https://test.invalid/api/'+resource,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+uid},body:JSON.stringify(body)});
test('release identity excludes run timing while retaining artifact and coverage identity',()=>{assert.deepEqual(releaseContract({releaseId:'r',artifactSha256:'a',elapsedSeconds:1,generatedThisRun:10}),releaseContract({releaseId:'r',artifactSha256:'a',elapsedSeconds:99,generatedThisRun:0}));});
test('every family sample has a valid immutable hash, provenance, four choices, and renderable solution',()=>{assert.equal(samples.length,72);for(const p of samples)validateRecord(p);assert.equal(new Set(samples.map(p=>p.topic+'/'+p.difficulty)).size,24);});
test('imports are idempotent, revisions immutable and consecutive, and cosmetic duplicates cannot change identity',()=>{
 const {sql}=fixture();const p=samples[0];assert.equal(insertProblem(sql,p),false);
 assert.throws(()=>insertProblem(sql,{...p,statement:'tampered'}),/hash/);
 const different={...p,statement:p.statement+'+0'};delete different.contentHash;different.contentHash=hash(different);assert.throws(()=>insertProblem(sql,different),/revision conflict/);
 const revision={...p,problemRevision:2,solutionSteps:[...p.solutionSteps,String.raw`\textnormal{An additional check.}`]};delete revision.contentHash;revision.contentHash=hash(revision);assert.equal(insertProblem(sql,revision),true);
 assert.throws(()=>sql.prepare('UPDATE bank_problems SET payload_json=?').run('{}'),/new problem revision/);
 assert.throws(()=>sql.exec('DELETE FROM bank_problems'),/historical/);
 const duplicate={...p,problemId:'cn_'+'a'.repeat(20)};delete duplicate.contentHash;duplicate.contentHash=hash(duplicate);assert.throws(()=>insertProblem(sql,duplicate),/Duplicate/);sql.close();
});
test('indexed selection preserves filters, stable identities, unique round problems, and bounded repetition relaxation',async()=>{
 const {sql,db}=fixture();const input={category:'integration',difficulty:'medium',count:3};
 const first=await selectBankQuestions(db,input);assert.equal(first.questions.length,3);assert.equal(new Set(first.questions.map(q=>q.problemId)).size,3);
 assert.ok(first.questions.every(q=>q.topic==='integration'&&q.difficulty==='medium'&&q.choiceOrder.length===4));
 const recent={problems:first.questions.map(q=>q.problemId),families:first.questions.map(q=>q.familyId)};
 assert.equal((await selectBankQuestions(db,input,recent)).relaxation,'recent-problems');
 const tagged=await selectBankQuestions(db,{...input,count:1,tag:'substitution'});assert.equal(tagged.questions[0].familyId,'quadratic-substitution');
 await assert.rejects(selectBankQuestions(db,{...input,tag:'not-published'}),BankUnavailableError);
 await assert.rejects(selectBankQuestions(db,{...input,count:4}),BankUnavailableError);
 await assertBankSetPlayable(db,first.questions);
 const id=first.questions[0].problemId;sql.prepare("UPDATE bank_publication SET state='retired',retirement_reason='test' WHERE problem_id=?").run(id);
 await assert.rejects(selectBankQuestions(db,input),BankUnavailableError);await assert.rejects(assertBankSetPlayable(db,first.questions),BankUnavailableError);assert.ok(sql.prepare('SELECT payload_json FROM bank_problems WHERE problem_id=?').get(id));sql.close();
});
test('bank mode makes zero model calls and keeps owner-bound sets, shared permutations, reviews, XP, and ratings',async()=>{
 const {sql,db}=fixture(),store=memoryStore();let now=100000;const originalFetch=globalThis.fetch;
 globalThis.fetch=async()=>{throw Error('Network/model call forbidden');};
 try{
 const api=createGameApi({store,now:()=>now,verify:async token=>({sub:token}),select:(input,recent)=>selectBankQuestions(db,input,recent),quota:async()=>true});
 const call=async(uid,resource,body,status=200)=>{const r=await api(resource,request(resource,body,uid));const v=await r.json();assert.equal(r.status,status,JSON.stringify(v));return v;};
 for(const uid of ['player-one','player-two'])await call(uid,'profile',{});
 store.data.get('users/player-one').xp=500;store.data.get('users/player-one').rating=123;
 const set=await call('player-one','questions',{category:'integration',difficulty:'easy',count:3,mode:'pvp'});assert.deepEqual(Object.keys(set).sort(),['questionCount','questionSetId']);
 await call('player-two','games',{action:'create',questionSetId:set.questionSetId,mode:'pvp',options:{}},403);
 const created=await call('player-one','games',{action:'create',questionSetId:set.questionSetId,mode:'pvp',options:{}});assert.equal(created.game.questions.length,0);
 await call('player-two','games',{action:'join',gameId:created.id,mode:'pvp'});now+=4000;
 const secret=store.data.get('gameSecrets/'+created.id);assert.equal(secret.roundSnapshot.questions.length,3);
 const a=await call('player-one','games',{action:'view',gameId:created.id}),b=await call('player-two','games',{action:'view',gameId:created.id});
 assert.deepEqual(a.game.questions,b.game.questions);for(const text of ['correctIndex','explanation','answerChoiceId','roundSnapshot','basisResults'])assert.ok(!JSON.stringify(a).includes(text));
 for(let i=0;i<3;i++){
   await call('player-one','games',{action:'answer',gameId:created.id,index:i,selectedOption:secret.questions[i].correctIndex});
   await call('player-two','games',{action:'answer',gameId:created.id,index:i,selectedOption:secret.questions[i].correctIndex});
 }
 assert.equal(store.data.get('users/player-one').xp,530);assert.equal(store.data.get('users/player-two').xp,30);
 const before=structuredClone(store.data.get('users/player-one'));await call('player-one','games',{action:'claim',gameId:created.id});assert.deepEqual(store.data.get('users/player-one'),before);
 const old=JSON.stringify(secret.roundSnapshot);sql.exec("UPDATE bank_publication SET state='retired',retirement_reason='test'");assert.equal(JSON.stringify(store.data.get('gameSecrets/'+created.id).roundSnapshot),old);
 await call('player-one','questions',{category:'integration',difficulty:'easy',count:3,mode:'test'},409);
 assert.ok(store.data.get('bankRecent/player-two').problems.length===3);
 }finally{globalThis.fetch=originalFetch;sql.close();}
});
test('public projection is an allowlist even when a revision gains new secret fields',()=>{const q={...samples[0],latexProblem:'x',options:['1','2','3','4'],correctIndex:0,explanation:['1']};const game=publicGame({mode:'test',status:'active',players:['u'],scores:{u:0},questions:[q]});assert.deepEqual(Object.keys(game.questions[0]).sort(),['difficulty','latexProblem','options','problemId','problemRevision','topic']);});
test('read quotas are separate from authoring and reports never reveal content',async()=>{
 const {sql,db}=fixture();assert.equal((await Promise.all(Array.from({length:15},()=>consumeBankReadQuota(db,'player-one',1000)))).filter(Boolean).length,12);
 assert.equal(sql.prepare("SELECT COUNT(*) AS n FROM ai_quota WHERE key='site:day'").get().n,0);
 const p=samples[0];const report=createProblemReport({db,layout:'original',verify:async()=>({sub:'player-one'}),quota:async()=>true});
 const r=await report(request('problems/report',{problemId:p.problemId,problemRevision:1,reason:'Please check this solution.'}));assert.deepEqual(await r.json(),{ok:true});assert.equal(sql.prepare('SELECT count(*) AS n FROM bank_reports').get().n,1);
 assert.equal((await report(request('problems/report',{problemId:p.problemId,problemRevision:1,reason:'short',answer:true}))).status,400);sql.close();
});
test('offline Batch plan bounds cost and matches unordered results by ID without approving model output',()=>{
 const plan=makePlan(2);assert.ok(plan.worstUSD<0.02);assert.equal(plan.authorizedUSD,0);
 const requestText=plan.requests.map(r=>JSON.stringify(r)).join('\n')+'\n';
 validateSubmission(plan,requestText,plan.worstUSD);
 assert.throws(()=>validateSubmission(plan,requestText+requestText,plan.worstUSD),/payload changed/);
 assert.throws(()=>validateSubmission({...plan,worstUSD:0},requestText,0),/payload changed/);
 assert.throws(()=>validateSubmission(plan,requestText,0),/Explicit cap/);
 assert.throws(()=>validateSubmission({...plan,status:'submitting'},requestText,plan.worstUSD),/ambiguous/);
 const row=id=>({custom_id:id,response:{status_code:200,body:{status:'completed',usage:{input_tokens:100,output_tokens:20},output:[{type:'message',content:[{type:'output_text',text:JSON.stringify({family:'proposal',topic:'integration',difficulty:'easy',techniques:['substitution'],mathematicalSpecification:'proposal',domainProof:'proposal',independentVerificationPlan:'proposal',distractorRationale:'proposal'})}]}]}}});
 consumeResults(plan,plan.requests.slice().reverse().map(r=>JSON.stringify(row(r.custom_id))).join('\n'));assert.equal(plan.counts.generated,2);assert.equal(plan.counts.approved,0);assert.equal(plan.counts.published,0);assert.equal(plan.costPerApprovedProblemUSD,null);
 consumeResults(plan,JSON.stringify(row(plan.requests[0].custom_id)));assert.equal(plan.counts.duplicate,1);assert.throws(()=>consumeResults(plan,JSON.stringify(row('unknown'))),/Unknown/);
});

test('release imports revalidate math, resume idempotently, and reject forged approval evidence',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'calculus-bank-')),sql=openDatabase(':memory:');
 const write=rows=>{const artifact=rows.map(p=>JSON.stringify(p)).join('\n')+'\n';writeFileSync(join(dir,'rows.jsonl'),artifact);const coverage={},families={};for(const p of rows){const key=p.topic+'/'+p.difficulty;coverage[key]=(coverage[key]||0)+1;families[p.familyId]=(families[p.familyId]||0)+1;}const manifest={schemaVersion:1,releaseId:'validated-fixture',artifact:'rows.jsonl',artifactSha256:createHash('sha256').update(artifact).digest('hex'),approvedCount:rows.length,coverage,families};writeFileSync(join(dir,'manifest.json'),JSON.stringify(manifest));return join(dir,'manifest.json');};
 try {
  const p=structuredClone(samples[0]);p.answerChoiceId=p.choices[1].choiceId;delete p.contentHash;p.contentHash=hash(p);
  await assert.rejects(importRelease(sql,write([p,...samples.slice(1)])),/mathematical verification failed/);
  assert.equal(sql.prepare('SELECT count(*) AS n FROM bank_problems').get().n,0);
  const manifest=write(samples);const first=await importRelease(sql,manifest),second=await importRelease(sql,manifest);
  assert.equal(first.imported,72);assert.equal(second.imported,0);assert.equal(second.duplicateSafeExisting,72);
  assert.equal(sql.prepare("SELECT count(*) AS n FROM bank_slots WHERE tag='*'").get().n,72);
 }finally{sql.close();rmSync(dir,{recursive:true,force:true});}
});

test('SQL exports resume without overwrites, propagate retirement and fail closed on incomplete activation',()=>{
 const dir=mkdtempSync(join(tmpdir(),'calculus-export-')),source=join(dir,'source.sqlite'),out=join(dir,'sql');
 const {sql}=fixture();sql.exec(`VACUUM INTO '${source}'`);sql.close();
 const target=openDatabase(':memory:');
 const exportRows=()=>{const result=spawnSync(process.execPath,['scripts/bank/admin.mjs','export',source,out],{encoding:'utf8'});assert.equal(result.status,0,result.stderr);return readdirSync(out).filter(n=>n.startsWith('bank-')).sort().map(n=>readFileSync(join(out,n),'utf8'));};
 try {
  const initial=exportRows();for(const text of initial)target.exec(text);for(const text of initial)target.exec(text);
  target.exec(readFileSync(join(out,'activate-after-verification.sql'),'utf8'));
  assert.equal(target.prepare('SELECT count(*) AS n FROM bank_problems').get().n,72);
  const operator=openDatabase(source);operator.prepare("UPDATE bank_publication SET state='retired',retirement_reason='Verified correction' WHERE problem_id=?").run(samples[0].problemId);operator.close();
  for(const text of exportRows())target.exec(text);for(const text of initial)target.exec(text);
  assert.equal(target.prepare('SELECT state FROM bank_publication WHERE problem_id=?').get(samples[0].problemId).state,'retired');
  assert.throws(()=>target.exec(readFileSync(join(out,'activate-after-verification.sql'),'utf8')),/CHECK constraint/);
  assert.throws(()=>target.exec(initial[0].replace(samples[0].contentHash,'0'.repeat(64))),/CHECK constraint/);
 }finally{target.close();rmSync(dir,{recursive:true,force:true});}
});
