"""Reconcile exact published ODE/MV sources without back-transferring menu qualification."""
from pathlib import Path
from collections import Counter,defaultdict
import copy,hashlib,json
P=Path(__file__).resolve().parent
# This evidence folder is under docs/bank/problem-quality/ode-mv/.
ROOT=P.parents[4]
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
def values(r):return sorted((c['choiceId'],c['math'])for c in r['choices'])
source=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl';expected='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677';assert sha(source)==expected
sourceLines=source.read_text().splitlines();original=[json.loads(x)for x in sourceLines if json.loads(x)['topic']in['differential equations','multivariable']];assert len(original)==768;byid={r['problemId']:r for r in original}
(P/'original-published-rows.jsonl').write_text(''.join(x+'\n'for x in sourceLines if json.loads(x)['problemId']in byid))
gp=ROOT/'docs/bank/problem-quality/ode-mv/final-v7/group-map.json';finalMap=json.load(open(gp))['records'];aliases=defaultdict(list)
for m in finalMap:
 for pid in m['historicalIdentityAliases']:aliases[pid].append(m)
finalRows={r['problemId']:r for r in lines(gp.parent/'sources/canonical-previews.jsonl')+lines(gp.parent/'sources/retained-originals.jsonl')}
mp=ROOT/'docs/bank/problem-quality/existing-multivariable-peer.json';op=ROOT/'scripts/bank/quality/ode-mv/evidence/independent/oldODE72.json';np=ROOT/'scripts/bank/quality/ode-mv/sources/retained-normalization.json'
mv={r['problemId']:(i,r)for i,r in enumerate(json.load(open(mp))['results'])};ode={r['problemId']:(i,r)for i,r in enumerate(json.load(open(op))['records'])};normal={r['problemId']:(i,r)for i,r in enumerate(json.load(open(np))['records'])}
for table in[mv,ode,normal]:
 for pid,(_,r)in table.items():assert r['sourceContentHash']==byid[pid]['contentHash']
assert json.load(open(op))['sourceArtifactSha256']==expected==json.load(open(np))['sourceArtifactSha256']
sourceRefs={str(p.relative_to(ROOT)):sha(p)for p in[mp,op,np,gp]}
revisions={};revisionChecks=[]
for name in['difficulty-revisions.jsonl','late-difficulty-revisions.jsonl','lower-difficulty-revisions.jsonl']:
 p=ROOT/'scripts/bank/quality/ode-mv/frozen'/name;sourceRefs[str(p.relative_to(ROOT))]=sha(p)
 for i,r in enumerate(lines(p)):
  old=byid[r['problemId']];prev=r['admission']['previous'];assert prev['contentHash']==old['contentHash']and prev['semanticHash']==old['semanticHash']and not prev['meaningChanged']
  assert r['choices']==old['choices']and r['answerChoiceId']==old['answerChoiceId'];assert r['semanticHash']==old['semanticHash']
  check={'problemId':old['problemId'],'publishedContentHash':old['contentHash'],'publishedRawSha256':digest(old),'revisionFile':str(p.relative_to(ROOT)),'revisionFileSha256':sha(p),'recordIndex':i,'revisionRawSha256':digest(r),'literalChoicesIncludingDescriptionsIdentical':True,'answerChoiceIdIdentical':True,'statementLiteralIdentical':r['statement']==old['statement'],'semanticIdentityUnchanged':True,'reviewedDifficulty':r['difficulty'],'qualificationTransfer':'No positive Olympiad qualification transferred; these are source-bound lower-level author editorial dispositions with unchanged original menus.'}
  if not check['statementLiteralIdentical']:check['statementDifferenceScope']='Previously recorded notation/prose formatting correction; original content/semantic hash and exact choice menu bind the mathematical task. No altered menu qualification is reused.'
  revisions[old['problemId']]=(r,check);revisionChecks.append(check)
# The root density review directly binds eight original sources; two headroom entries are excluded.
dp=ROOT/'docs/bank/problem-quality/density-classification-peer-v1.json';sourceRefs[str(dp.relative_to(ROOT))]=sha(dp);density={}
for i,r in enumerate(json.load(open(dp))['records']):
 pid=r['sourcePreview']['problemId']
 if pid in byid:
  old=byid[pid];assert r['sourcePreview']['sourceContentHash']==old['contentHash']and r['sourcePreview']['canonicalRawHash']==digest(old);assert r['passed'];density[pid]=(i,r)
