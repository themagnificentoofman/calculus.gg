// Source-bound review of the assembled series catalog and actual served forms.
// This reuses exact prior mathematics; it does not claim 705 fresh derivations.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {presentBankProblem} from '../../../../lib/server/solution-presentation.mjs';
import {normalizeNotation} from '../../../../lib/math-notation.mjs';
import {renderMath} from '../../../../lib/render-math.mjs';
import {formatProblemStatement,formatSolutionStep} from '../../../../lib/solution-format.mjs';
import {solutionQualityIssues} from '../../../../lib/bank/solution-quality.mjs';
import {auditOptions} from '../option-audit.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const [stageArg,outputArg]=process.argv.slice(2);
if(!stageArg||!outputArg)throw Error('Usage: series_final_v6.mjs STAGE NEW_OUTPUT_DIRECTORY');
const stage=resolve(stageArg),out=resolve(outputArg),bundle=resolve(root,'scripts/bank/quality/series/mathematical');
if(existsSync(resolve(out,'final-option-review.json')))throw Error('Preserve prior review outputs');
mkdirSync(out,{recursive:true});
const canonical=v=>v&&typeof v==='object'?Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')}}`:JSON.stringify(v);
const sha=v=>createHash('sha256').update(v).digest('hex');
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const lines=p=>readFileSync(p,'utf8').trim().split('\n').map(JSON.parse);
const artifact=p=>({path:relative(root,p),sha256:sha(readFileSync(p))});
const write=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
const byId=rows=>new Map(rows.map(r=>[r.problemId,r]));
const menu=r=>({answerChoiceId:r.answerChoiceId,choices:r.choices.map(c=>({choiceId:c.choiceId,math:normalizeNotation(c.math)}))});
const normalizedSteps=r=>r.solutionSteps.map(s=>normalizeNotation(s));

const candidates=lines(resolve(stage,'canonical-previews.jsonl'));
const retained=lines(resolve(stage,'retained-originals.jsonl'));
const current=[...candidates,...retained],currentById=byId(current);
assert.equal(current.length,705);assert.equal(currentById.size,705);
const originals=byId(lines(resolve(bundle,'full-source-records.jsonl')));
const finalReviewed=byId(lines(resolve(bundle,'review/effective705-final-v3.jsonl')));
const replacements=read(resolve(stage,'replacement-joins.json'));
assert.equal(replacements.length,162);
const sourceToDestination=new Map(replacements.map(r=>[r.oldPreviewProblemId,r.problemId]));
const destinationToSource=new Map(replacements.map(r=>[r.problemId,r.oldPreviewProblemId]));
const patchJoins=new Map(read(resolve(bundle,'source-joins.json')).map(r=>[r.sourcePreview.problemId,r]));
const priorReview=read(resolve(bundle,'complete705-supplemental-review.json'));
const priorFamilies=new Map(priorReview.families.map(f=>[f.familyId,f]));
const oldJoin=new Map(priorReview.sourceJoins.map(r=>[r.problemId,r]));
const priorPairs=byId(read(resolve(bundle,'review/mathematical-pairs-final-v3.json')).recordsEvidence);
const priorDomains=byId(read(resolve(bundle,'review/domain-inventory-final.json')).recordsEvidence);
const presentations=read(resolve(bundle,'source-presentations.json'));
const captured=byId(presentations.records);
const capacity=read(resolve(bundle,'capacity-after-options.json'));
const capacityById=byId(capacity.recordsEvidence);
const changes=byId(read(resolve(bundle,'difficulty-changes.json')));
const priorEntries=read(resolve(stage,'admission-previews.json'));
assert.equal(changes.size,13);assert.equal(capacity.records,705);
assert.equal(priorReview.counts.patchesAwaitingParentReview,0);
assert.equal(priorReview.counts.numericChoiceInequalityCertificates,3906);
assert.equal(priorReview.counts.unresolvedPairParses,0);

