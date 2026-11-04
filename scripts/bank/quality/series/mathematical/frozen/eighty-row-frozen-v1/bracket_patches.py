"""Separate78 bracketing repairs and2 exact duplicate-menu repairs.

No original constructor or admitted artifact changes. All new alternatives are
named index, endpoint, Jacobian or asymptotic-comparison mistakes.
"""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,itertools,json,re
import sympy as s
from literal_math import parse
from enclosures import enclose,dump
from atan_certificate import normalized_tangent
BASE=Path(__file__).resolve().parent
VERSION='series-bracket-and-atan-options-v1'
SLUGS=['geometric-tail','rational-telescope','borderline-exponential-comparison','floor-geometric-count','alternating-error','cubic-telescope','integral-tail-bound','theta-dual-moment']
ATAN_IDS={'cn_d9d932059411b98a11ad','cn_07da29bf43492c146f3b'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(v).replace(r'\log',r'\ln')
@lru_cache(None)
def originals():return {r['problemId']:r for r in map(json.loads,(BASE/'full-source-records.jsonl').read_text().splitlines())if any(r['familyId'].endswith(x)for x in SLUGS)or r['problemId']in ATAN_IDS}
def supports(record):
 old=originals().get(record.get('problemId'));return old is not None and H(record)==H(old)
def authored_pool(r):
 slug=next(x for x in SLUGS if r['familyId'].endswith(x));i=r['parameters']['instance'];m=s.Integer(i+4);x,k,N=s.symbols('x k N',positive=True);checks=[]
 if slug=='geometric-tail':
  t=m**(-m);A=t/(1-1/m)
  pool=[(t,'Return only the first included term'),(A/m,'Begin the geometric tail one index too late'),(A/m**2,'Begin the geometric tail two indices too late'),(A*m,'Include the preceding excluded term'),(A*m**2,'Include two preceding excluded terms'),(A+t,'Count the first included term twice')]
  assert s.simplify(A-m**(1-m)/(m-1))==0
  checks=[{'description':'Geometric tail first term and ratio','firstTerm':str(t),'ratio':str(1/m),'answer':str(A),'convergence':'The positive ratio is less than one.'}]
 elif slug=='rational-telescope':
  A=1/m;first=1/(m*(m+1))
  pool=[(1/(m+1),'Omit the first telescoping term'),(1/(m+2),'Omit the first two telescoping terms'),(first,'Return only the first included term'),(1/(m-1),'Include the preceding excluded term'),(A+first,'Count the first included term twice'),(m,'Invert the surviving endpoint reciprocal')]
  assert s.factor(1/(k+m)-1/(k+m+1)-1/((k+m)*(k+m+1)))==0
  checks=[{'description':'Adjacent reciprocal difference identity','difference':'1/(k+m)−1/(k+m+1)','term':'1/((k+m)(k+m+1))','result':True,'convergence':'The surviving upper endpoint tends to zero.'}]
 elif slug=='borderline-exponential-comparison':
  A=s.Integer(1)
  pool=[(s.Integer(0),'Confuse a nonzero bounded numerator with extra decay and use only termwise vanishing'),(1/m,'Treat the summation index as its displayed scale power and apply the p-test to the resulting wrong exponent'),(s.Rational(1,2),'Treat the nonzero limiting numerator as a Gaussian square-root decay'),(s.Integer(2),'Add an extra power requirement because the canceled exponent contains a square'),(m,'Use the canceled first-order exponential coefficient as the power threshold'),(m*m/2,'Treat the limiting logarithmic constant as an additional power of the index'),(m*m,'Use the quadratic Taylor coefficient as a decay exponent and omit its denominator two'),(m**3,'Use the cubic Taylor coefficient as a decay exponent and omit its denominator three')]
  assert s.limit(m/x+s.log(1-m*x)/x**2,x,0,dir='+')==-m*m/2
  checks=[{'description':'Canceled logarithm has finite exact limit','limit':str(-m*m/2),'result':True,'analyticStep':'Taylor remainder is bounded for0<m/k≤1/2. The numerator tends to exp(−m²/2)>0, so limit comparison with k^(−p) gives precisely p>1.'}]
 elif slug=='floor-geometric-count':
  Q=2**m;A=2/(Q-1)
  pool=[(1/(Q-1),'Omit the factor two from the inner geometric tail'),(2/(Q*(Q-1)),'Begin the outer block count one block too late'),(2/(Q+1),'Use an alternating rather than positive geometric ratio for the block tails'),(4/(Q-1),'Apply the inner geometric-tail factor two twice'),(2*Q/(Q-1),'Include a zero-th block that the floor count does not contain'),(m*A,'Multiply by the block size again after counting all eligible indices')]
  assert s.simplify(2*Q**-1/(1-Q**-1)-A)==0
  checks=[{'description':'Count positive multiples and sum geometric tails','identity':'floor(k/m)=sum_{j≥1}1_{mj≤k}','answer':str(A),'result':True,'analyticStep':'Nonnegative terms justify Tonelli; the outer geometric ratio2^(−m) is below one.'}]
 elif slug=='alternating-error':
  A=1/(m+1)
  pool=[(1/(m+2),'Skip the first omitted term'),(1/(m+3),'Skip the first two omitted terms'),(A/2,'Halve the first-omitted-term theorem bound'),(1/m,'Use the last included magnitude'),(1/(m-1),'Use the penultimate included magnitude'),(2*A,'Double the theorem bound')]
  checks=[{'description':'Standard alternating-series theorem uses the first omitted index','includedThrough':int(m),'firstOmittedIndex':int(m+1),'answer':str(A),'analyticStep':'The harmonic magnitudes are positive, decreasing and tend to zero. The question requests the standard first-omitted-term bound, not every looser valid inequality.'}]
 elif slug=='cubic-telescope':
  A=1/(2*m*(m+1));first=1/(m*(m+1)*(m+2))
  pool=[(1/(2*(m+1)*(m+2)),'Omit the first term after telescoping'),(1/(2*(m+2)*(m+3)),'Omit the first two terms after telescoping'),(first,'Return only the first included term'),(2*A,'Omit the half factor in the telescoping difference'),(1/(2*(m-1)*m),'Include the preceding excluded term'),(A+first,'Count the first included term twice')]
  assert s.factor((1/((k+m)*(k+m+1))-1/((k+m+1)*(k+m+2)))/2-1/((k+m)*(k+m+1)*(k+m+2)))==0
  checks=[{'description':'Exact two-factor reciprocal difference with factor one-half','result':True,'analyticStep':'The finite partial sum has a vanishing positive quadratic endpoint.'}]
 elif slug=='integral-tail-bound':
  A=1/(2*m*m)
  pool=[(1/(2*(m+1)**2),'Use the lower rather than upper comparison integral'),(1/(2*(m+2)**2),'Move the comparison endpoint two intervals too far'),(1/(3*m**3),'Keep the old negative power in the primitive'),(1/(m*m),'Omit the power-rule denominator two'),(1/(2*(m-1)**2),'Begin the comparison integral one interval too early'),(1/(2*(m-2)**2),'Begin the comparison integral two intervals too early')]
  assert s.diff(-1/(2*x*x),x)==x**-3 and s.integrate(x**-3,(x,m,s.oo))==A
  checks=[{'description':'Correct primitive and concrete endpoint integral','result':True,'answer':str(A),'analyticStep':'The positive function x^(−3) decreases, so the right-endpoint rectangles lie below the preceding unit strips.'}]
 else:
  A=1/(2*s.pi*m)
  pool=[(A/2,'Introduce a spurious one-sided lattice factor two'),(A/m,'Apply one extra reciprocal-argument power during differentiation'),(A/m**2,'Apply two extra reciprocal-argument powers during differentiation'),(2*A,'Omit the half-power derivative coefficient'),(m*A,'Drop the displayed positive scale from the resulting ratio'),(m*m*A,'Reverse rather than differentiate the reciprocal argument factor')]
  a=s.symbols('a',positive=True);theta=s.Function('Theta');derivative=s.diff(a**(-s.Rational(1,2))*theta(1/a),a);expected=-theta(1/a)/(2*a**s.Rational(3,2))-s.Subs(s.Derivative(theta(x),x),x,1/a)/a**s.Rational(5,2)
  assert s.simplify(derivative-expected)==0
  checks=[{'description':'Differentiate the theta modular identity including both chain-rule terms','result':True,'analyticStep':'The Gaussian series and its derivative converge locally uniformly for positive scale. Use Theta(a)=a^(−1/2)Theta(1/a) and Theta′(a)=−pi M(a); the displayed weighted moments leave Theta(a)/(2pi a).','answer':tex(A)}]
 patterns={'geometric-tail':r'\\sum_\{k=(\d+)\}', 'rational-telescope':r'k \+ (\d+)', 'cubic-telescope':r'k \+ (\d+)', 'borderline-exponential-comparison':r'e\^\{(\d+)k\}', 'floor-geometric-count':r'k/(\d+)\\rfloor', 'alternating-error':r'through\s*\}\s*(\d+)', 'integral-tail-bound':r'\\int_\{(\d+)\}', 'theta-dual-moment':r'M\((\d+)\)'}
 literal=re.search(patterns[slug],r['statement']);assert literal and int(literal[1])==m,(slug,r['statement'])
 checks.insert(0,{'description':'Read the finite parameter from the literal mathematical statement','displayedValue':int(literal[1]),'sourceInstance':i,'result':True})
 return slug,m,s.simplify(A),[(s.simplify(v),why)for v,why in pool],checks

def build_patch(record):
 if not supports(record):raise ValueError('Outside exact source guard')
 r=record;i=r['parameters']['instance'];correct=next(c for c in r['choices']if c['choiceId']==r['answerChoiceId']);A=parse(correct['math']);replaced=copy.deepcopy(r['choices']);checks=[];reason='';poolreport=[]
 if r['problemId']in ATAN_IDS:
  m=s.Integer(i+4);assert m in [6,9]
  norms=[normalized_tangent(parse(c['math']))for c in r['choices']];duplicate=[(j,k)for j,k in itertools.combinations(range(4),2)if norms[j][0]==norms[k][0]];assert len(duplicate)==1
  j,k=duplicate[0];assert r['answerChoiceId']not in [r['choices'][j]['choiceId'],r['choices'][k]['choiceId']]
  choices=copy.deepcopy(r['choices']);value=s.pi/2-s.atan(m+2);choices[k]={'choiceId':'ch_'+H([VERSION,s.srepr(value)])[:16],'math':tex(value),'misconception':'Omit the first two terms of the arctangent telescope'}
  checks=[{'description':'Duplicate wrong omission forms have the same exact tangent and branch','indices':[j,k],'normalizations':[norms[j][1],norms[k][1]]},{'description':'New wrong option has a distinct exact principal tangent','normalization':normalized_tangent(value)[1]}]
  reason='Two old wrong options were exactly equal by the arctangent difference formula on its principal branch. Replace one by a two-term omission; preserve the correct answer and all other source content.'
 else:
  slug,m,independent,pool,checks=authored_pool(r);assert s.simplify(s.expand_func(independent-A))==0
  lows=[x for x in pool if enclose(x[0]-A)[1]<0];highs=[x for x in pool if enclose(x[0]-A)[0]>0];assert len(lows)>=3 and len(highs)>=3
  target=[0,3,1,2][i%4];lo=lows[i%len(lows):]+lows[:i%len(lows)];hi=highs[i%len(highs):]+highs[:i%len(highs)];selected=lo[:target]+hi[:3-target]
  if slug=='borderline-exponential-comparison':
   def power_form(v,n):
    return bool(v.is_Rational and v>=0 and s.integer_nthroot(int(v.p),n)[1] and s.integer_nthroot(int(v.q),n)[1])
   feasible=[list(low+high)for low in itertools.combinations(lows,target)for high in itertools.combinations(highs,3-target)if all(any(power_form(v,n)for v,_ in low+high)for n in [2,3])]
   assert feasible;selected=feasible[i%len(feasible)]
  choices=[copy.deepcopy(correct)]+[{'choiceId':'ch_'+H([VERSION,s.srepr(v)])[:16],'math':tex(v),'misconception':why}for v,why in selected]
  poolreport=[{'expression':s.srepr(v),'math':tex(v),'misconception':why,'belowAnswer':v in [q[0]for q in lows]}for v,why in pool]
  reason='The old authored pool allowed only middle answer ranks. Add explicit unused misconception routes on both sides and cycle every feasible exact rank across the finite domain. No arbitrary numerical offsets or new construction ideas are introduced.'
 vals=[parse(c['math'])for c in choices];certs=[]
 for j,k in itertools.combinations(range(4),2):
  if r['problemId']in ATAN_IDS:
   u,uc=normalized_tangent(vals[j]);v,vc=normalized_tangent(vals[k]);assert u!=v;cert={'method':'principal arctangent injectivity and exact unequal rational tangents','tangents':[str(u),str(v)]}
  else:
   diff=s.factor_terms(s.expand_func(vals[j]-vals[k]));iv=enclose(diff);assert iv[0]>0 or iv[1]<0;cert={'method':'exact nonzero difference bounded by outward rational interval','difference':s.srepr(diff),'enclosure':dump(iv)}
  certs.append({'choiceIds':[choices[j]['choiceId'],choices[k]['choiceId']],**cert})
 assert next(c for c in choices if c['choiceId']==r['answerChoiceId'])==correct
 return {'patchVersion':VERSION,'problemId':r['problemId'],'familyId':r['familyId'],'instanceIndex':i,'sourceRevision':r['problemRevision'],'sourceContentHash':r['contentHash'],'sourceSemanticHash':r['semanticHash'],'sourceRawSHA256':H(r),'sourceChoicesSHA256':H(r['choices']),'choices':choices,'answerChoiceId':r['answerChoiceId'],'preservedCorrectChoice':correct,'replacedChoices':replaced,'authoredMisconceptionPool':poolreport,'reason':reason,'mathematicalChecks':checks,'sixChoiceInequalityCertificates':certs,'meaningChanged':False,'preserveStatementSolutionAndLineage':True,'newIndependentIdeas':0,'reviewStatus':'candidate-awaiting-independent-parent-review','humanReviewed':False,'formalProof':False}
def verify_patch(patch,record):
 try:return canonical(patch)==canonical(build_patch(record))
 except(ValueError,KeyError,AssertionError,StopIteration):return False
if __name__=='__main__':
 rows=[build_patch(r)for _,r in sorted(originals().items())];assert len(rows)==80
 (BASE/'bracket-option-patches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(rows),'inequalityCertificates':sum(len(r['sixChoiceInequalityCertificates'])for r in rows)}))
