import test from 'node:test';
import assert from 'node:assert/strict';
import {createGameApi} from '../lib/server/game-api.ts';
import {publicGame} from '../lib/server/game-engine.ts';
import {createLegacyPolicy,includesLegacyForMode} from '../lib/server/legacy-selection.mjs';
import {fixtureLegacyPolicy} from './fixtures/bank/legacy-policy-fixture.mjs';
import samples from './fixtures/bank/review-samples.json' with {type:'json'};
import {verifyLegacyEligibility} from '../scripts/bank/quality/verify-legacy-eligibility.mjs';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {canonical} from '../lib/bank/compact-codec.mjs';

test('saved Experimental preference defaults off and only affects new solo question selection',async()=>{
 const records=new Map(),calls=[];
 const tx={get:async key=>structuredClone(records.get(key)||null),set:(key,value)=>records.set(key,structuredClone(value)),delete:key=>records.delete(key)};
 const store={...tx,find:async()=>[],transaction:async fn=>fn(tx)};
 const q={latexProblem:'x',options:['1','2','3','4'],correctIndex:0,explanation:['1'],topic:'integration',difficulty:'easy'};
 const api=createGameApi({store,verify:async sub=>({sub}),quota:async()=>true,select:async(input,history)=>{calls.push({input,history});return {questions:[q],relaxation:'none'};}});
 const request=async(resource,body,expected=200)=>{const response=await api(resource,new Request('https://example.test/api/'+resource,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer player-one'},body:JSON.stringify(body)}));const value=await response.json();assert.equal(response.status,expected,JSON.stringify(value));return value;};
 const select=mode=>request('questions',{mode,category:'integration',difficulty:'easy',count:1});
 assert.equal((await request('profile',{})).profile.settings.includeLegacyProblems,false);
 await select('test');assert.equal(calls.at(-1).input.includeLegacy,false);
 records.set('bankRecent/player-one',{problems:['unchanged-history']});
 await request('profile',{patch:{settings:{includeLegacyProblems:true}}});
 for(const mode of ['test','rapid']){await select(mode);assert.equal(calls.at(-1).input.includeLegacy,true);assert.deepEqual(calls.at(-1).history,{problems:['unchanged-history']});}
 for(const mode of ['pvp','multiplayer']){await select(mode);assert.equal(calls.at(-1).input.includeLegacy,false);assert.deepEqual(calls.at(-1).history,{});}
 await request('questions',{mode:'pvp',category:'integration',difficulty:'easy',count:1,includeLegacy:true},400);
 for(const invalid of ['true',1,null,{}])await request('profile',{patch:{settings:{includeLegacyProblems:invalid}}},400);
 const pending=structuredClone([...records].filter(([key])=>key.startsWith('questionSets/')));
 await request('profile',{patch:{settings:{includeLegacyProblems:false}}});
 assert.deepEqual([...records].filter(([key])=>key.startsWith('questionSets/')),pending);
 assert.deepEqual(records.get('bankRecent/player-one'),{problems:['unchanged-history']});
 await select('test');assert.equal(calls.at(-1).input.includeLegacy,false);
 assert.equal(includesLegacyForMode('test',{includeLegacyProblems:'true'}),false);
});

test('Legacy marker is public without exposing private solutions; historical snapshots stay unchanged',()=>{
 const q={familyId:'polynomial-area',latexProblem:'x',options:['1','2','3','4'],correctIndex:0,explanation:['private'],topic:'integration',difficulty:'easy'};
 const game={mode:'test',status:'active',players:['player-one'],scores:{},questions:[q]},saved=structuredClone(game);
 const visible=publicGame(game).questions[0];assert.equal(visible.legacy,true);
 for(const field of ['familyId','explanation','correctIndex'])assert.equal(field in visible,false);
 assert.deepEqual(game,saved);
});

test('approval is tied to source hash, revision, origin and usefulness; renaming does not erase legacy',()=>{
 const p=samples[0],policy=fixtureLegacyPolicy([p]);
 assert.equal(policy.check(p,p.familyId,true),true);
 assert.throws(()=>policy.check({...p,contentHash:'f'.repeat(64)},p.familyId,true),/Unreviewed/);
 assert.throws(()=>policy.check({...p,problemRevision:2},p.familyId,true),/Unreviewed/);
 assert.throws(()=>policy.check({...p,familyId:'renamed-copy'},p.familyId,true),/Unreviewed/);
 assert.throws(()=>policy.check({...p,familyId:'renamed-copy',pedagogy:{constructionId:p.familyId}},'renamed-copy',false),/Unreviewed/,'missing database alias cannot erase canonical origin');
 assert.throws(()=>policy.check(p,p.familyId,false),/Unreviewed/);
 assert.throws(()=>createLegacyPolicy([{problemId:p.problemId}]),/evidence/);
});

test('mandatory build/import gate rejects fabricated, stale and incomplete legacy evidence',()=>{
 const root=mkdtempSync(join(tmpdir(),'legacy-evidence-')),p=samples[0],path='review.json';
 const evidence={status:'independently-reviewed',author:'fixture-author',reviewer:'fixture-peer',records:[{problem:p,constructionId:p.familyId,usefulness:'Isolated gate fixture; not live approval.',passed:true,literalOptionsVerified:true,currentPresentationVerified:true,difficulty:p.difficulty,easiestOptionsVisibleRoute:'Fixture exact operation',optionAuditDisposition:'Fixture-only finite review'}]};
 const approval={problemId:p.problemId,revision:p.problemRevision,contentHash:p.contentHash,familyId:p.familyId,constructionId:p.familyId,usefulness:evidence.records[0].usefulness,review:{path,sha256:'0'.repeat(64)}},registry={schemaVersion:1,records:[approval]};
 const write=()=>{const text=JSON.stringify(evidence);writeFileSync(join(root,path),text);approval.review.sha256=createHash('sha256').update(text).digest('hex');};
 try{
  assert.throws(()=>verifyLegacyEligibility(root,registry),/ENOENT/);
  write();assert.deepEqual(verifyLegacyEligibility(root,registry),{verified:1,reports:1});
  approval.review.sha256='0'.repeat(64);assert.throws(()=>verifyLegacyEligibility(root,registry),/hash mismatch/);
  evidence.records[0].literalOptionsVerified=false;write();assert.throws(()=>verifyLegacyEligibility(root,registry),/Incomplete/);
  evidence.records[0].literalOptionsVerified=true;evidence.records[0].problem={...p,problemRevision:2};write();assert.throws(()=>verifyLegacyEligibility(root,registry),/unique exact/);
  const malformed={...p,solutionSteps:['\\notARealCommand']};delete malformed.contentHash;
  malformed.contentHash=createHash('sha256').update(canonical(malformed)).digest('hex');
  evidence.records[0].problem=malformed;approval.contentHash=malformed.contentHash;write();
  assert.throws(()=>verifyLegacyEligibility(root,registry),/solution|review|render/i,'self-consistent evidence cannot bypass ordinary solution admission');
 }finally{rmSync(root,{recursive:true,force:true});}
});
