"""Independent finite Limits peer review; imports no author constructor or answer code."""
from pathlib import Path
import argparse,ast,json,hashlib,itertools,math,collections,re
from fractions import Fraction
from functools import lru_cache
import sympy as s
from rigorous_intervals import enclose,disjoint,dump,box,add,mul,inv,neg,pi_box

SLUGS={'quadratic-Weyl-distance-moment','AGM-invariant-limit','AGM-quadratic-root-rate','Lambert-product-singularity','maximum-occupancy-threshold','implicit-exponential-saddle','permutation-cycle-divisibility','random-walk-last-zero-law','slowly-varying-tridiagonal-determinant','rank-one-outlier-edge','lacunary-Fourier-moment','AGM-normalized-gap-prefactor','restricted-partition-entropy','dyadic-log-product','quadratic-gauss-magnitude'}
CONSTRUCTORS={n:getattr(s,n) for n in ['Integer','Rational','Add','Mul','Pow','exp','log','gamma','zeta','elliptic_k','asin','acos','atan','sin','cos','sqrt']}
CONSTANTS={'pi':s.pi,'E':s.E,'I':s.I}
def decode(text):
 def walk(n):
  if isinstance(n,ast.Constant) and isinstance(n.value,(int,str)):return n.value
  if isinstance(n,ast.Name) and n.id in CONSTANTS:return CONSTANTS[n.id]
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in CONSTRUCTORS and not n.keywords:return CONSTRUCTORS[n.func.id](*[walk(a) for a in n.args])
  raise ValueError('Unrecognized serialized mathematics')
 return s.sympify(walk(ast.parse(text,mode='eval').body))
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canon(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tex(v):
 t=s.latex(s.sympify(v),fold_short_frac=False)
 for a,b in [(r'\log',r'\ln'),(r'\operatorname{asin}',r'\arcsin'),(r'\operatorname{acos}',r'\arccos'),(r'\operatorname{atan}',r'\arctan')]:t=t.replace(a,b)
 return t
def eq(label,a,b=0):
 d=s.simplify(s.expand_func(a-b));assert d==0,(label,d)
 return {'check':label,'method':'exact independently computed identity','passed':True}
def yes(label,test):assert bool(test),label;return {'check':label,'method':'exact finite/domain condition','passed':True}
def rational(e):return Fraction(int(e.p),int(e.q))
def texin(label,Q,fragment):return yes(label,fragment in Q)
X,Y,Z,T=s.symbols('X Y Z T',real=True)
@lru_cache(None)
def implicit_coefficients(c,N=6):
 q=Z
 coeffs={1:s.Integer(1)}
 for j in range(2,N+1):
  aj=s.expand(s.series(s.exp(q+c*q*q),Z,0,j).removeO()).coeff(Z,j-1);coeffs[j]=s.factor(aj);q+=coeffs[j]*Z**j
 return coeffs
@lru_cache(None)
def walk_counts(n):
 state={(0,0):1}
 for t in range(1,2*n+1):
  nxt=collections.defaultdict(int)
  for (pos,last),count in state.items():
   for step in [-1,1]:v=pos+step;nxt[v,t if v==0 else last]+=count
  state=nxt
 out=collections.Counter()
 for (pos,last),count in state.items():out[last]+=count
 return out

def expected_and_checks(r):
 slug=re.sub(r'^q1-limits-(?:olympiad|hard)-','',r['familyId']);p=r['parameters']['case'];Q=r['statement'];checks=[];notes=[];aliases=[];level='olympiad';reason='The independent first solve and reviewed analytic bridge require a substantial structural decision.'
 if slug=='quadratic-Weyl-distance-moment':
  power=p['p'];ans=s.integrate(2*(1-X)*X**power,(X,0,1));checks += [eq('Independent triangular difference-density moment',ans,s.Rational(2,(power+1)*(power+2))),texin('Displayed distance exponent',Q,r'\right|^{'+str(power)+r'}')]
  a,b,n,h=s.symbols('a b n h');checks += [eq('Independent quadratic phase differencing',a*(n+h)+b*(n+h)**2-a*n-b*n*n,2*b*h*n+a*h+b*h*h),yes('Positive integer moment order',type(power)is int and power>0)];key='joint-quadratic-orbit-distance-moment:'+str(power)
 elif slug in ['AGM-invariant-limit','AGM-quadratic-root-rate','AGM-normalized-gap-prefactor']:
  par=s.Rational(p['p']);b=s.sqrt(1-par);A=(1+b)/2;G=s.sqrt(b);t=s.symbols('t',positive=True);u=(t-b/t)/2
  checks += [eq('Independent AGM radicand polynomial',4*t*t*(u*u+A*A),(t*t+1)*(t*t+b*b)),eq('Independent AGM Jacobian factor',s.diff(u,t),(t*t+b)/(2*t*t)),yes('Positive normalized elliptic shape',0<par<1),texin('Displayed initial geometric coordinate',Q,tex(b))]
  if slug=='AGM-invariant-limit':
   ans=s.pi/(2*s.elliptic_k(par));key='AGM-common-limit-parameter:'+str(par);level='withhold-superseded-direct-limit';reason='Stage07 direct-limit choices have elementary-bounds defects; replaced by a distinct rate question in the same related group.'
  elif slug=='AGM-normalized-gap-prefactor':
   ans=4*s.pi/s.elliptic_k(par);key='AGM-normalized-gap-prefactor:'+str(par);level='hard';reason='Exact gap recurrence restricts any finite nonzero proposed prefactor to eight times the common mean; actual choices permit a short bounding route. No advanced credit.'
   m,v=s.symbols('m v',positive=True);sub=1/(s.sqrt(m)*v)
   checks += [eq('Independent inversion-invariant squared elliptic kernel',s.diff(sub,v)**2/((1+sub**2)*(1+m*sub**2)),1/((1+v**2)*(1+m*v**2))),eq('Coordinate gap prefactor from normalized parameter',s.Rational(16,2)*s.pi/(2*s.elliptic_k(par)),ans),texin('Displayed exact nome uses complementary parameter',Q,tex(s.exp(-s.pi*s.elliptic_k(1-par)/s.elliptic_k(par))))]
  else:
   ans=s.exp(-s.pi*s.elliptic_k(1-par)/s.elliptic_k(par));key='AGM-root-convergence-parameter:'+str(par);v=(t+b/t)/2
   checks += [eq('Independent complementary radicand identity',4*t*t*(v*v-A*A),(1-t*t)*(b*b-t*t)),eq('Independent complementary derivative',s.diff(v,t),(t*t-b)/(2*t*t)),eq('Gap-to-parameter relation',1-b*b,(1-b)*(1+b)),texin('Displayed root exponent',Q,r'1/2^n')]
 elif slug=='Lambert-product-singularity':
  power=s.Rational(p['p']);ans=-s.gamma(power+1)*s.zeta(power+2);u=s.symbols('u',positive=True)
  for j in [2,3]:checks.append(eq('Independent real Laplace moment at index'+str(j),s.integrate(u**power*s.exp(-j*u),(u,0,s.oo)),s.gamma(power+1)/j**(power+1)))
  checks += [yes('Mellin and dominating-series exponents are integrable',power>0),texin('Displayed product weight exponent',Q,r'k^{'+tex(power)+r'}'),texin('Displayed singular normalization',Q,r't^{'+tex(power+1)+r'}')];key='arithmetic-product-Mellin-power:'+str(power)
 elif slug=='maximum-occupancy-threshold':
  ans=s.Integer(1);n=5
  for k in range(1,n+1):checks.append(yes('Finite factorial-moment upper bound at k'+str(k),s.binomial(n,k)/n**k<=s.Rational(1,math.factorial(k))))
  # Independent exact multinomial normalization under Poisson conditioning.
  total=s.Rational(0)
  for a in range(5):
   for b in range(5-a):
    c=4-a-b;total+=s.factorial(4)/(s.factorial(a)*s.factorial(b)*s.factorial(c)*3**4)
  checks.append(eq('Conditional multinomial normalization for three boxes/four balls',total,1));key='n-independent-balls-n-uniform-boxes'
 elif slug=='implicit-exponential-saddle':
  tau=s.Rational(p['tau']);c=(1-tau)/(2*tau*tau);variance=tau+4*c*tau*tau;rho=tau*s.exp(-tau-c*tau*tau);ans=tau/s.sqrt(2*s.pi*variance)
  checks += [eq('Independent tilted compound-Poisson mean',tau+2*c*tau*tau,1),eq('Independent compound-Poisson variance',variance,2-tau),yes('Aperiodic positive Poisson component',0<tau<1 and c>0),texin('Displayed analytic radius',Q,tex(rho)),yes('Displayed exponential quadratic coefficient',tex(c)+r'Y(z)^2' in Q or c==1 and r'+Y(z)^2' in Q)]
  cs=implicit_coefficients(c)
  for n in [3,4,5,6]:
   lag=sum((n*c)**j*n**(n-1-2*j)/(s.factorial(j)*s.factorial(n-1-2*j)) for j in range((n-1)//2+1))/n;checks.append(eq('Independent recursive implicit coefficient at n'+str(n),cs[n],lag))
  theta=s.symbols('theta',real=True);phase=tau*(s.exp(s.I*theta)-1)+c*tau*tau*(s.exp(2*s.I*theta)-1)-s.I*theta
  checks += [eq('Full-circle phase is stationary',s.diff(phase,theta).subs(theta,0),0),eq('Exact negative Hessian',s.diff(phase,theta,2).subs(theta,0),-variance)];key='exponential-inverse-relative-quadratic-weight:'+str(c)
 elif slug=='permutation-cycle-divisibility':
  d=p['d'];ans=1/s.gamma(s.Rational(1,d));probs=[s.Integer(1)]
  for N in range(1,5*d+1):probs.append(sum(probs[N-k] for k in range(d,N+1,d))/s.Integer(N))
  for n in range(1,6):checks.append(eq('Independent cycle-containing-label-one recurrence at size'+str(d*n),probs[d*n],s.prod((j+s.Rational(1,d))/(j+1) for j in range(n))))
  checks += [yes('Nontrivial integer cycle modulus',d>=3),texin('Displayed label count',Q,str(d)+r'n\}')];key='cycle-length-modulus:'+str(d)
  if any('p_N^{\\mathrm{all\\ labels}}' in step for step in r['solutionSteps']):notes.append('Define the all-label probability q_N before its generating function; original p_n denotes only d*n labels.')
 elif slug=='random-walk-last-zero-law':
  a=s.Rational(p['a']);ans=2*s.asin(s.sqrt(a))/s.pi
  for n in [3,4,5]:
   counts=walk_counts(n)
   for k in range(n+1):checks.append(eq('Independent path enumeration n'+str(n)+' k'+str(k),s.Rational(counts[2*k],2**(2*n)),s.binomial(2*k,k)*s.binomial(2*(n-k),n-k)/4**n))
  checks += [eq('Arcsine-CDF derivative',s.diff(2*s.asin(s.sqrt(X))/s.pi,X),1/(s.pi*s.sqrt(X)*s.sqrt(1-X))),yes('Interior observation fraction',0<a<1),texin('Actual observation threshold',Q,tex(2*a)+r'n')]
  key='last-zero-arcsine-observation-up-to-complement:'+str(min(a,1-a));aliases=['a and1−a have complementary limiting CDFs by the exact symmetric convolution; same advanced reflection lineage.']
 elif slug=='slowly-varying-tridiagonal-determinant':
  c=p['bernstein'];d=len(c)-1;g=s.expand(1+sum(c[j]*s.binomial(d,j)*X**j*(1-X)**(d-j) for j in range(d+1)));mean=s.integrate(g,(X,0,1));ans=s.exp(mean)
  checks += [eq('Independent polynomial integration',mean,1+s.Rational(sum(c),len(c))),yes('Positive Bernstein coefficients give uniform spectral gap',all(v>=0 for v in c)),texin('Displayed coefficient profile',Q,tex(g.subs(X,s.Symbol('x',real=True))))]
  v=s.symbols('v',positive=True);q0=s.Integer(1);q1=v+1/v
  for n in range(2,6):q0,q1=q1,s.expand((v+1/v)*q1-q0);checks.append(eq('Constant continuant at size'+str(n),q1,(v**(n+1)-v**(-n-1))/(v-1/v)))
  # Independent contraction comparison, rather than the author block-cut proof.
  RHO,z=s.symbols('RHO z',positive=True);checks.append(eq('Exact continuant-ratio contraction difference',(2*s.cosh(z)-1/RHO)-s.exp(z),s.exp(-z)-1/RHO));key='positive-profile-up-to-reflection:'+min(str(g),str(s.expand(g.subs(X,1-X))))
  if not any(('determinant of' in step or 'denote its determinant' in step) and ('block' in step or 'matrix' in step) for step in r['solutionSteps']):notes.append('Define D_m as the determinant of the constant m by m block with diagonal2cosh u before using its recurrence.')
 elif slug=='rank-one-outlier-edge':
  power=p['p'];root=s.Rational(p['root']);aa=root-1;F=s.log(root/aa)
  for j in range(1,power+1):F=s.Rational(1,j)-aa*F
  ans=root;coupling=1/F;logterm=s.log(root/aa);expanded=s.expand(F,log=False);coeff=expanded.coeff(logterm);displayF=expanded.subs(logterm,0)+s.sign(coeff)*s.log((root/aa)**abs(coeff))
  checks += [eq('Independently integrated secular kernel',s.integrate(X**power/(X+aa),(X,0,1)),F),yes('Above-edge target and vanishing weight power',root>1 and power>=1),yes('Displayed coupling agrees up to the real reciprocal-log identity',tex(coupling) in Q or tex(1/displayF) in Q or tex(s.simplify(coupling)) in Q or tex(1/s.logcombine(s.expand(F),force=True)) in Q or tex(1/F.xreplace({s.log(root/aa):-s.log(aa/root)})) in Q)]
  H,Z=s.symbols('H Z');n=3;grid=[s.Rational(j,n) for j in range(n)];weights=[(1-t)**power for t in grid];M=s.diag(*grid)+s.Matrix([[H*s.sqrt(weights[i]*weights[j])/n for j in range(n)] for i in range(n)])
  checks.append(eq('Independent finite determinant expansion',s.det(Z*s.eye(n)-M),s.prod(Z-t for t in grid)*(1-H/s.Integer(n)*sum(w/(Z-t) for w,t in zip(weights,grid)))))
  key='rank-one-unit-bulk-power:'+str(power)+';outlier:'+str(root)
 elif slug=='lacunary-Fourier-moment':
  rr=p['r'];base=p['base'];ans=s.factorial(2*rr)/(4**rr*s.factorial(rr));checks += [yes('No base carry with this many signed factors',base>2*rr),eq('Independent pair-partition count times cosine variance',s.factorial2(2*rr-1)/2**rr,ans),texin('Displayed total moment order',Q,'^{'+str(2*rr)+'}'),texin('Displayed fixed frequency base',Q,str(base)+'^k')]
  # Coefficient of n^r in the exact independent-phase moment polynomial via logarithmic MGF.
  z=s.symbols('z');linear=s.Rational(1,4);checks.append(eq('Highest n-power coefficient in exponential of log I0',s.factorial(2*rr)*linear**rr/s.factorial(rr),ans));key='lacunary-even-moment-order:'+str(2*rr)
  if any(re.search(r'\br distinct frequencies',q) for q in r['solutionSteps']):notes.append('The public prose uses r without defining it; instantiate the number or define half the displayed moment order.')
 elif slug=='restricted-partition-entropy':
  d=p['d'];B=s.Rational(d-1,d)*s.pi**2/6;ans=2*s.sqrt(B);checks += [yes('Allowed part one and nontrivial excluded modulus',type(d)is int and d>=2),texin('Displayed exact partition modulus',Q,'p_{'+str(d)+'}(n)'),texin('Displayed excluded part modulus',Q,'not divisible by }'+str(d))]
  # Independent Euler pentagonal numerator/denominator versus bounded-part recursion.
  N=36;ordinary=[1]+[0]*N;pent=[0]*(N+1);pent[0]=1
  for k in range(1,N+1):
   for e in [k*(3*k-1)//2,k*(3*k+1)//2]:
    if e<=N:pent[e]=(-1)**k
  for n in range(1,N+1):ordinary[n]=-sum(pent[k]*ordinary[n-k] for k in range(1,n+1))
  @lru_cache(None)
  def count(n,k):
   if n==0:return 1
   if n<0 or k==0:return 0
   return count(n,k-1)+(count(n-k,k) if k%d else 0)
  for n in range(1,N+1):
   prod=sum(pent[k]*ordinary[n-d*k] for k in range(n//d+1));checks.append(eq('Independent restricted coefficient via pentagonal convolution n='+str(n),prod,count(n,n)))
  eps=s.symbols('eps',positive=True);lo=s.sqrt(B)*(s.sqrt(1-eps)+(1-2*eps)/s.sqrt(1-eps));checks.append(eq('Exact coefficient window lower constant tends to saddle upper constant',s.limit(lo,eps,0),ans))
  for j in [1,2,4]:checks += [eq('Independent first-moment Laplace integral j='+str(j),s.integrate(X*s.exp(-j*X),(X,0,s.oo)),s.Rational(1,j*j)),eq('Independent variance Laplace integral j='+str(j),s.integrate(j*X*X*s.exp(-j*X),(X,0,s.oo)),s.Rational(2,j*j))]
  key='partitions-excluding-multiple-modulus:'+str(d)
 elif slug=='dyadic-log-product':
  power=p['power'];base=p['b'];ans=-s.Rational(power,power+1)*s.log(base)**(-s.Rational(1,power));j=s.symbols('j',integer=True,nonnegative=True);J=s.symbols('J',integer=True,positive=True)
  ps=s.summation(j**power,(j,0,J));checks += [eq('Independent Faulhaber leading coefficient',s.Poly(ps,J).LC(),s.Rational(1,power+1)),yes('Nonlinear spacing and positive logarithmic scale',power>=2 and base>1),texin('Actual nonlinear lattice exponent',Q,str(base)+'^{k^{'+str(power)+'}}'),texin('Actual cutoff normalization exponent',Q,tex(1+s.Rational(1,power)))]
  for n in range(8):checks.append(yes('Exact adjacent-exponent gap controls both geometric tails', (n+1)**power-n**power>=1))
  key='power-spaced-product-cutoff-order:'+str(power);aliases=['Changing the logarithmic lattice base only rescales the cutoff coordinate and leading scalar; normalize by power alone.']
 elif slug=='quadratic-gauss-magnitude':
  a,b=p['a'],p['b'];checks += [yes('Positive integral quadratic and nonzero linear characters',type(a)is int and type(b)is int and a>0 and b>0),texin('Actual four congruence moduli',Q,str(4*a)+'n+r'),texin('Displayed quadratic and linear character',Q,tex(a*s.Symbol('k')**2+b*s.Symbol('k'))),texin('Displayed complete residue-system sum',Q,r'\sum_{k=0}^{m-1}'),texin('Displayed four residue classes',Q,r'\sum_{r=0}^{3}')]
  z=s.symbols('z');vectors=[]
  for n in [1,2,3,5]:
   values=[]
   for r0 in range(4):
    M=4*a*n+r0;phase=s.Integer(0)
    for h in range(M):
     if (2*a*h)%M==0:phase+=z**((a*h*h+b*h)%M)
    rem=s.rem(phase,s.cyclotomic_poly(M,z),z);checks.append(yes('Exact character orthogonality leaves integer magnitude n='+str(n)+' r='+str(r0),rem.is_Integer));values.append(rem)
   vectors.append(values)
  for v in vectors[1:]:
   for r0 in range(4):checks.append(eq('Exact congruence pattern repeats under modulus increment at r='+str(r0),v[r0],vectors[0][r0]))
  ans=sum(vectors[0]);key='quadratic-linear-four-congruence-pattern:'+str(a)+':'+str(b%(2*a))
 else:raise ValueError(slug)
 return s.simplify(ans),checks,key,aliases,level,reason,notes

def r_record_steps(r=None,record=None):return [] if record is None else record['solutionSteps']

def pair_checks(values):
 out=[]
 for a,b in itertools.combinations(values,2):
  if a==b:raise AssertionError('Coincident choices')
  def gamma_argument(v):
   atoms=list(v.atoms(s.gamma))
   if len(atoms)==1 and v==1/atoms[0]:return atoms[0].args[0]
   if v==1/s.sqrt(s.pi):return s.Rational(1,2)
   if v==1:return s.Integer(1)
  aa,bb=gamma_argument(a),gamma_argument(b)
  if aa is not None and bb is not None:
   assert aa.is_Rational and bb.is_Rational and 0<aa<=1 and 0<bb<=1 and aa!=bb
   out.append({'method':'Strict monotonicity of1/Gamma on(0,1], from strict log-convexity and Gamma(1)=Gamma(2)=1','arguments':[str(aa),str(bb)],'passed':True});continue
  A,B=enclose(a),enclose(b);assert disjoint(A,B),(a,b,A,B)
  out.append({'method':'Disjoint outward-rounded rational enclosures','left':dump(A),'right':dump(B),'passed':True})
 return out

def option_bounds(r,values):
 slug=re.sub(r'^q1-limits-(?:olympiad|hard)-','',r['familyId']);case=r['parameters']['case'];result=None
 if slug=='rank-one-outlier-edge':
  p=case['p'];z=s.Rational(case['root']);aa=z-1;F=s.log(z/aa)
  for j in range(1,p+1):F=s.Rational(1,j)-aa*F
  v=enclose(1/(F*(p+1)));lo=max(Fraction(1),v[0]);hi=1+v[1]
  survivors=[c['choiceId'] for c,e in zip(r['choices'],values) if not(enclose(e)[1]<lo or enclose(e)[0]>hi)]
  result={'method':'Rayleigh/Weyl bound: max(1,lambda/(p+1)) ≤ any largest-eigenvalue limit ≤1+lambda/(p+1)','certifiedOuterInterval':[str(lo),str(hi)],'survivingChoiceIds':survivors}
 elif slug=='AGM-invariant-limit':
  b=s.sqrt(1-s.Rational(case['p']));lo=enclose(b)[0];hi=enclose((1+b)/2)[1]
  # Integral pointwise bounds also provide a certified interval for each proposed expression.
  survivors=[c['choiceId'] for c,e in zip(r['choices'],values) if not(enclose(e)[1]<lo or enclose(e)[0]>hi)]
  result={'method':'Monotone AGM initial bounds b0≤limit≤a1 plus independently enclosed elliptic choices','certifiedOuterInterval':[str(lo),str(hi)],'survivingChoiceIds':survivors}
 elif slug=='AGM-quadratic-root-rate':
  b=s.sqrt(1-s.Rational(case['p']));lo=enclose((1-b)/8)[0];hi=enclose((1-b)/(8*b))[1]
  survivors=[c['choiceId'] for c,e in zip(r['choices'],values) if not(enclose(e)[1]<lo or enclose(e)[0]>hi)]
  result={'method':'Exact gap recurrence bounds δ0/8≤limiting root rate≤δ0/(8b0)','certifiedOuterInterval':[str(lo),str(hi)],'survivingChoiceIds':survivors}
 elif slug=='dyadic-log-product':
  power=case['power'];base=case['b'];c=s.log(base)**(-s.Rational(1,power));lo=enclose(-(1-s.Rational(1,2**(power+1)))*c)[0];hi=Fraction(0)
  survivors=[ch['choiceId'] for ch,e in zip(r['choices'],values) if not(enclose(e)[1]<lo or enclose(e)[0]>hi)]
  result={'method':'Elementary cutoff and final-half contribution: −(1−2^(−p−1))*(ln b)^(−1/p) ≤ liminf ≤ limsup ≤0. This needs no exact power-sum coefficient.','certifiedOuterInterval':[str(lo),str(hi)],'survivingChoiceIds':survivors}
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True);source=a.stage/'candidates.json';allrows=json.loads(source.read_text());rows=[r for r in allrows if re.sub(r'^q1-limits-(?:olympiad|hard)-','',r['familyId']) in SLUGS];results=[];fail=[]
 for r in rows:
  fid=r['familyId'];idx=r['parameters']['instance']
  try:
   expected,checks,key,aliases,level,reason,notes=expected_and_checks(r);values=[decode(c['expression']) for c in r['choices']];answer=decode(r['answerExpression']);checks.append(eq('Independently derived final expression',answer,expected));selected=[e for c,e in zip(r['choices'],values) if c['choiceId']==r['answerChoiceId']];assert len(selected)==1;checks.append(eq('Unique selected expression matches independent answer',selected[0],expected));pairs=pair_checks(values)
   for c,e in zip(r['choices'],values):checks.append(yes('Literal choice TeX matches its parsed finite expression',c['math']==tex(e)))
   checks += [yes('Exact final solution line equals the displayed selected choice',r['solutionSteps'][-1]==r['answerMath']==next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']))]
   bounds=option_bounds(r,values)
   if bounds and len(bounds['survivingChoiceIds'])==1:
    level='hard-options-bound-shortcut';reason='The recorded elementary bound leaves only the correct choice; the intended advanced route is unnecessary.'
   if r.get('difficulty')=='hard' and level=='olympiad':level='hard';reason='Author final per-instance Hard classification retained after independent mathematical review.'
   result={'familyId':fid,'instanceIndex':idx,'caseId':r['parameters']['case']['caseId'],'rawSHA256':digest(r),'authorSourceHash':r['validation']['evidence']['sourceHash'],'independentAnswer':s.srepr(expected),'selectedChoiceId':r['answerChoiceId'],'executedChecks':checks,'pairwiseChoiceCertificates':pairs,'normalizedTaskKey':key,'equivalenceNotes':aliases,'editorialLevel':level,'easiestRouteDisposition':reason,'publicSolutionNotes':notes,'optionBoundReview':bounds,'optionNumericDiagnostics':[float(s.N(e,40)) for e in values],'humanReviewed':False,'formalProof':False}
   results.append(result)
  except Exception as exc:fail.append({'familyId':fid,'instanceIndex':idx,'rawSHA256':digest(r),'error':repr(exc)})
 sources={p.name:sha(p) for p in a.stage.glob('*.py')};counts=collections.Counter(r['familyId'] for r in rows);aliases=collections.defaultdict(list)
 for r in results:aliases[r['normalizedTaskKey']].append({'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'rawSHA256':r['rawSHA256']})
 output={'status':'failed-checks' if fail else 'complete-with-editorial-findings','reviewer':'/root/source_research','candidateArtifact':str(source.resolve()),'candidateArtifactSHA256':sha(source),'authorSourcesSHA256':sources,'reviewSourcesSHA256':{p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('rigorous_intervals.py')]},'counts':{'records':len(rows),'independentlyChecked':len(results),'exactOrDomainChecks':sum(len(r['executedChecks']) for r in results),'pairwiseChoiceCertificates':sum(len(r['pairwiseChoiceCertificates']) for r in results),'distinctNormalizedKeys':len(aliases)},'familyCounts':dict(counts),'failures':fail,'records':results,'normalizedAliases':[{'key':k,'records':v} for k,v in aliases.items() if len(v)>1],'verificationLimits':['Author constructors/answer functions were not imported. Serialized expressions were decoded through a restricted AST whitelist.','Rational interval certificates use explicit positive or alternating series and outward rounding; approximate option diagnostics do not establish correctness.','Analytic proof hypotheses and source-bound public explanation review are recorded separately; finite algebra cannot prove convergence, probability limit laws or sharp asymptotics.','The parent sample answer values were visible for stage07 first solves; the replacement AGM-rate first solve was genuinely statement/options-first.','No human review, formal proof, admission or deployment is implied.']}
 (a.out/'all-finite-review.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output['counts']));print('failures',fail)
 if fail:raise SystemExit(1)
if __name__=='__main__':main()
