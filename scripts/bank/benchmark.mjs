#!/usr/bin/env node
import { DatabaseSync } from 'node:sqlite';
import { readFileSync,statSync,writeFileSync } from 'node:fs';
import os from 'node:os';
import { sqliteD1 } from './sqlite-d1.mjs';
const [path='.bank-data/bank.sqlite',out='.bank-data/benchmark.json',layout='original']=process.argv.slice(2);
const compact=layout==='compact';
const {selectBankQuestions,POOL_SQL,SLOT_SQL}=await import(compact?'../../lib/server/compact-bank-selection.ts':'../../lib/server/bank-selection.ts');
const sql=new DatabaseSync(path,{readOnly:true});
const release=sql.prepare(`SELECT value FROM ${compact?'cbank':'bank'}_config WHERE key='active_release'`).get().value;
const count=sql.prepare(compact?"SELECT count(*) AS n FROM cbank_slots JOIN cbank_pools USING(pool_id) WHERE release_id=? AND tag='*'":"SELECT count(*) AS n FROM bank_slots WHERE release_id=? AND tag='*'").get(release).n;
if(count<100000)throw Error('Benchmark requires a genuinely populated >=100,000-row release');
let seed=0x20261102;
const rng=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296;};
const percentile=(xs,p)=>[...xs].sort((a,b)=>a-b)[Math.min(xs.length-1,Math.floor(xs.length*p))];
const reports=[];
for(const input of [{category:'integration',difficulty:'easy',count:20},{category:'all',difficulty:'hard',count:20},{category:'integration',difficulty:'medium',count:20,tag:'substitution'},{category:'multivariable',difficulty:'olympiad',count:20}]){
 const timings=[],familyCounts={},problemCounts={},statements=[],rows=[],levels={};let recent={},recentProblemRepeats=0;
 for(let i=0;i<250;i++){
  const metrics={statements:0,rows:0};const start=performance.now();
  const result=await selectBankQuestions(sqliteD1(sql,metrics),input,i<100?{}:recent,rng);
  timings.push(performance.now()-start);statements.push(metrics.statements);rows.push(metrics.rows);levels[result.relaxation]=(levels[result.relaxation]||0)+1;
  if(i>=100)recentProblemRepeats+=result.questions.filter(q=>recent.problems?.includes(q.problemId)).length;
  for(const q of result.questions){familyCounts[q.familyId]=(familyCounts[q.familyId]||0)+1;problemCounts[q.problemId]=(problemCounts[q.problemId]||0)+1;}
  recent={problems:[...(recent.problems||[]),...result.questions.map(q=>q.problemId)].slice(-100),families:result.questions.map(q=>q.familyId).slice(-20)};
 }
 const familyValues=Object.values(familyCounts),expected=5000/familyValues.length;
 reports.push({input,rounds:250,latencyMs:{p50:percentile(timings,.5),p95:percentile(timings,.95),p99:percentile(timings,.99),max:Math.max(...timings)},maxStatements:Math.max(...statements),maxReturnedCandidateRows:Math.max(...rows),distinctProblems:Object.keys(problemCounts).length,distinctFamilies:familyValues.length,maxFamilyShare:Math.max(...familyValues)/5000,familyChiSquare:familyValues.reduce((v,n)=>v+(n-expected)**2/expected,0),familyCounts,recentProblemRepeats,relaxations:levels});
}
const pool=sql.prepare(`SELECT * FROM ${compact?'cbank':'bank'}_pools WHERE release_id=? LIMIT 1`).get(release);
const plans={pool:sql.prepare('EXPLAIN QUERY PLAN '+POOL_SQL).all('easy','*','integration','integration'),slot:sql.prepare('EXPLAIN QUERY PLAN '+SLOT_SQL).all(...(compact?[pool.pool_id,0]:[pool.release_id,pool.topic,pool.difficulty,pool.tag,pool.family_id,0]))};
const report={layout,payloadDecompressionsPerRound:compact?20:0,environment:{platform:os.platform(),architecture:os.arch(),cpu:os.cpus()[0]?.model,node:process.version,sqlite:sql.prepare('SELECT sqlite_version() AS v').get().v},release,datasetSize:count,databaseBytes:statSync(path).size,rounds:1000,reports,plans,comparison:{liveGenerationLatencyMs:null,reason:'No live generation run or authorized benchmark spend. Prior path had a 70,000 ms timeout; that is not a measured latency.',bankOpenAICalls:0},limits:'Local SQLite with the production SQL and sampler, excluding Cloudflare network, Worker/Firebase transactions, authentication, and cold start. Family-uniform policy intentionally differs from row-uniform sampling. Parameter-level uniformity is limited by bounded oversampling and recency exclusions.'};
writeFileSync(out,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({datasetSize:count,databaseBytes:report.databaseBytes,cases:reports.map(r=>({input:r.input,latencyMs:r.latencyMs,maxStatements:r.maxStatements,distinctFamilies:r.distinctFamilies,maxFamilyShare:r.maxFamilyShare}))},null,2));sql.close();
