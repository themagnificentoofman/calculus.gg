#!/usr/bin/env node
// Bounded baseline evidence reconciliation only. No admission or application writes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {presentBankProblem as pinned} from '../../../../.bank-data/quality/baseline-source/lib/server/solution-presentation.mjs';
import {normalizeNotation as pinnedNotation} from '../../../../.bank-data/quality/baseline-source/lib/math-notation.mjs';
import {presentBankProblem as current} from '../../../../lib/server/solution-presentation.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../../..');
process.chdir(root);
const out=process.argv[2]||'docs/bank/problem-quality/series/original-baseline-reconciliation-v1';
if(fs.existsSync(out))throw Error('Use a NEW output directory; preserve earlier evidence.');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const stable=x=>JSON.stringify(sort(x));
function sort(x){return Array.isArray(x)?x.map(sort):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().filter(k=>x[k]!==undefined).map(k=>[k,sort(x[k])])):x;}
const objsha=x=>sha(stable(x));
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const lines=p=>fs.readFileSync(p,'utf8').trim().split('\n');
const jl=p=>lines(p).map(JSON.parse);
const eq=(a,b)=>stable(a)===stable(b);
const indexed=rows=>new Map(rows.map(r=>[r.problemId,r]));
const must=(ok,msg)=>{if(!ok)throw Error(msg);};
const menu=r=>r.choices.map(c=>c.math).sort();
const answer=r=>r.choices.find(c=>c.choiceId===r.answerChoiceId).math;
const task=r=>({statement:r.statement,menu:menu(r),answer:answer(r),assumptions:r.assumptions,solutionSteps:r.solutionSteps});
const compare=(a,b)=>({statement:a.statement===b.statement,unorderedMenu:eq(menu(a),menu(b)),markedAnswer:answer(a)===answer(b),solutionSteps:eq(a.solutionSteps,b.solutionSteps),assumptions:eq(a.assumptions,b.assumptions),orderedMenu:eq(a.choices.map(c=>c.math),b.choices.map(c=>c.math))});
const visibleSame=c=>c.statement&&c.unorderedMenu&&c.markedAnswer&&c.solutionSteps;
const counts=(rows,fn)=>Object.fromEntries([...rows.reduce((m,r)=>{const k=fn(r);m.set(k,(m.get(k)||0)+1);return m;},new Map())].sort(([a],[b])=>String(a).localeCompare(String(b))));
const src={
 published:'../milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl',
 baselineOptions:'.bank-data/quality/baseline-options.jsonl',
 baselineOptionSummary:'docs/bank/problem-quality/baseline-option-summary.json',
 frozen:'scripts/bank/quality/series/bundles/existing/frozen-olympiad-review-input.json',
 preview:'../quality-research/series-sources/existing-frozen/revision-candidates.jsonl',
 peer:'docs/bank/problem-quality/series/existing-series-peer-review.json',
 candidates:'.bank-data/quality/series-previews-v7/canonical-previews.jsonl',
 retained:'.bank-data/quality/series-previews-v7/retained-originals.jsonl',
 map:'docs/bank/problem-quality/series/final-v7/item-group-map.json',
 finalReview:'docs/bank/problem-quality/series/final-v7/final-option-review.json',
 served:'docs/bank/problem-quality/series/final-v7/served-records.jsonl',
 pinnedDigests:'docs/bank/problem-quality/baseline-source-digests.json',
 script:'scripts/bank/quality/peer/series_baseline_rebind.mjs',
 preservedFailure:'docs/bank/problem-quality/series/original-baseline-reconciliation-failures/baseline-option-canonical-menu-assumption.json',
 preservedSerializationFailure:'docs/bank/problem-quality/series/original-baseline-reconciliation-failures/python-json-number-serialization.json'
};
const expectedPublished='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677';
must(sha(fs.readFileSync(src.published))===expectedPublished,'Published release bytes changed');
const publishedLines=lines(src.published),all=publishedLines.map(JSON.parse),published=all.filter(r=>r.topic==='series');
// Earlier Python reviewers retain integral floats as 1.0. Use their exact JSON
// serialization instead of silently changing their raw-hash convention in JS.
const pythonHashes=JSON.parse(execFileSync('python3',['-c',
 'import json,hashlib,sys; print(json.dumps({p:{r["problemId"]:hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() for r in map(json.loads,open(p))} for p in sys.argv[1:]}))',src.published,src.preview],{encoding:'utf8',maxBuffer:4*1024*1024}));