const served=current.map(presentBankProblem),servedById=byId(served);
const binding=[],groups=[],normalizations=[];
let unchanged=0,patched=0,preservedPresentation=0;
for(const record of current){
 const oldId=destinationToSource.get(record.problemId)||record.problemId;
 const source=originals.get(oldId),reviewed=finalReviewed.get(oldId),capturedPresentation=captured.get(oldId);
 assert(source&&reviewed&&capturedPresentation,record.problemId);
 const pair=priorPairs.get(oldId),domain=priorDomains.get(oldId),earlier=oldJoin.get(oldId),cap=capacityById.get(oldId);
 assert(pair&&domain&&earlier&&cap,oldId);
 assert.equal(source.contentHash,cap.sourceContentHash);
 assert.equal(source.contentHash,earlier.sourceContentHash);
 assert.equal(source.semanticHash,record.semanticHash);
 assert.equal(record.familyId,source.familyId);
 assert.deepEqual(menu(record),menu(reviewed));
 assert.equal(pair.answerChoiceId,record.answerChoiceId);
 assert.equal(record.difficulty,cap.reviewedDifficulty);
 const presentation=servedById.get(record.problemId);
 assert.equal(presentation.statement,normalizeNotation(capturedPresentation.statement));
 assert.deepEqual(presentation.solutionSteps,normalizedSteps(capturedPresentation));
 preservedPresentation++;
 const patch=patchJoins.get(oldId);
 if(patch){
  assert.equal(record.problemId,sourceToDestination.get(oldId));
  assert.equal(source.contentHash,patch.sourcePreview.contentHash);
  const peer=resolve(bundle,patch.independentReview.path);
  assert.equal(sha(readFileSync(peer)),patch.independentReview.sha256);
  assert.equal(record.difficulty,patch.reviewedDifficulty);
  assert.equal(patch.qualifiedOlympiad,record.difficulty==='olympiad');
  // The composed private raw record must retain the exact source presentation.
  assert.equal(record.statement,normalizeNotation(capturedPresentation.statement));
  assert.deepEqual(record.solutionSteps,normalizedSteps(capturedPresentation));
  patched++;
 }else{assert.equal(canonical(record),canonical(source));unchanged++;}
 const rawMenu=record.choices.map(c=>({choiceId:c.choiceId,math:c.math}));
 const shownMenu=presentation.choices.map(c=>({choiceId:c.choiceId,math:c.math}));
 if(canonical(rawMenu)!==canonical(shownMenu))normalizations.push({problemId:record.problemId,familyId:record.familyId,oldPreviewProblemId:oldId,sourceContentHash:record.contentHash,before:rawMenu,after:shownMenu,kind:'existing-conservative-notation-normalization'});
 const exactChange=changes.get(oldId),entry=priorEntries[record.provenance?.authoring?.reviewId];
 const central=exactChange?.reason||entry?.review?.centralDecision||record.pedagogy.difficultyRationale;
 const primary=exactChange?record.familyId.endsWith('finite-cycle-resolvent')?'finite-cosine-moment-bounds':record.familyId.endsWith('totient-Lambert')?'geometric-series-bounds':'positive-partial-product-bound':record.pedagogy.primaryTechnique;
 groups.push({problemId:record.problemId,problemRevision:record.problemRevision,contentHash:record.contentHash,
  sourcePreviewProblemId:oldId,sourcePreviewContentHash:source.contentHash,semanticHash:record.semanticHash,
  familyId:record.familyId,canonicalConstruction:source.pedagogy.constructionId,constructionFamilyId:source.pedagogy.constructionId,
  relatedIdeaGroupId:cap.globalRelatedGroup,topicLocalIdeaGroupId:cap.reviewedGroup,
  structuralSignature:record.pedagogy.structuralSignature,primaryTechnique:primary,
  servedPrimaryTechnique:record.pedagogy.primaryTechnique,centralDecision:central,
  normalizedTaskKey:cap.normalizedKey,normalizationReason:cap.normalizationReason,
  qualifiedOlympiad:record.difficulty==='olympiad',recommendedDifficulty:record.difficulty,
  difficultyEvidence:exactChange?.peerReport||null,newIndependentIdeaCreditFromOptionRepair:0});
 binding.push({problemId:record.problemId,problemRevision:record.problemRevision,contentHash:record.contentHash,sourcePreviewProblemId:oldId,sourceContentHash:source.contentHash,
  semanticHash:record.semanticHash,familyId:record.familyId,canonicalUnchanged:!patch,
  optionPatch:patch?{route:patch.route,patchCanonicalSHA256:patch.patchCanonicalSHA256,independentReview:patch.independentReview}:null,
  normalizedMenuSha256:sha(canonical(menu(record))),earlierReviewedMenuSha256:sha(canonical(menu(reviewed))),
  priorMathematics:{resolutionStatus:pair.status,pairCertificates:Array.isArray(pair.pairCertificates)?pair.pairCertificates.length:0,
   oppositePairs:pair.oppositePairs?.length||0,domainStatus:domain.status,sourceJoinSha256:sha(canonical(earlier))},
  currentPresentationMatchesCapture:true,statementChangedOnlyByCurrentPresenter:record.statement!==presentation.statement,
  solutionChangedOnlyByCurrentPresenter:canonical(record.solutionSteps)!==canonical(presentation.solutionSteps),
  difficulty:record.difficulty,difficultyChanged:!!exactChange});
}
assert.equal(unchanged,543);assert.equal(patched,162);assert.equal(preservedPresentation,705);
assert.equal(binding.filter(r=>r.difficultyChanged).length,13);

