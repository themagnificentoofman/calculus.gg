#!/usr/bin/env node
import {legacyPolicy,legacyEligibilitySql} from '../../../lib/server/legacy-selection.mjs';
// Real serving selectors, real stage-aware histories. No production requests.
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {sqliteD1} from '../sqlite-d1.mjs';
import {topics,difficulties} from '../../../lib/server/questions-policy.mjs';
import {POOL_SQL,candidateColumns,candidateJoins,eligibleSql} from '../../../lib/server/compact-bank-selection.ts';

const sha=value=>createHash('sha256').update(value).digest('hex');
const avg=xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0;
const deviation=xs=>Math.sqrt(avg(xs.map(x=>(x-avg(xs))**2)));
const distribution=xs=>{const sorted=[...xs].sort((a,b)=>a-b);return {n:xs.length,min:sorted[0]??null,mean:avg(xs),median:sorted[Math.floor(sorted.length/2)]??null,p95:sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.95))]??null,max:sorted.at(-1)??null,sd:deviation(xs)};};
export const seeded=n=>()=>{n^=n<<13;n^=n>>>17;n^=n<<5;return (n>>>0)/4294967296;};
function descriptors(q,groups,role='candidate'){
 const family=groups.families[q.familyId];if(!family)throw Error('Missing independently reviewed group definition: '+q.familyId);
 // A finite case may have a simpler options-visible route than its siblings.
 // Apply the same exact revision disposition to both baseline and candidate.
 const m={...family,...groups.itemDefinitions?.[q.problemId+'@'+q.problemRevision]};
 return {lineage:groups.items?.[q.problemId]||q.lineageId||q.problemId,
  family:m.constructionFamilyId,idea:m.relatedIdeaGroupId,structure:m.structuralSignature,
  method:m.primaryTechnique,qualified:(m.qualificationByRole?.[role]?.qualifiedOlympiad??m.qualifiedOlympiad)===true,decision:m.centralDecision};
}
export function roundMeasures(questions,groups,seen=new Set(),role='candidate'){
 const ds=questions.map(q=>descriptors(q,groups,role)),count=k=>Object.values(ds.reduce((v,d)=>(v[d[k]]=(v[d[k]]||0)+1,v),{})),distinct=k=>count(k).length;
 const repeated=ds.filter(d=>seen.has(d.lineage)).length;
 return {exactEquivalentRepeats:repeated,withinRoundDuplicates:questions.length-distinct('lineage'),
  maxFamily:Math.max(0,...count('family')),sameFamilyAdjacency:ds.slice(1).filter((d,i)=>d.family===ds[i].family).length,
  distinctFamilies:distinct('family'),distinctIdeas:distinct('idea'),qualifiedIdeas:new Set(ds.filter(d=>d.qualified).map(d=>d.idea)).size,
  distinctStructures:distinct('structure'),distinctPrimaryMethods:distinct('method'),
  ideaConcentration:count('idea').reduce((n,c)=>n+(c/questions.length)**2,0),
  methodConcentration:count('method').reduce((n,c)=>n+(c/questions.length)**2,0),
  closeVariantWindows3:ds.slice(2).filter((_,i)=>new Set(ds.slice(i,i+3).map(d=>d.idea)).size<3||new Set(ds.slice(i,i+3).map(d=>d.structure)).size<3).length};
}
export function acceptanceFailures(rounds,input,contract){
 const failures=[];
 for(const [i,r] of rounds.entries()){
  if(r.error){failures.push({round:i+1,gate:'request-failure',detail:r.error});continue;}
  for(const key of ['exactEquivalentRepeats','withinRoundDuplicates','sameFamilyAdjacency'])if(r[key])failures.push({round:i+1,gate:key,value:r[key]});
  if(r.maxFamily>2)failures.push({round:i+1,gate:'family-cap',value:r.maxFamily});
  if(r.relaxation!=='none')failures.push({round:i+1,gate:'relaxation',value:r.relaxation});
  if(r.count!==contract.count)failures.push({round:i+1,gate:'question-count',value:r.count});
 }
 if(rounds.length!==contract.rounds[input.difficulty])failures.push({gate:'incomplete-horizon'});
 return failures;
}

