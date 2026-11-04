// Audit the exact option spelling produced by the current serving presenter.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {presentBankProblem} from '../../../lib/server/solution-presentation.mjs';
import {auditOptions} from './option-audit.mjs';
const [directory]=process.argv.slice(2);
if(!directory)throw Error('Supply a private stage with full canonical and retained records');
const stage=resolve(directory),names=['canonical-previews.jsonl','retained-originals.jsonl'];
const outputs=['served-option-input.jsonl','served-option-audit.json','served-option-binding.json'];
if(outputs.some(f=>existsSync(join(stage,f))))throw Error('Preserve previous served preview evidence');
const sha=v=>createHash('sha256').update(v).digest('hex');
const sources=Object.fromEntries(names.map(f=>[f,readFileSync(join(stage,f))]));
const records=Object.values(sources).flatMap(bytes=>bytes.toString().trim().split('\n').filter(Boolean).map(JSON.parse));
if(new Set(records.map(r=>r.problemId)).size!==records.length)throw Error('Duplicate effective identity');
const changes=[],inputs=records.map(source=>{
 const p=presentBankProblem(source);
 if(JSON.stringify(source.choices)!==JSON.stringify(p.choices))changes.push({problemId:p.problemId,revision:p.problemRevision,sourceContentHash:source.contentHash,beforeChoicesSha256:sha(JSON.stringify(source.choices)),afterChoicesSha256:sha(JSON.stringify(p.choices))});
 return Object.fromEntries(['problemId','familyId','choices','answerChoiceId','pedagogy'].map(k=>[k,p[k]]));
});
const content=inputs.map(r=>JSON.stringify(r)).join('\n')+'\n';
const report={...auditOptions(inputs),artifactSha256:sha(content),displayScope:'Current presentBankProblem normalization; canonical records are unchanged.'};
writeFileSync(join(stage,outputs[0]),content);
writeFileSync(join(stage,outputs[1]),JSON.stringify(report,null,2)+'\n');
writeFileSync(join(stage,outputs[2]),JSON.stringify({sourceArtifacts:Object.fromEntries(Object.entries(sources).map(([f,b])=>[f,sha(b)])),presenterSha256:sha(readFileSync('lib/server/solution-presentation.mjs')),notationSha256:sha(readFileSync('lib/math-notation.mjs')),records:records.length,changedSpellings:changes,servedInputSha256:sha(content)},null,2)+'\n');
console.log(JSON.stringify({records:records.length,notationChanged:changes.length,flaggedFamilies:Object.values(report.families).filter(f=>f.reviewRequired).length}));
