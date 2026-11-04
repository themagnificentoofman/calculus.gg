import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { openCompact } from '../scripts/bank/compact.mjs';
import { hash, canonical } from '../scripts/bank/admin.mjs';
import { sqliteD1 } from '../scripts/bank/sqlite-d1.mjs';
import { selectBankQuestions } from '../lib/server/compact-bank-selection.ts';
import { recordExposures, exposureWeight, MAX_EXPOSURES } from '../lib/bank/exposure.ts';
import { publicGame } from '../lib/server/game-engine.ts';

const seed=n=>()=>{n|=0;n=n+0x6D2B79F5|0;let t=Math.imul(n^n>>>15,1|n);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};
// Algorithm fixtures only: these deliberately repeated formulae are never
// authored, counted, imported, or reported as new mathematical constructions.
function fixture(families=30,perFamily=12){
 const sql=openCompact(':memory:'),sample=JSON.parse(readFileSync(new URL('./fixtures/bank/review-samples.json',import.meta.url)))[0];
 sql.exec("INSERT INTO cbank_releases VALUES ('qa-parent','{}',1,'published'); INSERT INTO cbank_releases VALUES ('qa-content','{}',1,'published'); INSERT INTO cbank_release_sources VALUES ('qa-content','qa-parent'); INSERT INTO cbank_config VALUES ('active_release','qa-content');");
 let ref=0;
 for(let f=0;f<families;f++){
  const family='qa-family-'+f,pool=f+1;
  sql.prepare('INSERT INTO cbank_pools VALUES (?,?,?,?,?,?,?)').run(pool,f===0?'qa-parent':'qa-content','integration','olympiad','*',family,perFamily);
  for(let i=0;i<perFamily;i++){
   ref++;const p={...structuredClone(sample),problemId:'cn_'+hash({f,i}).slice(0,20),schemaVersion:2,familyId:family,topic:'integration',difficulty:'olympiad',pedagogy:{constructionId:family,relatedIdeaGroupId:'qa-idea-'+f,structuralSignature:'qa-structure-'+f,primaryTechnique:'qa-technique-'+f,alternativeTechniques:['ignored-alternative'],prerequisites:[],reasoningDemand:['recognition'],answerForm:'exact-real',difficultyRationale:'algorithm fixture, not content',sourceRecordIds:[],responseFormat:'multiple-choice'}};
   delete p.contentHash;p.contentHash=hash(p);const {problemId,problemRevision,semanticHash,contentHash,...body}=p;
   sql.prepare('INSERT INTO cbank_shared VALUES (?,?,?)').run(ref,Buffer.from(hash({ref}),'hex'),'{}');
   sql.prepare('INSERT INTO cbank_problems VALUES (?,?,?,?,?,?,?)').run(ref,problemId,problemRevision,Buffer.from(contentHash,'hex'),Buffer.from(semanticHash,'hex'),ref,gzipSync(canonical(body)));
   sql.prepare("INSERT INTO cbank_publication VALUES (?,'approved',NULL)").run(ref);
   sql.prepare('INSERT INTO cbank_slots VALUES (?,?,?)').run(pool,i,ref);
   sql.prepare('INSERT INTO cbank_selection_features VALUES (?,?,?,?,?,?)').run(ref,p.pedagogy.relatedIdeaGroupId,p.pedagogy.structuralSignature,p.pedagogy.primaryTechnique,'recognition:'+p.pedagogy.primaryTechnique,1);
  }
 }
 return {sql,db:sqliteD1(sql)};
}
const counts=q=>q.reduce((a,p)=>(a[p.familyId]=(a[p.familyId]||0)+1,a),{});
test('broad pools preserve caps, adjacency, hard filters and exact uniqueness across seeded rounds',async()=>{
 const {sql,db}=fixture(12,20);
 try{for(let n=0;n<100;n++)for(const count of [5,20]){
  const r=await selectBankQuestions(db,{category:'integration',difficulty:'olympiad',count},{},seed(n));
  assert.equal(new Set(r.questions.map(q=>q.problemId)).size,count);
  assert.ok(Math.max(...Object.values(counts(r.questions)))<=2);
  assert.ok(r.questions.every((q,i)=>!i||q.familyId!==r.questions[i-1].familyId));
  assert.ok(r.questions.every(q=>q.topic==='integration'&&q.difficulty==='olympiad'&&q.bankRelease==='qa-content'));
  assert.equal(r.relaxation,'none');assert.ok(r.diagnostics.statements<=10);assert.ok(r.diagnostics.probes<=320);
 }}finally{sql.close();}
});
test('ten consecutive priority rounds avoid exact repeats when eligible inventory supports them',async()=>{
 const {sql,db}=fixture(30,12);let history={},now=1_000_000;const issued=new Set();
 try{for(let n=0;n<10;n++){
  const r=await selectBankQuestions(db,{category:'integration',difficulty:'olympiad',count:20},history,seed(400+n),now);
  for(const q of r.questions){assert.equal(issued.has(q.problemId),false);issued.add(q.problemId);}
  assert.equal(r.relaxation,'none');history=recordExposures(history,'round-'+n,r.questions,'attempted',now);now+=600_000;
 }assert.equal(issued.size,200);}finally{sql.close();}
});
test('small and retired inventories relax explicitly and never cross filters',async()=>{
 const {sql,db}=fixture(1,20);
 try{
  const r=await selectBankQuestions(db,{category:'integration',difficulty:'olympiad',count:20},{},seed(9));
  assert.equal(r.relaxation,'family-cap');assert.ok(r.diagnostics.reasons.includes('family-cap-impossible'));
  assert.ok(r.diagnostics.reasons.includes('adjacency-unavoidable'));
  await assert.rejects(selectBankQuestions(db,{category:'limits',difficulty:'olympiad',count:1}));
  await assert.rejects(selectBankQuestions(db,{category:'integration',difficulty:'easy',count:1}));
  await assert.rejects(selectBankQuestions(db,{category:'integration',difficulty:'olympiad',tag:'absent',count:1}));
  sql.exec("UPDATE cbank_publication SET state='retired'");
  await assert.rejects(selectBankQuestions(db,{category:'integration',difficulty:'olympiad',count:1}));
 }finally{sql.close();}
});
test('unseen issuance expires quickly; displays cannot replace attempts or renew penalties',()=>{
 const q={problemId:'cn_qa',familyId:'qa',context:{techniqueTags:['method']}};let h=recordExposures({},'round-one',[q],'issued',1000);
 assert.equal(exposureWeight(h.exposures[0],601_001),0);
 h=recordExposures(h,'round-one',[q],'displayed',2000);assert.equal(h.exposures[0].stage,'displayed');
 h=recordExposures(h,'round-one',[q],'attempted',3000);h=recordExposures(h,'round-one',[q],'displayed',4000);
 assert.equal(h.exposures[0].stage,'attempted');assert.equal(h.exposures[0].at,3000);
 assert.ok(exposureWeight(h.exposures[0],86400_000)>0);
 for(let i=0;i<600;i++)h=recordExposures(h,'round-'+i,[{...q,problemId:'cn_'+i}],'issued',5000+i);
 assert.equal(h.exposures.length,MAX_EXPOSURES);assert.ok(h.exposures.some(e=>e.stage==='attempted'));
});
test('solution-revealing pedagogy is absent from the public game projection',()=>{
 const game={players:['qa'],questions:[{latexProblem:'x',options:['1','2','3','4'],topic:'integration',difficulty:'olympiad',pedagogy:{primaryTechnique:'SECRET_METHOD',relatedIdeaGroupId:'SECRET_IDEA'},explanation:['SECRET_SOLUTION']}],answers:{},status:'active'};
 assert.equal(JSON.stringify(publicGame(game)).includes('SECRET'),false);
});

test('late reports of old rounds cannot crowd fresh history with expired displays',()=>{
 const q={problemId:'old',familyId:'old-family'},fresh={problemId:'fresh',familyId:'fresh-family'};
 const now=20*86400_000,history=recordExposures({},'fresh-round',[fresh],'issued',now);
 const result=recordExposures(history,'old-round',[q],'displayed',1,now);
 assert.deepEqual(result.exposures.map(e=>e.problemId),['fresh']);
});