const servedInput=served.map(r=>JSON.stringify(Object.fromEntries(['problemId','familyId','choices','answerChoiceId','pedagogy'].map(k=>[k,r[k]])))).join('\n')+'\n';
writeFileSync(resolve(out,'served-option-input.jsonl'),servedInput);
const audit={...auditOptions(served),artifactSha256:sha(servedInput)};
write('served-option-audit.json',audit);
const rawAudit=read(resolve(stage,'option-audit.json'));
const positionReason='A deterministic diagnostic permutation is not the production choice position. The serving selector freshly shuffles each choice set and derives the answer index from its preserved choice ID. This disposition applies only to position, never to expression features.';
const reasons={
 'm3-series-easy-binomial-total':'The correct value is 2^n, whose square status follows the parity of n. The odd n=5 case has correct 32 and wrong 16, so the bare square rule fails. All ten literal menus were inspected against the independently checked finite binomial identity; wrong endpoint and normalization routes supply square and nonsquare alternatives. The measured 45% development /65% held-out accuracy remains disclosed. No notation padding or new parameters are introduced to tune the split.',
 'm3-series-medium-weighted-binomial-total':'The genuine derivative-binomial answer n·2^(n−1) is divisible by powers of two. Alternatives 2^n and twice the correct value often have the same divisibility; endpoint-omission alternatives can differ by n. The flagged divisibility rules have only two unique held-out predictions, with other predictions tied. Their development accuracies are below44%, versus 2/3 held-out. This is a partial mathematical filter with an explicit finite-sample limitation, not a uniform answer identifier.',
 'm3-series-olympiad-Fourier-fourth-sine':'Every one of the eight menus contains at least two pure rational multiples of pi². The correct expression therefore has no unique pi² form. Actual simplification of the first sine term yields shorter rational alternatives at some angles and longer trigonometric expressions at others. The shortest-expression rule is25% development /75% held-out, with only two unique held-out predictions. The complete finite menus and underlying correct values remain those independently reviewed; no unsimplification is introduced to tune lengths.',
 'm3-series-easy-ratio-test-data':'All ten statements are factorial-ratio limits with the genuine outcomes zero or positive infinity, five of each. Every menu includes zero, infinity, one and a finite parameter; the last two are the errors from omitting the factorial shift. Length and noninteger features identify infinity, whose frequency is20% in the development half and80% in held-out. Choosing uniformly between the two intrinsic outcomes gives50% over the entire family; this limitation is explicit. Inventing another support would change the tasks, while padding infinity would obscure standard notation.'
};
const literalChecks=[];
for(const [f,reason]of Object.entries(reasons)){
 const rows=served.filter(r=>r.familyId===f);
 if(f.endsWith('binomial-total'))for(const r of rows){
  const n=Number(/\\binom\{(\d+)\}/.exec(r.statement)?.[1]);assert(Number.isInteger(n));
  const expected=BigInt(f.includes('weighted')?n:1)*2n**BigInt(f.includes('weighted')?n-1:n);
  const value=BigInt(r.choices.find(c=>c.choiceId===r.answerChoiceId).math);assert.equal(value,expected);
  literalChecks.push({problemId:r.problemId,familyId:f,check:'literal finite binomial identity',expected:expected.toString(),passed:true});
 }else if(f.endsWith('Fourier-fourth-sine'))for(const r of rows){
  const count=r.choices.filter(c=>/^\\frac\{(?:\d+ )?\\pi\^\{2\}\}\{\d+\}$/.test(c.math)).length;
  assert(count>=2);literalChecks.push({problemId:r.problemId,familyId:f,check:'at least two pure rational pi-square alternatives',count,passed:true});
 }else{
  assert.equal(rows.filter(r=>r.choices.find(c=>c.choiceId===r.answerChoiceId).math==='0').length,5);
  assert.equal(rows.filter(r=>r.choices.find(c=>c.choiceId===r.answerChoiceId).math==='\\infty').length,5);
  for(const r of rows){for(const m of ['0','1','\\infty'])assert(r.choices.some(c=>c.math===m));literalChecks.push({problemId:r.problemId,familyId:f,check:'both extended-real outcomes and two finite misconception alternatives',passed:true});}
 }
}
const flagDispositions=(name,result,form=false)=>result.flags.map(flag=>{
 const scores=result.results.find(r=>r.rule===flag.rule);assert(scores);
 const position=flag.rule.startsWith('shuffled-position-');
 const reason=position?positionReason:form&&name==='extended-real'?reasons['m3-series-easy-ratio-test-data']+' This form contains the eight original cases (four zero and four infinity); the two extensions have exact-expression metadata but remain included in the complete ten-item family review. Its separate four/four split is retained.':reasons[name];
 assert(reason,'New unexplained flag: '+name+'/'+flag.rule);
 return {...flag,training:scores.training,heldout:scores.heldout,
  disposition:position?'fresh-production-shuffle':'literal-mathematical-disposition-with-measured-residual',reason};
});
const families=Object.entries(audit.families).map(([familyId,result])=>{
 const earlier=priorFamilies.get(familyId);assert(earlier);
 return {familyId,records:result.items,trainingIds:result.trainingIds,heldoutIds:result.heldoutIds,
  flags:flagDispositions(familyId,result),smallSample:result.heldoutIds.length<3,
  smallSampleDisposition:result.heldoutIds.length<3?'One finite item cannot estimate held-out family performance. Its exact mathematics/options and source credit are reviewed individually; do not extrapolate an option-only accuracy estimate.':earlier.smallSampleDisposition,
  literalPairCoverage:earlier.literalPairCoverage,scalarRankDiagnostic:earlier.scalarRankDiagnostic,
  domainDisposition:earlier.domainDisposition,categoricalScope:earlier.categoricalScope,
  wrongChoiceMisconceptionInventory:earlier.wrongChoiceMisconceptionInventory,
  priorSourceReviewSha256:sha(canonical(earlier)),unresolved:false};
});
const forms=Object.entries(audit.answerForms).map(([answerForm,result])=>({answerForm,records:result.items,flags:flagDispositions(answerForm,result,true),trainingIds:result.trainingIds,heldoutIds:result.heldoutIds,scope:'A pooled answer form cannot clear a family-specific flag.'}));
const replicated=Object.entries(audit.families).flatMap(([familyId,r])=>r.results.filter(s=>!s.rule.startsWith('shuffled-position-')&&s.training.expectedTieBrokenAccuracy>=.625&&s.heldout.expectedTieBrokenAccuracy>=.625).map(s=>({familyId,rule:s.rule,training:s.training,heldout:s.heldout})));
assert.equal(replicated.length,0);
const counts={};
for(const level of ['easy','medium','hard','olympiad']){
 const rs=groups.filter(r=>r.recommendedDifficulty===level),fs=new Map();
 for(const r of rs){if(!fs.has(r.canonicalConstruction))fs.set(r.canonicalConstruction,new Set());fs.get(r.canonicalConstruction).add(r.normalizedTaskKey);}
 const horizon=level==='olympiad'?10:5;
 counts[level]={rawItems:rs.length,normalizedMeaningfulItems:new Set(rs.map(r=>r.normalizedTaskKey)).size,
  constructionFamilies:fs.size,topicLocalGroups:new Set(rs.map(r=>r.topicLocalIdeaGroupId)).size,
  globalRelatedGroups:new Set(rs.map(r=>r.relatedIdeaGroupId)).size,
  requiredHorizonRounds:horizon,capacityUnderFamilyCap2:[...fs.values()].reduce((n,set)=>n+Math.min(set.size,2*horizon),0),
  normalizedItemsPerFamily:Object.fromEntries([...fs].map(([f,keys])=>[f,keys.size]))};
 for(const k of ['rawItems','normalizedMeaningfulItems','constructionFamilies','topicLocalGroups'])assert.equal(counts[level][k],capacity.afterCounts[level][k]);
}
assert.equal(counts.olympiad.topicLocalGroups,30);assert.equal(counts.olympiad.normalizedMeaningfulItems,240);

