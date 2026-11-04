// Server-only, reviewed presentation. Canonical records and their hashes are
// never rewritten. Finite corrections bind to an exact immutable source hash.
import legacyHashes from './solution-reviews/legacy-hashes.json' with {type:'json'};
import finite from './solution-reviews/finite.json' with {type:'json'};
import {supports,corrected_solution,recipeVersion} from './solution-reviews/legacy.mjs';
import {normalizeNotation,NOTATION_VERSION} from '../math-notation.mjs';

export const SOLUTION_REVIEW_VERSION='worked-solutions-v1';
export function isReviewedLegacyHash(hash) {
 if(typeof hash!=='string'||! /^[a-f0-9]{64}$/.test(hash))return false;
 let lo=0,hi=legacyHashes.length/64-1;
 while(lo<=hi){const mid=Math.floor((lo+hi)/2),value=legacyHashes.slice(mid*64,(mid+1)*64);if(value===hash)return true;if(value<hash)lo=mid+1;else hi=mid-1;}
 return false;
}
const legacyNotation={differentialVariables:['x','y','z','t','u','s']};
const normalize=(steps,options)=>steps.map(step=>normalizeNotation(step,options));
const quality=(source,auditId)=>({version:SOLUTION_REVIEW_VERSION,notationVersion:NOTATION_VERSION,auditId,sourceContentHash:source.contentHash});
function finiteReview(p) {
 const entry=finite[p.problemId];
 return entry&&entry.sourceContentHash===p.contentHash&&entry.revision===p.problemRevision?entry:null;
}
export function presentBankProblem(p) {
 const entry=finiteReview(p);
 let steps,auditId,notation,statement=p.statement;
 if(entry){steps=entry.steps;auditId=entry.auditId;statement=entry.statement||statement;}
 else if(p.schemaVersion===1&&p.problemRevision===1&&isReviewedLegacyHash(p.contentHash)&&supports(p)) {
  steps=corrected_solution(p);auditId=recipeVersion;notation=legacyNotation;
  // The recipe ends with the evaluated combination; make the requested result explicit.
  steps=[...steps,p.choices.find(c=>c.choiceId===p.answerChoiceId).math];
 } else if(p.templateVersion==='standalone-polynomial-v2'&&p.validation?.evidence?.verificationRoute==='standalone-polynomial-v2') {
  // This registered constructor is independently re-executed at admission.
  steps=p.solutionSteps;auditId='standalone-polynomial-v2';
 }
 return {...p,statement:normalizeNotation(statement,notation),choices:p.choices.map(c=>({...c,math:normalizeNotation(c.math)})),solutionSteps:normalize(steps||p.solutionSteps,notation),
  ...(auditId?{solutionQuality:quality(p,auditId)}:{solutionQuality:undefined})};
}
// Saved round content is immutable. Review overlays are separate, after the
// answer/match gates; the exact source hash prevents cross-revision corrections.
export function reviewSavedQuestion(q) {
 const entry=finiteReview(q);
 if(entry)return {steps:normalize(entry.steps),version:SOLUTION_REVIEW_VERSION,sourceContentHash:q.contentHash,clarified:q.solutionReviewVersion!==SOLUTION_REVIEW_VERSION};
 // Legacy snapshots from the current selector include bounded parameters. Use
 // their exact audited source hash; never infer missing historical parameters.
 if(q.problemRevision===1&&isReviewedLegacyHash(q.contentHash)&&q.context?.parameters&&['cn-2026-11-02-full-v2','cn-2026-11-03-ideas-v3'].includes(q.bankRelease)){
  const p={...q,schemaVersion:1,templateVersion:'original-linear-families-v2',parameters:q.context.parameters,choices:q.options.map((math,i)=>({choiceId:String(i),math})),answerChoiceId:String(q.correctIndex)};
  if(supports(p))return {steps:normalize([...corrected_solution(p),q.options[q.correctIndex]],legacyNotation),version:SOLUTION_REVIEW_VERSION,sourceContentHash:q.contentHash,clarified:q.solutionReviewVersion!==SOLUTION_REVIEW_VERSION};
 }
 // New snapshots already contain reviewed legacy solutions. Historical legacy
 // snapshots lacking a full source record are kept verbatim, never guessed.
 if(q.solutionReviewVersion===SOLUTION_REVIEW_VERSION)return {steps:normalize(Array.isArray(q.explanation)?q.explanation:[q.explanation]),version:SOLUTION_REVIEW_VERSION,sourceContentHash:q.contentHash,clarified:false};
 return null;
}
export function savedSolutionReviews(questions=[]) {
 return Object.fromEntries(questions.flatMap((q,i)=>{const review=reviewSavedQuestion(q);return review?[[i,review]]:[];}));
}
