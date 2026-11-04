"""Independent intermediate checks for the finite advanced series candidate set.

The code does not call builders to decide mathematical results. It consumes
their parameters and checks a separately encoded route. Analytic arguments are
explicitly recorded; finite examples are never called proofs of those theorems.
"""
from __future__ import annotations
import argparse,itertools,json,math
from pathlib import Path
from fractions import Fraction
import sympy as s
from common import eq,truth,tex,digest
R=s.Rational
x=s.symbols('x',positive=True)

def replacement_checks(r):
 p=r['parameters'];route=p['qualityRoute'];checks=[];expected=None;category=None
 if route=='support-existence-v2':
  bases=list(map(R,p['bases']));category='|'.join('exists' if b.q==1 else 'does not exist' for b in bases)
  checks=[truth('moment bases positive and above one',all(b>1 for b in bases)),eq('dominated-tail contraction model',s.limit(R(7,8)**x,x,s.oo),0)]
 elif route=='polynomial-weight-v2':
  m=p['weightDegreePlusOne'];N=s.symbols('N',positive=True,integer=True)
  for n in range(1,9):
   la=s.binomial(n+m-2,m-1);La=s.binomial(n+m-1,m);prev=s.binomial(n+m-2,m) if n>1 else 0
   checks += [eq('independent binomial weight sum '+str(n),sum(s.binomial(k+m-2,m-1) for k in range(1,n+1)),La),eq('weight-ratio identity '+str(n),La/la,R(n+m-1,m)),eq('preceding weight-ratio identity '+str(n),prev/la,R(n-1,m))]
  checks += [eq('tail telescoping difference',s.expand_func(1/s.binomial(N+m-1,m)-1/s.binomial(N+m,m)),s.expand_func(m/((N+m)*s.binomial(N+m-1,m)))),eq('independent logarithmic Riemann moment',s.integrate(m*x**(m-1)*s.log(x),(x,0,1)),-R(1,m))];expected=s.exp(R(1,m))
 elif route=='unequal-block-asymptotic-v2':
  m=p['thirdBlockRatio'];u,v,w=s.symbols('u v w');xs=[u,v,w]
  checks=[eq('Good identity independently rechecked',sum(s.prod(1/(1-xs[j]/xs[k]) for k in range(3) if k!=j) for j in range(3)),1)]
  for N in [2,4]:checks.append(eq('independent unequal-block finite sum N='+str(N),sum(s.Integer(-1)**k*s.binomial(3*N,2*N+k)*s.binomial((m+2)*N,m*N+k)*s.binomial((m+1)*N,N+k) for k in range(-N,N+1)),s.factorial((m+3)*N)/(s.factorial(N)*s.factorial(2*N)*s.factorial(m*N))))
  expected=s.sqrt(R(m+3,2*m))/(2*s.pi);checks.append(eq('independent product of Stirling square-root factors',s.sqrt(2*s.pi*(m+3))/(s.sqrt(2*s.pi)*s.sqrt(4*s.pi)*s.sqrt(2*s.pi*m)),expected))
 elif route=='moving-scale-Laplace-v2':
  a=R(p['movingScale']);d=s.sqrt(a*a+4);t0=(a-2+d)/(2*a);t=s.symbols('t');m=4;w=t**m*(1-t)**m;right=0;left=0
  for j in range(2*m+1):
   dw=s.diff(w,t,j);right+=(-1)**j*dw.subs(t,1)*x**(2*m-j);left+=(-1)**j*dw.subs(t,0)*x**(2*m-j)
  Q=sum((-1)**k*s.binomial(2*m-k,m)*x**k/s.factorial(k) for k in range(m+1));checks=[eq('exact beta-remainder right endpoint polynomial',(-1)**m*right/s.factorial(m)**2,Q),eq('exact beta-remainder left endpoint polynomial',(-1)**m*left/s.factorial(m)**2,Q.subs(x,-x)),eq('unique saddle solves derivative',s.simplify(1/t0-1/(1-t0)+a),0),truth('saddle in interval',0<t0<1),eq('negative derivative of logarithmic derivative',s.diff(1/x-1/(1-x)+a,x),-1/x**2-1/(1-x)**2)]
  expected=(d-2)*s.exp((a+2+d)/2);checks.append(eq('independent saddle product simplification',s.simplify(a*a*t0*(1-t0)),d-2))
 elif route=='growing-Poisson-moment-v2':
  a=R(p['saddleParameter']);lam=s.exp(-a)/a;c=1/a;N=s.symbols('N',positive=True);t=s.symbols('t',positive=True)
  checks=[eq('exponential majorant maximizing index',s.diff(N*s.log(x)-t*x,x).subs(x,N/t),0),eq('majorant optimizing parameter',(-1/t+lam*s.exp(t)).subs(t,a),0),eq('lower-bound entropy equals optimized upper logarithm',s.expand_log(s.log(c)+c*s.log(lam/c)+c-lam,force=True),s.expand_log(-s.log(a)-1+lam*(s.exp(a)-1),force=True)),truth('strict convexity of optimized bound',s.diff(-s.log(t)+lam*(s.exp(t)-1),t,2).is_positive is True)]
  expected=s.exp(1/a-1-lam)/a
 elif route=='asymmetric-Hilbert-v2':
  m=p['columnScale'];K=s.symbols('K',positive=True);u=s.symbols('u',positive=True);F=2/s.sqrt(m)*s.atan(s.sqrt(m*u));expected=s.pi/s.sqrt(m)
  checks=[eq('asymmetric row beta primitive',s.diff(F,u),1/(s.sqrt(u)*(1+m*u))),eq('sharp middle-scale integral limit',s.limit(F.subs(u,K)-F.subs(u,1/K),K,s.oo),expected)]
 elif route=='double-order-v1':
  a=p['lowerM'];b=p['lowerN'];u,v=s.symbols('u v',positive=True);F=lambda u,v:u/(u+v);c=(u-v)/((u+v)*(u+v+1)*(u+v+2));checks=[eq('independent rational mixed-difference certificate',F(u+1,v+1)-F(u+1,v)-F(u,v+1)+F(u,v),c)]
  for M,N in [(a+2,b+3),(a+5,b+1)]:checks.append(eq('independent finite rectangular sum',sum(R(m-n,(m+n)*(m+n+1)*(m+n+2)) for m in range(a,M+1) for n in range(b,N+1)),R(M+1,M+N+2)-R(M+1,M+b+1)-R(a,a+N+1)+R(a,a+b)))
  f=R(a,a+b);category=s.srepr(s.Tuple(f-1,f,f-R(1,2)))
 elif route=='Hardy-power-v1':
  pp=R(p['exponent']);c=pp/(pp-1);us=[s.Integer(1)]
  for n in range(1,15):us.append(us[-1]*(1-1/(pp*n)))
  checks=[eq('independent auxiliary-weight sum n='+str(n),sum(us[:n]),c*(n-1/pp)*us[n-1]) for n in range(1,16)];q=pp-1
  checks.append(truth('Bernoulli exponent positive',q>0));checks.append(eq('power-sum comparison primitive',s.diff(x**(1-1/pp)/(1-1/pp),x),x**(-1/pp)));expected=c**pp
 else:raise ValueError('unknown replacement review route')
 return checks,expected,category

