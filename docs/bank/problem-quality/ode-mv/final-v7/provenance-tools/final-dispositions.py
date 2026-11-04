from pathlib import Path
from collections import Counter
import copy,json,hashlib,re
P=Path(__file__).resolve().parent;OLD=P.parent/'final1531-v4';ROOT=P.parents[2]/'problem-quality'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
def compact(s):return re.sub(r'\s','',re.sub(r'\\(?:,|!|;|quad|qquad|left|right)','',s))
a=json.load(open(P/'served-option-audit.json'));rawAudit=json.load(open(P/'raw-option-audit.json'));before=json.load(open(OLD/'family-form-dispositions-v4.json'));prior={f['familyId']:f for f in before['families']};oldAudit=json.load(open(OLD/'served-option-audit.json'));gm=json.load(open(P/'group-map.json'));maps={r['problemId']:r for r in gm['records']};served=lines(P/'served-records.jsonl');residual={r['familyId']:r for r in json.load(open(OLD/'residual-length-review.json'))['families']};families=[]
for fid,v in a['families'].items():
 rows=[r for r in served if r['familyId']==fid];previous=prior[fid];nonpos=[q for q in v['flags']if not q['rule'].startswith('shuffled-position')]
 status=previous['status'];reason=previous['disposition']
 if fid.endswith('nonnormal-transient-maximum'):
  assert not v['flags'];status='independently-repaired-and-final-actual-id-screen-clear';reason='All10 final menus were independently derived and every literal pair distinguished. The final actual-ID raw and served screens have no flags. Seven potential Olympiad menus retain a genuine alternative at t=1 surviving the elementary norm bounds; indices2/5/8 remain Hard. The failed v4 length invariant and frozen-v1 bound shortcut are preserved. No advanced credit is reclaimed by merely removing a cue.'
 elif fid.endswith('density-centroid'):
  assert all(r['difficulty']=='easy'for r in rows);status='accepted-easy-with-explicit-options-visible-shortcut';reason='The increasing-density argument puts the centroid strictly between1/2 and1, uniquely selecting every displayed answer; independent direct integrals agree. All10 records are now Easy through source-bound immutable amendments. The longest-literal tie and finite third-rank signal remain measurable and explicitly recorded; they do not justify the former Medium label. No assertion of cue-free options is made.'
 elif fid.endswith('ground-state-variance'):
  assert not any(q['rule']=='length-max'for q in v['flags']);status='independently-repaired-length-cue-with-numeric-rank-residual';reason='Three wrong values now come from coefficient-as-spatial-variance confusion; three additional revisions correct the inaccurate2/a misconception description. All active menus have accurate descriptions. Root independently verified all6 amended full tasks, the variational square, Schwartz boundary terms, equality case, normalized Gaussian moment, all24literal routes and36pairs. All8 retain one prior normalized task group and a substantively supported Olympiad decision. The unique-longest cue is removed and no length rule is flagged. The original minimum rule remains correct4/8(train.25/heldout.75); its four literal counterexamples and finite residual are preserved.'
 elif not v['flags']:
  status='screen-clear-with-prior-source-bound-review';reason='No fixed diagnostic flags appear on this exact served family. This bounded evidence does not itself establish mathematical correctness or difficulty; those inherit the exact immutable prior review joins in group-map.json.'
 elif not nonpos:
  status='reviewed-deterministic-shuffle-only';reason='All flags are positions under one fixed audit permutation. Actual play independently shuffles all4choices, so that audit position is not a persistent serving feature. No non-position rule is flagged in this family. This explanation applies only to these position flags.'
 binding=[{'problemId':r['problemId'],'revision':r['problemRevision'],'sourceContentHash':r['contentHash'],'sourceCanonicalRawHash':maps[r['problemId']]['sourceCanonicalRawHash'],'servedRawHash':digest(r),'servedChoiceMenuHash':digest(r['choices']),'answerChoiceId':r['answerChoiceId'],'sourceIdentityPath':maps[r['problemId']]['sourceIdentityPath'],'historicalIdentityAliases':maps[r['problemId']]['historicalIdentityAliases']}for r in rows]
 flags=[]
 for f in v['flags']:
  q=copy.deepcopy(next(q for q in v['results']if q['rule']==f['rule']))
  if f['rule']in['length-min','length-max']:
   cases=[]
   for r in rows:
    lengths={c['choiceId']:len(compact(c['math']))for c in r['choices']};ext=(min if f['rule'].endswith('min')else max)(lengths.values());pick=[k for k,n in lengths.items()if n==ext]
    cases.append({'problemId':r['problemId'],'selectedChoiceIds':pick,'correctSelected':r['answerChoiceId']in pick,'choiceLengths':lengths})
   q['literalCases']=cases;q['correctContained']=sum(c['correctSelected']for c in cases);q['uniqueCorrect']=sum(c['correctSelected']and len(c['selectedChoiceIds'])==1 for c in cases)
  flags.append(q)
 f={'familyId':fid,'items':len(rows),'difficultyCounts':dict(Counter(r['difficulty']for r in rows)),'status':status,'disposition':reason,'sourceBindings':binding,'servedFlagReview':flags,'rawFlagsFinal':rawAudit['families'][fid]['flags'],'priorV4Flags':oldAudit['families'][fid]['flags'],'sourceBoundRoutes':sorted({maps[r['problemId']]['centralDecision']for r in rows}),'newIndependentIdeasFromAmendments':0}
 if fid in residual and not fid.endswith('ground-state-variance'):
  f['causalLengthAssessment']=copy.deepcopy(residual[fid]['causalDiagnostic']);f['causalLengthReason']=residual[fid]['finding'];f['causalLengthDisposition']=residual[fid]['proposal']
 families.append(f)
