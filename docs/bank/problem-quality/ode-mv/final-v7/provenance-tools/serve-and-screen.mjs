import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [repoArg,stageArg,outArg]=process.argv.slice(2),repo=resolve(repoArg),stage=resolve(stageArg),out=resolve(outArg);
const {presentBankProblem}=await import(pathToFileURL(resolve(repo,'lib/server/solution-presentation.mjs')));
const {auditOptions}=await import(pathToFileURL(resolve(repo,'scripts/bank/quality/option-audit.mjs')));
const hash=v=>createHash('sha256').update(v).digest('hex');
const rows=['canonical-previews.jsonl','retained-originals.jsonl'].flatMap(f=>readFileSync(resolve(stage,f),'utf8').trim().split('\n').map(JSON.parse));
const diffs=[],full=[],input=[];
for(const r of rows){const p=presentBankProblem(r);full.push(p);input.push(Object.fromEntries(['problemId','familyId','choices','answerChoiceId','pedagogy'].map(k=>[k,p[k]])));
 const fields=['statement','choices','solutionSteps'].filter(k=>JSON.stringify(r[k])!==JSON.stringify(p[k]));if(fields.length)diffs.push({problemId:r.problemId,revision:r.problemRevision,sourceContentHash:r.contentHash,familyId:r.familyId,fields,choiceMathChanges:r.choices.flatMap((c,i)=>c.math===p.choices[i].math?[]:[{choiceId:c.choiceId,from:c.math,to:p.choices[i].math}])});}
const lite=input.map(r=>JSON.stringify(r)).join('\n')+'\n';
for(const f of ['served-options.jsonl','served-records.jsonl','served-option-audit.json','presentation-differences.json'])if(existsSync(resolve(out,f)))throw Error('Preserve earlier output '+f);
writeFileSync(resolve(out,'served-options.jsonl'),lite);writeFileSync(resolve(out,'served-records.jsonl'),full.map(r=>JSON.stringify(r)).join('\n')+'\n');
writeFileSync(resolve(out,'served-option-audit.json'),JSON.stringify({...auditOptions(input),artifactSha256:hash(lite)},null,2)+'\n');
writeFileSync(resolve(out,'presentation-differences.json'),JSON.stringify({records:rows.length,changedPresentations:diffs.length,recordsWithChoiceChanges:diffs.filter(r=>r.choiceMathChanges.length).length,sourceBindings:Object.fromEntries(['lib/server/solution-presentation.mjs','lib/math-notation.mjs','lib/server/solution-reviews/finite.json','lib/server/solution-reviews/quality.json','scripts/bank/quality/option-audit.mjs'].map(f=>[f,hash(readFileSync(resolve(repo,f)))])),records:diffs},null,2)+'\n');
console.log(JSON.stringify({records:rows.length,presentationChanges:diffs.length,choiceChanges:diffs.filter(r=>r.choiceMathChanges.length).length}));
