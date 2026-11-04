"""Independent literal mathematics/editorial review of the final76 series overlays.
No author constructor, answer-expression field, or author interval oracle is used.
"""
from pathlib import Path
from fractions import Fraction as Q
from functools import lru_cache
import json,hashlib,re,itertools,sys,collections
import sympy as s
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application
from rational_intervals import add,mul,power
from series_intervals import enclose as base_enclose,rounded
P=Path(__file__).resolve().parent
H=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
fh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def parse(tex):
 # Restricted root numeric grammar, explicitly extended only for zeta at
 # positive integer arguments and its printed integer powers.
 v=tex
 for command in [r'\left',r'\right',r'\,',r'\!',r'\ ']:v=v.replace(command,'')
 v=v.replace(r'\pi',' pi ')
 def group(pos):
  assert v[pos]=='{',tex
  depth=1;j=pos+1
  while depth:
   assert j<len(v),tex
   depth+=(v[j]=='{')-(v[j]=='}');j+=1
  return v[pos+1:j-1],j
 v=re.sub(r'\\zeta\^\{(\d+)\}\((\d+)\)',lambda m:'(zeta('+m[2]+'))**'+m[1],v).replace(r'\zeta',' zeta ')
 while r'\frac'in v or r'\sqrt'in v:
  i,cmd=min((v.index(cmd),cmd)for cmd in[r'\frac',r'\sqrt']if cmd in v);a,j=group(i+len(cmd))
  if cmd==r'\frac':b,j=group(j);rep='(('+a+')/('+b+'))'
  else:rep='sqrt('+a+')'
  v=v[:i]+rep+v[j:]
 v=v.replace('{','(').replace('}',')').replace('^','**');assert re.fullmatch(r'[0-9\sA-Za-z()+*/.,\-]+',v),tex;assert set(re.findall(r'[A-Za-z]+',v))<={'pi','zeta','sqrt'},tex
 out=parse_expr(v,local_dict={'pi':s.pi,'zeta':s.zeta,'sqrt':s.sqrt},transformations=standard_transformations+(implicit_multiplication_application,));assert not out.free_symbols
 for z in out.atoms(s.zeta):assert z.args[0].is_Integer and z.args[0]>1
 return out
@lru_cache(None)
def zeta_interval(n):
 assert n>=3;N=128;partial=sum((Q(1,k**n)for k in range(1,N+1)),Q(0));return rounded((partial+Q(1,(n-1)*(N+1)**(n-1)),partial+Q(1,(n-1)*N**(n-1))))
def bounds(v):
 if v.func==s.zeta:return zeta_interval(int(v.args[0]))
 if v.is_Add:
  out=(Q(0),)*2
  for t in v.args:out=rounded(add(out,bounds(t)))
  return out
 if v.is_Mul:
  out=(Q(1),)*2
  for t in v.args:out=rounded(mul(out,bounds(t)))
  return out
 if v.is_Pow and v.exp.is_Integer:return rounded(power(bounds(v.base),int(v.exp)))
 return base_enclose(v)
def equal(a,b):return s.simplify(s.expand_func(a-b))==0
@lru_cache(None)
def cycle_trace(n,antiperiodic=False):
 M=3*s.eye(n)
 for k in range(n-1):M[k,k+1]=M[k+1,k]=-1
 M[0,n-1]=M[n-1,0]=1 if antiperiodic else -1
 inv=M.inv(method='DM');assert M*inv==s.eye(n)
 return 2*s.trace(inv)