forms=[{'answerForm':name,'items':v['items'],'flags':v['flags'],'status':'screen-clear-only','scope':'Same fixed diagnostic on actual served choices; pooled results never clear individual family flags. Scalar classification and pair-equivalence inherit the separately bound literal finite reviews, including all97 formerly unsupported cases.','problemIds':[r['problemId']for r in served if r['pedagogy']['answerForm']==name]}for name,v in a['answerForms'].items()]
assert len(families)==151 and len(forms)==2 and all(not f['flags']for f in forms)
report={'status':'complete-final-v7-source-bound-dispositions-with-explicit-residuals','counts':{'records':1531,'families':151,'flaggedFamilies':sum(bool(f['servedFlagReview'])for f in families),'answerForms':2,'unresolvedMathematicsOrClassification':0},'sourceArtifacts':{str(p):sha(p)for p in[P/'served-option-audit.json',P/'raw-option-audit.json',P/'served-records.jsonl',P/'group-map.json',OLD/'family-form-dispositions-v4.json',OLD/'residual-length-review.json']},'families':families,'answerForms':forms,'limitations':['This is a final identity/served-presentation rebind and bounded diagnostic disposition, not a new independent solution of1531problems.','24family screens still flag. Fixed-shuffle flags and measurable non-position patterns receive individual dispositions; they are not silently deleted or all described as noise.','The three unchanged positive/sign-pair families have a .55 digit-length rate conditional on a .50two-positive baseline. The task-specific magnitude decisions remain necessary, and these are not credited as Olympiad ideas.','Density keeps its explicit unique qualitative shortcut at an honest Easy level. Remaining numeric-rank patterns with counterexamples are finite editorial residuals, not statistical guarantees.','No normalization, option repair, or difficulty amendment earns new independent-idea credit.'],'requiredActions':[]}
(P/'family-form-dispositions.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'families':len(families),'flagged':report['counts']['flaggedFamilies'],'statuses':dict(Counter(f['status']for f in families))}))
# Rebind all97 formerly unsupported scalar cases, including17 immutable option repairs.
specialPath=ROOT/'scripts/bank/quality/ode-special/disposition-joins.json';special=json.load(open(specialPath));reb=[]
for q in special['records']:
 candidates=[r for r in gm['records']if q['sourceProblemId']in r['historicalIdentityAliases']]
 assert len(candidates)==1,(q['sourceProblemId'],len(candidates));r=candidates[0];assert r['familyId']==q['familyId'];assert q['sourceMathPassed']and q['literalPairDistinctions']==6 and q['oppositeSumChecks']==6
 if q['replacementRawSha256']:assert r['rawSha256']==q['replacementRawSha256']
 else:assert r['sourceCanonicalRawHash']==q['sourceCanonicalRawHash']
 reb.append({'problemId':r['problemId'],'revision':r['revision'],'contentHash':r['contentHash'],'canonicalRawHash':r['sourceCanonicalRawHash'],'servedRawHash':r['servedRawHash'],'sourceProblemId':q['sourceProblemId'],'sourceCanonicalRawHash':q['sourceCanonicalRawHash'],'familyId':q['familyId'],'sourceReview':{k:q[k]for k in['inputFile','inputRecordIndex','reviewFile','reviewRecordIndex']},'finalMenuDisposition':q['finalMenuDisposition'],'replacementRawSha256':q['replacementRawSha256'],'pairDistinctions':6,'oppositeSumChecks':6,'passed':True})
(P/'scalar97-final-joins.json').write_text(json.dumps({'status':'complete97-final-actual-id-source-bound-scalar-dispositions','counts':{'records':97,'unchangedMenus':80,'repairedMenus':17,'unresolved':0},'sourceArtifact':str(specialPath),'sourceSha256':sha(specialPath),'records':reb,'scope':'Rebind prior literal mathematical scalar verification and17 independently reviewed repairs. This does not claim a fresh97-case solve.'},indent=2)+'\n');print(json.dumps({'scalar97':len(reb),'unresolved':0}))
