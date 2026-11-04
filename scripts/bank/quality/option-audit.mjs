#!/usr/bin/env node
// Option-only screen. No question text, technique, or difficulty enters a predictor.
// Small-family results are diagnostic evidence, not a statistical safety proof.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const hash=v=>createHash('sha256').update(String(v)).digest('hex');
const mean=xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0;
const compact=s=>s.replace(/\\(?:,|!|;|quad|qquad|left|right)/g,'').replace(/\s/g,'');
function perfectPower(value,degree){
 if(value<0n)return degree%2===1&&perfectPower(-value,degree);
 if(value<2n)return true;
 let lo=1n,hi=value;
 while(lo<=hi){const mid=(lo+hi)/2n,power=mid**BigInt(degree);if(power===value)return true;if(power<value)lo=mid+1n;else hi=mid-1n;}
 return false;
}
export function features(math){
 const text=compact(math),integer=/^-?\d+$/.test(text)?BigInt(text):null,ratio=/^(-?)\\frac\{(-?\d+)\}\{(\d+)\}$/.exec(text);
 const numeric=integer!==null?Number(integer):ratio?(ratio[1]?-1:1)*Number(ratio[2])/Number(ratio[3]):/^-?\d+\.\d+$/.test(text)?Number(text):null;
 let numerator=integer,denominator=1n;
 if(ratio){numerator=BigInt(ratio[2])*(ratio[1]?-1n:1n);denominator=BigInt(ratio[3]);const divisor=gcd(numerator,denominator);if(denominator===0n)numerator=null;else{numerator/=divisor;denominator/=divisor;}}
 const rationalPower=degree=>numerator===null?null:Number(perfectPower(numerator,degree)&&perfectPower(denominator,degree));
 return {text,length:text.length,integer,numeric:Number.isFinite(numeric)&&numeric!==null?numeric:null,absolute:numeric===null?null:Math.abs(numeric),rationalSquare:rationalPower(2),rationalCube:rationalPower(3),negative:Number(text.startsWith('-')),integerForm:Number(integer!==null),fraction:Number(/\\(?:d?frac)/.test(text)),root:Number(/\\sqrt/.test(text)),logarithm:Number(/\\(?:ln|log)/.test(text)),trigonometric:Number(/\\(?:sin|cos|tan|arcsin|arccos|arctan)/.test(text)),operator:Number(/\\operatorname/.test(text)),units:Number(/\\(?:mathrm|text)\{[A-Za-z]/.test(text)),decimalPlaces:/\.(\d+)/.exec(text)?.[1].length||0,trailingZeros:integer===null?null:(text.match(/0+$/)?.[0].length||0)};
}
const gcd=(a,b)=>b?gcd(b,a%b):a<0n?-a:a;
function prepared(record){
 const answer=record.answerChoiceId,choices=record.choices.map(c=>({...c,features:features(c.math)}));
 // Mirror the fact of production shuffling without relying on author order.
 choices.sort((a,b)=>hash('option-audit-shuffle/'+record.problemId+'/'+record.familyId+'/'+a.choiceId).localeCompare(hash('option-audit-shuffle/'+record.problemId+'/'+record.familyId+'/'+b.choiceId)));
 return {id:record.problemId||hash(JSON.stringify(record.parameters)),answer,choices,form:record.pedagogy?.answerForm||'unclassified'};
}
function predictors(training){
 const rules=[];
 // A lone sign-error alternative can couple the correct value to its own
 // negation. Once the question's sign is obvious, that construction pattern
 // leaks the magnitude too. Compare complete literal forms, not substrings.
 for(const sign of ['positive','negative'])rules.push({id:'opposite-pair-'+sign,pick:item=>{
  const selected=item.choices.flatMap((choice,index)=>{
   const value=choice.features.text,negative=value.startsWith('-');
   if(value==='0'||negative!==(sign==='negative'))return [];
   const opposite=negative?value.slice(1):'-'+value;
   return item.choices.some(other=>other!==choice&&other.features.text===opposite)?[index]:[];
  });return selected.length?selected:null;
 }});
 for(const feature of ['length','numeric','absolute','rationalSquare','rationalCube','negative','integerForm','fraction','root','logarithm','trigonometric','operator','units','decimalPlaces','trailingZeros'])for(const direction of ['min','max'])rules.push({id:feature+'-'+direction,pick:item=>{
  const values=item.choices.map(c=>c.features[feature]);if(values.some(v=>v===null))return null;
  const target=direction==='min'?Math.min(...values):Math.max(...values);return values.flatMap((v,i)=>v===target?[i]:[]);
 }});
 for(const feature of ['length','rationalSquare','rationalCube','negative','integerForm','fraction','root','logarithm','trigonometric','operator','units','decimalPlaces','trailingZeros'])rules.push({id:feature+'-minority',pick:item=>{
  const values=item.choices.map(c=>c.features[feature]);if(values.some(v=>v===null))return null;
  const frequencies=values.map(v=>values.filter(x=>x===v).length),minimum=Math.min(...frequencies);return frequencies.flatMap((f,i)=>f===minimum?[i]:[]);
 }});
 for(let rank=0;rank<4;rank++)rules.push({id:'numeric-rank-'+(rank+1),pick:item=>{const values=item.choices.map(c=>c.features.numeric);if(values.some(v=>v===null)||new Set(values).size!==4)return null;const target=[...values].sort((a,b)=>a-b)[rank];return [values.indexOf(target)];}});
 for(let position=0;position<4;position++)rules.push({id:'shuffled-position-'+(position+1),pick:()=>[position]});
 const answers=training.map(item=>item.choices.find(c=>c.choiceId===item.answer)?.features.integer);
 const learned=answers.every(x=>typeof x==='bigint')?answers.reduce(gcd,0n):null;
 const divisors=[2n,3n,4n,5n,6n,7n,8n,9n,10n,12n,16n,24n,25n,60n,100n,144n,360n,1000n,10000n,14400n,100000n];
 if(learned&&learned>1n)divisors.push(learned);
 for(const d of new Set(divisors))rules.push({id:'integer-divisible-'+d,learnedOnlyFromTraining:d===learned,pick:item=>{
  if(item.choices.some(c=>c.features.integer===null))return null;
  const selected=item.choices.flatMap((c,i)=>c.features.integer%d===0n?[i]:[]);return selected.length?selected:null;
 }});
 return rules;
}
function score(rule,items){
 let applicable=0,uniquePredictions=0,uniqueCorrect=0;
 const values=items.map(item=>{
  const selected=rule.pick(item);if(!selected?.length)return .25;applicable++;
  const correct=selected.some(i=>item.choices[i].choiceId===item.answer);
  if(selected.length===1){uniquePredictions++;if(correct)uniqueCorrect++;}
  return correct?1/selected.length:0;
 });
 return {items:items.length,applicable,expectedTieBrokenAccuracy:mean(values),uniquePredictions,uniqueCorrect};
}
export function auditGroup(records){
 const ordered=records.map(prepared).sort((a,b)=>hash('quality-option-split-v1/'+a.id).localeCompare(hash('quality-option-split-v1/'+b.id)));
 const split=Math.max(1,Math.floor(ordered.length/2)),training=ordered.slice(0,split),heldout=ordered.slice(split);
 const results=predictors(training).map(rule=>({rule:rule.id,learnedOnlyFromTraining:rule.learnedOnlyFromTraining===true,training:score(rule,training),heldout:score(rule,heldout)}));
 const ranked=[...results].sort((a,b)=>b.training.expectedTieBrokenAccuracy-a.training.expectedTieBrokenAccuracy||a.rule.localeCompare(b.rule)),selected=ranked[0];
 const flags=results.filter(r=>heldout.length>=3&&r.heldout.expectedTieBrokenAccuracy>=.625&&r.heldout.applicable>=3).map(r=>({rule:r.rule,accuracy:r.heldout.expectedTieBrokenAccuracy,unique:r.heldout.uniquePredictions,uniqueCorrect:r.heldout.uniqueCorrect}));
 return {items:records.length,trainingIds:training.map(i=>i.id),heldoutIds:heldout.map(i=>i.id),chance:.25,selectedUsingTrainingOnly:selected,flags,results,
  reviewRequired:flags.length>0||heldout.length<3,limitedSample:heldout.length<20,mathematicalEquivalence:'Not established by this screen; independently checked in the admission verifier.'};
}
export function auditOptions(records){
 const families={},forms={};for(const p of records){(families[p.familyId]||=[]).push(p);(forms[p.pedagogy?.answerForm||'unclassified']||=[]).push(p);}
 return {version:'quality-option-screen-v1',records:records.length,split:'SHA-256 quality-option-split-v1/id; lower half training, upper half held out; unchanged across reruns',
  limitations:['Small finite families need editorial review; this screen cannot prove absence of all option-only cues.','Numeric magnitude/divisibility are measured only for directly parsed integers, decimal constants and rational fractions. Unsupported expressions remain explicitly inapplicable; length/form screens still apply.','Position results use a deterministic audit permutation; production uses fresh shared shuffles.','All flagged families require documented options-visible disposition. A pooled average cannot clear a flagged family.'],
  families:Object.fromEntries(Object.entries(families).map(([id,rows])=>[id,auditGroup(rows)])),answerForms:Object.fromEntries(Object.entries(forms).map(([id,rows])=>[id,auditGroup(rows)]))};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [input,out]=process.argv.slice(2);if(!out||existsSync(out))throw Error('Supply input JSONL and a NEW report path; preserve prior failures');
 const content=readFileSync(input,'utf8'),records=content.trim().split('\n').map(JSON.parse),report=auditOptions(records);
 writeFileSync(out,JSON.stringify({...report,artifactSha256:hash(content)},null,2)+'\n');
 console.log(JSON.stringify({records:report.records,families:Object.keys(report.families).length,flaggedFamilies:Object.values(report.families).filter(f=>f.reviewRequired).length,publicationApproval:false}));
}
