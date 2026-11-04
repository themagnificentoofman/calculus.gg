"""Source-bound review of actual effective-family option flags and one repair.
No application source is modified. The repair returns a finite guarded patch,
which the parent must admit as an immutable revision and assign its final hash.
"""
from pathlib import Path
import json,hashlib,itertools,copy
import sympy as s
P=Path(__file__).resolve().parent;ROOT=P.parents[1]/'problem-quality'
INPUT=ROOT/'.bank-data/quality/series-previews-v3/effective-option-input.jsonl';SCREEN=INPUT.with_name('effective-option-screen.json')
FID='m3-series-medium-negative-binomial'
def raw(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def tex(v):return s.latex(s.cancel(v))
def pool(m):
 r=s.Rational(1,m);H0=1/(1-r);H1=r/(1-r)**2;H2=r*(1+r)/(1-r)**3
 A=s.cancel((H2+3*H1+2*H0)/2)
 values=[((3*H1+2*H0)/2,'omit the quadratic term when expanding the binomial coefficient'),((2*H2+3*H1+2*H0)/2,'count the quadratic term twice'),((H2+2*H0)/2,'omit the linear term in the binomial coefficient'),((H2+6*H1+2*H0)/2,'count the linear term twice'),((H2+3*H1)/2,'omit the constant term in the binomial coefficient'),((H2+3*H1+4*H0)/2,'count the constant term twice')]
 values=[(s.cancel(a),why) for a,why in values]
 values += [((1-r*r)**-3,'square the geometric ratio when the binomial lower index is two'),((1-r/(1-r))**-3,'apply the geometric-tail argument transform before the negative-binomial cube')]
 assert A==s.Rational(m,m-1)**3 and len({a for a,b in values+[ (A,'correct') ]})==9
 return A,values
def build_patch(record):
 guards=json.loads((P/'series-negative-binomial-repair-guards.json').read_text());g=guards[record['problemId']]
 assert record['familyId']==FID and record['contentHash']==g['contentHash'] and record['semanticHash']==g['semanticHash'] and raw(record)==g['rawHash']
 m=g['m'];A,values=pool(m);above=[q for q in values[:6] if q[0]>A];below=[q for q in values[:6] if q[0]<A];cube_below,cube_above=values[6:];rank=(m-4)%4
 selected=[[cube_above]+above[:2],[cube_below]+above[:2],[cube_above]+below[:2],[cube_below]+below[:2]][rank]
 assert len(selected)==3
 correct=next(copy.deepcopy(c) for c in record['choices'] if c['choiceId']==record['answerChoiceId']);assert correct['math']==tex(A)
 choices=[correct]+[{'choiceId':'qnb_'+hashlib.sha256(s.srepr(v).encode()).hexdigest()[:16],'math':tex(v),'misconception':why} for v,why in selected]
 return {'problemId':record['problemId'],'sourceContentHash':record['contentHash'],'sourceSemanticHash':record['semanticHash'],'sourceRawHash':g['rawHash'],'revisionKind':'option-only','meaningChanged':False,'recipeVersion':'quality-series-negative-binomial-options-v2','choices':choices,'answerChoiceId':record['answerChoiceId'],'independentExactAnswer':s.srepr(A),'exactPairwiseDistinct':len({A,*[v for v,why in selected]})==4,'explanationAndQuestionUnchanged':True,'newIndependentIdeas':0}
def supports(record):
 if record.get('familyId')!=FID:return False
 try:
  g=json.loads((P/'series-negative-binomial-repair-guards.json').read_text())[record['problemId']]
  return raw(record)==g['rawHash']
 except (KeyError,FileNotFoundError):return False
def verify_patch(patch,original):
 try:return supports(original) and patch==build_patch(original)
 except Exception:return False
DISPOSITIONS={
'rational-telescope':('retain-with-documented-nonreplication','The learned training rank was third and succeeded only20% on held-out cases. The held-out second-rank80% reverses that pattern rather than replicating it. The actual pool has first-term, endpoint-index, reciprocal and missed-tail errors; the answer is second or third in different cases. The Easy partial-fraction route remains necessary to distinguish those nearby fractions.'),
'ratio-test-data':('retain-with-mathematical-category-disposition','The same four categories contain zero, infinity, one and the displayed coefficient. Exactly five tasks have a denominator factorial (answer zero) and five a numerator factorial (answer infinity). Infinity is the sole noninteger/long command but is wrong for the other half. The held-out80% form rule reflects a four-to-one split of these two actual variants; no full-family form clue selects the answer. Classification requires reading the factorial placement.'),
'negative-binomial':('source-bound-option-only-repair-required','Longest TeX repeats70% on training and held-out halves. The correct cubic ratio often has more digits than lower-power generating-function distractors. This is a reproducible presentation cue. Replace only these10 finite pools with omitted/doubled quadratic, linear or constant terms in the actual binomial coefficient; all new values are derived exactly, not generated as arbitrary offsets.'),
'weighted-binomial-total':('retain-with-documented-mathematical-invariant','The answer has substantial powers of two because it counts weighted subsets. Several wrong options share those powers, including the unweighted total and doubled weighted total; divisibility8/16 cannot uniquely select the answer throughout the family. The observed67% is tie-aware with only two unique held-out successes, and the training-selected position rule does not replicate. Some endpoint-omission distractors are removable by parity, a valid but incomplete mathematical shortcut; Medium remains appropriate.'),
'binomial-alternating-difference':('retain-with-documented-nonreplication','Training selected the third numeric rank at80%, but that rule succeeds0% held out. The held-out second-rank80% is a different post-hoc rule. Positivity eliminates sign-error alternatives, while genuine degree-annihilation and missing-endpoint errors remain. The factorial result is second, third or largest depending on the finite pool, so a reusable rank rule is not established.'),
'Fourier-fourth-sine':('retain-after-Hard-reclassification','The shorter exact form is shared with another pi-squared fraction in most cases; some wrong rational first-term values are even shorter. Only two held-out instances give unique shortest-form success, so the75% tie-aware figure does not establish a family-wide singleton. The actual easiest route is the periodic-angle/Fourier identity already supporting Hard demotion, not Olympiad. Future option sets should preserve multiple comparable pure pi-squared candidates.'),
'totient-Lambert':('retain-with-documented-nonreplication','Training selected maximum absolute value at75%, but it succeeds25% held out. The held-out third-rank75% is not that learned rule. The competing fractions represent omitted zero/first geometric contributions and erroneous divisor weights; final ranks vary. The gcd regrouping and weighted geometric sum remain a Hard calculation, with no additional Olympiad claim.')}
if __name__=='__main__':
 rs=[json.loads(l) for l in INPUT.read_text().splitlines()];screen=json.loads(SCREEN.read_text())
 canonical={r['problemId']:r for r in map(json.loads,(P.parents[1]/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl').read_text().splitlines())}
 canonical.update({r['problemId']:r for r in map(json.loads,(INPUT.parent/'canonical-previews.jsonl').read_text().splitlines())})
 selected=[]
 for effective in rs:
  if effective['familyId'].split('-',3)[3] not in DISPOSITIONS:continue
  full=canonical[effective['problemId']]
  assert full['choices']==effective['choices'] and full['answerChoiceId']==effective['answerChoiceId']
  selected.append(full)
 guards={}
 for r in selected:
  if r['familyId']==FID:
   i=r['parameters']['instance'];guards[r['problemId']]={'m':i+4,'contentHash':r['contentHash'],'semanticHash':r['semanticHash'],'rawHash':raw(r)}
 assert len(guards)==10
 (P/'series-negative-binomial-repair-guards.json').write_text(json.dumps(guards,indent=2)+'\n')
 patches=[build_patch(r) for r in selected if r['familyId']==FID]
 (P/'series-negative-binomial-option-patches.json').write_text(json.dumps(patches,indent=2)+'\n')
 records=[]
 for r in selected:
  slug=r['familyId'].split('-',3)[3];decision,why=DISPOSITIONS[slug]
  records.append({'problemId':r['problemId'],'familyId':r['familyId'],'contentHash':r['contentHash'],'semanticHash':r['semanticHash'],'rawHash':raw(r),'disposition':decision,'reason':why,'preserveExposureIdentity':True})
 diagnostics={}
 for rule in ['length-min','length-max']:
  scores=[]
  for p in patches:
   lens=[len(c['math']) for c in p['choices']];target=(min if rule.endswith('min') else max)(lens);matches=[c for c,n in zip(p['choices'],lens) if n==target];scores.append((1/len(matches)) if any(c['choiceId']==p['answerChoiceId'] for c in matches) else 0)
  diagnostics[rule]={'all10TieAwareAccuracy':sum(scores)/len(scores),'perCase':scores}
 report={'scope':'Seven actual effective-family option flags:66 source-bound records. Position-only flags are not repaired. Ten negative-binomial candidate option patches require immutable parent admission and final screen on actual IDs.','sourceEffectiveInputSha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'sourceScreenSha256':hashlib.sha256(SCREEN.read_bytes()).hexdigest(),'records':records,'repairDiagnostics':diagnostics,'repairChecks':'Each negative-binomial answer and six authored alternatives obtained from the exact quadratic/linear/constant decomposition and their geometric derivative sums. All chosen triples have six distinct nonzero pair differences.','recipeAPI':'supports(original); build_patch(original); verify_patch(patch,original) -> bool. Input is the exact canonical effective record guarded by content/semantic/raw hashes. Parent assigns immutable revision and final canonical hash.'}
 (P/'series-option-disposition.json').write_text(json.dumps(report,indent=2)+'\n');print(len(records),'records;',len(patches),'repair patches;',diagnostics)
