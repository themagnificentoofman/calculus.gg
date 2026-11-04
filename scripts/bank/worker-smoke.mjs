#!/usr/bin/env node
// Local workerd + D1 compatibility check, with the committed 72-family fixture only.
import { Miniflare } from 'miniflare';
import { build } from 'esbuild';
import { readFileSync,mkdtempSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { openDatabase,insertProblem } from './admin.mjs';
import { openCompact,syncCompact } from './compact.mjs';
import { exportCompact,runImport,verifyImported,activateVerified } from './compact-import.mjs';
const dir=mkdtempSync(join(tmpdir(),'compact-worker-')),source=openDatabase(':memory:'),target=openCompact(':memory:');
const samples=JSON.parse(readFileSync('tests/fixtures/bank/review-samples.json','utf8'));
source.prepare("INSERT INTO bank_releases VALUES ('smoke','{}',?,'published')").run(samples.length);
for(const p of samples){insertProblem(source,p);for(const tag of ['*',...p.techniqueTags]){source.prepare('INSERT INTO bank_pools VALUES (?,?,?,?,?,?)').run('smoke',p.topic,p.difficulty,tag,p.familyId,1);source.prepare('INSERT INTO bank_slots VALUES (?,?,?,?,?,?,?,?)').run('smoke',p.topic,p.difficulty,tag,p.familyId,0,p.problemId,1);}}
syncCompact(source,target,'smoke');const plan=exportCompact(target,join(dir,'import'));
const fixtureReviews=samples.map(p=>({problemId:p.problemId,revision:p.problemRevision,contentHash:p.contentHash,familyId:p.familyId,constructionId:p.familyId,review:{path:'isolated-worker-fixture-only',sha256:'0'.repeat(64)},usefulness:'Worker storage/selector compatibility fixture; not production admission.'}));
const bundle=await build({stdin:{contents:`import {selectBankQuestions} from './lib/server/compact-bank-selection.ts';import {createLegacyPolicy} from './lib/server/legacy-selection.mjs';const policy=createLegacyPolicy(${JSON.stringify(fixtureReviews)});export default {async fetch(request,env){const result=await selectBankQuestions(env.DB,{category:'integration',difficulty:'easy',count:3,includeLegacy:true},{},undefined,undefined,policy);return Response.json({count:result.questions.length,ids:result.questions.map(q=>q.problemId),hashes:result.questions.map(q=>q.contentHash)});}};`,resolveDir:process.cwd()},bundle:true,write:false,format:'esm',platform:'browser',target:'es2022'});
const modules=[{type:'ESModule',path:'index.mjs',contents:bundle.outputFiles[0].text}];
const mf=new Miniflare({modules,modulesRoot:process.cwd(),compatibilityDate:'2026-04-01',d1Databases:{DB:'local-compact-smoke'}});
try{
  const db=await mf.getD1Database('DB');
  for(const migration of ['0001_problem_bank.sql','0002_compact_bank.sql','0004_flimsy_carlie_cooper.sql','0005_brief_skaar.sql','0006_quality_membership.sql','0007_quality_lookup.sql'])await db.exec(readFileSync('drizzle/'+migration,'utf8').replace(/--[^\n]*/g,'').replaceAll('\n',' '));
  await runImport(db,join(dir,'import'),{local:true});const verification=await verifyImported(db,plan);assert.equal(verification.verified,72);
  await activateVerified(db,plan,verification,'smoke');
  const response=await mf.dispatchFetch('http://local.invalid/'),body=await response.json();assert.equal(response.status,200);assert.equal(body.count,3);assert.equal(new Set(body.ids).size,3);assert.ok(body.hashes.every(h=>/^[a-f0-9]{64}$/.test(h)));
  console.log(JSON.stringify({runtime:'local workerd/Miniflare D1',verified:verification.verified,selected:body.count,cloudMetrics:'Not a production quota measurement'}));
}finally{await mf.dispose();source.close();target.close();rmSync(dir,{recursive:true,force:true});}