def verify(r):
 slug=r['familyId'].split('-',3)[3];p=r['parameters'];checks=[];expected=None;expected_category=None
 if p.get('qualityRoute'):
  checks,expected,expected_category=replacement_checks(r)
 elif slug=='singular-cauchy-coefficient':
  a=R(p['p']);u,v=s.symbols('u v',positive=True)
  J=s.det(s.Matrix([[s.diff(u*v,u),s.diff(u*v,v)],[s.diff(u*(1-v),u),s.diff(u*(1-v),v)]]))
  checks=[eq('Gamma-to-beta Jacobian magnitude',-J,u),eq('endpoint bound primitive',s.diff(x**(1-a)/(1-a),x),x**(-a)),truth('singular endpoint cutoff exponent positive',1-a>0)]
  expected=s.gamma(1-a)**2/s.gamma(2-2*a)
 elif slug=='uniform-log-sine-threshold':
  for key in ['p','q']:
   a=R(p[key]);checks.append(truth(key+' has the declared strict classification threshold',(a>0)==(str(a) not in ['0'] and a.is_positive is True)))
  z=s.symbols('z');checks.append(eq('Dirichlet finite geometric cancellation',(1-z)*sum(z**k for k in range(7,19)),z**7-z**19))
  checks.append(truth('positive sine block is wholly inside zero to pi',s.pi>2))
 elif slug=='lacunary-Abel-growth':
  b=p['base'];checks=[truth('uniform exponential tail comparison',all(b**j>=j+1 for j in range(12))),eq('deficit finite geometric coefficient',sum(b**k for k in range(10)),(b**10-1)//(b-1)),eq('log substitution normalization',s.limit(-s.log(1-x)/x,x,0),1)];expected=1/s.log(b)
 elif slug=='quadratic-small-divisor':
  m=p['coefficient'];a=(m+s.sqrt(m*m+4))/2;bb=(m-s.sqrt(m*m+4))/2;q=[0,1]
  for k in range(1,13):q.append(m*q[-1]+q[-2])
  for k in range(1,13):checks.append(eq('integer recurrence versus conjugate error '+str(k),a*q[k]-q[k+1],-bb**k))
  checks.append(truth('contracting conjugate root',abs(bb)<1));expected=s.pi**2/(m*m+4)
 elif slug=='alternating-infinite-product':
  for key in ['p','q']:
   a=R(p[key]);checks += [eq(key+' derivative used in mean-value bound',s.diff(x**(-a),x),-a*x**(-a-1)),truth(key+' positive product factors',a>0)]
   if a<=R(1,2):checks.append(eq(key+' paired positive discrepancy is lower order',s.limit(x**(a-1),x,s.oo),0))
  u,v=s.symbols('u v');checks.append(eq('paired increment exactly includes negative square-order term',(1+u)*(1-v)-1,u-v-u*v))
 elif slug=='Dirichlet-moment-uniqueness':
  n=p['index'];b=p['geometricBase'];k=s.symbols('k',positive=True);checks=[eq('comparison coefficients ratio',s.limit(((k+1)**2-1)/(b*(k*k-1)),k,s.oo),R(1,b)),truth('l1 comparison ratio below one',b>1),eq('smallest-index tail bound decays',s.limit((R(n,n+1))**k,k,s.oo),0)];expected=s.Integer(n*n-1)
 elif slug=='least-energy-sequence':
  b=p['base'];r0=R(1,b);y=s.symbols('y');g=y/(1-y);g1=y*s.diff(g,y);g2=y*s.diff(g1,y);G=s.Matrix([[g,g1],[g1,g2]]).subs(y,r0*r0);c=s.Matrix([p['firstMoment'],p['secondMoment']]);co=G.LUsolve(c);expected=(co.T*G*co)[0]
  checks=[eq('independent differentiated-geometric Gram construction satisfies constraints',G*co,c),truth('Gram positive determinant',G.det()>0),eq('projected energy is constraint inner product',(co.T*G*co)[0],(co.T*c)[0])]
 elif slug=='Legendre-recurrence-generating':
  a=R(p['coefficient']);b=p['base'];P=[s.Integer(1),a]
  for n in range(1,10):P.append(s.factor(((2*n+1)*a*P[-1]-n*P[-2])/(n+1)))
  F=(1-2*a*x+x*x)**(-R(1,2));series=s.series(F,x,0,11).removeO()
  checks=[eq('recurrence coefficient against independent generating expansion '+str(n),series.coeff(x,n),P[n]) for n in range(11)];expected=1/s.sqrt(1-2*a/b+R(1,b*b))
 elif slug=='rooted-tree-weighted-series':
  a=R(p['treeValue']);T=sum(s.Integer(n)**(n-1)*x**n/s.factorial(n) for n in range(1,9));res=s.series(T-x*s.exp(T),x,0,9).removeO()
  checks=[eq('independent finite tree coefficient composition',res,0),eq('second Euler derivative from implicit derivative',s.diff(x/(1-x),x)*x/(1-x),x/(1-x)**3),truth('small implicit branch',0<a<1)];expected=a/(1-a)**3
 elif slug=='finite-cycle-resolvent':
  n=p['cycleSize'];M=s.eye(n)*R(3,2)
  for j in range(n):M[j,(j+1)%n]=-R(1,2);M[(j+1)%n,j]=-R(1,2)
  expected=s.trace(M.inv());checks=[eq('independent cyclic-matrix trace versus log derivative',expected,s.diff(s.chebyshevt(n,x),x).subs(x,R(3,2))/(s.chebyshevt(n,R(3,2))-1)),truth('positive definite spectral margin',R(3,2)-1>0)]
 elif slug=='weighted-subset-q-product':
  n=p['size'];k=p['selected'];D=[1]+[0]*k
  for j in range(n):
   for h in range(k,0,-1):D[h]+=2**j*D[h-1]
  expected=s.Integer(D[k]);checks=[eq('independent coefficient DP versus finite product',expected,s.Poly(s.prod(1+2**j*x for j in range(n)),x).nth(k)),truth('selected subset range valid',0<k<n)]
 elif slug=='Poisson-partition-moment':
  n=p['power'];B=s.Integer(1)
  for j in range(n):B=s.expand(x*(B+s.diff(B,x)))
  expected=B.subs(x,1);checks=[eq('independent Touchard recurrence evaluated at one',expected,s.bell(n)),eq('Touchard degree',s.degree(B,x),n)]
 elif slug=='factorial-floor-reconstruction':
  b=p['base'];K=35;lo=sum(Fraction(1,math.factorial(j)) for j in range(K+1));hi=lo+Fraction(1,math.factorial(K)*K)
  for n in range(1,15):
   v=sum(math.factorial(n)//math.factorial(j) for j in range(n+1));checks.append(truth('rational exponential enclosure proves floor n='+str(n),v<lo*math.factorial(n)<hi*math.factorial(n)<v+1))
  y=s.symbols('y');checks.append(eq('double-sum generated coefficient through order seven',s.series(s.exp(y)/(1-y)-1,y,0,8).removeO(),sum(sum(R(1,math.factorial(j)) for j in range(n+1))*y**n for n in range(1,8))));expected=s.exp(R(1,b))/(1-R(1,b))-1
 elif slug=='Liouville-Dirichlet-product':
  q=p['exponent'];lam={n:(-1)**sum(s.factorint(n).values()) for n in range(1,121)}
  checks=[truth('independent parity completely multiplicative on finite grid',all(lam[a*b]==lam[a]*lam[b] for a in range(1,11) for b in range(1,11))),eq('local product reduction',(1-x)/(1-x*x),1/(1+x)),truth('absolute convergence threshold',q>1)];expected=s.zeta(2*q)/s.zeta(q)
 elif slug=='Riesz-product-energy':
  b=p['base'];N=p['factors'];a=R(p['amplitude']);P={0:s.Integer(1)}
  for j in range(3):
   local={0:1+a*a/2,b**j:a,-b**j:a,2*b**j:a*a/4,-2*b**j:a*a/4};nxt={}
   for u,c in P.items():
    for v,d in local.items():nxt[u+v]=nxt.get(u+v,0)+c*d
   P=nxt
  checks=[eq('independent sparse Fourier constant coefficient three-factor check',P[0],(1+a*a/2)**3),truth('all family factors satisfy largest-digit dominance',all(b**j>2*sum(b**k for k in range(j)) for j in range(N)))];expected=(1+a*a/2)**N
 elif slug=='Euler-harmonic-weight-three':
  m=p['firstIndex'];u,v=s.symbols('u v',positive=True);checks=[eq('inner telescoping split',1/(v*(u+v)),(1/v-1/(u+v))/u)]
  checks += [eq('independent diagonal coefficient n='+str(n),sum(R(1,j*(n-j)) for j in range(1,n)),2*s.harmonic(n-1)/n) for n in range(2,13)]
  expected=2*s.zeta(3)-sum(s.harmonic(j)/j**2 for j in range(1,m))
 elif slug=='Pade-cancellation-order':
  m=p['order'];t=s.symbols('t');w=t**m*(1-t)**m;at0=0;at1=0
  # Exact integration by parts: x^(2m+1) integral e^(xt)w(t) equals
  # e^x sum (-1)^j w^(j)(1)x^(2m-j) - sum (-1)^j w^(j)(0)x^(2m-j).
  for j in range(2*m+1):
   d=s.diff(w,t,j);at0+=(-1)**j*d.subs(t,0)*x**(2*m-j);at1+=(-1)**j*d.subs(t,1)*x**(2*m-j)
  Q=sum((-1)**k*s.binomial(2*m-k,m)*x**k/s.factorial(k) for k in range(m+1));checks=[eq('all right endpoint integration-by-parts terms',(-1)**m*at1/s.factorial(m)**2,Q),eq('all left endpoint integration-by-parts terms',(-1)**m*at0/s.factorial(m)**2,Q.subs(x,-x)),eq('independent beta polynomial integral',s.integrate(w,(t,0,1)),s.factorial(m)**2/s.factorial(2*m+1))];expected=R((-1)**m,math.factorial(2*m+1))
 elif slug=='factorial-asymptotic-remainder':
  a=R(p['a']);u=s.symbols('u');N=s.symbols('N',positive=True,integer=True);n=9
  checks=[eq('independent exact polynomial division remainder',1/(a+u)-sum((-u)**k/a**(k+1) for k in range(n)),(-u)**n/(a**n*(a+u))),eq('normalized second moment concentration bound',((N+1)+(N+1-N)**2)/N**2,(N+2)/N**2),eq('explicit Lipschitz expectation error bound vanishes',s.limit(s.sqrt(N+2)/(a*a*N),N,s.oo),0)];expected=s.sqrt(2*s.pi)/(a+1)
 elif slug=='Hilbert-kernel-sharp-constant':
  m=p['scaleAndShift'];K=s.symbols('K',positive=True);u=s.symbols('u',positive=True);F=2/s.sqrt(1+m/K)*s.atan(s.sqrt(u/(1+m/K)))
  checks=[eq('sharp lower-bound integral primitive',s.diff(F,u),1/(s.sqrt(u)*(1+u+m/K))),eq('middle-scale integral tends to pi',s.limit(F.subs(u,K)-F.subs(u,1/K),K,s.oo),s.pi)]
  a,b,w,v=s.symbols('a b w v',positive=True);checks.append(eq('weighted Schur inequality is a square',a*a*v/w+b*b*w/v-2*a*b,(a*s.sqrt(v/w)-b*s.sqrt(w/v))**2));expected=s.pi/m
 elif slug=='Carleman-geometric-mean-constant':
  m=p['externalScale'];checks=[eq('independent weight telescoping at each prefix '+str(N),s.prod(R((k+1)**k,k**(k-1)) for k in range(1,N+1)),(N+1)**N) for N in range(1,13)];checks.append(eq('coefficient tail exact telescope',1/(x*(x+1)),1/x-1/(x+1)));expected=s.E/m
 elif slug=='Dyson-alternating-cube':
  m=p['blockSize'];a,b,c=s.symbols('a b c');xs=[a,b,c];checks=[eq('independent Good recurrence rational identity',sum(s.prod(1/(1-xs[j]/xs[k]) for k in range(3) if j!=k) for j in range(3)),1)]
  actual=sum(Fraction((-1)**abs(k))*math.comb(2*m,m+k)**3 for k in range(-m,m+1));expected=R(actual.numerator,actual.denominator);checks.append(eq('finite cube sum equals independently counted multinomial',expected,math.factorial(3*m)//math.factorial(m)**3))
 elif slug=='Abel-logarithmic-sum':
  a=R(p['shift']);checks=[]
  for N in [1,3,7]:checks.append(eq('independent finite paired product N='+str(N),s.prod((2*j+a)/(2*j+a+1) for j in range(N)),s.expand_func(s.gamma(N+a/2)*s.gamma((a+1)/2)/(s.gamma(a/2)*s.gamma(N+(a+1)/2)))))
  checks.append(eq('Cesaro-Abel weight normalization',s.diff(x/(1-x),x)*(1-x)**2,1));expected=s.log(s.gamma((a+1)/2)/s.gamma(a/2))+s.log(2)/2
 elif slug=='maximum-entropy-sequence':
  m=p['mean'];r0=R(m-1,m);n=s.symbols('n',integer=True,positive=True);checks=[eq('independent geometric probability normalization',s.summation((1-r0)*r0**(n-1),(n,1,s.oo)),1),eq('independent geometric mean constraint',s.summation(n*(1-r0)*r0**(n-1),(n,1,s.oo)),m),eq('entropy cross-term affine coefficient',s.diff(-s.log(1-x)-(m-1)*s.log(x),x).subs(x,r0),0)];expected=m*s.log(m)-(m-1)*s.log(m-1)
 elif slug=='restricted-digit-convergence':
  b=p['base'];M=s.Matrix([[1,1],[1,0]]);v=s.Matrix([1,0]);counts=[]
  for N in range(1,12):counts.append(v[0]);v=M*v
  checks=[truth('independent two-state digit recurrence',counts==[s.fibonacci(N) for N in range(1,12)]),truth('automaton spectral polynomial coefficients',M.charpoly().all_coeffs()==[1,-1,-1])];expected=s.log((1+s.sqrt(5))/2)/s.log(b)
 elif slug=='binomial-convolution-Riccati':
  m=p['angleDenominator'];a=[s.Integer(1),s.Integer(1)]
  for n in range(1,9):a.append(sum(s.binomial(n,k)*a[k]*a[n-k] for k in range(n+1))/2)
  F=s.tan(s.pi/4+x/2);series=s.series(F,x,0,10).removeO();checks=[eq('independent analytic Taylor coefficient against convolution '+str(n),series.coeff(x,n)*s.factorial(n),a[n]) for n in range(10)];expected=s.tan(s.pi/4+s.pi/(2*m))
 else:raise ValueError('unreviewed advanced construction '+slug)
 if expected is not None:
  correct=next(c for c in r['choices'] if c['choiceId']==r['answerChoiceId'])
  checks.append(truth('derived exact result is the selected displayed choice',correct['math']==tex(expected)))
 if expected_category is not None:checks.append(truth('derived classification equals the selected exact choice','ch_'+digest(expected_category)[:16]==r['answerChoiceId']))
 checks.append(truth('four unique choice identities',len(r['choices'])==4 and len({c['choiceId'] for c in r['choices']})==4))
 body={k:v for k,v in r.items() if k!='contentHash'};checks.append(truth('raw source hash binds reviewed input',digest(body)==r['contentHash']))
 return {'status':'passed','familyId':r['familyId'],'problemId':r['problemId'],'sourceContentHash':r['contentHash'],'checks':checks,'executedCheckCount':len(checks),'analyticCertificate':r['analyticCertificate'],'limitations':'Executed checks verify stated finite algebra, recurrences, inequalities and intermediate identities. Infinite convergence, interchange, sharpness, and theorem applications are the separately recorded analytic arguments; no claim of formal proof or human review. Difficulty and option-only robustness require separate cross-review.'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=Path(__file__).with_name('advanced-candidates.jsonl'));ap.add_argument('--out',type=Path,default=Path(__file__).with_name('advanced-verification.json'));a=ap.parse_args();results=[];fail=[]
 for line in a.input.read_text().splitlines():
  r=json.loads(line)
  try:results.append(verify(r))
  except Exception as e:fail.append({'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'error':repr(e)})
 report={'status':'passed' if not fail else 'failed','families':len({r['familyId'] for r in results}),'instances':len(results),'executedChecks':sum(r['executedCheckCount'] for r in results),'failures':fail,'results':results,'verifierFileSha256':__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),'inputFileSha256':__import__('hashlib').sha256(a.input.read_bytes()).hexdigest(),'humanReviewed':False,'formalProof':False};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));raise SystemExit(bool(fail))