must(all.length===2504&&published.length===384,'Unexpected published scope');
const publishedLineById=new Map(all.map((r,i)=>[r.problemId,publishedLines[i]]));
const originals=indexed(published),baseline=indexed(jl(src.baselineOptions)),frozen=read(src.frozen),frozenById=new Map(frozen.map(r=>[r.original.problemId,r]));
const peer=read(src.peer),previewRows=jl(src.preview),preview=indexed(previewRows);
must(sha(fs.readFileSync(src.preview))===peer.sourceArtifactSha256,'Peer source artifact mismatch');
const peerById=new Map(peer.families.flatMap(f=>f.coverage.map(c=>[c.problemId,{family:f,coverage:c}])));
must(peerById.size===72&&frozen.length===128,'Unexpected old evidence scope');
const finalRows=[...jl(src.candidates),...jl(src.retained)],final=indexed(finalRows),mapping=indexed(read(src.map).records),reviews=indexed(read(src.finalReview).records),served=indexed(jl(src.served));
must(finalRows.length===705&&final.size===705,'Final source scope changed');
const baselineAudit=read(src.baselineOptionSummary),pinnedDigests=read(src.pinnedDigests);
must(baselineAudit.artifactSha256===sha(fs.readFileSync(src.baselineOptions)),'Baseline option audit input changed');
const presenterFiles=['lib/server/solution-presentation.mjs','lib/server/solution-reviews/finite.json','lib/server/solution-reviews/legacy.mjs','lib/server/solution-reviews/legacy-hashes.json','lib/math-notation.mjs'];
for(const rel of presenterFiles){const p='.bank-data/quality/baseline-source/'+rel;must(sha(fs.readFileSync(p))===pinnedDigests.files[rel],`Pinned source changed: ${rel}`);src['pinned:'+rel]=p;src['current:'+rel]=rel;}
src['current:quality.json']='lib/server/solution-reviews/quality.json';
const artifacts=Object.entries(src).map(([role,p])=>({role,path:p,sha256:sha(fs.readFileSync(p))}));
const sourceHashes=new Map(artifacts.map(a=>[a.path,a.sha256]));
const thetaFamily='m3-series-olympiad-theta-dual-moment';
const thetaIds=['cn_297032565022a61e3071','cn_5895dd68aa8998ee472e'];
const fourierId='cn_e4b050067795dade3e09';
const assumptionProofs={
 'gaussian-domain-implication':{
  appliesTo:thetaIds,
  originalAssumptions:['All series and their parameter derivatives converge uniformly on every compact interval inside a>0.','Theta(a)>=1, so the displayed denominator is nonzero.'],
  finalAssumptions:['Real variables on the explicitly stated domain; all restrictions in the statement apply.'],
  proof:['The identical displayed definitions have real a>0 and sums over every integer n. For any compact interval [epsilon,R] with epsilon>0, an r-th parameter derivative of exp(-pi*a*n^2) has absolute value at most pi^r*|n|^(2r)*exp(-pi*epsilon*n^2). The analogous bound for M has the additional polynomial factor n^2.','For fixed r, these majorants are summable: a fixed polynomial is bounded by a constant times exp(pi*epsilon*n^2/2), leaving a convergent Gaussian tail. The Weierstrass M-test proves the stated local uniform convergence and the derivative interchange already used in the identical worked solution.','Every theta summand is nonnegative and the n=0 summand equals 1, hence Theta(a)>=1. These assumptions add no restriction beyond the same displayed positive-real domain and do not supply the Poisson duality identity.'],
  effect:'Task/domain/solution meaning preserved. This does not transfer the repaired family menu distribution.'
 },
 'fourier-envelope-implication':{
  appliesTo:[fourierId],originalAssumptions:['Absolute convergence follows from the k^-2 envelope.'],finalAssumptions:['Real variables on the explicitly stated domain; all restrictions in the statement apply.'],
  proof:['For every positive integer k, 0<=sin(pi*k/6)^4/k^2<=1/k^2. The convergent reciprocal-square series proves the original assumption directly from the unchanged statement.'],effect:'Task/domain/solution meaning preserved; the exact finite task can use the later Hard-level reference.'
 }
};
const records=[],pinnedRows=[],presenterDifferences=[],peerJoins=[];
for(const p of published){
 const id=p.problemId,f=final.get(id),m=mapping.get(id),rev=reviews.get(id),s=pinned(p),n=current(p),t=current(f),captured=served.get(id),b=baseline.get(id);
 must(f&&m&&rev&&captured,`Missing same-ID reference ${id}`);
 must(b.contentHash===p.contentHash&&b.problemRevision===p.problemRevision&&eq(b.choices,s.choices)&&b.answerChoiceId===p.answerChoiceId,`Baseline pinned option source mismatch ${id}`);
 must(f.semanticHash===p.semanticHash&&m.semanticHash===p.semanticHash,`Changed semantic identity ${id}`);
 must(m.contentHash===f.contentHash&&rev.contentHash===f.contentHash&&captured.contentHash===f.contentHash,`Final source join mismatch ${id}`);
 must(eq(task(t),task(captured)),`Current task no longer matches captured final v7 ${id}`);
 pinnedRows.push(s);
 const comp=compare(s,t),presenterComp=compare(s,n),fullDisplaySame=visibleSame(comp);
 const proofId=thetaIds.includes(id)?'gaussian-domain-implication':id===fourierId?'fourier-envelope-implication':null;
 if(proofId){must(fullDisplaySame,`Special visible task changed ${id}`);must(eq(s.assumptions,assumptionProofs[proofId].originalAssumptions)&&eq(t.assumptions,assumptionProofs[proofId].finalAssumptions),`Special assumptions changed ${id}`);}
 const taskReviewBound=fullDisplaySame&&(comp.assumptions||!!proofId);
 const solution=frozenById.get(id);
 let frozenBinding=null;
 if(solution){
  const o=solution.original,r=solution.review;
  const exactFields=Object.keys(o).filter(k=>!['provenance','validation'].includes(k));
  must(exactFields.every(k=>eq(o[k],p[k]))&&r.originalContentHash===p.contentHash,`Frozen projection mismatch ${id}`);
  must(r.originalRecordSha256===pythonHashes[src.published][id],`Frozen review does not bind full published record ${id}`);
  frozenBinding={reviewEvidenceId:r.reviewEvidenceId,originalContentHash:r.originalContentHash,originalRecordSha256:r.originalRecordSha256,fullPublishedStableJsonSha256:pythonHashes[src.published][id],serialization:'Python sorted compact JSON, ensure_ascii=False, preserving integral floats',fullPublishedHashMatches:true,projectionExactFields:exactFields,projectionMetadataDifferences:['provenance','validation'],projectionSha256:objsha(o),reviewRowSha256:objsha(r),normalizedReviewStepsMatchPinned:eq(r.solutionSteps.map(x=>pinnedNotation(x)),s.solutionSteps),scope:'Source-bound solution evidence; not an options-visible difficulty or family-menu certificate.'};
 }
 let priorPeer=null;
 const pc=peerById.get(id);
 if(pc){
  const pr=preview.get(id),c=pc.coverage;
  must(pr.contentHash===c.contentHash&&pr.semanticHash===c.semanticHash&&pythonHashes[src.preview][id]===c.rawHash,`Peer preview join failed ${id}`);
  must(c.contentHash!==p.contentHash&&pr.semanticHash===p.semanticHash,`Unexpected old peer binding ${id}`);
  priorPeer={publishedContentHash:p.contentHash,reviewedPreviewContentHash:c.contentHash,reviewedPreviewRawSha256:c.rawHash,reviewedPreviewSemanticHash:c.semanticHash,publishedSemanticHash:p.semanticHash,sameSemanticHash:true,literalRawComparison:compare(p,pr),peerRecommendedDifficulty:pc.family.recommendedDifficulty,peerQualifiedOlympiad:pc.family.qualifiedOlympiad,sourceArtifactSha256:peer.sourceArtifactSha256,coverageRowSha256:objsha(c),disposition:'Coverage binds the unpublished revision preview. No whole-family options/difficulty transfer to published original.'};
  peerJoins.push({problemId:id,familyId:p.familyId,...priorPeer});
 }
 if(!eq(task(s),task(n)))presenterDifferences.push({problemId:id,publishedContentHash:p.contentHash,comparison:presenterComp,pinnedTask:task(s),currentTask:task(n),disposition:'Recorded difference only; no general semantic equivalence or repaired statement inherited.'});
 const taskLevelQualified=taskReviewBound&&m.qualifiedOlympiad;
 must(!taskLevelQualified||thetaIds.includes(id),'Unreviewed positive task-level qualification');
 records.push({
  problemId:id,problemRevision:p.problemRevision,contentHash:p.contentHash,semanticHash:p.semanticHash,familyId:p.familyId,topic:'series',publishedRecordSha256:pythonHashes[src.published][id],publishedRecordSerialization:'Python sorted compact JSON, ensure_ascii=False',publishedLineSha256:sha(publishedLineById.get(id)),publishedDifficulty:p.difficulty,
  canonicalConstruction:m.canonicalConstruction,constructionFamilyId:m.constructionFamilyId||m.canonicalConstruction,relatedIdeaGroupId:m.relatedIdeaGroupId,topicLocalIdeaGroupId:m.topicLocalIdeaGroupId,structuralSignature:m.structuralSignature,normalizedTaskKey:m.normalizedTaskKey,normalizationReason:m.normalizationReason,
  primaryTechnique:taskReviewBound?m.primaryTechnique:p.pedagogy.primaryTechnique,centralDecision:taskReviewBound?m.centralDecision:p.pedagogy.difficultyRationale,
  groupBinding:{sourceMap:src.map,sourceMapSha256:sourceHashes.get(src.map),sourceMapRowSha256:objsha(m),sameIdAndSemanticHash:true,scope:'Grouping/lineage of the same mathematical task; no new task or construction credit. Semantic hash alone does not bind changed choices or difficulty.'},
  recommendedDifficulty:taskReviewBound?m.recommendedDifficulty:p.difficulty,
  difficultyReviewStatus:taskReviewBound?'exact-pinned-task-rebound-to-reviewed-level; family-context-not-transferred':'published-label-fallback; exact-baseline-options-visible-level-not-demonstrated',
  taskLevelReviewBound:taskReviewBound,taskLevelQualifiedOlympiad:taskLevelQualified,qualifiedOlympiad:false,
  qualificationStatus:taskLevelQualified?'unsupported-full-baseline-qualification: original-theta-family-always-middle-menu-pattern':p.difficulty==='olympiad'?(taskReviewBound?'exact-task-reclassified-below-olympiad':'unsupported: old-peer-preview-or-final-task-menu-not-bound'):'not-a-positive-Olympiad-candidate',
  pinnedTaskSha256:objsha(task(s)),pinnedSolutionQuality:s.solutionQuality||null,pinnedVersusCurrentOriginal:presenterComp,
  finalTaskReference:{problemId:id,problemRevision:f.problemRevision,contentHash:f.contentHash,semanticHash:f.semanticHash,taskSha256:objsha(task(t)),reviewRowSha256:objsha(rev),recommendedDifficulty:m.recommendedDifficulty,qualifiedOlympiad:m.qualifiedOlympiad,primaryTechnique:m.primaryTechnique,centralDecision:m.centralDecision,comparison:comp,assumptionImplicationProof:proofId,scope:taskReviewBound?'Exact finite visible task and worked steps, with identical or explicitly implied assumptions. Final family-level option distributions are not inherited.':'Grouping reference only; task-level review does not bind the baseline display/menu.'},
  frozenSolutionReview:frozenBinding,originalPeerPreviewBinding:priorPeer,newIndependentIdeaCredit:0,admitted:false
 });
}
must(records.length===384&&records.every(r=>r.qualifiedOlympiad===false),'Baseline qualification scope changed');
must(records.filter(r=>r.taskLevelReviewBound).length===125,'Unexpected exact pinned task count');
must(records.filter(r=>r.taskLevelQualifiedOlympiad).length===2,'Unexpected task-level theta scope');
const thetaRankCases=pinnedRows.filter(r=>r.familyId===thetaFamily).map(p=>{
 const rows=p.choices.map(c=>{const match=/^\\frac\{1\}\{(\d+)\s*\\pi\}$/.exec(c.math);must(match,'Unsupported theta choice; do not approximate');return {choiceId:c.choiceId,math:c.math,positiveDenominator:BigInt(match[1])};});
 must(rows.every(r=>r.positiveDenominator>0n)&&new Set(rows.map(r=>String(r.positiveDenominator))).size===4,'Invalid theta denominator');
 const ordered=[...rows].sort((a,b)=>a.positiveDenominator>b.positiveDenominator?-1:1),rank=ordered.findIndex(c=>c.choiceId===p.answerChoiceId)+1;
 return {problemId:p.problemId,contentHash:p.contentHash,instanceIndex:p.parameters.instance,correctRank:rank,exactAscendingOrder:ordered.map(c=>({...c,positiveDenominator:String(c.positiveDenominator)})),certificate:'All values are 1/(d*pi) with distinct positive integers d. Because pi>0, descending integer denominators give exact ascending values; no numerical approximation.',middleTwoContainsCorrect:rank===2||rank===3};
});
must(thetaRankCases.length===8&&thetaRankCases.every(r=>r.middleTwoContainsCorrect),'Theta baseline pattern changed');
const thetaDiagnostic={familyId:thetaFamily,scope:'Bounded exact comparison of the eight actual published theta menus, prompted by proposed review transfer; no new global predictor search.',cases:thetaRankCases,correctRankCounts:counts(thetaRankCases,r=>r.correctRank),allCorrectAnswersAmongMiddleTwo:true,middleTwoUniformTieBrokenAccuracy:0.5,chance:0.25,oldGenericAudit:baselineAudit.families[thetaFamily],oldGenericAuditLimitation:'The generic numeric parser accepts integers, decimals and rational constants, not these pi-denominator expressions. Its no-flag result does not establish a balanced exact rank distribution. The middle-two relation is recorded separately; thresholds are not changed.',finalFamilyDistributionNotTransferred:true,qualificationDisposition:'The two literal task matches retain mathematical/level evidence only. No fully qualified original baseline Olympiad credit is demonstrated in this report.'};
const familyRows=[...new Set(published.map(r=>r.familyId))].sort().map(familyId=>{
 const rs=records.filter(r=>r.familyId===familyId),audit=baselineAudit.families[familyId];
 return {familyId,records:rs.length,publishedDifficulties:counts(rs,r=>r.publishedDifficulty),recommendedDifficultiesWithFallback:counts(rs,r=>r.recommendedDifficulty),exactPinnedTaskReviewBindings:rs.filter(r=>r.taskLevelReviewBound).length,allFamilyVisibleTasksMatchFinal:rs.every(r=>r.taskLevelReviewBound),frozenPublishedSolutionBindings:rs.filter(r=>r.frozenSolutionReview).length,oldPreviewPeerBindings:rs.filter(r=>r.originalPeerPreviewBinding).length,qualifiedOlympiad:0,baselineGenericAudit:audit||null,baselineGenericAuditScope:'Actual published choices after the pinned baseline presenter, original audit parser and finite split. No-flag does not prove absence of all cues.',baselineFamilyReviewInherited:false};
});
const peerFamilies=peer.families.map(f=>{const rows=peerJoins.filter(r=>r.familyId===f.familyId);return {familyId:f.familyId,rows:rows.length,allCoverageHashesBindPreview:true,publishedContentHashMatches:0,sameSemanticHashes:rows.length,rawStatementMatches:rows.filter(r=>r.literalRawComparison.statement).length,rawUnorderedMenuMatches:rows.filter(r=>r.literalRawComparison.unorderedMenu).length,rawCorrectMathMatches:rows.filter(r=>r.literalRawComparison.markedAnswer).length,peerQualifiedOlympiad:f.qualifiedOlympiad,peerRecommendedDifficulty:f.recommendedDifficulty,disposition:'Preserve peer as preview review; do not relabel its hashes as published original review.'};});
fs.mkdirSync(out,{recursive:true});
const write=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n');
const writejl=(name,rows)=>fs.writeFileSync(path.join(out,name),rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
fs.writeFileSync(path.join(out,'published-series.jsonl'),published.map(r=>publishedLineById.get(r.problemId)).join('\n')+'\n');
writejl('pinned-served-series.jsonl',pinnedRows);
writejl('normalized-record-map.jsonl',records);
write('peer-preview-joins.json',{sourceArtifact:artifacts.find(r=>r.role==='preview'),families:peerFamilies,records:peerJoins});
write('assumption-implication-evidence.json',assumptionProofs);
write('theta-baseline-family-rank.json',thetaDiagnostic);
write('pinned-versus-current-original.json',{records:presenterDifferences.length,scope:'Exact difference inventory; current code is not used to simulate the baseline.',differences:presenterDifferences});
const report={
 status:'complete-source-bound-baseline-evidence-reconciliation',reviewer:'series_final_review',purpose:'Baseline metrics only; not admission, publication, new authorship or a fresh solution review of all 384 problems.',baselinePresenter:{pinnedCommit:pinnedDigests.commit,codeRoot:'.bank-data/quality/baseline-source',currentCodeUsedOnlyAsFinalReference:true},sourceArtifacts:artifacts,
 counts:{publishedReleaseRecords:2504,publishedSeriesRecords:384,publishedFamilies:48,publishedDifficulties:counts(records,r=>r.publishedDifficulty),sameIdAndSemanticGroupJoins:384,exactPublishedOptionSourceJoins:384,unchangedFinalCanonicalContentHashes:records.filter(r=>r.contentHash===r.finalTaskReference.contentHash).length,frozenSolutionBindingsToFullPublishedRecord:128,oldPeerRows:72,oldPeerRowsWhoseCoverageHashMatchesPublished:0,oldPeerRowsWhoseCoverageHashMatchesPreview:72,oldPeerRawMenuMatchesPublished:peerJoins.filter(r=>r.literalRawComparison.unorderedMenu).length,pinnedStatementMatchesFinal:records.filter(r=>r.finalTaskReference.comparison.statement).length,pinnedMenuMatchesFinal:records.filter(r=>r.finalTaskReference.comparison.unorderedMenu).length,pinnedCorrectMathMatchesFinal:records.filter(r=>r.finalTaskReference.comparison.markedAnswer).length,pinnedWorkedStepsMatchFinal:records.filter(r=>r.finalTaskReference.comparison.solutionSteps).length,exactPinnedTaskWithEqualAssumptions:records.filter(r=>r.taskLevelReviewBound&&r.finalTaskReference.comparison.assumptions).length,exactPinnedTaskWithProvedImpliedAssumptions:records.filter(r=>r.taskLevelReviewBound&&r.finalTaskReference.assumptionImplicationProof).length,taskLevelReviewBindings:125,publishedLabelFallbacks:259,taskLevelOnlyOlympiad:2,fullyQualifiedBaselineOlympiad:0,fullyQualifiedBaselineOlympiadGroups:0,fullyQualifiedBaselineOlympiadNormalizedTasks:0,currentPresenterDiffersFromPinnedOriginal:presenterDifferences.length,recommendedDifficultiesIncludingExplicitFallbacks:counts(records,r=>r.recommendedDifficulty)},
 conclusion:'The 72-row peer coverage is authentic but binds a 128-record unpublished revision preview, including 71 changed menus. The frozen solution review separately binds 128 full published records exactly. Every original series row has a truthful published-hash group/task map. Only 125 exact pinned visible tasks can reuse later task-level review, including two theta tasks; original theta family menu context prevents transferring full qualification. Zero fully qualified original baseline series Olympiad records are currently demonstrated by this evidence.',
 limitations:['No fresh blind solving of all 384 problems; no human or player-calibration claim.','Same semantic hashes justify the same-mathematics lineage join, not menu, easiest-level or admission transfer.','Unsupported qualification means insufficient exact evidence in this report, not a proof that the mathematical problem cannot be Olympiad-level.','Recommended difficulty on 259 unmatched displays is explicitly the published-label fallback, not a new quality finding.','Choice order and choice IDs may differ where the literal math menu is the same; production shuffling makes author order irrelevant to this task equivalence, while immutable historical choice IDs remain unchanged.','The exact theta rank diagnostic is bounded to eight published cases. No general classifier or thresholds were changed.'],families:familyRows,humanReviewed:false,admitted:false,imported:false,active:false
};
report.outputs=fs.readdirSync(out).map(name=>({path:path.join(out,name),sha256:sha(fs.readFileSync(path.join(out,name)))}));
write('reconciliation-report.json',report);
fs.writeFileSync(path.join(out,'README.md'),`# Original series baseline evidence reconciliation\n\nThis directory binds all 384 published M3 series rows to the pinned baseline presenter at commit ${pinnedDigests.commit}. It changes no published records, application behavior, admission, or selector.\n\nThe 72-row prior peer report binds an unpublished revision preview; 71 of its menus differ from the published originals. The frozen solution review independently binds 128 **full published canonical record hashes**, despite its reduced metadata projection. The two reviews must not be conflated.\n\nAll 384 rows receive same-ID/same-semantic group and normalized-task joins. For difficulty, 122 have the identical pinned statement, menu, answer, worked steps and assumptions as the later reviewed record; three more have the same visible task and worked steps plus explicitly proved, meaning-neutral assumptions. The remaining 259 retain a clearly marked unreviewed published-label fallback. This is not a fresh solve of all 384.\n\nTwo theta cases have exact task-level Olympiad evidence, but **zero fully qualified original baseline series Olympiad records are demonstrated**: all eight original theta menus place the correct answer among the middle two values. The later balanced family audit cannot be inherited. The old generic no-flag result, its parser limitation, the exact eight-case rank evidence, and the source joins are all preserved.\n\nUse normalized-record-map.jsonl for baseline joins and qualifiedOlympiad for conservative credit. taskLevelQualifiedOlympiad is deliberately separate and is not full qualification. See reconciliation-report.json for counts, bindings and limits. Reproduce with node scripts/bank/quality/peer/series_baseline_rebind.mjs NEW_OUTPUT_DIRECTORY; existing evidence directories are never overwritten.\n`);
console.log(JSON.stringify({output:out,reportSha256:sha(fs.readFileSync(path.join(out,'reconciliation-report.json'))),mapSha256:sha(fs.readFileSync(path.join(out,'normalized-record-map.jsonl'))),counts:report.counts}));
