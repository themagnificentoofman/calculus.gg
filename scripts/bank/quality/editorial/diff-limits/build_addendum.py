"""Source-bound editorial metadata only. Never modifies frozen raw candidates."""
from pathlib import Path
import os,json,hashlib,re,collections
import sympy as s
P=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('DIFF_LIMITS_FROZEN_BUNDLE',P.parent/'portable/diff-limits'))
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canon(v).encode()).hexdigest()
def filehash(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def tex(v):return re.sub(r'\s+','',v.replace(r'\left','').replace(r'\right',''))
def equal_literal(raw,value):
 assert tex(raw)==tex(s.latex(value)),(raw,s.latex(value))
 return {'kind':'literal-exact-expression-match','literal':raw,'independentlyComputedExpression':s.srepr(value),'passed':True}
def refine(r,c,old):
 f=r['familyId'];st=r['statement'];math=c['math'];x=s.Symbol('x',real=True)
 if f=='m3-differentiation-medium-moving-integral-endpoints' and old in['omit a derivative contribution','misapply the chain or product rule']:
  m=int(re.search(r'\\int_x\^\{?(\d+)x',st)[1]);correct=s.diff(s.exp(m*x)-s.exp(x),x).subs(x,0);assert correct==m-1
  if old=='omit a derivative contribution':v=s.Integer(m);new='Omit the lower-endpoint derivative term.';route='Differentiate only the upper endpoint: m exp(mx) at zero is m.'
  else:v=s.Integer(m+1);new='Add the lower-endpoint derivative instead of subtracting it.';route='Use m exp(mx)+exp(x) at zero instead of their difference.'
 elif f=='m3-limits-medium-exponential-variable-power' and old in['drop a leading contribution','discard the first surviving limit term']:
  m=int(re.search(r'\\left\((\d+) x \+ 1',st)[1]);assert s.limit(s.log(1+m*x)/x,x,0,dir='+')==m
  if old=='drop a leading contribution':v=s.exp(s.Rational(1,m));new='Invert the inner linear scale after taking the logarithm of the power limit.';route='Replace the correct logarithmic limit m by 1/m before exponentiating.'
  else:v=s.Integer(0);new='Take the limit of the logarithm numerator alone, omitting division by x and exponentiation.';route='The logarithm numerator log(1+mx) tends to zero, which is not the original power limit.'
 elif f=='m3-limits-hard-recurrence-limit' and old in['omit the endpoint correction','retain a lower-order term','use the wrong asymptotic scale']:
  C=int(re.search(r'\\sqrt\{(\d+)\+a_n',st)[1]);m=(1+s.sqrt(1+4*C))/2;assert m.is_integer and m*(m-1)==C
  if old=='omit the endpoint correction':v=s.sqrt(C);new='Omit the recursive term inside the square root and return the first iterate.';route='Setting a_n to zero gives sqrt(C); the fixed-point equation instead retains the limiting a_n.'
  elif old=='retain a lower-order term':v=s.Integer(C);new='Return the radicand constant, omitting both the square root and the fixed-point equation.';route='Select C itself from a_(n+1)=sqrt(C+a_n), not a root of L^2-L-C=0.'
  else:v=m-1;new='Take the absolute value of the negative fixed-point root.';route='The second quadratic root is 1-m; taking its absolute value incorrectly returns m-1.'
 elif f=='m3-differentiation-olympiad-noncommuting-operator' and old in['use an inappropriate rule','reverse a relation','omit a contribution']:
  m=int(re.search(r'L\^\{(\d+)\}',st)[1]);fx=s.exp(-x*x+x);assert s.simplify(s.diff(fx,x)+2*x*fx-fx)==0
  if old=='use an inappropriate rule':v=s.Integer(m);new='Multiply the eigenfunction by the iteration count instead of raising its eigenvalue to that power.';route='Mistake L^m f for m Lf; here the true eigenvalue is one.'
  elif old=='reverse a relation':v=s.factorial(m);new='Treat the operator iterate as differentiating a degree-m monomial m times at zero.';route='The unrelated monomial derivative produces m!, whereas the displayed function is an eigenfunction of L.'
  else:v=s.Integer(2)**m;new='Treat the coefficient two in the variable multiplication term as the operator eigenvalue.';route='Use 2^m despite the derivative cancellation showing the actual eigenvalue is one.'
 else:return None
 return {'originalEvidenceLabel':old,'reviewedLabel':new,'mathematicalWrongRoute':route,'check':equal_literal(math,v)}
def main():
 joins=json.loads((SOURCE/'source-joins.json').read_text());cache={};entries=[];refinements=[];mapcount=0;kindcount=0;labelcount=collections.Counter();families=collections.Counter()
 for j in joins['records']:
  if not j['route'].startswith('diff-limits'):continue
  name=j['sourceFile'];f=SOURCE/name
  if name not in cache:
   assert filehash(f)==joins['sourceArtifacts'][name]
   cache[name]=json.loads(f.read_text())
  r=cache[name][j['sourceRecordIndex']];assert digest(r)==j['rawSha256']
  missing=any('misconception'not in c for c in r['choices']);kind=r['provenance']['kind'];unsupported=kind in['original-constructor-extension','original-finite-pool-replacement']
  if not missing and not unsupported:continue
  reviewId=f"quality-review:{j['route']}:{j['familyId']}:{j['index']}";e={'reviewId':reviewId,'rawSha256':j['rawSha256'],'route':j['route'],'familyId':j['familyId'],'index':j['index'],'sourceFile':name,'sourceRecordIndex':j['sourceRecordIndex'],'sourceFileSha256':filehash(f),'expectedChoices':[{k:c[k]for k in('choiceId','math')}for c in r['choices']]}
  if missing:
   assert all('misconception'not in c for c in r['choices']);evidence=r['validation']['evidence']['choiceMisconceptions'];assert set(evidence)=={c['math']for c in r['choices']};mapping={};detail=[]
   for c in r['choices']:
    old=evidence[c['math']];fixed=refine(r,c,old);lab=fixed['reviewedLabel']if fixed else old
    assert (lab=='correct')==(c['choiceId']==r['answerChoiceId']);mapping[c['choiceId']]=lab;labelcount[lab]+=1
    if fixed:
     d={'reviewId':reviewId,'rawSha256':j['rawSha256'],'choiceId':c['choiceId'],'math':c['math'],**fixed};refinements.append(d);detail.append(d)
   assert len(mapping)==4;e['choiceMisconceptions']=mapping;e['choiceLabelSource']={'field':'validation.evidence.choiceMisconceptions, keyed by exact literal math','liftingChecks':'Complete equality of all four literal expressions, unique choice IDs, correct marker exactly matches answerChoiceId. Existing public labels are absent; no existing public differing label is overwritten.','explicitRefinements':detail};mapcount+=1;families[r['familyId']]+=1
  if unsupported:
   assert r['provenance']['lineage']['originalFamilyId'] and r['provenance']['lineage']['newIdeaCredit']==0
   e['originalProvenanceKind']=kind;e['proposedCanonicalKind']='original';e['preservedProvenance']=r['provenance'];e['provenanceRationale']='Independently authored finite extension or purposeful finite-pool replacement of the named original construction. The specialized kind describes constructor workflow, not an adapted external source. Preserve the complete original lineage and any sourceContentHash; award no new independent-idea credit.';kindcount+=1
  e['reviewStatus']='author-metadata-audit-complete; independent-metadata-review-pending';entries.append(e)
 assert mapcount==324 and kindcount==184 and len(entries)==508
 assert len({e['rawSha256']for e in entries})==508
 report={'schemaVersion':1,'status':'source-bound-author-metadata-audit-complete-pending-independent-review','scope':'Metadata-only addendum for exact frozen D/L raw records. No problem ID, statement, answer, choice expression, solution, source provenance, level or historical record is modified.','counts':{'records':len(entries),'completeChoiceMaps':mapcount,'choiceLabels':4*mapcount,'originalKindMappings':kindcount,'explicitEvidenceLabelRefinements':len(refinements)},'sourceClosure':{'source-joins.json':filehash(SOURCE/'source-joins.json'),**joins['sourceArtifacts']},'familyMapCounts':dict(sorted(families.items())),'withdrawalPolicy':'The seven redundant noncommuting-operator indices1..7 remain withdrawal dispositions. Their presence in this reviewed metadata inventory does not authorize their admission.','priorIndependentMathEvidence':{'path':'evidence/peer-lower577.json','sha256':filehash(SOURCE/'evidence/peer-lower577.json'),'scope':'All577 lower records independently rederived and literal-pair checked; this metadata audit does not replace that mathematical evidence.'},'entries':entries,'refinements':refinements,'distinctReviewedLabels':dict(sorted(labelcount.items())),'limitations':'AI editorial review with executed source guards and exact checks for refined labels. No human or formal proof claim. Parent independent metadata review remains required.'}
 (P/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 h=filehash(P/'report.json');supp={}
 for e in entries:
  v={'rawSha256':e['rawSha256'],'report':'docs/bank/problem-quality/diff-limits-editorial-supplement.json','reportSha256':h}
  for k in('choiceMisconceptions','originalProvenanceKind'):
   if k in e:v[k]=e[k]
  supp[e['reviewId']]={'editorialSupplement':v}
 (P/'adapter-supplements.json').write_text(json.dumps(supp,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'counts':report['counts'],'reportSha256':h,'supplementsSha256':filehash(P/'adapter-supplements.json')}))
if __name__=='__main__':main()
