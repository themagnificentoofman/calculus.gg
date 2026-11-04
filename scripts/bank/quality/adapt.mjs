// Explicit new-constructor admission. This never changes frozen M3 builders.
import {createHash} from 'node:crypto';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {normalizeNotation} from '../../../lib/math-notation.mjs';
import {solutionQualityIssues} from '../../../lib/bank/solution-quality.mjs';
export const VERSION='reviewed-quality-constructions-v1';
export const canonical=v=>v&&typeof v==='object'?Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')}}`:JSON.stringify(v);
export const digest=v=>createHash('sha256').update(canonical(v)).digest('hex');
const demands={'strategy-selection':['method-selection'],'hypothesis-checking':['recognition'],'proof of applicability':['synthesis'],'proof':['synthesis'],'modeling':['reframing'],'local computation':['execution'],'geometric synthesis':['reframing','synthesis'],'method selection and synthesis':['method-selection','synthesis'],'reframing and synthesis':['reframing','synthesis'],'reframing and convergence':['reframing','convergence']};
const validDemand=new Set(['execution','recognition','method-selection','reframing','convergence','synthesis']);
function slug(v){const result=v.toLowerCase().replace(/[^a-z0-9-]/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'');if(!/^[a-z][a-z0-9-]{1,63}$/.test(result))throw Error('Technique requires reviewed bounded slug: '+v);return result;}
function assertAdmission(admission,raw,sourceDigest){
 if(!admission||admission.rawSha256!==sourceDigest||admission.familyId!==raw.familyId||!Number.isInteger(admission.index)||admission.index<0)throw Error('Unknown or changed finite source');
 const review=admission.review;
 if(review?.status!=='independently-reviewed'||!review.author||!review.reviewer||review.author===review.reviewer||!review.report||! /^[a-f0-9]{64}$/.test(review.reportSha256)||!review.centralDecision||!review.nearestNeighbor||!review.easiestOptionsVisibleRoute||!review.difficultyRationale||!['easy','medium','hard','olympiad'].includes(review.difficulty))throw Error('Independent options-visible mathematical/editorial review is incomplete');
 if(review.difficulty==='olympiad'&&review.qualifiedOlympiad!==true)throw Error('Unqualified construction cannot enter Olympiad');
 if(!admission.verifier||!admission.module||!admission.finiteDomain||!review.optionAuditReport||! /^[a-f0-9]{64}$/.test(review.optionAuditSha256))throw Error('Finite verification and held-out choice review required');
 const supplement=admission.editorialSupplement;
 if(supplement!==undefined){
  if(!supplement||supplement.rawSha256!==sourceDigest||!supplement.report||! /^[a-f0-9]{64}$/.test(supplement.reportSha256)||Object.keys(supplement).some(k=>!['rawSha256','report','reportSha256','choiceMisconceptions','originalProvenanceKind'].includes(k)))throw Error('Unbound or unsupported editorial supplement');
  if(supplement.choiceMisconceptions!==undefined){
   const labels=supplement.choiceMisconceptions;
   if(!labels||Object.keys(labels).length!==raw.choices.length||raw.choices.some(c=>typeof labels[c.choiceId]!=='string'||!labels[c.choiceId].trim()||labels[c.choiceId].length>1000||(c.misconception&&c.misconception!==labels[c.choiceId]))||labels[raw.answerChoiceId]!=='correct')throw Error('Editorial labels must cover the exact choices without replacing existing routes');
  }
  if(supplement.originalProvenanceKind!==undefined&&(!['original-constructor-extension','original-finite-pool-replacement'].includes(supplement.originalProvenanceKind)||raw.provenance?.kind!==supplement.originalProvenanceKind))throw Error('Unreviewed original provenance clarification');
 }
}
function provenance(raw,admission){
 const p=raw.provenance||{},adapted=p.kind==='adapted';
 if(adapted){
  const a=admission.adaptation;
  const fields=['sourceRecordId','sourceUrl','sourceItemLocator','upstreamCopyright','modificationNotice','sourceInspectionEvidenceId','permissionEvidenceId','licenseScope','licenseUrl'];
  if(!a||!a.sourceRegister||! /^[a-f0-9]{64}$/.test(a.sourceRegisterSha256)||fields.some(k=>typeof p[k]!=='string'||!p[k].trim())||!Array.isArray(p.upstreamCreators)||!p.upstreamCreators.length||p.independentOriginal!==false||p.sourceLicense!=='CC-BY-SA-4.0'||p.adapterLicense!=='CC-BY-SA-4.0'||p.license!=='CC-BY-SA-4.0'||p.licenseUrl!=='https://creativecommons.org/licenses/by-sa/4.0/'||a.sourceRecordId!==p.sourceRecordId)throw Error('Adapted content lacks exact permission, attribution, modifications, or share-alike binding');
  return {...p,sourceItem:p.sourceItemLocator,authoring:{version:VERSION,independentOriginal:false,sourceTextReused:true,rawSha256:admission.rawSha256,reviewId:admission.reviewId}};
 }
 if(p.kind&&p.kind!=='original'&&admission.editorialSupplement?.originalProvenanceKind!==p.kind)throw Error('Unregistered provenance kind');
 if(raw.source?.thirdPartyProblemAdapted===true||p.independentOriginal===false||p.sourceTextReused===true)throw Error('Adapted material cannot use original admission');
 return {kind:'original',sourceUrl:null,sourceItem:null,license:'LicenseRef-CalculusNinja-Original',attribution:p.attribution||raw.source?.attribution||'Original Calculus Ninja content. AI-assisted authorship and independent AI editorial review with reproducible mathematical checks; no human certification or player-calibration claim.',authoring:{version:VERSION,independentOriginal:true,sourceTextReused:false,rawSha256:admission.rawSha256,reviewId:admission.reviewId,theoremReferenceURLs:p.theoremReferenceURLs||raw.theoremReferences||[],referencePurpose:'Mathematical references only; no third-party problem adaptation.'}};
}
export function adaptCandidate(input,admission){
 // Bind the exact Python canonical source bytes, including numerical-audit
 // literals such as 4.0. Re-serializing them in JS would incorrectly attest a
 // different source. Preserve unsafe integral literals as decimal strings in
 // evidence rather than silently rounding a large mathematical integer.
 const sourceDigest=typeof input==='string'?createHash('sha256').update(input).digest('hex'):digest(input);
 const raw=typeof input==='string'?JSON.parse(input,(key,value,context)=>{
  if(typeof value==='number'&&Number.isInteger(value)&&!Number.isSafeInteger(value)){
   if(!context?.source)throw Error('Exact numeric source context is unavailable');
   return context.source;
  }
  return value;
 }):input;
 assertAdmission(admission,raw,sourceDigest);
 const review=admission.review,previous=admission.previous,meta=raw.pedagogy;
 if(!meta)throw Error('Pedagogy required');
 const reasoning=[...new Set((Array.isArray(meta.reasoningDemand)?meta.reasoningDemand:[meta.reasoningDemand]).flatMap(d=>demands[d]||[d]))];
 if(reasoning.some(d=>!validDemand.has(d)))throw Error('Unregistered reasoning demand');
 const pedagogy={...meta,constructionId:raw.familyId,relatedIdeaGroupId:review.relatedIdeaGroupId||meta.relatedIdeaGroupId,structuralSignature:review.structuralSignature||meta.structuralSignature,primaryTechnique:review.primaryTechnique||meta.primaryTechnique,alternativeTechniques:meta.alternativeTechniques||[],prerequisites:meta.prerequisites||[],sourceRecordIds:meta.sourceRecordIds||[],responseFormat:'multiple-choice',reasoningDemand:reasoning,difficultyRationale:review.difficultyRationale};
 const choices=raw.choices.map(c=>({choiceId:c.choiceId,math:normalizeNotation(c.math),misconception:c.misconception||admission.editorialSupplement?.choiceMisconceptions?.[c.choiceId]}));
 if(choices.length!==4||choices.some(c=>typeof c.misconception!=='string'||!c.misconception.trim())||new Set(choices.map(c=>c.math.replace(/\s/g,''))).size!==4)throw Error('Four distinct reviewed choices and explicit wrong routes required');
 const topic=raw.topic,statement=normalizeNotation(raw.statement),steps=raw.solutionSteps.map(s=>normalizeNotation(s));
 if(previous&&(!/^cn_[a-f0-9]{20}$/.test(previous.problemId)||!Number.isInteger(previous.revision)||previous.revision<1||! /^[a-f0-9]{64}$/.test(previous.sourceContentHash)||! /^[a-f0-9]{64}$/.test(previous.semanticHash)))throw Error('An immutable revision requires exact prior identity and mathematical lineage');
 if(previous?.meaningChanged===true&&!review.semanticChangeReason)throw Error('Semantic revision requires an explicit independently reviewed change reason');
 const body={schemaVersion:2,problemId:previous?.problemId||'cn_'+digest([VERSION,admission.module,raw.familyId,admission.index]).slice(0,20),problemRevision:previous?previous.revision+1:1,
  familyId:raw.familyId,templateVersion:VERSION,parameters:{instance:admission.index},
  semanticHash:previous&&!previous.meaningChanged?previous.semanticHash:digest({statement,topic}),statement,choices,answerChoiceId:raw.answerChoiceId,solutionSteps:steps,
  assumptions:raw.assumptions?.length?raw.assumptions:raw.conditions?.length?raw.conditions:['Real variables on the explicitly stated domain; all restrictions in the statement apply.'],topic,difficulty:review.difficulty,subtopic:pedagogy.relatedIdeaGroupId,
  techniqueTags:[...new Set([pedagogy.primaryTechnique,...pedagogy.alternativeTechniques].map(slug))],pedagogy,provenance:provenance(raw,admission),
  validation:{status:'passed',methods:['registered-finite-source-reconstruction',admission.verifier,'exact-choice-inequivalence','independent-options-visible-editorial-review'],humanReviewed:false,
   evidence:{verificationRoute:VERSION,parameterDomain:admission.finiteDomain,assumptionsChecked:true,solutionDerivationChecked:true,uniqueCorrectOption:true,reviewId:admission.reviewId,rawSha256:admission.rawSha256,independentReviewReport:review.report,independentReviewReportSha256:review.reportSha256,optionAuditReport:review.optionAuditReport,optionAuditSha256:review.optionAuditSha256,executedChecks:raw.verificationEvidence||raw.automatedChecks||raw.validation?.evidence?.checks||raw.validation?.evidence||[],analyticCertificate:raw.analyticCertificate||[],formalProofAssistantChecked:false,numericalAgreementUsedAsProof:false,editorialReview:'AI-assisted independent review; not human certification or player calibration.'}},
  estimates:{difficulty:review.difficulty,solveSeconds:review.solveSeconds||raw.estimatedSolveSeconds||360,basis:review.difficultyRationale+' Editorial estimate; player calibration pending.'}};
 const issues=solutionQualityIssues(body);if(issues.length)throw Error('Quality admission: '+issues.join(' '));
 const result={...body,contentHash:digest(body)};
 if(admission.contentHash&&result.contentHash!==admission.contentHash)throw Error('Reviewed destination hash changed');
 return result;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 for await(const line of createInterface({input:process.stdin,crlfDelay:Infinity})){
  try{const {raw,rawCanonical,admission}=JSON.parse(line);process.stdout.write(JSON.stringify({record:adaptCandidate(rawCanonical??raw,admission)})+'\n');}
  catch(error){process.stdout.write(JSON.stringify({error:error.message})+'\n');}
 }
}
