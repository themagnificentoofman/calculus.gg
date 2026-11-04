#!/usr/bin/env node
// Offline matched evaluation. Never creates accounts, games, or production traffic.
import { DatabaseSync } from 'node:sqlite';
import { writeFileSync,readFileSync } from 'node:fs';
import { sqliteD1 } from './sqlite-d1.mjs';
import { selectBankQuestions as baseline } from '../../lib/server/baseline-compact-selection.ts';
import { selectBankQuestions as candidate } from '../../lib/server/compact-bank-selection.ts';
import { recordExposures } from '../../lib/bank/exposure.ts';
import { topics,difficulties } from '../../lib/server/questions-policy.mjs';
const legacy=JSON.parse(readFileSync(new URL('../../lib/bank/legacy-features.json',import.meta.url)));
const [beforePath,afterPath,outputPath,scope='all']=process.argv.slice(2);
if(!outputPath)throw Error('Usage: evaluate-quality.mjs BASELINE.sqlite CANDIDATE.sqlite REPORT.json');
const before=new DatabaseSync(beforePath,{readOnly:true}),after=new DatabaseSync(afterPath,{readOnly:true});
const seed=n=>()=>{n^=n<<13;n^=n>>>17;n^=n<<5;return (n>>>0)/4294967296;};
const avg=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
const p95=xs=>[...xs].sort((a,b)=>a-b)[Math.floor(xs.length*.95)];
function features(q){const p=q.pedagogy,l=legacy[q.familyId];return {family:q.familyId,idea:p?.relatedIdeaGroupId||l?.idea||q.familyId,structure:p?.structuralSignature||l?.structure||q.familyId,technique:p?.primaryTechnique||l?.technique||q.familyId,alternatives:p?.alternativeTechniques||[],reasoning:p?.reasoningDemand||['execution']};}
function measure(qs){const fs=qs.map(features),freq=k=>Object.values(fs.reduce((a,f)=>(a[f[k]]=(a[f[k]]||0)+1,a),{})),div=k=>freq(k).length,conc=k=>freq(k).reduce((n,c)=>n+(c/qs.length)**2,0),adj=k=>fs.slice(1).filter((f,i)=>f[k]===fs[i][k]).length;
 return {distinctFamilies:div('family'),distinctIdeas:div('idea'),distinctPrimaryTechniques:div('technique'),distinctStructures:div('structure'),distinctAlternativeTags:new Set(fs.flatMap(f=>f.alternatives)).size,distinctReasoningDemands:new Set(fs.flatMap(f=>f.reasoning)).size,familyConcentration:conc('family'),ideaConcentration:conc('idea'),maxFamilyCount:Math.max(...freq('family')),adjacentFamily:adj('family'),adjacentIdea:adj('idea'),adjacentStructure:adj('structure'),exactDuplicates:qs.length-new Set(qs.map(q=>q.problemId)).size};}
async function study(db,select,input,rounds,carry=false){let history={},lastSeen=new Map(),seen=new Set(),repeats=0,returns=[],stats=[],timings=[],statements=[],returnedRows=[],relaxations={},reasons={},sample=[];const rng=seed(0x20261103+topics.indexOf(input.category)*17+difficulties.indexOf(input.difficulty)*107+input.count*919);const now=1793700000000;
 for(let i=0;i<rounds;i++){const metrics={statements:0,rows:0},start=performance.now(),r=await select(sqliteD1(db,metrics),input,carry?history:{},rng,now+i*300000);timings.push(performance.now()-start);statements.push(metrics.statements);returnedRows.push(metrics.rows);stats.push(measure(r.questions));relaxations[r.relaxation]=(relaxations[r.relaxation]||0)+1;for(const reason of r.diagnostics?.reasons||[])reasons[reason]=(reasons[reason]||0)+1;
  for(const q of r.questions){if(seen.has(q.problemId))repeats++;seen.add(q.problemId);if(lastSeen.has(q.familyId))returns.push(i-lastSeen.get(q.familyId));}
  for(const q of r.questions)lastSeen.set(q.familyId,i);
  if(carry){history=select===candidate?recordExposures(history,'offline-'+i,r.questions,'attempted',now+i*300000):{problems:[...(history.problems||[]),...r.questions.map(q=>q.problemId)].slice(-100),families:r.questions.map(q=>q.familyId).slice(-20)};if(i<2)sample.push(r.questions.map((q,j)=>({ordinal:j+1,problemId:q.problemId,...features(q),statement:q.latexProblem,choices:q.options,answerIndex:q.correctIndex,solution:q.explanation})));}
 }
 return {input,rounds,history:carry?'attempted; five-minute session spacing':'independent empty histories',mean:Object.fromEntries(Object.keys(stats[0]).map(k=>[k,avg(stats.map(s=>s[k]))])),max:Object.fromEntries(Object.keys(stats[0]).map(k=>[k,Math.max(...stats.map(s=>s[k]))])),exactAcrossRoundRepeats:repeats,distinctProblems:seen.size,meanFamilyReturnIntervalRounds:returns.length?avg(returns):null,relaxations,reasons,latencyMs:{mean:avg(timings),p95:p95(timings),max:Math.max(...timings)},maxStatements:Math.max(...statements),maxReturnedRows:Math.max(...returnedRows),sample};
}
const matched=[];
for(const category of topics)for(const difficulty of difficulties)for(const count of [5,20]){if(scope==='priority'&&(category!=='integration'||difficulty!=='olympiad'))continue;const input={category,difficulty,count};matched.push({baseline:await study(before,baseline,input,100),candidate:await study(after,candidate,input,100)});console.log(category,difficulty,count);}
const repeated=[];
for(const input of [{category:'integration',difficulty:'olympiad',count:20},...(scope==='priority'?[]:topics.filter(t=>t!=='integration').map(category=>({category,difficulty:'olympiad',count:20})))])repeated.push({baseline:await study(before,baseline,input,10,true),candidate:await study(after,candidate,input,10,true)});
const narrow=[];
for(const input of [{category:'integration',difficulty:'medium',count:20,tag:'substitution'},{category:'integration',difficulty:'olympiad',count:5,tag:'parameter-differentiation'}]){try{narrow.push(await study(after,candidate,input,100,true));}catch(e){narrow.push({input,unavailable:e.message});}}
const failures=matched.filter(({candidate:c})=>c.max.exactDuplicates||c.input.count===20&&(c.max.maxFamilyCount>2||c.max.adjacentFamily));
const report={schemaVersion:1,seed:'20261103 matched per-cell xorshift32; production uses crypto.getRandomValues',baselineRelease:before.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,candidateRelease:after.prepare("SELECT value FROM cbank_config WHERE key='active_release'").get().value,matched,repeated,narrow,broadAcceptanceFailures:failures.map(p=>p.candidate.input),limitations:['Offline SQLite timings include decoding; exclude network, cold starts, Firebase and authentication.','Returned rows are not billed D1 rows read. Hosted counters must be measured separately.','Alternative-method tags are separate and do not inflate primary-technique counts.','Analytic metadata is an editorial classification, not evidence of player learning.','Sparse and retired adversarial cases are tested in selection-quality.test.mjs.']};
writeFileSync(outputPath,JSON.stringify(report,null,2)+'\n');before.close();after.close();if(failures.length)process.exitCode=1;
