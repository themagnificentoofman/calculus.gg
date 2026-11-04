/* Strictly render every revised field, and exercise portable lookup guards. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const base=__dirname;
let katex;
const candidates=[];
if(process.env.BANK_AUDIT_KATEX)candidates.push(process.env.BANK_AUDIT_KATEX);
for(let p=base;;p=path.dirname(p)){candidates.push(path.join(p,'node_modules/katex'));if(path.dirname(p)===p)break;}
candidates.push('/Users/zhenxg/Documents/Codex/2026-11-03/sign/work/solution-audit/node_modules/katex');
for(const p of candidates){try{katex=require(p);break;}catch(e){}}
if(!katex)throw Error('Set BANK_AUDIT_KATEX to the repository KaTeX package');
const file=process.env.BANK_AUDIT_CORRECTIONS||path.join(base,'correction-data.json'),data=JSON.parse(fs.readFileSync(file));
let expressions=0,solutionSteps=0,statements=0;const errors=[];
function inspect(value,item,field){
 expressions++;
 try{
  if(/\\(?:log\b|operatorname\{(?:asin|acos|atan)\})/.test(value))throw Error('Noncanonical function name');
  if(value.includes('\\begin{gathered}'))throw Error('Hard-wrapped gathered prose');
  if(/Here\s+m\s*=|F\(b\)-F\(a\)/.test(value))throw Error('Unbound original explanation pattern');
  for(const match of value.matchAll(/\\textnormal\{([^{}]*)\}/g))if(/[_^]/.test(match[1]))throw Error('ASCII exponent/subscript inside prose');
  katex.renderToString(value,{displayMode:true,throwOnError:true,strict:'error',trust:false});
 }catch(e){errors.push({problemId:item.problemId,familyId:item.familyId,instance:item.instance,field,error:String(e),value});}
}
for(const item of data.corrections){
 for(const [i,value] of item.solutionSteps.entries()){inspect(value,item,'solutionSteps['+i+']');solutionSteps++;}
 if(item.statement){inspect(item.statement,item,'statement');statements++;}
 if(item.solutionSteps.at(-1)!==item.answerMath)errors.push({problemId:item.problemId,error:'Final step differs from guarded original answer expression'});
 for(const [i,check] of item.checks.entries())for(const field of ['left','right'])if(check[field])inspect(check[field],item,'checks['+i+'].'+field);
}
const report={correctionVersion:data.correctionVersion,records:data.corrections.length,solutionSteps,statementOverrides:statements,renderedExpressions:expressions,errors,correctionDataSha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),katexVersion:katex.version,mode:'throwOnError=true, strict=error, trust=false',limitations:'Strict parser/render verification; visual responsive layout is verified by the parent app workflow.'};
fs.writeFileSync(path.join(base,'render-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,errors:errors.slice(0,5)}));
if(errors.length)process.exit(1);
