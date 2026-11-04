// Rebind the final series stage to exact v6 evidence and the independent
// complete-term display peer. No canonical, registry or eligibility edits.
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
const [stageArg,outArg]=process.argv.slice(2);
if(!stageArg||!outArg)throw Error('Usage: series_final_v7.mjs STAGE NEW_OUTPUT_DIRECTORY');
const stage=resolve(stageArg),out=resolve(outArg),oldStage=resolve(root,'.bank-data/quality/series-previews-v6');
if(existsSync(out))throw Error('Preserve previous evidence; output directory must be new');
mkdirSync(out,{recursive:true});
const canonical=v=>v&&typeof v==='object'?Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')}}`:JSON.stringify(v);
const sha=v=>createHash('sha256').update(v).digest('hex');
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const lines=p=>readFileSync(p,'utf8').trim().split('\n').map(JSON.parse);
const byId=rows=>new Map(rows.map(r=>[r.problemId,r]));
const artifact=p=>({path:relative(root,p),sha256:sha(readFileSync(p))});
const write=(name,value)=>writeFileSync(resolve(out,name),JSON.stringify(value,null,2)+'\n');
const oldDir=resolve(root,'docs/bank/problem-quality/series/final-v6');
const previous=read(resolve(oldDir,'final-option-review.json'));
const previousMap=read(resolve(oldDir,'item-group-map.json'));
const previousAudit=read(resolve(oldDir,'served-option-audit.json'));
const oldById=byId(['canonical-previews.jsonl','retained-originals.jsonl'].flatMap(n=>lines(resolve(oldStage,n))));
const candidates=lines(resolve(stage,'canonical-previews.jsonl')),retained=lines(resolve(stage,'retained-originals.jsonl'));
const records=[...candidates,...retained],currentById=byId(records),served=records.map(presentBankProblem),servedById=byId(served);
assert.equal(candidates.length,571);assert.equal(retained.length,134);assert.equal(currentById.size,705);
assert.deepEqual([...currentById.keys()].sort(),[...oldById.keys()].sort());
const joins=read(resolve(stage,'replacement-joins.json')),joinById=byId(joins);
assert.equal(joins.length,8);
const lattice=resolve(root,'scripts/bank/quality/series/lattice');
const rawPath=resolve(root,'scripts/bank/quality/late-final-raw/series-lattice-display.jsonl');
const raw=lines(rawPath),rawByIndex=new Map(raw.map(r=>[r.instanceIndex,r]));
const proposal=read(resolve(lattice,'proposal.json'));
const proposals=new Map(proposal.records.map(r=>[r.sourcePreview.problemId,r]));
const peerPath=resolve(root,'docs/bank/problem-quality/lattice-display-owner-peer-v1.json');
const peer=read(peerPath),peerByIndex=new Map(peer.records.map(r=>[r.index,r]));
assert.equal(sha(readFileSync(peerPath)),'92a42ada1eb837c7102846ed69271ae83ebb68f913f16e64234f98ee253ed40b');
assert.equal(peer.inputSha256,sha(readFileSync(rawPath)));
assert.equal(peer.originalsSha256,sha(readFileSync(resolve(lattice,'source-records.jsonl'))));
assert.equal(peer.servedSha256,sha(readFileSync(resolve(lattice,'served-records.jsonl'))));
assert.equal(peer.reviewerCodeSha256,sha(readFileSync(resolve(root,'scripts/bank/quality/peer/lattice_display.py'))));
assert.equal(peer.author,'series_final_review');assert.equal(peer.reviewer,'root');
assert.equal(peer.instances,8);assert.equal(peer.literalEqualities,32);
const admissions=read(resolve(stage,'admission-previews.json'));
const priorBindings=byId(previous.records),priorGroups=byId(previousMap.records);
const binding=[],groups=[],normalizations=[],metadataCorrections=[];
let unchanged=0,latticeChanges=0,choiceEqualities=0;
for(const record of records){
 const old=oldById.get(record.problemId),shown=servedById.get(record.problemId),oldShown=presentBankProblem(old);
 const before=priorBindings.get(record.problemId),oldGroup=priorGroups.get(record.problemId);
 assert(before&&oldGroup);assert.equal(before.contentHash,old.contentHash);
 assert.equal(record.semanticHash,old.semanticHash);assert.equal(record.difficulty,old.difficulty);
 assert.equal(record.answerChoiceId,old.answerChoiceId);assert.equal(record.familyId,old.familyId);
 assert.equal(shown.statement,oldShown.statement);
 const join=joinById.get(record.problemId);
 let displayAmendment=null;
 if(join){
  latticeChanges++;
  assert.equal(record.familyId,'m3-series-olympiad-lattice-resolvent');
  const index=record.parameters.instance,authored=rawByIndex.get(index),checked=peerByIndex.get(index),proposed=proposals.get(record.problemId);
  assert(authored&&checked&&proposed);assert(checked.passed&&checked.equivalentConclusion&&checked.allEarlierStepsIdentical);
  assert.equal(checked.rawSha256,sha(canonical(authored)));assert.equal(join.rawSha256,checked.rawSha256);
  assert.equal(record.provenance.authoring.rawSha256,checked.rawSha256);
  assert.equal(checked.sourcePreview.problemId,old.problemId);assert.equal(checked.sourcePreview.sourceContentHash,old.contentHash);
  assert.equal(checked.sourcePreview.canonicalRawHash,sha(canonical(old)));
  assert.equal(authored.statement,shown.statement);assert.deepEqual(authored.choices,shown.choices);assert.deepEqual(authored.solutionSteps,shown.solutionSteps);
  assert.deepEqual(shown.solutionSteps.slice(0,-1),oldShown.solutionSteps.slice(0,-1));
  assert.equal(shown.solutionSteps.at(-1),shown.choices.find(c=>c.choiceId===shown.answerChoiceId).math);
  assert.deepEqual(proposed.choices,shown.choices);assert.deepEqual(proposed.solutionSteps,shown.solutionSteps);
  for(const equality of checked.literalChoiceEqualities){
   assert(equality.signedCompleteTermsIdentical);
   assert.equal(equality.before,oldShown.choices.find(c=>c.choiceId===equality.choiceId).math);
   assert.equal(equality.after,shown.choices.find(c=>c.choiceId===equality.choiceId).math);
   choiceEqualities++;
  }
  const entry=admissions[record.provenance.authoring.reviewId];assert(entry);
  assert.equal(entry.review.reportSha256,sha(readFileSync(peerPath)));
  for(const supplement of entry.supplementalReports){assert.equal(supplement.sha256,sha(readFileSync(resolve(root,supplement.path))));}
  metadataCorrections.push({reviewId:entry.reviewId,sourceAdmissionEntrySha256:sha(canonical(entry)),
   currentAuthor:entry.review.author,currentReviewer:entry.review.reviewer,
   requiredAuthor:peer.author,requiredReviewer:peer.reviewer,
   reason:'Use the bound display peer identity and preserve earlier complete-task proof in supplementalReports. Owner confirmed this metadata-only correction at final central admission; canonical task/choice/hash values remain unchanged.'});
  displayAmendment={priorActualProblemId:old.problemId,priorActualRevision:old.problemRevision,priorActualContentHash:old.contentHash,
   rawSha256:checked.rawSha256,ownerPeer:artifact(peerPath),choiceEqualities:4,equivalentFinalConclusion:true,earlierCurrentStepsUnchanged:true,
   pairInequalityInheritance:'The four literal equalities preserve all six prior pair-inequality certificates for this menu.',newIndependentIdeaCredit:0};
 }else{
  assert.equal(canonical(record),canonical(old));assert.equal(canonical(shown),canonical(oldShown));unchanged++;
 }
 if(canonical(record.choices)!==canonical(shown.choices))normalizations.push({problemId:record.problemId,problemRevision:record.problemRevision,contentHash:record.contentHash,before:record.choices,after:shown.choices});
 const menu={answerChoiceId:shown.answerChoiceId,choices:shown.choices.map(c=>({choiceId:c.choiceId,math:c.math}))};
 binding.push({...before,problemRevision:record.problemRevision,contentHash:record.contentHash,
  canonicalUnchanged:before.canonicalUnchanged&&!join,unchangedFromV6:!join,
  normalizedMenuSha256:sha(canonical(menu)),displayAmendment,
  currentPresentationMatchesCapture:!join,currentPresentationMatchesReviewedAmendment:!!join,
  statementChangedOnlyByCurrentPresenter:record.statement!==shown.statement,
  solutionChangedOnlyByCurrentPresenter:canonical(record.solutionSteps)!==canonical(shown.solutionSteps)});
 const entry=admissions[record.provenance.authoring.reviewId];
 groups.push({...oldGroup,problemRevision:record.problemRevision,contentHash:record.contentHash,
  priorActualContentHash:old.contentHash,centralDecision:join?entry.review.centralDecision:oldGroup.centralDecision,
  normalizedTaskKey:oldGroup.normalizedTaskKey,
  destinationDeclaredLineageAlias:join?entry.review.normalizedLineageKey:null,
  lineageAliasDisposition:join?'Preserve the established normalized task key and expose the alternate spelling as an alias; no extra task capacity or new idea is created.':null,
  newIndependentIdeaCreditFromOptionRepair:0});
}
assert.equal(unchanged,697);assert.equal(latticeChanges,8);assert.equal(choiceEqualities,32);
assert.equal(binding.filter(r=>r.difficultyChanged).length,13);
assert.equal(binding.filter(r=>r.canonicalUnchanged).length,535);
assert.equal(binding.filter(r=>r.optionPatch).length,162);
const servedInput=served.map(r=>JSON.stringify(Object.fromEntries(['problemId','familyId','choices','answerChoiceId','pedagogy'].map(k=>[k,r[k]])))).join('\n')+'\n';
writeFileSync(resolve(out,'served-option-input.jsonl'),servedInput);
writeFileSync(resolve(out,'served-records.jsonl'),served.map(r=>JSON.stringify(r)).join('\n')+'\n');
const audit={...auditOptions(served),artifactSha256:sha(servedInput)},rawAudit=auditOptions(records);
write('served-option-audit.json',audit);write('raw-option-audit.json',rawAudit);
const priorFamilies=new Map(previous.families.map(f=>[f.familyId,f]));
const families=Object.entries(audit.families).map(([familyId,current])=>{
 const prior=priorFamilies.get(familyId);assert(prior);
 assert.deepEqual(current.flags,previousAudit.families[familyId].flags);
 if(familyId!=='m3-series-olympiad-lattice-resolvent')assert.deepEqual(current,previousAudit.families[familyId]);
 const row={...prior,unresolved:false,flags:current.flags.map(flag=>{
  const old=prior.flags.find(f=>f.rule===flag.rule);assert(old);
  const measured=current.results.find(r=>r.rule===flag.rule);return {...old,...flag,training:measured.training,heldout:measured.heldout};
 })};
 if(familyId==='m3-series-olympiad-lattice-resolvent'){
  row.supplementalSurfaceDiagnostic={prior:prior.supplementalSurfaceDiagnostic,
   current:current.results.find(r=>r.rule==='opposite-pair-negative'),
   disposition:'resolved-by-independently-reviewed-all-eight-complete-term-order-normalization',
   sourceBinding:artifact(peerPath),actualDestinationIds:joins.map(r=>r.problemId),
   noMathematicalPairClaimChanged:true,newIndependentIdeaCredit:0};
  assert.equal(row.supplementalSurfaceDiagnostic.current.training.applicable,0);
  assert.equal(row.supplementalSurfaceDiagnostic.current.heldout.applicable,0);
  assert.equal(row.supplementalSurfaceDiagnostic.current.training.expectedTieBrokenAccuracy,.25);
  assert.equal(row.supplementalSurfaceDiagnostic.current.heldout.expectedTieBrokenAccuracy,.25);
 }
 return row;
});
const forms=Object.entries(audit.answerForms).map(([answerForm,current])=>{
 const prior=previous.answerForms.find(f=>f.answerForm===answerForm);assert(prior);
 assert.deepEqual(current.flags,previousAudit.answerForms[answerForm].flags);
 return {...prior,flags:current.flags.map(flag=>{const old=prior.flags.find(f=>f.rule===flag.rule),score=current.results.find(s=>s.rule===flag.rule);assert(old);return {...old,...flag,training:score.training,heldout:score.heldout};})};
});
const replicated=Object.entries(audit.families).flatMap(([familyId,f])=>f.results.filter(s=>!s.rule.startsWith('shuffled-position-')&&s.training.expectedTieBrokenAccuracy>=.625&&s.heldout.expectedTieBrokenAccuracy>=.625).map(s=>({familyId,...s})));
assert.equal(replicated.length,0);
const counts={};
for(const level of ['easy','medium','hard','olympiad']){
 const rs=groups.filter(r=>r.recommendedDifficulty===level),fs=new Map();
 for(const r of rs){if(!fs.has(r.canonicalConstruction))fs.set(r.canonicalConstruction,new Set());fs.get(r.canonicalConstruction).add(r.normalizedTaskKey);}
 const horizon=level==='olympiad'?10:5;
 counts[level]={rawItems:rs.length,normalizedMeaningfulItems:new Set(rs.map(r=>r.normalizedTaskKey)).size,
  constructionFamilies:fs.size,topicLocalGroups:new Set(rs.map(r=>r.topicLocalIdeaGroupId)).size,globalRelatedGroups:new Set(rs.map(r=>r.relatedIdeaGroupId)).size,
  requiredHorizonRounds:horizon,capacityUnderFamilyCap2:[...fs.values()].reduce((n,set)=>n+Math.min(set.size,2*horizon),0),
  normalizedItemsPerFamily:Object.fromEntries([...fs].map(([f,keys])=>[f,keys.size]))};
 assert.deepEqual(counts[level],previousMap.counts[level]);
}
const failures=[];let expressions=0;
for(const r of served){
 const check=(math,location)=>{expressions++;try{renderMath(math,true);}catch(e){failures.push({problemId:r.problemId,location,math,error:e.message});}};
 for(const [i,math]of[r.statement,...r.choices.map(c=>c.math),...r.solutionSteps].entries())check(math,i);
 for(const b of [...formatProblemStatement(r.statement),...r.solutionSteps.flatMap(formatSolutionStep)])if(b.kind==='math')check(b.value,'formatted');else for(const p of b.parts)if(p.kind==='math')check(p.value,'inline');
 for(const issue of solutionQualityIssues(r))failures.push({problemId:r.problemId,location:'solution-quality',error:issue});
}
write('served-render.json',{records:705,expressions,strict:true,failures});assert.equal(failures.length,0);
const sourcePaths=[...['canonical-previews.jsonl','retained-originals.jsonl','replacement-joins.json','admission-previews.json'].flatMap(f=>[resolve(stage,f),resolve(oldStage,f)]),
 ...['final-option-review.json','item-group-map.json','served-option-audit.json','preserved-failures/attempt1.json'].map(f=>resolve(oldDir,f)),
 ...['proposal.json','source-records.jsonl','served-records.jsonl','runtime.py'].map(f=>resolve(lattice,f)),
 rawPath,peerPath,resolve(root,'scripts/bank/quality/peer/lattice_display.py'),resolve(root,'scripts/bank/quality/series/mathematical/difficulty-changes.json'),
 resolve(root,'lib/server/solution-presentation.mjs'),resolve(root,'lib/math-notation.mjs'),resolve(root,'scripts/bank/quality/option-audit.mjs'),fileURLToPath(import.meta.url)];
