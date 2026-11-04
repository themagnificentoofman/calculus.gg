import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const candidates=[];
if(process.env.CN_KATEX_MODULE)candidates.push(path.resolve(process.env.CN_KATEX_MODULE));
for(let parent=here;;parent=path.dirname(parent)){candidates.push(path.join(parent,'node_modules/katex/dist/katex.mjs'));if(parent===path.dirname(parent))break;}
candidates.push(path.resolve(here,'../../milestone3/node_modules/katex/dist/katex.mjs'));
const katexPath=candidates.find(p=>fs.existsSync(p));
if(!katexPath)throw new Error('Set CN_KATEX_MODULE or install katex in a repository ancestor');
const {default:katex}=await import(pathToFileURL(katexPath).href);
const root=new URL('./',import.meta.url);const input=JSON.parse(fs.readFileSync(new URL('render-input.json',root),'utf8'));
const errors=[];
for (const row of input){try{katex.renderToString(row.math,{throwOnError:true,strict:'error',trust:false,displayMode:true,output:'htmlAndMathml'});}catch(e){errors.push({problemId:row.problemId,kind:row.kind,index:row.index,error:String(e),math:row.math});}}
const report={expressionCount:input.length,errorCount:errors.length,errors,scope:'Every corrected solution step and optional statement parsed in strict untrusted KaTeX; responsive layout is the parent UI renderer responsibility.',inputSha256:crypto.createHash('sha256').update(fs.readFileSync(new URL('render-input.json',root))).digest('hex')};
fs.writeFileSync(new URL('render-checks.json',root),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({expressions:input.length,errors:errors.length,firstErrors:errors.slice(0,8)}));if(errors.length)process.exitCode=1;
