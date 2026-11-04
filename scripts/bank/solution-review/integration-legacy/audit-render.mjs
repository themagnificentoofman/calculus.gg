import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {corrected_solution,supports,familyIds} from './legacy-solutions.mjs';
const require=createRequire(import.meta.url);
const katex=require('../../calculus-ninja/node_modules/katex');
const base=path.dirname(new URL(import.meta.url).pathname);
const io=JSON.parse(fs.readFileSync(path.join(base,'io3-solutions.json'),'utf8'));
const edges=JSON.parse(fs.readFileSync(path.join(base,'legacy-edge-records.json'),'utf8'));
let mathCount=0;const errors=[],ascii=[],rows=[];
function check(id,steps) {
  for (const [index,step] of steps.entries()) {
    try{katex.renderToString(step,{displayMode:true,throwOnError:true,strict:'error'});mathCount++}catch(e){errors.push({id,index,step,error:e.message})}
    for(const m of step.matchAll(/\\text(?:normal)?\{([^{}]*)\}/g)) if(/[=<>^_]|\b(?:ln|log|sqrt|sin|cos|tan)\s*\(/.test(m[1]))ascii.push({id,index,prose:m[1]});
  }
}
for(const r of io){check(r.problemId,r.solutionSteps);rows.push(r)}
for(const [family,recs] of Object.entries(edges))for(const r of recs){if(!supports(r))throw new Error('Unsupported '+family);const old=JSON.stringify(r);const steps=corrected_solution(r);if(old!==JSON.stringify(r))throw new Error('Mutation');check(r.problemId,steps);rows.push({problemId:r.problemId,familyId:family,solutionSteps:steps})}
const report={io3Instances:io.length,legacyFamilies:familyIds.length,legacyEdgeInstances:Object.values(edges).flat().length,renderedExpressions:mathCount,syntaxErrors:errors,asciiMathematicalProse:ascii,scope:'Strict KaTeX syntax plus math-in-prose heuristic; no browser geometry claim.'};
fs.writeFileSync(path.join(base,'render-audit.json'),JSON.stringify(report,null,2)+'\n');fs.writeFileSync(path.join(base,'review-solutions.json'),JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify(report,null,2));process.exitCode=errors.length?1:0;
