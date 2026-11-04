import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,copyFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {openDatabase,insertProblem,canonical} from '../scripts/bank/admin.mjs';
import {openCompact,syncCompact} from '../scripts/bank/compact.mjs';
import {prepareDelta,servingManifest} from '../scripts/bank/delta.mjs';
import {selectBankQuestions,assertBankSetPlayable} from '../lib/server/compact-bank-selection.ts';
import {sqliteD1} from '../scripts/bank/sqlite-d1.mjs';
import reviewedQuality from '../lib/server/solution-reviews/quality.json' with {type:'json'};
const sha=v=>createHash('sha256').update(v).digest('hex');

test('large finite policy manifests remain fully bound without oversized SQL literals',()=>{
 const manifest={schemaVersion:2,releaseId:'qa-v4',parentRelease:'qa-v3',approvedCount:3292,artifactSha256:'a'.repeat(64),coverage:{'integration/easy':120},exclusions:Array.from({length:1400},(_,i)=>({problemId:'cn_'+i,revision:1,scope:'global',reason:'Exact finite disposition, preserved with historical content.'}))};
 assert.ok(Buffer.byteLength(canonical(manifest))>90000);
 const stored=servingManifest(manifest);
 assert.ok(Buffer.byteLength(canonical(stored))<5000);
 assert.equal(stored.fullManifestSha256,sha(canonical(manifest)));
 assert.equal(stored.policy.exclusions.count,1400);
 assert.equal(stored.policy.exclusions.sha256,sha(canonical(manifest.exclusions)));
 const changed=structuredClone(manifest);changed.exclusions[0].reason+=' Revised evidence.';
 assert.notEqual(servingManifest(changed).fullManifestSha256,stored.fullManifestSha256);
});

