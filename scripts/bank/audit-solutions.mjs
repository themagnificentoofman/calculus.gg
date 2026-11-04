#!/usr/bin/env node
// Complete local inventory scan. Does not query or mutate production.
import { DatabaseSync } from 'node:sqlite';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { canonical,reconstruct } from '../../lib/bank/compact-codec.mjs';
import { renderMath } from '../../lib/render-math.mjs';
import { normalizeNotation } from '../../lib/math-notation.mjs';
import { assertSolutionQuality } from '../../lib/bank/solution-quality.mjs';
import { formatSolutionStep } from '../../lib/solution-format.mjs';

const [database,output,mode='current']=process.argv.slice(2);
if(!database||!output)throw Error('Usage: audit-solutions.mjs IMMUTABLE_DATABASE.sqlite REPORT.json [baseline]');
const present=mode==='baseline'?p=>p:(await import('../../lib/server/solution-presentation.mjs')).presentBankProblem;
const db=new DatabaseSync(database,{readOnly:true});
const rows=db.prepare('SELECT b.*,s.metadata_json FROM cbank_problems b JOIN cbank_shared s USING(shared_id) JOIN cbank_publication u USING(problem_ref) WHERE u.state=\'approved\' ORDER BY b.problem_ref');
const counters={records:0,sourceHashesChecked:0,uniqueRenderedExpressions:0,renderFailures:0,formatFailures:0,reviewedRecords:0,changedSolutions:0,changedStatements:0,notationChanges:0};
const patterns={builderPreface:0,gatheredProse:0,unnamedIntegralBounds:0,nonstandardNaturalLog:0,asciiPowersInProse:0};
const rendered=new Set(),failures=[],families={},examples=[];const started=performance.now();
const check=(s,p,location)=>{if(rendered.has(s))return;rendered.add(s);counters.uniqueRenderedExpressions++;try{renderMath(s,true);}catch(e){counters.renderFailures++;if(failures.length<50)failures.push({id:p.problemId,location,error:e.message});}};
for(const row of rows.iterate()){
 const original=reconstruct(row,JSON.parse(gunzipSync(row.payload_gzip).toString('utf8'))),{contentHash,...body}=original;
 if(createHash('sha256').update(canonical(body)).digest('hex')!==contentHash)throw Error('Immutable source hash mismatch '+original.problemId);
 counters.sourceHashesChecked++;
 if(mode==='legacy'&&original.templateVersion!=='original-linear-families-v2')continue;
 const p=present(original);counters.records++;
 if(mode!=='baseline'){try{assertSolutionQuality(p,{render:false});counters.reviewedRecords++;}catch(e){counters.formatFailures++;if(failures.length<50)failures.push({id:p.problemId,error:e.message});}}
 counters.changedSolutions+=JSON.stringify(p.solutionSteps)!==JSON.stringify(original.solutionSteps)?1:0;
 counters.changedStatements+=p.statement!==original.statement?1:0;
 counters.notationChanges+=[p.statement,...p.choices.map(c=>c.math),...p.solutionSteps].some(s=>normalizeNotation(s)!==s)?1:0;
 families[p.familyId]??={items:0,topic:p.topic,difficulty:p.difficulty,templateVersion:p.templateVersion,firstProblemId:p.problemId};families[p.familyId].items++;
 const text=p.solutionSteps.join('\n');
 patterns.builderPreface+=/^\\textnormal\{(?:Here |In this derivation, )\}m=/.test(p.solutionSteps[0])?1:0;
 patterns.gatheredProse+=/\\begin\{gathered\}\\textnormal\{/.test(text)?1:0;
 patterns.unnamedIntegralBounds+=/F\(b\)-F\(a\)/.test(text)?1:0;
 patterns.nonstandardNaturalLog+=/\\log(?![A-Za-z_])/.test(text)?1:0;
 patterns.asciiPowersInProse+=p.solutionSteps.some(s=>/\\textnormal\{[^{}]*(?:[A-Za-z]\^|textasciicircum)/.test(s))?1:0;
 for(const [index,s] of [p.statement,...p.choices.map(c=>c.math),...p.solutionSteps].entries())check(s,p,index);
 for(const step of p.solutionSteps)for(const block of formatSolutionStep(step)) {
  if(block.kind==='math')check(block.value,p,'formatted-math');
  else for(const part of block.parts)if(part.kind==='math')check(part.value,p,'inline-math');
 }
 if(p.problemId==='cn_c05d5e5ff7186cb58716')examples.push({original,presented:p});
 if(counters.records%10000===0)console.log(JSON.stringify({records:counters.records,uniqueExpressions:rendered.size,failures:counters.renderFailures}));
}
db.close();
const report={mode,...counters,familyCount:Object.keys(families).length,patterns,families,examples,failures,elapsedMs:performance.now()-started,scope:'Every approved record in the immutable combined local copy of the two active releases. No production games, DB writes or model calls. Hash/render/format checks are automated; mathematical and editorial family audit evidence is separate.'};
writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...counters,patterns,elapsedMs:report.elapsedMs}));if(counters.renderFailures||counters.formatFailures)process.exitCode=1;