export function compareIntegration(candidate,baseline,development){
 if(baseline.role!=='baseline'||development.role!=='baseline'||development.phase!=='development'||baseline.phase!==candidate.phase)throw Error('Matched pinned baseline phases required');
 for(const report of [baseline,development]){
  if(report.groupDefinitionsSha256!==candidate.groupDefinitionsSha256||report.contractSha256!==candidate.contractSha256)throw Error('Baseline and candidate must use identical reviewed groups and horizon contract');
 }
 const cell=report=>report.cells.find(c=>c.input.category==='integration'&&c.input.difficulty==='olympiad');
 const proposed=cell(candidate),prior=cell(baseline),dev=cell(development);
 if(!proposed||!prior||!dev?.tolerance)throw Error('Integration comparison or predeclared variability tolerances missing');
 const differences=proposed.runs.map(run=>{
  const match=prior.runs.find(r=>r.seed===run.seed);if(!match)throw Error('Missing matched baseline seed');
  return {seed:run.seed,ideaMeanLoss:match.means.distinctIdeas-run.means.distinctIdeas,methodMeanLoss:match.means.distinctPrimaryMethods-run.means.distinctPrimaryMethods,nearCloneMeanIncrease:run.means.closeVariantWindows3-match.means.closeVariantWindows3};
 });
 if(differences.length!==prior.runs.length)throw Error('Matched baseline sequence count differs');
 const metrics=Object.fromEntries(Object.keys(dev.tolerance).map(key=>[key,{...distribution(differences.map(d=>d[key])),allowedMean:dev.tolerance[key]}]));
 const failures=Object.entries(metrics).filter(([,m])=>m.mean>m.allowedMean+1e-12).map(([metric,m])=>({gate:'integration-regression',metric,value:m.mean,tolerance:m.allowedMean}));
 return {tolerance:dev.tolerance,metrics,matchedSeeds:differences,failures};
}

function capacity(db,input,horizon,groups,baseline=false){
 const originScope=legacyPolicy.selection(input.includeLegacy);
 const pools=db.prepare(POOL_SQL).all(input.difficulty,input.tag||'*',input.category,input.category,baseline?'[]':originScope.excludedFamilies),items=new Map();
 for(const pool of pools){
  const rows=db.prepare(`WITH context(active_release,legacy_families,legacy_revisions) AS (VALUES (?,?,?)) SELECT ${candidateColumns}
   FROM cbank_slots s ${candidateJoins} WHERE s.pool_id=? AND ${baseline?eligibleSql:legacyEligibilitySql(eligibleSql)}`).all(pool.active_release,legacyPolicy.familyJson,originScope.revisions,pool.pool_id);
  for(const row of rows){const family=groups.families[row.source_family];if(!family)throw Error('Unreviewed inventory family: '+row.source_family);
   const group={...family,...groups.itemDefinitions?.[row.problem_id+'@'+row.revision]};
   const lineage=groups.items?.[row.problem_id]||row.lineage_id,old=items.get(lineage);
   if(!old||row.revision>old.revision)items.set(lineage,{...row,realFamily:group.constructionFamilyId,idea:group.relatedIdeaGroupId,qualified:(group.qualificationByRole?.[baseline?'baseline':'candidate']?.qualifiedOlympiad??group.qualifiedOlympiad)===true});
  }
 }
 const families={};for(const item of items.values())families[item.realFamily]=(families[item.realFamily]||0)+1;
 const effective=Object.values(families).reduce((n,u)=>n+Math.min(u,2*horizon),0);
 return {catalogPools:pools.length,distinctMathematicalItems:items.size,constructionFamilies:Object.keys(families).length,
  relatedIdeas:new Set([...items.values()].map(x=>x.idea)).size,qualifiedOlympiadIdeas:new Set([...items.values()].filter(x=>x.qualified).map(x=>x.idea)).size,
  eligibleUnseenByFamily:families,effectiveCapacity:effective,required:20*horizon,headroom:effective/(20*horizon),necessaryGate:effective>=20*horizon};
}

