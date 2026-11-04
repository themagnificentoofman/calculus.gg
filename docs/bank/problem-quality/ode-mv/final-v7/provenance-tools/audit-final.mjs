import{readFileSync,writeFileSync,existsSync}from'node:fs';
import{resolve}from'node:path';
import{pathToFileURL}from'node:url';
import{createHash,}from'node:crypto';
import{createRequire}from'node:module';
const [repoArg,stageArg,outArg]=process.argv.slice(2),repo=resolve(repoArg),stage=resolve(stageArg),out=resolve(outArg);
const{auditOptions}=await import(pathToFileURL(resolve(repo,'scripts/bank/quality/option-audit.mjs'))),require=createRequire(resolve(repo,'package.json')),katex=require('katex');
const hash=x=>createHash('sha256').update(x).digest('hex');const read=p=>readFileSync(resolve(p),'utf8');
const rows=['canonical-previews.jsonl','retained-originals.jsonl'].flatMap(f=>read(resolve(stage,f)).trim().split('\n').map(JSON.parse));
if(rows.length!==1531||new Set(rows.map(r=>r.problemId)).size!==1531)throw Error('Invalid final population');
const lite=rows.map(r=>Object.fromEntries(['problemId','familyId','choices','answerChoiceId','pedagogy'].map(k=>[k,r[k]])));const raw=lite.map(r=>JSON.stringify(r)).join('\n')+'\n';
writeFileSync(resolve(out,'raw-options.jsonl'),raw);writeFileSync(resolve(out,'raw-option-audit.json'),JSON.stringify({...auditOptions(lite),artifactSha256:hash(raw)},null,2)+'\n');
const served=read(resolve(out,'served-records.jsonl')).trim().split('\n').map(JSON.parse),records=[],failures=[];let expressions=0;
for(const r of served){let n=0;for(const[field,strings]of[['statement',[r.statement]],['choices',r.choices.map(c=>c.math)],['solutionSteps',r.solutionSteps]])for(let i=0;i<strings.length;i++){try{katex.renderToString(strings[i],{throwOnError:true,strict:'error',output:'htmlAndMathml'});expressions++;n++;}catch(e){failures.push({problemId:r.problemId,field,index:i,math:strings[i],error:e.message});}}records.push({problemId:r.problemId,revision:r.problemRevision,contentHash:r.contentHash,expressions:n,passed:!failures.some(x=>x.problemId===r.problemId)});}
writeFileSync(resolve(out,'render.json'),JSON.stringify({status:failures.length?'failed':'passed',records:served.length,expressions,strict:true,servedInputSha256:hash(read(resolve(out,'served-records.jsonl'))),katexVersion:require('katex/package.json').version,perRecord:records,failures,scope:'Strict rendering of every final served statement, all four choices, and every solution step; no mathematical proof inferred from successful rendering.'},null,2)+'\n');console.log(JSON.stringify({records:rows.length,expressions,renderFailures:failures.length,rawFlaggedFamilies:Object.values(auditOptions(lite).families).filter(f=>f.flags.length).length}));if(failures.length)process.exitCode=1;
