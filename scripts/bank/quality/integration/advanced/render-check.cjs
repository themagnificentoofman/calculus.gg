const fs=require('node:fs');const path=require('node:path');const {createRequire}=require('node:module');
const repo=path.resolve(process.argv[2]||path.join(__dirname,'../../problem-quality'));
const katex=createRequire(path.join(repo,'package.json'))('katex');
const files=process.argv.slice(3);let count=0,fail=[];
for(const file of files){for(const line of fs.readFileSync(file,'utf8').trim().split('\n')){const r=JSON.parse(line);for(const [field,expr] of [['statement',r.statement],...r.choices.map((c,i)=>['choice'+i,c.math]),...r.solutionSteps.map((s,i)=>['step'+i,s])]){try{katex.renderToString(expr,{throwOnError:true,strict:'error'});count++;}catch(e){fail.push({problemId:r.problemId,familyId:r.familyId,instanceIndex:r.instanceIndex,field,error:String(e),expression:expr});}}}}
const report={expressions:count,failures:fail,strict:true};fs.writeFileSync(path.join(__dirname,'render-report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({expressions:count,failures:fail.length,first:fail.slice(0,3)}));process.exitCode=fail.length?1:0;
