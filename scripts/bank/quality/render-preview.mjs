// Complete strict expression/fragment rendering for an immutable preview batch.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {renderMath} from '../../../lib/render-math.mjs';
import {formatProblemStatement,formatSolutionStep} from '../../../lib/solution-format.mjs';
import {solutionQualityIssues} from '../../../lib/bank/solution-quality.mjs';
const [input,output]=process.argv.slice(2);if(!output||existsSync(output))throw Error('Supply an input and new report path');
const bytes=readFileSync(input),records=bytes.toString().trim().split('\n').map(JSON.parse),failures=[];let expressions=0;
for(const p of records){
 const check=(math,location)=>{expressions++;try{renderMath(math,true);}catch(e){failures.push({problemId:p.problemId,location,math,error:e.message});}};
 for(const [i,math]of[p.statement,...p.choices.map(c=>c.math),...p.solutionSteps].entries())check(math,i);
 for(const block of [...formatProblemStatement(p.statement),...p.solutionSteps.flatMap(formatSolutionStep)]){
  if(block.kind==='math')check(block.value,'formatted');else for(const part of block.parts)if(part.kind==='math')check(part.value,'inline');
 }
 for(const issue of solutionQualityIssues(p))failures.push({problemId:p.problemId,location:'semantic-format-admission',error:issue});
}
const report={records:records.length,expressions,strict:true,sourceArtifactSha256:createHash('sha256').update(bytes).digest('hex'),failures,scope:'Every source expression and actual formatter math fragment. Mathematical proof, option-only editorial review, source admission and visual browser inspection are separate gates.'};
writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({records:records.length,expressions,failures:failures.length}));process.exitCode=failures.length?1:0;