def derive(q,old):
 f=q['familyId'];t=old['statement'];x=s.symbols('x',real=True);checks=[];pars={};analytic=[]
 def ck(name,a,b):assert equal(a,b),(name,a,b);checks.append({'description':name,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
 if f.endswith('nth-term-test'):
  m=s.Integer(re.search(r'\\frac\{(\d+)k\+1\}\{k\+2\}',t)[1]);A=m;ck('Literal rational-sequence limit',s.limit((m*x+1)/(x+2),x,s.oo),A);route='Divide numerator and denominator by the index, then let its reciprocal tend to zero.';level='easy';nearest='Dominant linear terms, not a convergence claim about the sum; the statement asks only for the term limit.'
 elif f.endswith('easy-power-series-radius'):
  m=s.Integer(re.search(r'\\frac\{x\}\{(\d+)\}',t)[1]);A=m;route='The geometric series converges exactly when |x/m|<1, so its radius is m.';level='easy';nearest='The factorial-ratio radius family requires a coefficient quotient limit; this is a direct geometric ratio.'
 elif f.endswith('dyadic-infinite-product'):
  m=s.Integer(re.search(r'\\frac\{1\}\{(\d+)\}',t)[1]);r=1/m;A=1/(1-r);N=5;ck('Finite difference-of-squares telescope',(1-x)*s.prod(1+x**(2**k)for k in range(N)),1-x**(2**N));route='Multiply a finite product by1−q to telescope successive differences of squares, then use q^(2^N)→0.';level='medium'if q['instanceIndex']in[1,5,9]else'hard';nearest='A binary product telescope shares its binary expansion identity with the integration product family; it is not a new idea from changing m.';analytic=['0<q=1/m<1. The exact finite product identity gives convergence and its positive limit.']
 elif f.endswith('power-series-ratio-radius'):
  m=s.Integer(re.search(r'\((\d+)x\)\^k',t)[1]);A=4/m;k=s.symbols('k',positive=True);ratio=m*(k+1)**2/((2*k+2)*(2*k+1));ck('Limiting literal factorial-coefficient quotient',s.limit(ratio,k,s.oo),m/4);route='Cancel consecutive factorial coefficients and take the quotient limit; the radius is its reciprocal.';level='medium';nearest='Unlike a geometric radius, the factorial quotient must first be reduced; endpoint convergence is irrelevant to the radius.'
 elif f.endswith('quadratic-weight'):
  m=s.Integer(re.search(r'(\d+)\^\{- k\}',t)[1]);G=1/(1-x);E=x*s.diff(G,x);E2=s.factor(x*s.diff(E,x));A=m*(m+1)/(m-1)**3;ck('Two Euler derivatives',E2,x*(1+x)/(1-x)**3);ck('Literal reciprocal-base substitution',E2.subs(x,1/m),A);route='Apply x*d/dx twice to the geometric series, then substitute the displayed reciprocal base.';level='medium';nearest='One Euler derivative gives a linear weight; the displayed square requires the second product-rule contribution.';analytic=['The geometric power series and both derivatives converge uniformly on compact subsets of |x|<1, and1/m lies inside that disk.']
 elif f.endswith('totient-Lambert'):
  m=s.Integer(re.search(r'\}\{(\d+)\^k-1\}',t)[1]);A=m/(m-1)**2
  for n in range(1,33):ck('Finite divisor-identity check n='+str(n),sum(s.totient(d)for d in s.divisors(n)),s.Integer(n))
  ck('Arithmetic-geometric sum formula',(x*s.diff(1/(1-x),x)).subs(x,1/m),A);route='With the actual options, bound the positive sum between its first term and a geometric majorant using φ(k)≤k≤2^(k−1); these bounds isolate the answer without the divisor identity.';level='medium';nearest='The intended Lambert regrouping uses Σ_{d|n}φ(d)=n, but this menu does not require that decision.';analytic=['Partition the integers1..n by gcd with n to prove Σ_{d|n}φ(d)=n for every n; finite checks only illustrate the identity. All summands are nonnegative, so Tonelli permits divisor regrouping. φ(k)≤k also supplies an absolutely convergent majorant.']
 elif f.endswith('Liouville-Dirichlet-product'):
  m=s.Integer(re.search(r'\}\{n\^\{(\d+)\}\}',t)[1]);A=s.zeta(2*m)/s.zeta(m)
  for n in range(1,49):ck('Square-support convolution check n='+str(n),sum((-1)**sum(s.factorint(d).values())for d in s.divisors(n)),s.Integer(int(s.integer_nthroot(n,2)[1])))
  route='Convolve the Liouville sequence with1. At every prime power the alternating divisor sum is1 for even exponent and0 for odd exponent, so the convolution is the square indicator. Absolute Dirichlet multiplication gives S*zeta(s)=zeta(2s).';level='hard';nearest='This is the arithmetic-convolution counterpart of an Euler product, not the totient divisor-sum identity; the requested exponent changes the finite exact value.';analytic=['The literal exponent s is an integer≥2. Since |lambda(n)|=1, the Dirichlet series is absolutely convergent, so its convolution with the positive zeta series is justified. zeta(s)>0 permits division. Even zeta values are evaluated by the classical Bernoulli-number formula.']
 else:
  assert f.endswith('finite-cycle-resolvent');m=s.Integer(re.search(r'cos\(2\\pi k/(\d+)\)',t)[1]);assert r'\frac32' in t and int(re.search(r'\\sum_\{k=0\}\^\{(\d+)\}',t)[1])==m-1;A=cycle_trace(int(m));checks.append({'description':'Exact inverse residual for the integer cyclic matrix','dimension':int(m),'result':'M times its independently computed rational inverse equals the identity matrix'});route='Diagonalize the cyclic shift by Fourier modes:2*trace((3I−adjacency)^(-1)) is the displayed sum. Exact rational matrix inversion supplies a separate answer oracle.';level='hard'if q['instanceIndex']in[0,4]else'olympiad';nearest='A periodic finite resolvent needs a global Fourier/characteristic-polynomial decision. The antiperiodic counterpart is a substantive competing boundary condition; indices0/4 omit it and are isolated by low cosine moments.';analytic=['Every denominator is at least1/2. The cyclic Fourier eigenvectors give adjacency eigenvalues2*cos(2*pi*k/n), so the matrix is invertible and its inverse trace equals the sum. The antiperiodic matrix changes only the wraparound edge sign and corresponds to odd half-grid angles.']
 pars['literalScaleOrOrder']=int(m)
 if not analytic:analytic=['All displayed scales are positive, and the asserted familiar limit or ratio test is used in its real domain.']
 return A,pars,checks,route,level,nearest,analytic

def misconception_values(f,m,A):
 if f.endswith('nth-term-test'):v=[0,1,1/m,2*m,m*m,m+1]
 elif f.endswith('easy-power-series-radius'):v=[1/m,1,m/(m-1),2*m,m*m,m*m/(m-1)]
 elif f.endswith('dyadic-infinite-product'):v=[1+1/m,(1+1/m)*(1+1/m**2),m/(m+1),m/(m-2),A*(1+1/m),A*(1+1/m**2)]
 elif f.endswith('power-series-ratio-radius'):v=[1/(4*m),2/m,1/m,4*m,8/m,16/m]
 elif f.endswith('quadratic-weight'):v=[m/(m-1)**2,m*m/(m-1)**3,(m+1)/(m-1)**3,A+1/m,A*m/(m-1),m*(m*m+4*m+1)/(m-1)**4]
 elif f.endswith('totient-Lambert'):v=[1/(m-1)**2,1/(m-1),m/(m+1)**2,m*m/(m-1)**2,2*A,m*(m+1)/(m-1)**3]
 elif f.endswith('Liouville-Dirichlet-product'):v=[1/s.zeta(m),1/(s.zeta(m)*s.zeta(2*m)),s.zeta(2*m)/s.zeta(m)**2,1/s.zeta(2*m),1/A,s.zeta(2*m)]
 else:v=[cycle_trace(int(m),True),A/m,1/A,A-2,A*m,A+2,2*A-2]
 return list(map(s.sympify,v))

def shortcut(q,m,vals):
 f=q['familyId'];out=[];answer=next(i for i,c in enumerate(q['choices'])if c['choiceId']==q['answerChoiceId'])
 if f.endswith('totient-Lambert'):
  L=1/(m-1);U=m/((m-1)*(m-2));tight=m*m/(m-1)**3;assert L<vals[answer]<U
  for i,v in enumerate(vals):
   if i!=answer:assert v<=L or v>U
  out=[{'kind':'certified-options-visible-geometric-bound','strictLower':str(L),'upper':str(U),'tighterStrictUpper':str(tight),'uniqueChoiceInside':q['choices'][answer]['choiceId'],'excludedChoices':[{'choiceId':c['choiceId'],'lowerDifference':str(vals[i]-L),'upperDifference':str(vals[i]-U)}for i,c in enumerate(q['choices'])if i!=answer],'proof':'S>the k=1 term. For every k, φ(k)≤k≤2^(k−1) and1/(m^k−1)≤m^(−k)/(1−1/m); sum the resulting geometric series. Using k directly gives the sharper strict upper m²/(m−1)^3. All inequalities are exact rational comparisons.','recommendedDifficulty':'medium'}]
 elif f.endswith('dyadic-infinite-product')and q['instanceIndex']in[1,5,9]:
  L=s.prod(1+m**(-2**k)for k in range(3));assert all(v<L for i,v in enumerate(vals)if i!=answer)and vals[answer]>L;out=[{'kind':'finite-positive-product-lower-bound','threeFactorLower':str(L),'strictlyBelowCorrect':str(vals[answer]-L),'wrongChoiceDifferences':[str(v-L)for i,v in enumerate(vals)if i!=answer],'proof':'The first3 positive factors already exceed every wrong option, and every later factor is greater than1. Convergence follows from summable logarithms or the finite telescope.','recommendedDifficulty':'medium'}]
 elif f.endswith('finite-cycle-resolvent')and q['instanceIndex']in[0,4]:
  L=m*s.Rational(70,81);U=m*s.Rational(670,729);assert L<vals[answer]<U;assert all(v<L or v>U for i,v in enumerate(vals)if i!=answer);out=[{'kind':'finite-cosine-moment-geometric-remainder','strictLower':str(L),'strictUpper':str(U),'choiceComparisons':[{'lowerDifference':str(v-L),'upperDifference':str(v-U)}for v in vals],'proof':'For n>6, discrete Fourier orthogonality gives odd cosine moments0 through degree5 and even moments1/2,3/8,5/16 through degree6. Expand1/(3/2−c)=(2/3)*Σ_{j=0}^5(2c/3)^j+(2c/3)^6/(3/2−c). Its remainder is nonnegative and at most2*(2c/3)^6. Summing gives n*70/81<S<n*670/729 and exactly excludes the actual wrong choices.','recommendedDifficulty':'hard'}]
 return out

def main(folder,out):
 source=Path(folder);patchbytes=(source/'support-option-patches.json').read_bytes();assert hashlib.sha256(patchbytes).hexdigest()=='cd251b4e864fbb178fa13f5f1050fab2c0df7a98a3cb9e31f78eaad90430b7df';oldbytes=(source/'full-source-records.jsonl').read_bytes();originals={r['problemId']:r for r in map(json.loads,oldbytes.splitlines())};records=[];failures=[]
 for q in json.loads(patchbytes):
  try:
   old=originals[q['problemId']];assert H(old)==q['sourceRawSHA256']and old['contentHash']==q['sourceContentHash']and old['semanticHash']==q['sourceSemanticHash']and H(old['choices'])==q['sourceChoicesSHA256'];assert q['meaningChanged']is False and q['preserveStatementSolutionAndLineage']is True
   A,pars,checks,route,level,nearest,analytic=derive(q,old);vals=[parse(c['math'])for c in q['choices']];matches=[i for i,v in enumerate(vals)if equal(v,A)];assert len(matches)==1 and q['choices'][matches[0]]['choiceId']==q['answerChoiceId'];assert next(c for c in old['choices']if c['choiceId']==old['answerChoiceId'])==q['choices'][matches[0]]
   pairs=[]
   for a,b in itertools.combinations(vals,2):
    lo,hi=bounds(a-b);assert lo>0 or hi<0,('Unseparated options',a,b,lo,hi);pairs.append({'lower':str(lo),'upper':str(hi)})
   m=s.Integer(pars['literalScaleOrOrder']);wrong=misconception_values(q['familyId'],m,A);pool=q['authoredMisconceptionPool'];assert len(wrong)==len(pool);mistakes=[]
   for expected,item in zip(wrong,pool):
    literal=parse(item['math']);assert equal(literal,expected),(item['misconception'],literal,expected);mistakes.append({'misconception':item['misconception'],'independentlyReconstructedValue':s.srepr(expected),'literalPoolValueMatched':True})
   for c in q['choices']:
    if c['choiceId']!=q['answerChoiceId']:assert any(c['misconception']==item['misconception']and equal(parse(c['math']),parse(item['math']))for item in pool)
   visible=shortcut(q,m,vals);records.append({'problemId':q['problemId'],'familyId':q['familyId'],'index':q['instanceIndex'],'sourceRawSHA256':q['sourceRawSHA256'],'sourceContentHash':q['sourceContentHash'],'sourceSemanticHash':q['sourceSemanticHash'],'patchSHA256':H(q),'independentAnswer':s.srepr(A),'literalCorrectChoiceUnchanged':True,'sixLiteralPairEnclosures':pairs,'independentIntermediateChecks':checks,'namedMisconceptionChecks':mistakes,'easiestOptionsVisibleRoute':visible[0]['proof']if visible else route,'fullDerivationRoute':route,'analyticConditions':analytic,'nearestNeighbor':nearest,'recommendedDifficulty':level,'authorRecommendedDifficulty':q['recommendedDifficulty'],'difficultyDisagreement':level!=q['recommendedDifficulty'],'qualifiedOlympiad':level=='olympiad','shortcutCertificates':visible,'newIndependentIdeas':0,'preserveLineage':True,'passed':True})
  except Exception as e:failures.append({'problemId':q['problemId'],'familyId':q['familyId'],'index':q['instanceIndex'],'error':type(e).__name__+': '+str(e)})
 deps=['series_last76_peer.py','series_intervals.py','rational_intervals.py'];report={'author':'source_research','reviewer':'integration_research','sourcePath':str(source.resolve()),'inputSHA256':hashlib.sha256(patchbytes).hexdigest(),'originalsSHA256':hashlib.sha256(oldbytes).hexdigest(),'reviewCodeSHA256':{f:fh(P/f)for f in deps},'counts':{'attempted':len(json.loads(patchbytes)),'passed':len(records),'failed':len(failures),'literalPairInequalities':6*len(records),'independentIntermediateChecks':sum(len(r['independentIntermediateChecks'])for r in records),'namedMisconceptionsChecked':sum(len(r['namedMisconceptionChecks'])for r in records)},'records':records,'failures':failures,'scope':'Independent literal statement/choice derivations and exact outward rational comparisons. Correct-choice labels and author family names were visible, so this is not fully blind. No author constructor or expression field is used as an oracle; authored misconception names are read only after the statement-first routes were recorded. Zeta bounds use an independently written finite Dirichlet sum plus integral-test tail; existing root pi/rational interval arithmetic is reused as infrastructure. Analytic obligations and editorial levels are separate from exact identities. No human/formal certification or final combined-ID screen approval is claimed.','remaining':'The all8 totient and2 cycle menu difficulty blockers require immutable metadata dispositions or separately reviewed option amendments. The final actual-ID per-family/per-form screen remains separate.'}
 family_reviews=[]
 for f in sorted({r['familyId']for r in records}):
  rr=[r for r in records if r['familyId']==f]
  family_reviews.append({'familyId':f,'records':len(rr),'nearestNeighbor':rr[0]['nearestNeighbor'],'easiestOptionsVisibleRoutes':sorted({r['easiestOptionsVisibleRoute']for r in rr}),'recommendedDifficultyByIndex':{str(r['index']):r['recommendedDifficulty']for r in rr},'difficultyRationale':'Classified from the actual menu. Exact bounds lower the level where they isolate one option; finite parameter size creates no new idea or difficulty credit. Other cases retain the recorded representation or convergence decision.','newIndependentIdeas':0})
 report['familyReviews']=family_reviews
 stale=[]
 for q in records:
  old=originals[q['problemId']]
  if any('Here 'in v or 'Here }m='in v for v in old['solutionSteps']):stale.append({k:q[k]for k in ['problemId','familyId','index','sourceRawSHA256','sourceContentHash']})
 report['presentationInheritance']={'requiredForAll76':True,'sourceRawHistoricalGenericPrefaces':stale,'count':len(stale),'rule':'Apply the existing exact-source current statement/solution presentation before creating a new option revision. Do not copy historical generic steps into a new hash and assume the old presenter guard will match. This review does not assert the eventual canonical stage has regressed; source guards themselves remain immutable.'}
 first=Path(out).with_name('last76-statement-first-review.json');report['statementFirstEvidenceSHA256']=fh(first)
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']));print(json.dumps(failures));return not failures
if __name__=='__main__':raise SystemExit(0 if main(*sys.argv[1:])else 1)
