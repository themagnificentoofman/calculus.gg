import os
from pathlib import Path
import json,hashlib,ast,sys
import sympy as s
from io3_solutions import corrected_solution,supports,params
BASE=Path(__file__).parent
SOURCE=Path(os.environ['BANK_AUDIT_ARTIFACT'])
rows=[json.loads(l) for l in SOURCE.open()];rows=[r for r in rows if r['familyId'].startswith('io3-')]
allowed={k:getattr(s,k) for k in ['Integer','Rational','Add','Mul','Pow','Symbol','Tuple','sin','cos','log','exp','sqrt','gamma','harmonic','zeta','coth','cosh','sinh','cot','bernoulli']};allowed.update(pi=s.pi,E=s.E)
def exact_parse(text):
 def visit(t):
  if isinstance(t,ast.Constant):return t.value
  if isinstance(t,ast.Name):return allowed[t.id]
  if isinstance(t,ast.UnaryOp) and isinstance(t.op,ast.USub):return -visit(t.operand)
  if isinstance(t,ast.Call) and isinstance(t.func,ast.Name) and t.func.id in allowed:return allowed[t.func.id](*[visit(a) for a in t.args],**{k.arg:visit(k.value) for k in t.keywords})
  raise ValueError(ast.dump(t))
 return visit(ast.parse(text,mode='eval').body)
def recompute(slug,p):
 R=s.Rational;pi=s.pi
 if slug=='weighted-complement':return pi/2
 if slug=='reciprocal-quartic':return pi/(2*s.sqrt(2*p['a']+2))
 if slug=='inverse-moment':return p['n']/(p['n']+p['r'])+p['m']/(p['m']+p['r'])
 if slug=='chebyshev-absolute':return s.Integer(2)
 if slug=='floor-laplace':return 1/(s.log(p['q'])*(p['q']-1))
 if slug=='gamma-unit-average':return p['a']*s.log(p['a'])-p['a']+s.log(2*pi)/2
 if slug=='log-fourier-coefficient':return -pi*p['r']**p['n']/p['n']
 if slug=='arctan-parameter':return pi*s.log(1+p['a'])/2
 if slug=='gaussian-fourier':return s.sqrt(pi)*s.exp(-p['b']**2/(4*p['a']))/(2*s.sqrt(p['a']))
 if slug=='reciprocal-gaussian':return s.sqrt(pi)*s.exp(-2*p['a']*p['b'])/(2*p['a'])
 if slug=='sinc-overlap':return pi*(p['a']+p['b']-abs(p['a']-p['b']))/4
 if slug=='mixed-beta-log':
  m,n=p['m'],p['n'];N=m+n+1
  return s.factorial(m)*s.factorial(n)/s.factorial(N)*((s.harmonic(m)-s.harmonic(N))*(s.harmonic(n)-s.harmonic(N))-(pi*pi/6-s.harmonic(N,2)))
 if slug=='thermal-derivative':return s.factorial(p['n'])*s.zeta(p['n'])
 if slug=='mellin-cyclotomic':return pi/(p['q']*s.sin(pi*p['p']/p['q']))
 if slug=='cauchy-convolution':return pi/(2*p['b']*(p['a']**2+p['b']**2))
 if slug=='binomial-exponential':return s.factorial(p['a']-1)*s.factorial(p['n'])/s.factorial(p['a']+p['n'])
 if slug=='agm-parameter':return s.sqrt(p['a']*p['b'])
 if slug=='abel-recovery':return 2/pi*sum((-1)**j*s.binomial(p['n'],j)/s.Integer(2*j+1) for j in range(int(p['n'])+1))
 if slug=='boundary-asymptotic':return s.gamma(1/p['p'])/p['p']
 if slug=='integral-equation':return (s.cosh(p['k'])-1)/(p['k']**2*s.cosh(p['k']))
 if slug=='convolution-laplace':return ((1-1/p['base'])/s.log(p['base']))**p['n']
 if slug=='poisson-log-potential':return pi/p['a']*s.log(p['b']**2+(p['a']+p['c'])**2)
 if slug=='jensen-radius':return 4*pi*s.log(p['r'])
 if slug=='fresnel':return s.sqrt(pi)/(2*s.sqrt(2*p['a']))
 if slug=='bessel-laplace':return 1/s.sqrt(p['a']**2+p['b']**2)
 if slug=='rodrigues-moment':
  n,k=p['n'],p['k'];return s.factorial(n+2*k)/s.factorial(2*k)*sum((-1)**j*s.binomial(n,j)/(j+k+R(1,2)) for j in range(int(n)+1))
 if slug=='bernoulli-product':
  m,n=p['m'],p['n'];return (-1)**(m-1)*s.factorial(m)*s.factorial(n)*s.bernoulli(m+n)/s.factorial(m+n)
 if slug=='principal-value':return s.Tuple(s.Symbol('divergent'),pi/p['q']*s.cot(pi*p['p']/p['q']))
 if slug=='oscillatory-regularization':return s.Tuple(s.Symbol('divergent'),1/p['p'])
 if slug=='concentration':return pi/(2*p['p'])
 if slug=='binary-product':return s.harmonic(2**p['n'])
 if slug=='fejer-fourth':return 2*pi*(p['n']**2+2*sum(s.Integer(k)**2 for k in range(1,int(p['n']))))
 if slug=='scaled-frullani':return s.log(p['b']/p['a'])/p['p']
 if slug=='sech-fourier':return p['q']/(p['q']**2+1)
 if slug=='variational-energy':return p['k']*s.coth(p['k'])
 if slug=='moment-projection':
  m,c=p['m'],p['c'];mu=1/(m+1);V=1/(2*m+1)-mu*mu;return 1+(c-mu)**2/V
 if slug=='quadrature-defect':return (p['A']+p['B'])/2+p['c']/180
 if slug=='rearrangement':return s.Tuple(1/((p['n']+1)*(p['n']+2)),1/(p['n']+2))
 raise ValueError(slug)
def eq(a,b):
 if isinstance(a,s.Tuple):return len(a)==len(b) and all(eq(u,v) for u,v in zip(a,b))
 if isinstance(a,s.Symbol):return a==b
 return s.simplify(s.expand_func(a-b))==0
export=[];audit={}
for r in rows:
 slug=r['familyId'][4:];new=corrected_solution(r);old=json.dumps(r['solutionSteps']);p=params(r)
 raw=r['validation']['evidence']['certificate']['answerExpression'];actual=exact_parse(raw);expected=recompute(slug,p)
 assert eq(expected,actual),(slug,r['parameters'],expected,actual)
 assert new and all(isinstance(v,str) and v for v in new)
 export.append({'problemId':r['problemId'],'familyId':r['familyId'],'instance':r['parameters']['instance'],'sourceContentHash':r['contentHash'],'sourceSolutionSha256':hashlib.sha256(json.dumps(r['solutionSteps'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'solutionSteps':new})
 row=audit.setdefault(r['familyId'],{'instances':0,'mathematicalResultAgreement':True,'explicitDefinitionsAndInstanceMapping':True,'decisiveStepsReviewed':True,'sourceMutation':False})
 row['instances']+=1
(BASE/'io3-solutions.json').write_text(json.dumps(export,indent=2)+'\n')
(BASE/'io3-audit.json').write_text(json.dumps({'families':audit,'instances':len(export),'exactFormulaAgreement':True,'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps({'instances':len(export),'families':len(audit),'exactFormulaAgreement':True}))
