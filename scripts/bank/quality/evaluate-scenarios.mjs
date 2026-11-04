#!/usr/bin/env node
// Supplementary fixtures use the final real catalog. They are not horizon runs
// or player telemetry; all history is explicit, retained, and source-bound.
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,writeFileSync,existsSync,copyFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {selectBankQuestions,POOL_SQL,candidateColumns,candidateJoins,eligibleSql} from '../../../lib/server/compact-bank-selection.ts';
import {legacyPolicy,legacyEligibilitySql} from '../../../lib/server/legacy-selection.mjs';
import {selectionFeatures} from '../../../lib/server/selection-vocabulary.mjs';
import {recordExposures,MAX_EXPOSURES} from '../../../lib/bank/exposure.ts';
import {sqliteD1} from '../sqlite-d1.mjs';
import {seeded,roundMeasures} from './evaluate-horizons.mjs';
import {topics,difficulties} from '../../../lib/server/questions-policy.mjs';

const [database,groupsPath,out]=process.argv.slice(2);
if(!out||existsSync(out))throw Error('Use a new report: DATABASE GROUPS REPORT');
const sha=b=>createHash('sha256').update(b).digest('hex'),originalHash=sha(readFileSync(database));
const groups=JSON.parse(readFileSync(groupsPath)),db=new DatabaseSync(database,{readOnly:true});
assert.match(db.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get()?.value||'',/quality-v4$/,'supplementary fixtures require the locally activated quality release');
const now=Date.UTC(2026,10,4,12),checks=[],failures=[];
function inventory(sql,input){
 const scope=legacyPolicy.selection(false),pools=sql.prepare(POOL_SQL).all(input.difficulty,input.tag||'*',input.category,input.category,scope.excludedFamilies),items=new Map();
 for(const pool of pools)for(const row of sql.prepare(`WITH context(active_release,legacy_families,legacy_revisions) AS (VALUES (?,?,?)) SELECT ${candidateColumns} FROM cbank_slots s ${candidateJoins} WHERE s.pool_id=? AND ${legacyEligibilitySql(eligibleSql)}`).all(pool.active_release,legacyPolicy.familyJson,scope.revisions,pool.pool_id)){
  const prior=items.get(row.lineage_id);if(!prior||prior.revision<row.revision)items.set(row.lineage_id,selectionFeatures(row));
 }
 return {pools,rows:[...items.values()]};
}
function historyOf(rows,at=now-3600000){
 let history={};
 for(const row of rows)history=recordExposures(history,'fixture-prior-'+row.problem_id,[{problemId:row.problem_id,familyId:row.source_family,constructionFamilyId:row.family_id,lineageId:row.lineage_id,pedagogy:{relatedIdeaGroupId:row.idea,structuralSignature:row.structure,primaryTechnique:row.technique,reasoningDemand:[]}}],'attempted',at,now);
 return history;
}
async function run(name,input,history={},expectation={},sql=db,seed=401){
 const metrics={statements:0,rows:0},began=performance.now(),before=JSON.stringify(history);
 let result,error;
 try{result=await selectBankQuestions(sqliteD1(sql,metrics),input,history,seeded(seed),now);}catch(e){error=e.message;}
 const check={name,input,initialHistoryEntries:history.exposures?.length||0,historySha256:sha(before),localMs:performance.now()-began,queries:metrics.statements,returnedRows:metrics.rows,error:error||null};
 try{
  assert.equal(JSON.stringify(history),before,'selection must not rewrite saved history');
  if(expectation.error){assert.ok(error,'genuinely unavailable inventory must fail');}
  else{
   assert.ifError(error);assert.equal(result.questions.length,input.count);
   const measures=roundMeasures(result.questions,groups,new Set((history.exposures||[]).map(e=>e.lineageId||e.problemId)));
   Object.assign(check,{relaxation:result.relaxation,diagnostics:result.diagnostics,measures,ids:result.questions.map(q=>q.problemId),families:result.questions.map(q=>q.constructionFamilyId)});
   assert.equal(measures.withinRoundDuplicates,0);assert.ok(result.questions.every(q=>q.difficulty===input.difficulty&&(input.category==='all'||q.topic===input.category)));
   if(expectation.unseen){assert.equal(measures.exactEquivalentRepeats,0);assert.equal(result.relaxation,'none');assert.ok(measures.maxFamily<=2);assert.equal(measures.sameFamilyAdjacency,0);}
   if(expectation.relaxation)assert.equal(result.relaxation,expectation.relaxation);
   if(expectation.fallback)assert.ok(result.diagnostics.fallbackRows>0);
   assert.ok(result.diagnostics.probes<=320);assert.ok(result.diagnostics.catalogPools<=1024);
   assert.ok(result.diagnostics.fallbackRows<=2*input.count*result.diagnostics.catalogPools);
   assert.ok(metrics.rows<=result.diagnostics.catalogPools+512+320+2*input.count*result.diagnostics.catalogPools+input.count);
  }
  check.passed=true;
 }catch(e){check.passed=false;check.failure=e.message;failures.push({name,detail:e.message});}
 checks.push(check);return result;
}
try{
 for(const category of topics)for(const difficulty of difficulties){
  const input={category,difficulty,count:20},inv=inventory(db,input);
  await run('short/'+category+'/'+difficulty,{...input,count:5},{},{unseen:true});
  const kept=[],perFamily=new Map();
  // Exactly twenty unseen tasks, with a feasible cap and ordering.
  for(const row of inv.rows){const n=perFamily.get(row.family_id)||0;if(n<2){kept.push(row.lineage_id);perFamily.set(row.family_id,n+1);}if(kept.length===20)break;}
  assert.equal(kept.length,20);const unseen=new Set(kept),seen=inv.rows.filter(r=>!unseen.has(r.lineage_id));assert.ok(seen.length<=MAX_EXPOSURES);
  await run('returning-constrained/'+category+'/'+difficulty,input,historyOf(seen),{unseen:true});
  assert.ok(inv.rows.length<=MAX_EXPOSURES);
  await run('returning-exhausted/'+category+'/'+difficulty,input,historyOf(inv.rows),{relaxation:'recent-problems'});
 }
 for(const difficulty of difficulties){
  const input={category:'all',difficulty,count:20},inv=inventory(db,input),history=historyOf(inv.rows.slice(0,MAX_EXPOSURES));assert.equal(history.exposures.length,MAX_EXPOSURES);
  await run('retention-bound/all/'+difficulty,input,history,{unseen:true});
  const off=await run('default-origin/all/'+difficulty,input,{}, {unseen:true});
  const on=await run('opt-in-empty-allowlist/all/'+difficulty,{...input,includeLegacy:true},{},{unseen:true});
  assert.deepEqual(on.questions,off.questions,'empty legacy approval set changes no selection');
 }
 // A normal returning player carries five actually selected/attempted rounds.
 for(const category of topics){let history={};for(let i=0;i<5;i++){
  const selected=await run('returning-sufficient/'+category+'/'+i,{category,difficulty:'olympiad',count:20},history,{unseen:true},db,800+i);
  if(selected)history=recordExposures(history,'selected-prior-'+i,selected.questions,'attempted',now-1800000+i*60000,now);
 }}
 const drills=db.prepare("SELECT DISTINCT topic,difficulty,tag FROM cbank_pools WHERE tag!='*' ORDER BY topic,difficulty,tag").all();
 let sparse;
 for(const row of drills){const input={category:row.topic,difficulty:row.difficulty,tag:row.tag,count:5},inv=inventory(db,input);if(inv.rows.length>=5&&inv.rows.length<20){sparse={input,inv};break;}}
 assert.ok(sparse,'final catalog must supply an actual narrow-drill fixture');
 await run('narrow-drill',sparse.input,{},{});
 await run('sparse-drill-insufficient',{...sparse.input,count:20},{},{error:true});
 const clone=out.replace(/\.json$/,'.mass-retirement.sqlite');if(existsSync(clone))throw Error('Preserve prior scenario database');copyFileSync(database,clone);
 const retired=new DatabaseSync(clone);
 try{
  const input={category:'integration',difficulty:'easy',count:5},rows=inventory(retired,input).rows,keepFamily=rows[0].family_id;
  retired.exec("INSERT INTO cbank_releases VALUES ('scenario-withdrawal','{}',1,'published')");
  const insert=retired.prepare("INSERT INTO cbank_release_exclusions VALUES ('scenario-withdrawal',?,'global','Local mass-retirement fixture only')");
  for(const row of rows)if(row.family_id!==keepFamily)insert.run(row.problem_ref);
  const remaining=inventory(retired,input).rows;
  await run('mass-retirement-single-family',{...input,count:Math.min(5,remaining.length)},{},{},retired);
  for(const row of remaining)insert.run(row.problem_ref);
  await run('mass-retirement-empty',{...input,count:1},{},{error:true},retired);
  assert.equal(retired.prepare('SELECT count(*) n FROM cbank_problems').get().n,db.prepare('SELECT count(*) n FROM cbank_problems').get().n);
 }finally{retired.close();}
 assert.ok(checks.some(c=>c.diagnostics?.catalogPools>192),'exercise actual largest inherited catalog above the old bound');
 assert.equal(sha(readFileSync(database)),originalHash);
}catch(e){failures.push({name:'scenario-driver',detail:e.stack});}finally{db.close();}
const report={databaseSha256:originalHash,groupsSha256:sha(readFileSync(groupsPath)),checks,failures,passed:failures.length===0,scope:'Offline final-catalog supplemental fixtures, SQLite returned rows and local elapsed time; no hosted billing or telemetry claim.',historyPolicy:'Actual attempted-history adapter; no history rewrite/reset within a sequence; at most 512 retained entries.',legacy:'Exact approval set is empty; opt-in/default parity is verified, not a claim of playable legacy coverage.'};
writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({checks:checks.length,failures,passed:report.passed}));if(!report.passed)process.exitCode=1;