const sources=sourcePaths.map(artifact);
write('item-group-map.json',{status:'final-v7-actual-id-source-bound-group-map',sourceArtifacts:sources,counts,records:groups,
 scope:'All prior normalized task keys, 13 demotions and 30 Olympiad groups/240 normalized tasks persist. The eight display changes preserve the same task; alternate destination lineage strings are aliases, never extra capacity.',admitted:false});
write('notation-normalizations.json',{records:normalizations.length,normalizations,sourceArtifacts:sources.filter(s=>s.path.includes('math-notation')||s.path.includes('solution-presentation'))});
const report={status:'complete-actual-v7-source-served-format-and-option-review',reviewer:'series_final_review',sourceArtifacts:sources,
 counts:{effectiveRecords:705,candidateRecords:571,retainedOriginalRecords:134,unchangedFullCanonicalFromV6:697,
  unchangedFullCanonicalFromFrozen705:535,priorIndependentOptionReplacementsRebound:162,independentlyCheckedDisplayAmendments:8,literalDisplayEqualities:32,
  mandatoryDifficultyChangesPreserved:13,servedNotationMenuChanges:normalizations.length,
  servedStatementChanges:binding.filter(r=>r.statementChangedOnlyByCurrentPresenter).length,servedSolutionChanges:binding.filter(r=>r.solutionChangedOnlyByCurrentPresenter).length,
  constructionFamilies:families.length,flaggedFamilies:families.filter(r=>r.flags.length).length,smallSampleOnlyFamilies:families.filter(r=>r.smallSample&&!r.flags.length).length,
  answerForms:forms.length,flaggedAnswerForms:forms.filter(r=>r.flags.length).length,numericPairCertificatesRebound:3906,scalarMenus:642,tupleMenus:9,categoricalMenus:54,
  unresolvedPairOrDomainCases:0,unresolvedPresentationDispositions:0,replicatedNonPositionSignals:0,strictRenderedExpressions:expressions},
 records:binding,families,answerForms:forms,replicatedNonPositionSignals:replicated,capacity:counts,admissionMetadataCorrections:metadataCorrections,
 servedOptionInput:artifact(resolve(out,'served-option-input.jsonl')),servedOptionAudit:artifact(resolve(out,'served-option-audit.json')),
 servedRender:artifact(resolve(out,'served-render.json')),normalizedGroupMap:artifact(resolve(out,'item-group-map.json')),
 rawVersusServedFlagComparison:Object.keys(audit.families).map(f=>({familyId:f,rawFlags:rawAudit.families[f].flags,servedFlags:audit.families[f].flags})),
 scope:'697 exact v6 canonical records are unchanged. Eight new private display candidates join the owner complete-term equality review and earlier complete-task mathematics. All 705 actual served menus are screened; every standard flag/form disposition is preserved and the extra lattice leading-sign finding is now resolved. The earlier 3,906 pair inequalities remain valid by exact menu identity or literal value equality. This is not 705 fresh mathematical derivations.',
 limitations:['Finite option screens do not establish the absence of every conceivable clue; the intrinsic zero/infinity support and previous measured divisibility/form residuals remain explicit.',
  'No new generic heuristic, selector horizon run, player calibration, human certification, import or deployment is claimed.',
  'Owner must make the eight explicit metadata-only reviewer-identity corrections in central admission and attach this final screen. No canonical task/choice/hash rewrite is requested.',
  'Complete programmatic expression/fragment rendering is not a fresh responsive browser layout review.'],
 humanReviewed:false,formalProof:false,admitted:false,imported:0,active:0};
write('final-option-review.json',report);
console.log(JSON.stringify({counts:report.counts,olympiad:counts.olympiad,report:artifact(resolve(out,'final-option-review.json')),groupMap:artifact(resolve(out,'item-group-map.json'))}));