test('actual delta preparation exports flattened memberships, new revisions, exclusions and persistent withdrawals idempotently',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'quality-delta-contract-')),baseline=join(dir,'baseline.sqlite'),source=openDatabase(':memory:'),db=openCompact(baseline);
 try{
  const slug='quality-delta-contract-fixture',family='standalone-'+slug;
  const spec={slug,coefficients:[[1,1],[2,1]],operation:'definite-integral',point:[0,1],upper:[1,1],distractors:[{value:[1,1],misconception:'Omit linear term'},{value:[3,1],misconception:'Use endpoint value'},{value:[4,1],misconception:'Double the complete result'}],topic:'integration',difficulty:'easy',pedagogy:{constructionId:family,relatedIdeaGroupId:'test-polynomial-integral',structuralSignature:'test-only',primaryTechnique:'power-rule',alternativeTechniques:[],prerequisites:['polynomial integration'],reasoningDemand:['execution'],answerForm:'rational',difficultyRationale:'Contract fixture only; not release coverage.',sourceRecordIds:[],responseFormat:'multiple-choice'}};
  const built=spawnSync('.bank-venv/bin/python',['-c',"import sys,json;sys.path.insert(0,'scripts/bank/content');import standalone;s=json.load(sys.stdin);print(json.dumps([standalone.build(s),standalone.build(dict(s,revision=2,difficulty='medium'))]))"],{input:JSON.stringify(spec),encoding:'utf8'});
  assert.equal(built.status,0,built.stderr);const [old,revised]=JSON.parse(built.stdout);
  assert.throws(()=>insertProblem(source,old),/source-bound/,'a mathematical constructor alone cannot confer editorial admission');
  // The test's isolated process supplies two exact, test-only review entries.
  // No registry file is written and no production approval path is bypassed.
  for(const p of [old,revised]){
   assert.equal(p.choices.find(c=>c.choiceId===p.answerChoiceId).math,'2','independent fixture integral of 1+2x on [0,1]');
   assert.deepEqual(new Set(p.choices.map(c=>c.math)),new Set(['1','2','3','4']));
   reviewedQuality[p.problemId+'@'+p.problemRevision]={sourceContentHash:p.contentHash,revision:p.problemRevision,auditId:'isolated-delta-test-fixture'};
  }
  insertProblem(source,old);
  for(const release of ['v1','v2','v3']){
   source.prepare("INSERT INTO bank_releases VALUES (?,'{}',1,'published')").run(release);
   source.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?)').run(release,'integration','easy','*',family,1);
   source.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run(release,'integration','easy','*',family,0,old.problemId,1);
   syncCompact(source,db,release);
  }
  db.exec("UPDATE cbank_releases SET state='published'; INSERT INTO cbank_release_sources VALUES ('v2','v1'),('v3','v1'),('v3','v2'); INSERT INTO cbank_config VALUES ('active_release','v3')");
  const original=db.prepare('SELECT * FROM cbank_problems').all();db.close();
  const text=canonical(revised)+'\n';writeFileSync(join(dir,'items.jsonl'),text);
  const manifest={schemaVersion:2,releaseId:'v4',parentRelease:'v3',artifact:'items.jsonl',artifactSha256:sha(text),approvedCount:1,coverage:{'integration/medium':1},families:{[family]:1},priorOperation:{kind:'delta',bundleId:'settled-fixture'},operationAllowance:{reads:500000,writes:100000,bytes:150000000},exclusions:[{problemId:old.problemId,revision:1,scope:'global',reason:'Contract fixture: globally invalid prior revision'}],withdrawals:[{sourceReleaseId:'v1',familyId:family,reason:'Contract fixture: withdrawn old pool'}],lineage:[{problemId:old.problemId,lineageId:old.problemId}]};
  const path=join(dir,'manifest.json');writeFileSync(path,JSON.stringify(manifest));
  const output=join(dir,'prepared'),result=await prepareDelta(path,baseline,output),again=await prepareDelta(path,baseline,join(dir,'repeat'));
  assert.equal(again.bundleId,result.bundleId,'repeat preparation does not multiply membership or change plan identity');
  const plan=JSON.parse(readFileSync(join(output,'plan.json')));assert.deepEqual(plan.parentSources,['v1','v2','v3']);assert.equal(plan.cells.length,28);
  for(const table of ['cbank_release_exclusions','cbank_withdrawn_families','cbank_problem_lineage'])assert.equal(plan.tableHashes.find(t=>t.table===table).count,1);
  const targetPath=join(dir,'imported.sqlite');copyFileSync(baseline,targetPath);const target=openCompact(targetPath),d1=sqliteD1(target);
  try{
   for(let pass=0;pass<2;pass++)for(const batch of plan.batches){target.exec('BEGIN');try{for(const sql of JSON.parse(readFileSync(join(output,batch.file))))target.exec(sql);target.exec('COMMIT');}catch(error){target.exec('ROLLBACK');throw error;}}
   assert.equal(target.prepare("SELECT count(*) n FROM cbank_release_sources WHERE release_id='v4'").get().n,3);
   assert.equal(target.prepare('SELECT count(*) n FROM cbank_problems').get().n,2);
   const oldQuestions=(await selectBankQuestions(d1,{category:'integration',difficulty:'easy',count:1})).questions;assert.equal(oldQuestions[0].problemRevision,1);
   target.exec("UPDATE cbank_releases SET state='published' WHERE release_id='v4'; UPDATE cbank_config SET value='v4' WHERE key='active_release'");
   const current=await selectBankQuestions(d1,{category:'integration',difficulty:'medium',count:1});assert.equal(current.questions[0].problemRevision,2);
   await assert.rejects(assertBankSetPlayable(d1,oldQuestions),'globally incorrect pending set cannot begin a new game');
   target.exec("UPDATE cbank_config SET value='v3' WHERE key='active_release'");
   await assert.rejects(selectBankQuestions(d1,{category:'integration',difficulty:'easy',count:1}),'pointer rollback does not revive globally invalid revision');
   assert.deepEqual(target.prepare('SELECT * FROM cbank_problems WHERE revision=1').all(),original,'canonical historical bytes are unchanged');
  }finally{target.close();}
 }finally{source.close();try{db.close();}catch{}rmSync(dir,{recursive:true,force:true});}
});
