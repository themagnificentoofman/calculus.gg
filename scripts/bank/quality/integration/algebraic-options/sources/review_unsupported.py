"""Explicit scope audit of157 records outside the initial scalar grammar.

This audits pair relations, not mathematical answers already covered by the
pinned independent reports. Non-scalar tasks retain those reports unchanged.
"""
from pathlib import Path
import json,itertools,hashlib,collections
import sympy as s
from unsupported_scalar_parser import parse
P=Path(__file__).resolve().parent;ROOT=P.parents[2]/'problem-quality'
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[json.loads(l)for l in(P/'full-preview-inputs.jsonl').read_text().splitlines()]
diag=P/'prior-evidence/initial-mathematical-opposites.json';u={r['problemId']:r for r in json.loads(diag.read_text())['records']if r['status']!='parsed-exact-real-scalar'}
scalar={'io3-arctan-parameter','io3-binary-product','io3-gamma-unit-average','io3-integral-equation','io3-mellin-cyclotomic','io3-thermal-derivative','io3-variational-energy','m3-integration-easy-odd-even'}
why={
'io3-oscillatory-regularization':'The options are ordered pairs of an ordinary-convergence assertion and a damping-limit value. Negating the pair is not the task semantics.',
'io3-principal-value':'The options pair the ordinary-integral status with a principal value. Scalar sign predicates are not predicates on the full categorical pair.',
'io3-rearrangement':'The options are ordered minimum/maximum pairs. The full vector, rather than an isolated coordinate, determines correctness.',
'quality-integration-olympiad-capped-two-moment-extrema':'The options form a two-by-two product of candidate lower and upper extrema. Each coordinate has two alternatives; no categorical or scalar sign singleton selects the full pair.',
'quality-integration-olympiad-homogeneous-Hilbert-kernel-norm':'The options form a two-by-two product of candidate positive sharp constants and yes/no attainment. Negation is undefined for the attainment coordinate.',
'quality-integration-olympiad-monic-L1-polynomial-extremum':'The first coordinate is a positive minimum norm and the second a polynomial coefficient. A scalar sign test cannot select their ordered pair; both coordinates vary.',
'quality-integration-olympiad-nonconvex-mean-relaxation':'The options form a two-by-two product of infimum values and yes/no attainment. Infimum and attainment are separate requested decisions.',
'quality-integration-olympiad-nonlinear-uniform-bound-threshold':'The options are parameter intervals with strict/non-strict endpoints. Endpoint values and inclusion must both be checked; scalar negation is not a meaningful relation on these sets.',
'quality-integration-olympiad-three-node-Peano-sharpness':'The options form a two-by-two product of positive sharp constants and attainment claims. Sign of the constant does not resolve attainment.'}
reports=[P/'prior-evidence'/f for f in ['new-integration-peer-v2.json','integration-peer-review.json','integration-option-peer-v2.json','headroom-all-finite-review.json']];evidence=[]
for p in reports:
 d=json.loads(p.read_text());items=d.get('results',d.get('records',[]));evidence.append((p,d,items))
old={r['problemId']:r for r in map(json.loads,(P/'unsupported-baseline-evidence-inputs.jsonl').read_text().splitlines())}
norm=lambda z:z.replace(r'\log',r'\ln').replace(' ','')
result=[]
for r in rows:
 if r['problemId']not in u:continue
 raw=r['provenance']['authoring'].get('rawSha256');entry={'problemId':r['problemId'],'familyId':r['familyId'],'sourceContentHash':r['contentHash'],'sourceSemanticHash':r['semanticHash'],'canonicalRawHash':H(r),'constructorRawHash':raw,'originalDiagnostic':u[r['problemId']]}
 if r['familyId']in scalar:
  v=[parse(c['math'])for c in r['choices']];assert all(q.is_real is not False and q.is_finite is not False for q in v);pairs=[(i,j)for i,j in itertools.combinations(range(4),2)if s.simplify(v[i]+v[j])==0];a=next(i for i,c in enumerate(r['choices'])if c['choiceId']==r['answerChoiceId']);entry.update(status='explicit-scalar-grammar-check-passed',parsedValues=[s.srepr(q)for q in v],oppositePairs=pairs,pairedCorrect=any(a in pair for pair in pairs),disposition='Three newly found odd-even singleton pairs are separately source-bound in the addendum.'if len(pairs)==1 else 'No exact opposite pair exists in this literal menu; the earlier unsupported result was a grammar limitation.')
 else:
  assert r['familyId']in why;entry.update(status='scalar-opposite-predicate-not-applicable',disposition=why[r['familyId']])
 # Join prior evidence by exact authored raw hash or immutable original content.
 matches=[]
 for p,d,items in evidence:
  for q in items:
   if (raw and raw in [q.get('rawSha256'),q.get('rawSHA256')])or(q.get('problemId')==r['problemId']and q.get('sourceContentHash')==r['contentHash']):matches.append({'reportPath':str(p),'reportSha256':fh(p),'entryHash':H(q),'binding':'rawConstructorHash'if raw in[q.get('rawSha256'),q.get('rawSHA256')]else'originalContentHash','originalRecord':q})
 if not matches and r['problemId']in old:
  before=old[r['problemId']]
  assert before['semanticHash']==r['semanticHash']
  assert sorted(norm(c['math'])for c in before['choices'])==sorted(norm(c['math'])for c in r['choices'])
  oldanswer=norm(next(c['math']for c in before['choices']if c['choiceId']==before['answerChoiceId']))
  nowanswer=norm(next(c['math']for c in r['choices']if c['choiceId']==r['answerChoiceId']))
  assert oldanswer==nowanswer
  for p,d,items in evidence:
   for q in items:
    if q.get('problemId')==before['problemId']and q.get('sourceContentHash')==before['contentHash']:
     matches.append({'reportPath':str(p),'reportSha256':fh(p),'entryHash':H(q),'binding':'baseline content hash plus unchanged semanticHash and all4 literal choices (natural-log notation normalization only)','baselineSourceContentHash':before['contentHash'],'baselineRawHash':H(before),'originalRecord':q})
 entry['priorIndependentEvidence']=matches
 if not matches:
  e=r['validation']['evidence'];entry['preservedCanonicalEvidenceReference']={k:e.get(k)for k in ['independentReviewReport','independentReviewReportSha256','reviewId','rawSha256','uniqueCorrectOption']};entry['evidenceLimitation']='This sign-scope audit does not independently reissue the prior proof/choice certificate. The exact canonical reference is preserved for parent admission to join.'
 result.append(entry)
assert len(result)==157;assert sum(r['status']=='explicit-scalar-grammar-check-passed'for r in result)==57
assert len([r for r in result if len(r.get('oppositePairs',[]))==1])==3
report={'scope':'Exact mathematical-opposite scope review, not a replacement for prior independent answer/proof checks. Separate AI review; no human/formal certification.','sourceSha256':{'initialDiagnostic':fh(diag),'fullInput':fh(P/'full-preview-inputs.jsonl'),'parser':fh(P/'unsupported_scalar_parser.py')},'counts':{'initiallyUnsupported':157,'explicitlyParsedScalars':57,'scalarMenusWithNoOppositePair':54,'newlyFoundSingletonPairs':3,'nonScalarPredicateNotApplicable':100},'families':dict(collections.Counter(r['familyId']for r in result)),'records':result}
(P/'unsupported-scope-review.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts']);print('unjoined',sum(not r['priorIndependentEvidence']for r in result))