const renderFailures=[];let expressions=0;
for(const p of served){
 const check=(math,location)=>{expressions++;try{renderMath(math,true);}catch(e){renderFailures.push({problemId:p.problemId,location,math,error:e.message});}};
 for(const [i,math]of[p.statement,...p.choices.map(c=>c.math),...p.solutionSteps].entries())check(math,i);
 for(const b of [...formatProblemStatement(p.statement),...p.solutionSteps.flatMap(formatSolutionStep)])if(b.kind==='math')check(b.value,'formatted');else for(const part of b.parts)if(part.kind==='math')check(part.value,'inline');
 for(const issue of solutionQualityIssues(p))renderFailures.push({problemId:p.problemId,location:'solution-quality',error:issue});
}
write('served-render.json',{records:705,expressions,strict:true,failures:renderFailures});assert.equal(renderFailures.length,0);
const sourceFiles=[resolve(stage,'canonical-previews.jsonl'),resolve(stage,'retained-originals.jsonl'),resolve(stage,'admission-previews.json'),resolve(stage,'replacement-joins.json'),resolve(stage,'effective-option-input.jsonl'),resolve(stage,'option-audit.json'),
 ...['full-source-records.jsonl','source-joins.json','source-presentations.json','capacity-after-options.json','difficulty-changes.json','complete705-supplemental-review.json','review/effective705-final-v3.jsonl','review/mathematical-pairs-final-v3.json','review/domain-inventory-final.json'].map(f=>resolve(bundle,f)),
 ...Object.keys(presentations.sourceFiles).map(f=>resolve(root,f)),resolve(root,'lib/server/compact-bank-selection.ts'),resolve(root,'scripts/bank/quality/option-audit.mjs'),fileURLToPath(import.meta.url)];