async function sequence(db,select,record,input,baseSeed,groups,contract,role){
 const rng=seeded(parseInt(sha(baseSeed+'/'+input.category+'/'+input.difficulty).slice(0,8),16)),seen=new Set(),lastFamily=new Map(),lastIdea=new Map(),methodWindows=new Set();
 let history={},details=[],rounds=[],familyReturns=[],ideaReturns=[],methodRecurrences=0;
 const start=Date.UTC(2026,10,4,3,0),spacing=contract.historyPolicy.roundSpacingMinutes*60000;
 for(let index=0;index<contract.rounds[input.difficulty];index++){
  const now=start+index*spacing,metrics={statements:0,rows:0},began=performance.now();
  try{
   const selected=await select(sqliteD1(db,metrics),input,history,rng,now),qs=selected.questions,ds=qs.map(q=>descriptors(q,groups,role));
   const measured=roundMeasures(qs,groups,seen,role);
   rounds.push({...measured,count:qs.length,relaxation:selected.relaxation,diagnostics:selected.diagnostics,localMs:performance.now()-began,queries:metrics.statements,returnedRows:metrics.rows,
    items:qs.map((q,i)=>({id:q.problemId,revision:q.problemRevision,lineage:ds[i].lineage,family:ds[i].family,idea:ds[i].idea,method:ds[i].method}))});
   details.push(qs.map((q,i)=>({problemId:q.problemId,revision:q.problemRevision,statement:q.latexProblem,choices:q.options,answer:q.options[q.correctIndex],...ds[i]})));
   for(let i=0;i<ds.length;i++){
    const d=ds[i],at=index*20+i;seen.add(d.lineage);
    if(lastFamily.has(d.family))familyReturns.push(at-lastFamily.get(d.family));lastFamily.set(d.family,at);
    if(lastIdea.has(d.idea))ideaReturns.push(at-lastIdea.get(d.idea));lastIdea.set(d.idea,at);
    // Carry the same attempted history implementation as this source version;
    // no resets, shortened legacy adapter, or invented attempted displays.
    history=record(history,'offline-'+baseSeed+'-'+index,[qs[i]],'attempted',now+(i+1)*contract.historyPolicy.secondsBetweenAttempts*1000);
   }
   const methods=rounds.flatMap(r=>r.items?.map(q=>q.method)||[]);
   for(let i=Math.max(0,methods.length-22);i+2<methods.length;i++){
    if(i<methods.length-qs.length-2)continue;
    const key=JSON.stringify(methods.slice(i,i+3));if(methodWindows.has(key))methodRecurrences++;methodWindows.add(key);
   }
  }catch(error){rounds.push({error:error.message,queries:metrics.statements,returnedRows:metrics.rows});break;}
 }
 const failures=acceptanceFailures(rounds,input,contract),valid=rounds.filter(r=>!r.error);
 return {seed:baseSeed,input,rounds,failures,historyEntries:history.exposures?.length||0,historyBytes:Buffer.byteLength(JSON.stringify(history)),
  familyReturnIntervalQuestions:distribution(familyReturns),ideaReturnIntervalQuestions:distribution(ideaReturns),repeatedMethodWindows3:methodRecurrences,
  means:Object.fromEntries(['distinctIdeas','qualifiedIdeas','distinctPrimaryMethods','closeVariantWindows3','ideaConcentration','methodConcentration'].map(k=>[k,avg(valid.map(r=>r[k]))])),details};
}