assert len(density)==8
# These are exact original-menu findings, not the later repaired qualification.
rp=ROOT/'docs/bank/problem-quality/ode-mv/final-v7/history/residual-length-review.json';sourceRefs[str(rp.relative_to(ROOT))]=sha(rp)
ground=next(r for r in json.load(open(rp))['families']if r['familyId'].endswith('ground-state-variance'));groundBlocked={}
for i,c in enumerate(ground['cases']):
 old=byid[c['problemId']];assert c['sourceContentHash']==old['contentHash']and c['positiveChoices']==old['choices']
 if c['correctStrictlyLongest']:groundBlocked[old['problemId']]={'path':str(rp.relative_to(ROOT)),'fileSha256':sha(rp),'familyId':old['familyId'],'caseIndex':i,'finding':'The correct original choice alone has the longest literal representation; this is the exact failed original menu later repaired. Do not transfer the repaired-menu qualification backwards.'}
assert len(groundBlocked)==3
records=[]
for old in original:
 pid=old['problemId'];assert len(aliases[pid])==1;fm=aliases[pid][0];fr=finalRows[fm['problemId']];sameSemantic=old['semanticHash']==fr['semanticHash'];ped=old['pedagogy'];refs=[];reviewed=None;route=None;reviewKind='no-original-menu-classification-evidence-bound';qualified=False;originalPeerQualified=None;qualificationReason='Published non-Olympiad label; no advanced qualification asserted.'if old['difficulty']!='olympiad'else'No exact original-menu advanced qualification established.'
 normalized=fm['normalizedTaskKey']if sameSemantic else'original-published-task:'+pid
 if pid in normal:
  i,n=normal[pid];assert n['sourceSemanticHash']==old['semanticHash'];refs.append({'path':str(np.relative_to(ROOT)),'fileSha256':sha(np),'recordIndex':i,'sourceContentHash':old['contentHash'],'purpose':'Original-source normalization only; not a difficulty or positive-qualification certificate.','originalNormalizedTaskKey':n['normalizedLineageKey']})
 if pid in mv:
  i,r=mv[pid];assert r['semanticHash']==old['semanticHash']and r['passed'];reviewed=r['difficultyRecommended'];route=r['easiestOptionsVisibleRoute'];qualified=r['qualifiedOlympiad'];originalPeerQualified=qualified;reviewKind='exact-published-content-independent-multivariable-peer';qualificationReason='Independent original-source peer explicitly reviewed this exact content hash and options-visible route.'
  refs.append({'path':str(mp.relative_to(ROOT)),'fileSha256':sha(mp),'recordIndex':i,'sourceContentHash':old['contentHash'],'purpose':'Independent mathematical and options-visible classification of this exact published record.'})
 if pid in ode:
  i,r=ode[pid];assert r['sourceSemanticHash']==old['semanticHash'];level=r['proposedDifficulty'];reviewed=level if level in['hard','olympiad']else None;route=r['shortestOptionsVisibleRoute'];qualified=level=='olympiad';originalPeerQualified=qualified if reviewed else None;reviewKind='exact-published-content-original-ODE-route-peer';qualificationReason='Original-source ODE editorial peer reviewed one full menu per family and applied the symbolic route to the finite coefficient domain; not a fresh all-instance mathematical solve.'
  refs.append({'path':str(op.relative_to(ROOT)),'fileSha256':sha(op),'recordIndex':i,'sourceContentHash':old['contentHash'],'purpose':r['reviewScope']})
 if pid in revisions:
  r,check=revisions[pid];reviewed=r['difficulty'];route=r.get('review',{}).get('easiestOptionsVisibleRoute')or r.get('estimates',{}).get('basis')or r['pedagogy']['difficultyRationale'];qualified=False;reviewKind='source-bound-unchanged-original-menu-editorial-demotion';qualificationReason='A lower-level editorial route is bound to the original content hash and identical literal menu. This does not claim a new independent blind difficulty certification.'
  refs.append({'path':check['revisionFile'],'fileSha256':check['revisionFileSha256'],'recordIndex':check['recordIndex'],'sourceContentHash':old['contentHash'],'revisionRawSha256':check['revisionRawSha256'],'purpose':'Source-bound unchanged-menu lower-level editorial disposition; no positive qualification transferred.'})
 if pid in density:
  i,r=density[pid];reviewed='easy';route=r['qualitativeProof'];qualified=False;reviewKind='exact-original-source-root-qualitative-classification';qualificationReason='The root review binds this original canonical raw hash and its unchanged actual menu; exactly one choice lies between1/2 and1.';refs.append({'path':str(dp.relative_to(ROOT)),'fileSha256':sha(dp),'recordIndex':i,'sourceContentHash':old['contentHash'],'sourceCanonicalRawHash':digest(old),'purpose':'Independent qualitative route and direct integral calculation for the unchanged original menu.'})
 known=[]
 if pid in groundBlocked:
  qualified=False;known.append(groundBlocked[pid]);qualificationReason='Earlier exact-source peer retained the nonroutine mathematical route, but this exact original menu has a later confirmed unique-length giveaway. Effective baseline qualification is withheld; the repaired menu’s qualification is not back-transferred.';reviewKind+='-with-original-menu-blocker'
 if old['difficulty']!='olympiad':assert not qualified
 descriptors={k:fm[k]for k in['canonicalConstruction','relatedIdeaGroupId','structuralSignature','primaryTechnique']}if sameSemantic else{'canonicalConstruction':ped['constructionId'],'relatedIdeaGroupId':ped['relatedIdeaGroupId'],'structuralSignature':ped['structuralSignature'],'primaryTechnique':ped['primaryTechnique']}
 records.append({'problemId':pid,'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'contentHash':old['contentHash'],'sourceRawSha256':digest(old),'semanticHash':old['semanticHash'],'familyId':old['familyId'],'topic':old['topic'],'publishedDifficulty':old['difficulty'],'publishedAnswerChoiceId':old['answerChoiceId'],'publishedLiteralChoicesHash':digest(old['choices']),**descriptors,'normalizedTaskKey':normalized,'publishedAuthoringRoute':ped['difficultyRationale'],'reviewedRoute':route,'centralDecision':route or ped['difficultyRationale'],'reviewedDifficulty':reviewed,'recommendedDifficulty':reviewed or old['difficulty'],'recommendedDifficultyBasis':'bound-original-menu-review'if reviewed else'published-label-only-not-new-review','qualifiedOlympiad':qualified,'originalPeerQualifiedOlympiad':originalPeerQualified,'qualificationReason':qualificationReason,'reviewEvidenceKind':reviewKind,'evidence':refs,'knownOriginalMenuFindings':known,'finalLineage':{'problemId':fr['problemId'],'revision':fr['problemRevision'],'contentHash':fr['contentHash'],'semanticHash':fr['semanticHash'],'sameSemanticTask':sameSemantic,'literalChoicesIncludingDescriptionsIdentical':old['choices']==fr['choices'],'literalChoiceValuesAndIdsIdentical':values(old)==values(fr),'answerChoiceIdIdentical':old['answerChoiceId']==fr['answerChoiceId'],'normalizedTaskKeyReusedOnlyForSameSemanticTask':sameSemantic,'qualificationInheritedFromFinalMenu':False},'newIndependentIdeaCredit':0})
summary={}
for topic in['differential equations','multivariable']:
 rs=[r for r in records if r['topic']==topic];q=[r for r in rs if r['qualifiedOlympiad']];summary[topic]={'publishedRecords':len(rs),'publishedDifficultyCounts':dict(Counter(r['publishedDifficulty']for r in rs)),'reviewedDifficultyCounts':dict(Counter(r['reviewedDifficulty']or'not-established'for r in rs)),'exactOriginalPeerQualifiedBeforeKnownMenuBlocker':sum(r['originalPeerQualifiedOlympiad']is True for r in rs),'effectiveQualifiedOlympiadRecords':len(q),'qualifiedNormalizedItems':len({r['normalizedTaskKey']for r in q}),'qualifiedConstructionGroups':len({r['canonicalConstruction']for r in q}),'qualifiedRelatedIdeaGroups':len({r['relatedIdeaGroupId']for r in q}),'sameSemanticFinalLineages':sum(r['finalLineage']['sameSemanticTask']for r in rs),'originalMenuBlockers':sum(bool(r['knownOriginalMenuFindings'])for r in rs)}
report={'status':'complete-source-bound-original-published-descriptors','sourceArtifact':str(source),'sourceArtifactSha256':expected,'originalPublishedSubsetSha256':sha(P/'original-published-rows.jsonl'),'records':records,'summary':summary,'sourceReferences':sourceRefs,'scope':'768exact ORIGINAL published ODE/MV records. Published difficulty is preserved separately from review classification. Positive qualification comes only from exact original-source peer evidence, with later confirmed original-menu blockers applied. Final-v7 descriptors/normalized keys are reused only across demonstrably identical semantic tasks; no revised-menu qualification is back-transferred. This is not a fresh768-record mathematical solve or a count of the full four-topic final pool.','limitations':['32lower-level original records have changed semantic identities in the candidate; final task/classification is not transferred to those originals.','Original ODE route review is finite-family editorial review, not all-instance independent solving.','Conservative difficulty-only revisions are author editorial dispositions bound to exact original menus; they are not mislabeled independent blind fit reviews.','Three original ground-state menus retain the old mathematical Olympiad decision in reviewedDifficulty but are effectively unqualified because their exact original unique-length cue was later confirmed. The amended menu qualification is not used backwards.','The old MV peer explicitly covers the exact published72 content hashes, despite its different aggregate input-artifact hash. The per-record hash joins are all exact.']}
(P/'descriptor-map.json').write_text(json.dumps(report,indent=2)+'\n');(P/'unchanged-menu-revision-bindings.json').write_text(json.dumps({'records':revisionChecks,'count':len(revisionChecks),'scope':'Exact original content-hash and full literal-menu equality, separate from changed explanation/difficulty metadata.'},indent=2)+'\n');print(json.dumps(summary))
