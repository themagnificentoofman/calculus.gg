"""Last bounded76-menu rank-support amendment; originals and other patches frozen."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,itertools,json,re
import sympy as s
from literal_math import parse
from enclosures import enclose,dump
BASE=Path(__file__).resolve().parent
VERSION='series-upper-lower-support-options-v1'
SLUGS=['nth-term-test','power-series-radius','dyadic-infinite-product','power-series-ratio-radius','quadratic-weight','totient-Lambert','Liouville-Dirichlet-product','finite-cycle-resolvent']
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(v).replace(r'\log',r'\ln')
@lru_cache(None)
def originals():return {r['problemId']:r for r in map(json.loads,(BASE/'full-source-records.jsonl').read_text().splitlines())if any(r['familyId'].endswith(x)for x in SLUGS)}
def supports(record):
 old=originals().get(record.get('problemId'));return old is not None and H(old)==H(record)
def authored(r):
 slug=next(x for x in SLUGS if r['familyId'].endswith(x));i=r['parameters']['instance'];m=s.Integer(i+4);x=s.symbols('x',positive=True);checks=[];bound=None;required=None
 if slug=='nth-term-test':
  A=m;pool=[(0,'Assume that every sequence used in a series tends to zero'),(1,'Ignore the numerator leading coefficient'),(1/m,'Invert the leading-coefficient ratio'),(2*m,'Multiply by the denominator constant instead of its leading coefficient'),(m*m,'Square the numerator leading coefficient when dividing by the index'),(m+1,'Keep the numerator constant as part of its leading coefficient')]
  assert s.limit((m*x+1)/(x+2),x,s.oo)==A;checks=[{'description':'Independent rational-function limit from leading coefficients','result':True}];pattern=r'\\frac\{(\d+)k\+1\}'
 elif slug=='power-series-radius':
  A=m;pool=[(1/m,'Return the coefficient-root limit rather than its reciprocal'),(1,'Ignore the scale in the geometric ratio'),(m/(m-1),'Return the coefficient-series sum at x=1 instead of a radius'),(2*m,'Return the full width of the convergence interval instead of its radius'),(m*m,'Square the ratio scale when taking the coefficient root'),(m*m/(m-1),'Multiply the ratio scale by the coefficient-series sum at x=1')]
  assert s.solve(s.Eq(x/m,1),x)[0]==A;checks=[{'description':'Geometric ratio condition gives absolute x less than the displayed scale','result':True,'condition':'|x/m|<1'}];pattern=r'\\frac\{x\}\{(\d+)\}'
 elif slug=='dyadic-infinite-product':
  u=1/m;A=1/(1-u);pool=[(1+u,'Keep only the first factor'),((1+u)*(1+u*u),'Keep only the first two factors'),(1/(1+u),'Use the negative-ratio telescoping denominator'),(1/(1-2*u),'Subtract the ratio twice in the final denominator'),(A*(1+u),'Include the first factor again after the full telescoping product'),(A*(1+u*u),'Include the second factor again after the full telescoping product')]
  for N in [1,2,3,4]:assert s.prod(1+u**(2**j)for j in range(N))==(1-u**(2**N))/(1-u)
  checks=[{'description':'Independent finite binary-product identity at four exact truncations','result':True,'analyticStep':'Inductively(1−u) product_{j=0}^{N−1}(1+u^(2^j))=1−u^(2^N). With0<u<1 the endpoint tends to zero, proving convergence and value.'}];pattern=r'\\frac\{1\}\{(\d+)\}'
 elif slug=='power-series-ratio-radius':
  A=4/m;pool=[(1/(4*m),'Invert the limiting factorial ratio'),(2/m,'Keep only one of the two factors of two'),(1/m,'Discard both factors of two in the denominator ratio'),(4*m,'Multiply by the variable scale rather than dividing by it'),(8/m,'Count the factorial factor two one additional time'),(16/m,'Square the limiting factorial-ratio reciprocal')]
  assert s.limit((x+1)**2/((2*x+2)*(2*x+1)),x,s.oo)==s.Rational(1,4);checks=[{'description':'Exact limiting ratio of consecutive factorial coefficients','value':'1/4','result':True,'convergenceCondition':'|m x|/4<1'}];pattern=r'\((\d+)x\)\^k'
 elif slug=='quadratic-weight':
  A=m*(m+1)/(m-1)**3;C=m*(m*m+4*m+1)/(m-1)**4
  pool=[(m/(m-1)**2,'Apply the Euler derivative only once'),(m*m/(m-1)**3,'Omit the second numerator contribution from the product rule'),((m+1)/(m-1)**3,'Lose the numerator scale during substitution'),(A+1/m,'Count the first included term twice'),(A*m/(m-1),'Retain an extra geometric summation factor'),(C,'Apply the Euler derivative three times and weight by the cube of the index')]
  F=x/(1-x);D=x*s.diff(F,x);DD=x*s.diff(D,x);DDD=x*s.diff(DD,x);assert s.simplify(DD.subs(x,1/m)-A)==0 and s.simplify(DDD.subs(x,1/m)-C)==0;checks=[{'description':'Independent second and third Euler derivatives of geometric series','result':True,'analyticStep':'All differentiated series converge locally uniformly for|x|<1; the actual ratio1/m lies inside that disk.'}];pattern=r'(\d+)\^\{- k\}'
 elif slug=='totient-Lambert':
  A=m/(m-1)**2;pool=[(1/(m-1)**2,'Insert an extra generating-function variable after the divisor regrouping'),(1/(m-1),'Replace the divisor sum by one'),(m/(m+1)**2,'Alternate the divisor-sum geometric terms'),(m*m/(m-1)**2,'Omit the numerator generating-function variable'),(2*A,'Count each divisor contribution twice when reversing the two sums'),(m*(m+1)/(m-1)**3,'Replace the divisor identity by the square of the index')]
  for n in range(1,31):assert sum(s.totient(d)for d in s.divisors(n))==n
  assert s.simplify((x*s.diff(1/(1-x),x)).subs(x,1/m)-A)==0
  checks=[{'description':'Exact divisor identity checked for30 integers and differentiated geometric series independently computed','result':True,'analyticStep':'Classify integers1..n by gcd with n to prove sum_{d|n}phi(d)=n for all n. All terms are nonnegative, so Tonelli justifies regrouping. The resulting differentiated geometric series converges for1/m<1.'}];pattern=r'\}\{(\d+)\^k-1\}'
 elif slug=='Liouville-Dirichlet-product':
  p=s.Integer(i+2);A=s.zeta(2*p)/s.zeta(p);pool=[(1/s.zeta(p),'Omit the denominator Euler factor that restores even prime powers'),(1/(s.zeta(p)*s.zeta(2*p)),'Invert the even-prime-power correction instead of dividing by its local factor'),(s.zeta(2*p)/s.zeta(p)**2,'Apply the local factor1−u twice'),(1/s.zeta(2*p),'Invert the square-only Euler product'),(s.zeta(p)/s.zeta(2*p),'Invert every local Liouville factor'),(s.zeta(2*p),'Discard all nonsquare terms')]
  assert s.cancel(1/(1+x)-(1-x)/(1-x*x))==0
  checks=[{'description':'Independent local Euler-factor identity','result':True,'analyticStep':'Complete multiplicativity follows from adding prime multiplicities. Absolute convergence for p>1 permits finite prime products to exhaust the Dirichlet series. Each local factor is1/(1+u)=(1−u)/(1−u²).','exponent':int(p)},{'description':'The inverse square-only product is above the answer while still below one','result':True,'analyticStep':'For every prime u=prime^(−p)≤1/4, (1−u)(1+u)^2>1. Thus (1−u²)^−2<(1−u)^−1, and multiplying convergent positive factors gives zeta(2p)^2<zeta(p).'}];pattern=r'n\^\{(\d+)\}';m=p
 else:
  n=s.Integer([13,17,19,23,29,31,37,41][i]);D=[s.Integer(1),s.Integer(3)]
  for j in range(2,int(n)+1):D.append(3*D[-1]-D[-2])
  determinant=D[int(n)]-D[int(n)-2]-2;A=2*n*D[int(n)-1]/determinant
  B=2*n*D[int(n)-1]/(determinant+4);required=B
  pool=[(B,'Use the antiperiodic rather than periodic angle set'),(A/n,'Average the resolvents instead of summing them'),(1/A,'Invert the logarithmic derivative'),(A-2,'Omit the angle-zero endpoint contribution'),(n*A,'Count every vertex multiplicity an additional time'),(A+2,'Include the angle2pi endpoint even though angle zero already occurs'),(2*A-2,'Count every nonzero paired-angle contribution twice while retaining the zero angle once')]
  matrix=s.zeros(int(n))
  for j in range(int(n)):
   matrix[j,j]=3;matrix[j,(j+1)%int(n)]=-1;matrix[(j+1)%int(n),j]=-1
  assert matrix.det(method='domain-ge')==determinant
  checks=[{'description':'Independent cyclic tridiagonal determinant and principal cofactor recurrence','matrixSize':int(n),'determinant':str(determinant),'principalMinor':str(D[int(n)-1]),'result':True,'analyticStep':'The cyclic matrix3I−adjacency has eigenvalues3−2cos(2pi k/n)>0. By cyclic symmetry its inverse trace is n times the common principal cofactor divided by its determinant. The required sum is twice this trace.'}];bound=(s.Rational(2,3)*n,2*n);pattern=r'k/(\d+)';m=n
 literal=re.search(pattern,r['statement']);assert literal and int(literal[1])==m,(slug,r['statement']);checks.insert(0,{'description':'Literal finite parameter independently read from statement','value':int(m),'result':True})
 return slug,s.simplify(A),[(s.simplify(v),why)for v,why in pool],checks,required,bound

def build_patch(record):
 if not supports(record):raise ValueError('Outside exact source guard')
 r=record;i=r['parameters']['instance'];correct=next(c for c in r['choices']if c['choiceId']==r['answerChoiceId']);slug,A,pool,checks,required,bound=authored(r);assert s.simplify(s.expand_func(parse(correct['math'])-A))==0
 lo=[p for p in pool if enclose(p[0]-A)[1]<0];hi=[p for p in pool if enclose(p[0]-A)[0]>0];assert len(lo)>=3 and len(hi)>=3,(slug,len(lo),len(hi))
 target=[0,3,1,2][i%4];combos=[]
 for low in itertools.combinations(lo,target):
  for high in itertools.combinations(hi,3-target):
   group=list(low+high)
   if required is not None and target>0 and not any(v==required for v,_ in group):continue
   if bound is not None and not any(bound[0]<v<bound[1]for v,_ in group):continue
   combos.append(group)
 assert combos;chosen=combos[i%len(combos)];choices=[copy.deepcopy(correct)]+[{'choiceId':'ch_'+H([VERSION,s.srepr(v)])[:16],'math':tex(v),'misconception':why}for v,why in chosen];values=[parse(c['math'])for c in choices];certs=[]
 for j,k in itertools.combinations(range(4),2):
  diff=s.factor_terms(s.expand_func(values[j]-values[k]));iv=enclose(diff);assert iv[0]>0 or iv[1]<0;certs.append({'choiceIds':[choices[j]['choiceId'],choices[k]['choiceId']],'difference':s.srepr(diff),'outwardRationalEnclosure':dump(iv)})
 assert next(c for c in choices if c['choiceId']==r['answerChoiceId'])==correct
 poolreport=[{'expression':s.srepr(v),'math':tex(v),'misconception':why,'belowAnswer':v in[q[0]for q in lo]}for v,why in pool]
 actualLevel=r['difficulty'];levelNote='No new advanced idea or extra instance is claimed by changing alternatives.'
 if slug=='dyadic-infinite-product'and target==3:
  actualLevel='medium';levelNote='These three lower alternatives are eliminated by the first three positive factors plus convergence of the infinite product; the actual menu admits a shorter Medium route.'
 return {'patchVersion':VERSION,'problemId':r['problemId'],'familyId':r['familyId'],'instanceIndex':i,'sourceRevision':r['problemRevision'],'sourceContentHash':r['contentHash'],'sourceSemanticHash':r['semanticHash'],'sourceRawSHA256':H(r),'sourceChoicesSHA256':H(r['choices']),'choices':choices,'answerChoiceId':r['answerChoiceId'],'preservedCorrectChoice':correct,'replacedChoices':copy.deepcopy(r['choices']),'authoredMisconceptionPool':poolreport,'mathematicalChecks':checks,'sixChoiceInequalityCertificates':certs,'correctNumericRank':target+1,'feasibleRanks':[1,2,3,4],'elementaryBound':None if bound is None else{'interval':list(map(str,bound)),'wrongSurvivors':[c['choiceId']for c,v in zip(choices,values)if c['choiceId']!=r['answerChoiceId']and bound[0]<v<bound[1]]},'recommendedDifficulty':actualLevel,'difficultyNote':levelNote,'reason':'The old finite pool restricted the answer to one half of the numeric ranks. Additional named errors allow all four ranks. The original mathematics, correct choice, question and explanation remain unchanged.','meaningChanged':False,'preserveStatementSolutionAndLineage':True,'newIndependentIdeas':0,'reviewStatus':'candidate-awaiting-independent-parent-review','humanReviewed':False,'formalProof':False}
def verify_patch(patch,record):
 try:return canonical(patch)==canonical(build_patch(record))
 except(ValueError,KeyError,AssertionError,StopIteration):return False
if __name__=='__main__':
 rows=[build_patch(r)for _,r in sorted(originals().items())];assert len(rows)==76
 (BASE/'support-option-patches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(rows),'pairCertificates':sum(len(r['sixChoiceInequalityCertificates'])for r in rows),'recommendedMediumDemotions':[(r['familyId'],r['instanceIndex'])for r in rows if r['recommendedDifficulty']=='medium'and originals()[r['problemId']]['difficulty']=='hard']}))