const sources=sourceFiles.map(artifact);
write('item-group-map.json',{status:'independently-reviewed-source-bound-rebind',sourceArtifacts:sources,
 scope:'Retains the existing independently reviewed normalized tasks and related groups. The13 finite demotions use their independently established easiest options-visible route for the method metric. The original served method tag is retained separately so the owner can reconcile serving metadata without erasing exposure.',
 counts,records:groups,qualifiedOlympiadGroupDeficitFrom30:0,olympiadNormalizedDeficitFrom240:0,admitted:false});
write('notation-normalizations.json',{records:normalizations.length,normalizations,sourceArtifacts:sources.filter(x=>x.path.includes('math-notation')||x.path.includes('solution-presentation')||x.path.includes('solution-reviews'))});
const report={status:'complete-actual-destination-and-served-series-option-review',reviewer:'series_final_review',sourceArtifacts:sources,
 counts:{effectiveRecords:705,candidateRecords:candidates.length,retainedRecords:retained.length,unchangedFullCanonicalRecords:unchanged,sourceBoundOptionReplacements:patched,changedPrivateIds:replacements.filter(r=>r.oldPreviewProblemId!==r.problemId).length,
  mandatoryDifficultyChanges:13,capturedPresentationsMatched:preservedPresentation,servedNotationMenuChanges:normalizations.length,
  servedStatementChanges:binding.filter(r=>r.statementChangedOnlyByCurrentPresenter).length,servedSolutionChanges:binding.filter(r=>r.solutionChangedOnlyByCurrentPresenter).length,
  constructionFamilies:families.length,flaggedFamilies:families.filter(r=>r.flags.length).length,smallSampleOnlyFamilies:families.filter(r=>r.smallSample&&!r.flags.length).length,
  answerForms:forms.length,flaggedAnswerForms:forms.filter(r=>r.flags.length).length,numericPairCertificatesRebound:3906,scalarMenus:642,tupleMenus:9,categoricalMenus:54,
  unresolvedPairOrDomainCases:0,replicatedNonPositionSignals:replicated.length,strictRenderedExpressions:expressions},
 families,answerForms:forms,records:binding,literalFlagChecks:literalChecks,replicatedNonPositionSignals:replicated,
 rawVersusServedFlagComparison:Object.keys(audit.families).map(f=>({familyId:f,rawFlags:rawAudit.families[f].flags,servedFlags:audit.families[f].flags})),
 servedOptionInput:artifact(resolve(out,'served-option-input.jsonl')),servedOptionAudit:artifact(resolve(out,'served-option-audit.json')),servedRender:artifact(resolve(out,'served-render.json')),normalizedGroupMap:artifact(resolve(out,'item-group-map.json')),
 scope:'All705 actual destination records rejoin the exact reviewed menu and domain evidence.543 full canonical records are unchanged;162 changed menus rejoin independent patches and inherit the current source-bound statement/solution. The existing bounded option screen is rerun on actual served notation; every family/form flag has a concrete disposition. This pass does not claim705 fresh answer derivations.',
 limitations:['Finite diagnostic splits do not prove absence of every possible learned clue. Intrinsic zero/infinity outcomes and measured divisibility/form residuals remain explicitly disclosed.',
 'No new generic classifiers or held-out horizon seeds were introduced. Main selector/session tests and full release admission remain owner gates.',
 'Human review, formal proof, player calibration, import, activation and deployment are not claimed.',
 'The13 changed easiest routes are reflected in the per-item method map; the original serving metadata is also recorded for reconciliation. No new related idea or normalized capacity is credited.'],
 humanReviewed:false,formalProof:false,admitted:false,imported:0,active:0};
write('final-option-review.json',report);
console.log(JSON.stringify({counts:report.counts,capacity:counts,report:artifact(resolve(out,'final-option-review.json')),groupMap:artifact(resolve(out,'item-group-map.json'))}));