export async function evaluate(config){
 const contract=JSON.parse(readFileSync(config.contract)),groups=JSON.parse(readFileSync(config.groups));
 if(!['development','heldout'].includes(config.phase))throw Error('Explicit development or heldout phase required');
 if(groups.status!=='independently-reviewed')throw Error('Group definitions have not passed independent review');
 if(contract.seeds.development.length<20||contract.seeds.heldout.length<20||new Set([...contract.seeds.development,...contract.seeds.heldout]).size!==contract.seeds.development.length+contract.seeds.heldout.length)throw Error('At least twenty distinct development and twenty separate held-out seeds required');
 const source=resolve(config.source);
 if(config.role==='baseline'){
  if(!config.baselineSourceDigests||Object.keys(config.baselineSourceDigests).length<5)throw Error('Pin selector, presenter, notation, review and exposure source files');
  for(const [file,digest] of Object.entries(config.baselineSourceDigests))if(sha(readFileSync(resolve(source,file)))!==digest)throw Error('Pinned baseline source differs: '+file);
 }
 const select=await import(pathToFileURL(resolve(source,'lib/server/compact-bank-selection.ts'))),exposure=await import(pathToFileURL(resolve(source,'lib/bank/exposure.ts')));
 if(config.role==='baseline'&&sha(readFileSync(resolve(source,'lib/server/compact-bank-selection.ts')))!==config.baselineSelectorSha256)throw Error('Pinned baseline selector differs');
 const db=new DatabaseSync(config.database,{readOnly:true}),cells=[],failures=[];
 try{
  for(const category of [...topics,'all'])for(const difficulty of difficulties){
   if(config.only&&config.only!==category+'/'+difficulty)continue;
   const input={category,difficulty,count:20,...(config.role==='baseline'?{}:{includeLegacy:config.includeLegacy===true})},inventory=capacity(db,input,contract.rounds[difficulty],groups,config.role==='baseline'),runs=[];
   if(!inventory.necessaryGate)failures.push({input,gate:'effective-capacity',inventory});
   for(const seed of contract.seeds[config.phase])runs.push(await sequence(db,select.selectBankQuestions,exposure.recordExposures,input,seed,groups,contract,config.role));
   const roundRows=runs.flatMap(r=>r.rounds.filter(x=>!x.error));
   const stats=Object.fromEntries(['distinctIdeas','qualifiedIdeas','distinctPrimaryMethods','distinctStructures','closeVariantWindows3','ideaConcentration','methodConcentration','localMs','queries','returnedRows'].map(k=>[k,distribution(roundRows.map(r=>r[k]))]));
   for(const run of runs)for(const failure of run.failures)failures.push({input,seed:run.seed,...failure});
   if(difficulty==='olympiad'&&stats.qualifiedIdeas.mean<contract.mainGates.olympiadMeanQualifiedIdeas)failures.push({input,gate:'olympiad-idea-mean',value:stats.qualifiedIdeas.mean});
   if(difficulty==='olympiad'&&inventory.qualifiedOlympiadIdeas<30)failures.push({input,gate:'olympiad-planning-floor',value:inventory.qualifiedOlympiadIdeas});
   const score=r=>r.failures.length*1000-r.means.qualifiedIdeas+r.means.closeVariantWindows3;
   const worst=[...runs].sort((a,b)=>score(b)-score(a))[0];
   const samples={representative:{seed:runs[0].seed,rounds:runs[0].details},worst:{seed:worst.seed,rounds:worst.details}};
   const tolerance=config.role==='baseline'&&config.phase==='development'&&category==='integration'&&difficulty==='olympiad'?{
    ideaMeanLoss:Math.max(.25,2*deviation(runs.map(r=>r.means.distinctIdeas))),methodMeanLoss:Math.max(.5,2*deviation(runs.map(r=>r.means.distinctPrimaryMethods))),nearCloneMeanIncrease:Math.max(.2,2*deviation(runs.map(r=>r.means.closeVariantWindows3)))}:null;
   cells.push({input,inventory,stats,tolerance,runs:runs.map(({details,...run})=>run),samples});
   console.log(JSON.stringify({role:config.role,phase:config.phase,input,capacity:inventory.effectiveCapacity,meanIdeas:stats.qualifiedIdeas.mean,failedSequences:runs.filter(r=>r.failures.length).length}));
  }
  const report={version:contract.version,role:config.role,phase:config.phase,source,databaseSha256:sha(readFileSync(config.database)),baselineSourceDigests:config.baselineSourceDigests||null,sourceSelectorSha256:sha(readFileSync(resolve(source,'lib/server/compact-bank-selection.ts'))),
   release:db.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get()?.value,groupDefinitionsSha256:sha(readFileSync(config.groups)),contractSha256:sha(readFileSync(config.contract)),cells,failures,passed:failures.length===0,
   limits:['Offline SQLite timings and returned rows are not hosted latency or billed D1 reads.','Editorial group/difficulty review is AI-assisted, not human certification or player calibration.','The declared horizon is finite; returning-player and exhaustion fixtures are separate.']};
  if(config.role==='candidate'&&(!config.only||config.only==='integration/olympiad')){
   if(!config.baselineReport||!config.baselineDevelopmentReport)throw Error('Candidate evaluation requires matched baseline and frozen development tolerances');
   const comparison=compareIntegration(report,JSON.parse(readFileSync(config.baselineReport)),JSON.parse(readFileSync(config.baselineDevelopmentReport)));
   report.integrationComparison={...comparison,baselineReportSha256:sha(readFileSync(config.baselineReport)),developmentBaselineSha256:sha(readFileSync(config.baselineDevelopmentReport))};
   report.failures.push(...comparison.failures);report.passed=report.failures.length===0;
  }
  report.completeMatrix=cells.length===28;
  return report;
 }finally{db.close();}
}

if(process.argv[1]&&resolve(process.argv[1])===new URL(import.meta.url).pathname){
 const [configPath,out]=process.argv.slice(2);if(!out)throw Error('Usage: evaluate-horizons.mjs CONFIG.json NEW_REPORT.json');
 if(existsSync(out))throw Error('Preserve prior failed seeds/results: use a new report path');
 const report=await evaluate(JSON.parse(readFileSync(configPath)));writeFileSync(out,JSON.stringify(report,null,2)+'\n');if(!report.passed)process.exitCode=1;
}
