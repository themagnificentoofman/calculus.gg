// Read-only capture of the currently reviewed source presentation. No bank writes.
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const [repo,input,output]=process.argv.slice(2);
if(!output)throw Error('Usage: node capture_presentations.mjs REPO FULL_RECORDS_JSONL OUTPUT_JSON');
const hash=s=>createHash('sha256').update(s).digest('hex');
const deps=['lib/server/solution-presentation.mjs','lib/server/solution-reviews/finite.json','lib/server/solution-reviews/quality.json','lib/server/solution-reviews/legacy-hashes.json','lib/server/solution-reviews/legacy.mjs','lib/math-notation.mjs'];
const before=Object.fromEntries(deps.map(p=>[p,hash(readFileSync(resolve(repo,p)))]));
const {presentBankProblem}=await import(pathToFileURL(resolve(repo,'lib/server/solution-presentation.mjs')));
const rows=readFileSync(input,'utf8').trim().split('\n').map(JSON.parse).map(r=>{
 const p=presentBankProblem(r);
 return {problemId:r.problemId,sourceRevision:r.problemRevision,sourceContentHash:r.contentHash,sourceSemanticHash:r.semanticHash,statement:p.statement,solutionSteps:p.solutionSteps,sourceSolutionQuality:p.solutionQuality??null,canonicalStatementChanged:p.statement!==r.statement,canonicalSolutionsChanged:JSON.stringify(p.solutionSteps)!==JSON.stringify(r.solutionSteps)};
});
for(const path of deps)if(hash(readFileSync(resolve(repo,path)))!==before[path])throw Error('Presentation source changed while capturing');
writeFileSync(output,JSON.stringify({scope:'Exact-source presentation capture for inheritance by new immutable option revisions; original source records and saved snapshots are unchanged.',inputFileSHA256:hash(readFileSync(input)),sourceFiles:before,records:rows},null,2)+'\n');
console.log(JSON.stringify({records:rows.length,changedStatements:rows.filter(x=>x.canonicalStatementChanged).length,changedSolutions:rows.filter(x=>x.canonicalSolutionsChanged).length}));
