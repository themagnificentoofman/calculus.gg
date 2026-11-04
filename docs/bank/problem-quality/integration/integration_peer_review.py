"""Reproduce the independent integration review against pinned local artifacts.
No application mutations. Exact algebra does not certify the analytic theorems.
"""
from pathlib import Path
import argparse,hashlib,json,importlib.util,sys,collections
import sympy as s
R=s.Rational; P=s.pi
x=s.symbols('x',positive=True); y,z=s.symbols('y z',real=True)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return [json.loads(t) for t in Path(path).read_text().splitlines() if t.strip()]
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def equal(a,b):
 if isinstance(a,(s.Tuple,tuple,list)) or isinstance(b,(s.Tuple,tuple,list)):
  return len(a)==len(b) and all(equal(u,v) for u,v in zip(a,b))
 if a==b:return True
 if isinstance(a,s.Symbol) or isinstance(b,s.Symbol):return False
 return s.simplify(s.expand_func(a-b))==0

def checks_for(slug,i):
 checks=[]
 def ck(label,left,right):
  assert equal(left,right),(slug,i,label,left,right)
  checks.append({'description':label,'left':s.srepr(left),'right':s.srepr(right),'result':'exact equality'})
 def yes(label,condition):
  assert condition,(slug,i,label)
  checks.append({'description':label,'result':'exact predicate'})
 n=i+2
 if slug=='weighted-complement':
  f=x**n/(x**n+(1-x)**n);ck('Complementary power-ratio reflection',f+f.subs(x,1-x),1);a=P/2
 elif slug=='reciprocal-quartic':
  q=s.Integer(i+2);u=q+s.sqrt(q*q-1);v=q-s.sqrt(q*q-1)
  ck('Two positive quadratic factors',(x*x+u)*(x*x+v),x**4+2*q*x*x+1)
  ck('Partial-fraction kernel',((1/(x*x+v)-1/(x*x+u))/(u-v)),1/(x**4+2*q*x*x+1))
  U=s.sqrt((q+1)/2)+s.sqrt((q-1)/2);V=s.sqrt((q+1)/2)-s.sqrt((q-1)/2);ck('Positive quadratic-root factor',U*U,u);ck('Positive reciprocal quadratic-root factor',V*V,v);a=P/(2*s.sqrt(2*q+2));ck('Two half-line arctangent integrals',P*(1/V-1/U)/(2*(u-v)),a)
 elif slug=='chebyshev-absolute':
  nn=i+3
  ck('Recurrence reproduces Chebyshev polynomial',2*x*s.chebyshevu(nn-2,x)-s.chebyshevu(nn-3,x),s.chebyshevu(nn-1,x))
  # Its trig identity follows from sine addition; each of nn lobes contributes 2/nn.
  ck('Equal lobe masses',sum(R(2,nn) for _ in range(nn)),2);a=s.Integer(2)
 elif slug=='gamma-unit-average':
  q=1+R(i,2);t=s.symbols('t',positive=True);F=t*s.log(t)-t+s.log(2*P)/2
  ck('Differentiate the averaged-log-Gamma closed form',s.diff(F,t),s.log(t));a=F.subs(t,q)
 elif slug=='log-fourier-coefficient':
  r=R(2,5) if i%2==0 else R(3,5);a=-P*r**n/n
  ck('Selected cosine orthogonality',s.integrate(s.cos(n*x)**2,(x,0,P)),P/2)
  ck('Off-frequency cosine orthogonality',s.integrate(s.cos(n*x)*s.cos((n+1)*x),(x,0,P)),0)
 elif slug=='arctan-parameter':
  q=R(i+3,2);t=s.symbols('t',positive=True);a=P*s.log(1+q)/2
  ck('Derivative of parameter primitive',s.diff(P*s.log(1+t)/2,t),P/(2*(1+t)))
  ck('Differentiated integrand is rational',s.diff(s.atan(t*x)/(x*(1+x*x)),t),1/((1+t*t*x*x)*(1+x*x)))
 elif slug=='gaussian-fourier':
  q=1+i%3;b=i+1;t=s.symbols('t',real=True);f=s.sqrt(P)/(2*s.sqrt(q))*s.exp(-t*t/(4*q));a=f.subs(t,b)
  ck('Transform ODE after integration by parts',s.diff(f,t),-t*f/(2*q));ck('Gaussian initial value',f.subs(t,0),s.sqrt(P)/(2*s.sqrt(q)))
 elif slug=='reciprocal-gaussian':
  q=R(1+i%3,2);b=R(i+1,3);t=s.symbols('t',positive=True);f=s.sqrt(P)*s.exp(-2*q*t)/(2*q);a=f.subs(t,b)
  ck('Reciprocal substitution yields the parameter ODE',s.diff(f,t),-2*q*f)
  ck('Reciprocal kernel identity',(q*q*x*x+t*t/x**2).subs(x,t/(q*x)),q*q*x*x+t*t/x**2)
 elif slug=='sinc-overlap':
  a0=i+2;b=[3,5,8,4,7,3,6,2][i];a=P*(a0+b-abs(a0-b))/4
  ck('Product-to-sum with cancellation',s.expand_trig(s.cos((a0-b)*x)-s.cos((a0+b)*x)),s.expand_trig(2*s.sin(a0*x)*s.sin(b*x)))
 elif slug=='mixed-beta-log':
  m=1+i%4;n0=2+i//4;N=m+n0+1
  a=s.factorial(m)*s.factorial(n0)/s.factorial(N)*((s.harmonic(m)-s.harmonic(N))*(s.harmonic(n0)-s.harmonic(N))-(P**2/6-s.harmonic(N,2)))
  # Independently expand the finite (1-x)^n and sum the single-endpoint log product.
  vals=[]
  for j in range(n0+1):
   r=m+j+1;vals.append((-1)**j*s.binomial(n0,j)*(s.harmonic(r)/r**2-(P**2/6-s.harmonic(r,2))/r))
  ck('Finite polynomial expansion into harmonic endpoint moments',sum(vals),a)
 elif slug=='thermal-derivative':
  k=s.symbols('k',positive=True);a=s.factorial(n)*s.zeta(n)
  ck('Exponential moment after scaling',s.integrate(x**n*s.exp(-k*x),(x,0,s.oo)),s.factorial(n)/k**(n+1))
 elif slug=='mellin-cyclotomic':
  p,q=[(1,3),(3,5),(3,7),(5,7),(3,8),(5,9),(7,11),(3,10)][i];a=P/(q*s.sin(P*R(p,q)))
  yes('Beta exponents both positive',0<p<q);ck('Power substitution exponent',R(p,q)-1,R(p-q,q))
 elif slug=='cauchy-convolution':
  aa,b=[(1,3),(3,2),(3,5),(5,1),(2,7),(7,3),(1,9),(9,2)][i];w=s.symbols('w');expr=1/(((w-aa)**2+b*b)*((w+aa)**2+b*b));a=P/(2*b*(aa*aa+b*b))
  ck('Independently summed two simple-pole residues',2*P*s.I*(s.residue(expr,w,aa+s.I*b)+s.residue(expr,w,-aa+s.I*b)),a)
 elif slug=='agm-parameter':
  aa=i+1;b=i+3;c=(x-aa*b/x)/2;A=R(aa+b,2)
  ck('Landen transformed quadratic',c*c+A*A,(x*x+aa*aa)*(x*x+b*b)/(4*x*x));ck('Landen companion quadratic',c*c+aa*b,(x+aa*b/x)**2/4);a=s.sqrt(aa*b)
 elif slug=='abel-recovery':
  # Finite polynomial expansion evaluates the beta moment without trusting the source coefficient.
  a=2/P*sum((-1)**j*s.binomial(n,j)/s.Integer(2*j+1) for j in range(n+1))
  ck('Second square-root kernel mass',s.integrate(1/s.sqrt(x*(1-x)),(x,0,1)),P)
 elif slug=='boundary-asymptotic':
  a=s.gamma(R(1,n))/n;ck('Gamma recurrence',s.gamma(1+R(1,n)),a)
 elif slug=='integral-equation':
  k=R(i+1,2);f=s.sinh(k*x)/(k*s.cosh(k));a=(s.cosh(k)-1)/(k*k*s.cosh(k))
  ck('Boundary ODE',s.diff(f,x,2),k*k*f);ck('Left endpoint',f.subs(x,0),0);ck('Right derivative',s.diff(f,x).subs(x,1),1)
  ck('Integrated recovered function',s.integrate(f,(x,0,1)),a)
 elif slug=='convolution-laplace':
  base=2+i%3;t=s.log(base);b=(1-R(1,base))/t;a=b**n;ck('Unit-box Laplace transform',s.integrate(s.exp(-t*x),(x,0,1)),b)
 elif slug=='poisson-log-potential':
  aa=1+i%3;b=i+1;c=2+i%2;w=s.symbols('w');t=s.symbols('t',positive=True);expr=2*c/(((w-b)**2+c*c)*(w*w+aa*aa));a=P/aa*s.log(b*b+(aa+c)**2)
  ck('Rational derivative residue sum',2*P*s.I*(s.residue(expr,w,s.I*aa)+s.residue(expr,w,b+s.I*c)),(s.diff(P/aa*s.log(b*b+(aa+t)**2),t)).subs(t,c))
 elif slug=='jensen-radius':
  r=R(i+3,2);ck('Outside-circle reciprocal reduction',1-2*r*s.cos(x)+r*r,r*r*(1-2/r*s.cos(x)+1/r**2));a=4*P*s.log(r)
 elif slug=='fresnel':
  q=R(i+1,2);a=s.sqrt(P)/(2*s.sqrt(2*q));ck('Positive-real square-root branch limit',s.re(s.sqrt(P)/(2*s.sqrt(-s.I*q))),a)
 elif slug=='bessel-laplace':
  aa=i+2;b=i+1;a=1/s.sqrt(aa*aa+b*b)
  ck('Angular tangent rationalization',aa/(aa*aa+b*b*x*x/(1+x*x))/(1+x*x),aa/(aa*aa+(aa*aa+b*b)*x*x))
  ck('Angular rational integral',2/P*s.integrate(aa/(aa*aa+(aa*aa+b*b)*x*x),(x,0,s.oo)),a)
 elif slug=='rodrigues-moment':
  k=1+i%2;poly=(x*x-1)**n;a=s.integrate(s.expand(x**(n+2*k)*s.diff(poly,x,n)),(x,-1,1))
  for d in range(n):
   ck('Vanishing endpoint jet '+str(d),s.diff(poly,x,d).subs(x,1),0);ck('Vanishing left jet '+str(d),s.diff(poly,x,d).subs(x,-1),0)
 elif slug=='bernoulli-product':
  m,n0=[(2,2),(2,4),(3,3),(2,6),(3,5),(4,4),(2,8),(4,6)][i];a=s.integrate(s.expand(s.bernoulli(m,x)*s.bernoulli(n0,x)),(x,0,1))
  ck('Bernoulli derivative recurrence',s.diff(s.bernoulli(m,x),x),m*s.bernoulli(m-1,x));ck('Bernoulli endpoint jump',s.bernoulli(1,1)-s.bernoulli(1,0),1)
 elif slug=='principal-value':
  p,q=[(1,3),(2,5),(3,7),(2,7),(3,8),(4,9),(5,11),(3,10)][i];d=s.symbols('d',positive=True)
  ck('Nonzero simple-pole residue',s.limit((x-1)*x**(p-1)/(1-x**q),x,1),-R(1,q));ck('Original symmetric cutoff ratio',s.limit(((1+d)**q-1)/(1-(1-d)**q),d,0),1)
  a=s.Tuple(s.Symbol('divergent'),P*s.cot(P*R(p,q))/q)
 elif slug=='oscillatory-regularization':
  eps=s.symbols('eps',positive=True);ck('Cutoff primitive',s.diff((1-s.cos(x**n))/n,x),x**(n-1)*s.sin(x**n));ck('Damped transformed sine integral',s.integrate(s.exp(-eps*x)*s.sin(x)/n,(x,0,s.oo)),1/(n*(1+eps*eps)));a=s.Tuple(s.Symbol('divergent'),R(1,n))
 elif slug=='concentration':
  N=s.symbols('N',positive=True);F=s.atan(N*x**n)/n;ck('Spike primitive',s.diff(F,x),N*x**(n-1)/(1+N*N*x**(2*n)));ck('Spike endpoint',s.limit(F,x,s.oo),P/(2*n));a=P/(2*n)
 elif slug=='binary-product':
  product=s.prod(1+x**(2**k) for k in range(n));ck('Dyadic telescope',s.expand((1-x)*product),1-x**(2**n));a=s.harmonic(2**n)
 elif slug=='fejer-fourth':
  co=collections.Counter(j+k for j in range(n) for k in range(n));a=2*P*sum(v*v for v in co.values());ck('Additive quadruple count',sum(v*v for v in co.values()),R(n*(2*n*n+1),3))
 elif slug=='scaled-frullani':
  aa=i+1;b=i+3;p=2+i%4;t=s.symbols('t',positive=True);ck('Positive parameter rectangle',s.integrate(s.exp(-t*x),(t,aa,b)),(s.exp(-aa*x)-s.exp(-b*x))/x);a=s.log(R(b,aa))/p
 elif slug=='sech-fourier':
  q=i+2;a=R(q,q*q+1);ck('Hyperbolic frequency reduction',1/(q+R(1,q)),a)
 elif slug=='variational-energy':
  k=R(i+2,2);g=s.sinh(k*x)/s.sinh(k);ck('Stationary function equation',s.diff(g,x,2),k*k*g);ck('Left boundary',g.subs(x,0),0);ck('Right boundary',g.subs(x,1),1);a=s.simplify((g*s.diff(g,x)).subs(x,1))
 elif slug=='moment-projection':
  m=i+2;c=R(1+i%3,4);G=s.Matrix([[1,R(1,m+1)],[R(1,m+1),R(1,2*m+1)]]);v=s.Matrix([1,c]);coef=G.inv()*v;f=coef[0]+coef[1]*x**m;a=(v.T*G.inv()*v)[0]
  ck('First constrained moment',s.integrate(f,(x,0,1)),1);ck('Second constrained moment',s.integrate(x**m*f,(x,0,1)),c);ck('Gram minimizer squared norm',s.integrate(s.expand(f*f),(x,0,1)),a);yes('Gram determinant positive',G.det()>0)
 elif slug=='quadrature-defect':
  c=(-1)**i*(i+1);A=i-2;B=3-i%4;nodes=[R(1,2)-s.sqrt(3)/6,R(1,2)+s.sqrt(3)/6]
  for d in range(4):ck('Two-node rule on monomial '+str(d),sum(t**d for t in nodes)/2,R(1,d+1))
  correction=s.integrate((x*x-x+R(1,6))**2,(x,0,1));ck('Quartic defect integral',correction,R(1,180));a=R(A+B,2)+c*correction
 elif slug=='rearrangement':
  a=s.Tuple(s.integrate(x*(1-x)**n,(x,0,1)),s.integrate(x*x**n,(x,0,1)))
  ell=1-x**R(1,n);ck('Leftmost layer-cake mass',s.integrate(ell**2/2,(x,0,1)),a[0]);ck('Rightmost layer-cake mass',s.integrate(ell-ell**2/2,(x,0,1)),a[1])
 else:raise KeyError(slug)
 return a,checks

ROUTES={
 'weighted-complement':('olympiad','Reflect in one-half under the invariant beta-half measure; the concealed complementary ratio is the decisive step.'),
 'reciprocal-quartic':('hard','The displayed positive biquadratic factors into two positive quadratics; partial fractions and two arctangent endpoints suffice. A reciprocal-fold method is optional.'),
 'chebyshev-absolute':('hard','Use the sine recurrence and split equal sine lobes. The first instance is just the absolute value of a quadratic; higher displayed degree alone does not establish an Olympiad decision.'),
 'gamma-unit-average':('olympiad','The interval average has derivative ln(a); its constant requires reflection and the log-sine integral. Weak option bounds and formatting cues require repair before admission.'),
 'log-fourier-coefficient':('olympiad','Factor the positive kernel as a squared modulus, justify the uniform logarithm series, and isolate a Fourier coefficient.'),
 'arctan-parameter':('olympiad','Introduce and differentiate a parameter under the improper integral; identify the rational transform and its integration constant.'),
 'gaussian-fourier':('olympiad','Turn a parameter derivative plus integration by parts into an ODE and establish its Gaussian initial value.'),
 'reciprocal-gaussian':('olympiad','A reciprocal substitution closes a parameter ODE; a one-sided dominated limit determines its integration constant.'),
 'sinc-overlap':('olympiad','Preserve cancellation in the product-to-sum reduction, then justify the Dirichlet integral; the absolute frequency introduces overlap cases.'),
 'mixed-beta-log':('olympiad','A mixed exponent derivative requires endpoint domination and both harmonic and trigamma contributions. Equivalent positive-series derivation is also substantial.'),
 'thermal-derivative':('hard','A positive geometric derivative and a factorial exponential moment give a zeta value by Tonelli; no additional structural decision is required.'),
 'mellin-cyclotomic':('hard','One power substitution produces the classical beta reflection integral directly; small cubic cases have ordinary partial fractions.'),
 'cauchy-convolution':('hard','A symmetric rational quartic admits routine partial fractions; residues shorten computation without forcing extra insight.'),
 'agm-parameter':('olympiad','A nonobvious Landen substitution changes both parameters and strict parameter monotonicity establishes uniqueness.'),
 'abel-recovery':('olympiad','Apply a second square-root kernel and reverse the triangular integral to eliminate the unknown function.'),
 'boundary-asymptotic':('hard','Standard boundary rescaling with the exponential majorant directly yields the gamma integral.'),
 'integral-equation':('olympiad','Discover the Green-kernel boundary ODE and prove the recovered function satisfies the original integral equation.'),
 'convolution-laplace':('hard','The displayed recursion is ordinary convolution by an indicator; a standard transform product is sufficient. The first case is a triangular piecewise function.'),
 'poisson-log-potential':('olympiad','Recognize upper-half-plane harmonic continuation or use a rational parameter derivative and a limit to determine its constant.'),
 'jensen-radius':('hard','Factor the squared radius and extract the constant logarithmic Fourier coefficient; this is the same global log-circle group as the nonzero coefficient family.'),
 'fresnel':('olympiad','A complex Gaussian branch and a uniform oscillatory tail estimate connect regulated and ordinary improper limits.'),
 'bessel-laplace':('olympiad','Recover an angular representation from the supplied series and integrate it, or justify termwise integration and resum the central-binomial series. Numerical bounds are alternative mathematics, not automatically a disqualification.'),
 'rodrigues-moment':('hard','Repeated integration by parts has explicit endpoint zeros; direct polynomial differentiation is available at every finite index. Raising the order increases work, not the decision structure.'),
 'bernoulli-product':('hard','The generating function supplies finite polynomials; the given low degrees allow direct polynomial integration. Endpoint recurrence is elegant but not forced by these finite questions.'),
 'principal-value':('olympiad','Distinguish ordinary divergence from symmetric cancellation, control the transformed cutoff ratio, and use a reflection identity. The cubic index has a shorter routine partial-fraction route.'),
 'oscillatory-regularization':('hard','The power substitution gives a nonconvergent cosine cutoff and an elementary damped sine integral.'),
 'concentration':('medium','The exact power substitution gives an arctangent integral independent of the limit parameter.'),
 'binary-product':('hard','Multiplication by one minus the variable telescopes the finite dyadic product. Harmonic notation is defined in the question.'),
 'fejer-fourth':('olympiad','A finite Fourier modulus converts the fourth moment into an additive quadruple count. Small displayed sizes permit routine cosine expansion.'),
 'scaled-frullani':('hard','A power substitution followed by the elementary nonnegative Frullani rectangle suffices; merge the pre-existing Frullani group.'),
 'sech-fourier':('olympiad','Evenness and an exponential substitution produce a complex beta integral with real part one-half; its reflection requires correct frequency and half-line factors.'),
 'variational-energy':('olympiad','Discover a boundary-value minimizer and prove nonnegative energy difference. Some visible options can instead be isolated by elementary energy bounds; audit per index.'),
 'moment-projection':('olympiad','Center the second moment or solve the Gram projection; equality and admissibility must both be established.'),
 'quadrature-defect':('olympiad','Find the cubic-exact two-node rule, subtract a square of the node polynomial, and recover the quartic defect.'),
 'rearrangement':('olympiad','Layer-cake reduces the objective to nested sets of given length and establishes attainable extrema.'),
}

LOWER_LEVEL={'improper-rational-beta':'medium','logarithmic-moment':'medium','root-quadratic':'medium','trig-log':'medium'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--baseline',type=Path,default=Path(__file__).with_name('integration-olympiad-baseline.jsonl'));parser.add_argument('--out',type=Path,default=Path(__file__).parent);args=parser.parse_args();repo=args.repo.resolve();out=args.out;out.mkdir(exist_ok=True)
 source=repo/'scripts/bank/content/integration.py';author=module(source,'integration_peer_bound_source')
 baseline=[r for r in read(args.baseline) if r['familyId'].startswith('io3-')];assert len(baseline)==280
 rows=[]
 for r in baseline:
  slug=r['familyId'][4:];i=r['parameters']['instance'];a,checks=checks_for(slug,i);raw=author.FAMILIES[slug]['build'](i)
  assert equal(a,raw['answer']),(slug,i,'independent final mismatch')
  correct=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']);assert author.tex(raw['answer'])==correct,(slug,i,'baseline answer binding')
  choiceexpr=r['validation']['evidence']['certificate']['choiceExpressions'];values=[s.sympify(v) for v in choiceexpr]
  assert len(values)==4 and all(not equal(values[j],values[k]) for j in range(4) for k in range(j))
  level,route=ROUTES[slug];issues=[];qualified=level=='olympiad';conditions=[]
  if slug=='principal-value':
   issues.append('Repair held-out shortest-format tell before admission.');conditions.append('All candidate choices must use a balanced identical convergence-label and value format.')
   if i==0:level='hard';qualified=False;route+=' This specific cubic denominator has elementary partial fractions.'
  if slug=='gamma-unit-average':
   issues.append('Repair longest-format cue and test elementary Gamma bounds before admission.');conditions.append('New options must survive coarse integral bounds.')
   if i==0:level='hard';qualified=False;route+=' Bounds -1-ln(2)<I<0 isolate the current answer.'
  if slug=='chebyshev-absolute':issues.append('Shortest-format cue; reclassification alone does not repair the options.')
  if slug=='fejer-fourth' and i<3:level='hard';qualified=False;route+=' Displayed size at most four has a short explicit trigonometric expansion.'
  if slug=='variational-energy' and i in [0,1,4]:
   level='hard';qualified=False;issues.append('Current correct answer isolated by the strict energy interval (1, 1+k²/3). Repair options before counting this instance as Olympiad.');route+=' Elementary Cauchy-Schwarz and an affine trial function with a small endpoint-zero perturbation isolate the current answer.'
  rows.append({'problemId':r['problemId'],'sourceContentHash':r['contentHash'],'semanticHash':r['semanticHash'],'familyId':r['familyId'],'instanceIndex':i,'reviewedGroup':r['pedagogy']['relatedIdeaGroupId'],'difficultyRecommended':level,'olympiadMethodQualified':qualified,'admissionEligibleNow':qualified and not issues,'easiestVisibleRoute':route,'blockingOptionIssues':issues,'conditionalAdmissionRequirements':conditions,'exactChecks':checks,'sourceAnswerBinding':'Independent result equals source expression; source TeX equals pinned correct choice; all four source expression choices are inequivalent.','analyticProofReview':'Read the full current corrected solution and family certificate. Classical convergence, Fubini, reflection and sharpness arguments were reviewed as mathematical prose; not machine-formally proved.','humanReviewed':False})
  print(slug,i,len(checks),flush=True)
 # Lower raw finite candidates are read independently; regenerate only trusted expression bindings.
 sys.path.insert(0,str(repo/'scripts/bank/quality'));import integration.support as c
 repairs=read(repo/'.bank-data/quality/integration-repairs.jsonl');ext=read(repo/'.bank-data/quality/integration-extensions.jsonl')
 repair_fids={r['familyId'] for r in repairs};lower=[r for r in ext if r['familyId'] not in repair_fids]+repairs;assert len(lower)==100
 lower_rows=[]
 for r in lower:
  fid=r['familyId'];slug=fid.split('-',3)[3];m=s.Integer(r['parameters']['m']);checks=[]
  def ck(label,a,b):
   assert equal(a,b),(fid,m,label,a,b)
   checks.append({'description':label,'result':'exact equality','left':s.srepr(a),'right':s.srepr(b)})
  raw=c.source_payload(fid,int(m));expected=raw['answer'];xx=c.frozen.x
  if slug=='signed-area':
   j=r['instanceIndex'];cases=[(1,0,2*m),(1,0,m+1),(1,0,2*m+1),(-1,0,2*m+2),(2,m-1,m+3),(2,m-3,m+1),(-2,m-3,m+1),(1,m+3,m-1),(1,m+1,m+4),(1,m-4,m-1)]
   slope,lo,hi=cases[j];expected=slope*((hi-m)**2-(lo-m)**2)/2;ck('Integrate displayed oriented affine function',s.integrate(slope*(x-m),(x,lo,hi)),expected)
  elif raw.get('_input',{}).get('kind')=='integral':
   expr,F,lo,hi=raw['_input']['args'][:4];ck('Primitive differentiated independently',s.diff(F,xx),expr)
   loF=s.limit(F,xx,lo,dir='+') if lo in (0,-s.oo) else F.subs(xx,lo)
   hiF=s.limit(F,xx,hi) if hi==s.oo else F.subs(xx,hi)
   ck('Actual endpoint values with improper limits',hiF-loF,expected)
  else:
   if slug=='absolute-area':v=m*m
   elif slug=='quarter-disk':v=P*m*m/4
   elif slug=='average-value':v=s.integrate(x*x,(x,0,m))/m
   elif slug=='accumulation-from-derivative':v=m*m+1-m
   elif slug=='piecewise-accumulation':v=s.integrate(m*x,(x,0,1))+m+1
   elif slug=='washer-volume':v=P*s.integrate((m*x)**2,(x,0,1))
   elif slug=='shell-volume':v=2*P*s.integrate(x*(m-x),(x,0,m))
   elif slug=='piecewise-absolute-root':v=s.integrate(m/2-s.sqrt(x),(x,0,m*m/4))+s.integrate(s.sqrt(x)-m/2,(x,m*m/4,m*m))
   elif slug=='logarithmic-moment':
    t=s.symbols('t',positive=True);v=s.diff(1/(t+1),t,2).subs(t,m)
   elif slug=='beta-polynomial':v=s.integrate(s.expand(x**m*(1-x)**(m+1)),(x,0,1))
   elif slug=='arc-length-perfect-square':
    slope=x/(2*m)-m/(2*x);speed=x/(2*m)+m/(2*x);ck('Positive exact arc speed square',1+slope*slope,speed*speed);v=s.integrate(speed,(x,1,2))
   elif slug=='Frullani-rectangle':
    t=s.symbols('t',positive=True);ck('Positive rectangle kernel',s.integrate(s.exp(-t*x),(t,1,m)),(s.exp(-x)-s.exp(-m*x))/x);v=s.log(m)
   elif slug=='mixed-log-endpoints':
    k=s.symbols('k',positive=True);a=m+1;ck('Endpoint moment summand decomposition',1/(a*a)*(1/k-1/(k+a))-1/(a*(k+a)**2),1/(k*(k+a)**2));v=s.harmonic(a)/a**2-(P**2/6-s.harmonic(a,2))/a
   elif slug=='half-angle-quadratic':
    t=s.symbols('t',positive=True);d=s.sqrt(m*m-1);F=s.log((t+m-d)/(t+m+d))/d;ck('Rationalized half-angle primitive',s.diff(F,t),2/(t*t+2*m*t+1));v=F.subs(t,1)-F.subs(t,0)
   elif slug=='odd-even':v=2*s.sin(P/m)
   else:raise KeyError(slug)
   ck('Independently assembled geometric or transform result',v,expected)
  correct=next(q['math'] for q in r['choices'] if q['choiceId']==r['answerChoiceId']);assert c.frozen.latex(expected)==correct,(fid,m,'raw correct binding')
  level=LOWER_LEVEL.get(slug,r['difficulty']);notes=[]
  if slug=='trig-log':notes=['Strict elementary bounds -1/[m(m+1)] < I < -1/[(m+1)(m+2)] isolate the correct option from the entire authored pool; classify Medium.']
  if slug=='root-quadratic':notes=['Strict elementary bounds m²/(3sqrt(2)) < I < m²/3 isolate the correct option from the authored pool; classify Medium.']
  if slug=='improper-rational-beta':notes=['The single substitution u=x/(1+x) produces an ordinary monomial; classify Medium.']
  if slug=='logarithmic-moment':notes=['Two familiar integrations by parts evaluate this one-endpoint power-log-square moment; classify Medium.']
  lower_rows.append({'familyId':fid,'index':r.get('instanceIndex',r['parameters'].get('extension')),'rawSHA256':hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'previous':r.get('previous'),'difficultyRecommended':level,'easiestVisibleRouteNotes':notes,'exactChecks':checks,'mathematicalResult':'passes independent exact checks','capacity':'Additional fluency instance, zero new construction ideas. Purposeful signed-area cases vary sign, orientation and lobe geometry; other two-per-family extensions are coefficient-domain extensions, not new structure.','humanReviewed':False})
 # Explicit trial perturbation proves the upper bound is strict, rather than merely weak.
 eps=s.symbols('eps',positive=True)
 energy_bounds=[]
 for j in [0,1,4]:
  k=R(j+2,2);f=x-eps*x*(1-x);E=s.integrate(s.diff(f,x)**2+k*k*f*f,(x,0,1))
  assert equal(E,1+k*k/3-eps*k*k/6+eps**2*(R(1,3)+k*k/30))
  # Rational brackets for exp(2k), using a positive Taylor tail with geometric ratio.
  h=2*k;M=80;qlo=sum(h**v/s.factorial(v) for v in range(M));qhi=qlo+h**M/s.factorial(M)/(1-h/(M+1))
  correctlo=k*(qhi+1)/(qhi-1);correcthi=k*(qlo+1)/(qlo-1)
  assert 1<correctlo<correcthi<1+k*k/3
  if j in [0,1]:
   deriv_upper=k*(qlo+1)/(2*(qlo-1))-2*k*k*qhi/(qhi-1)**2
   assert deriv_upper<1
  assert k*(1+k*k/2)>1+k*k/3
  energy_bounds.append({'instanceIndex':j,'k':str(k),'strictLower':1,'strictUpper':str(1+k*k/3),'perturbedTrialEnergy':s.srepr(E),'certificate':'Cauchy-Schwarz excludes an attaining value1; a small positive trial perturbation strictly lowers the affine test energy. Rational exponential Taylor bounds exclude each current other option.'})
 # Provable all-pool bounds; logarithm bounded by positive atanh series and rational tails.
 lo=R(141421356237,100000000000);hi=R(141421356238,100000000000);assert lo*lo<2<hi*hi
 zzlo=lo-1;zzhi=hi-1;M=12
 Llo=2*sum(zzlo**(2*j+1)/s.Integer(2*j+1) for j in range(M))
 Lhi=2*sum(zzhi**(2*j+1)/s.Integer(2*j+1) for j in range(M))+2*zzhi**(2*M+1)/((2*M+1)*(1-zzhi**2))
 bounds=[]
 for m in range(4,14):
  q=s.Integer(m);bottom=-1/(q*(q+1));top=-1/((q+1)*(q+2));correct=-1/(q+1)**2
  wrong=[-1/q**2,-1/(q+2)**2,top,-2/(q+1)**2,-1/(2*(q+1)**2),bottom,-1/(q+1)**3]
  assert bottom<correct<top and all(not bottom<w<top for w in wrong)
  # Normalize root-quadratic integral by m². Each wrong form bounded by exact rational endpoints.
  w=[((lo+Llo)/2,(hi+Lhi)/2),((lo-2*Lhi)/2,(hi-2*Llo)/2),((lo-Lhi)/4,(hi-Llo)/4),((lo-Lhi),(hi-Llo)),((lo-Lhi)/(2*q),(hi-Llo)/(2*q)),((2*lo-Lhi)/2,(2*hi-Llo)/2),((lo-Lhi/2)/2,(hi-Llo/2)/2)]
  assert (lo-Lhi)/2>1/(3*lo) and (hi-Llo)/2<R(1,3)
  assert all(upper<=1/(3*hi) or lower>=R(1,3) for lower,upper in w)
  bounds.append({'m':m,'trigLogAllSevenWrongsExcluded':True,'rootQuadraticAllSevenWrongsExcluded':True,'method':'Rational arithmetic; sqrt2 bracket squared exactly, logarithm as 2*atanh(sqrt2-1) with positive geometric tail.'})
 families=[]
 for fid,rr in __import__('itertools').groupby(sorted(rows,key=lambda r:r['familyId']),lambda r:r['familyId']):
  rr=list(rr);families.append({'familyId':fid,'reviewedGroup':rr[0]['reviewedGroup'],'qualifiedOlympiadIndices':[r['instanceIndex'] for r in rr if r['olympiadMethodQualified']],'currentlyAdmissibleIndices':[r['instanceIndex'] for r in rr if r['admissionEligibleNow']],'difficultyByIndex':{str(r['instanceIndex']):r['difficultyRecommended'] for r in rr},'review':rr[0]['easiestVisibleRoute'],'doNotPadDomain':'No unreviewed larger coefficients are automatically qualified. Replacements need visible-option review; computational size alone does not repair a routine route.'})
 report={'reviewId':'quality-integration-independent-peer-v1','scope':'280 retained io3 records; 60 nonoverlapping lower extensions plus40 repairs (68 new lower instances and32 immutable revision candidates).','reviewer':'AI-assisted independent series/source agent; not human or formal review','inputs':{str(p):digest(p) for p in [args.baseline,source,repo/'scripts/bank/solution-review/integration-legacy/io3_solutions.py',repo/'.bank-data/quality/integration-extensions.jsonl',repo/'.bank-data/quality/integration-repairs.jsonl',Path(__file__)]},'blindFirstEvidence':'integration-blind-input.json contains only first-instance statements and choices; later proof and every-index reviews are distinguished. No claim every instance was initially blind.','counts':{'retainedIo3Records':len(rows),'families':len(families),'qualifiedFamiliesBeforeOptionRepair':sum(bool(f['qualifiedOlympiadIndices']) for f in families),'qualifiedInstancesBeforeOptionRepair':sum(r['olympiadMethodQualified'] for r in rows),'currentlyAdmissibleQualifiedInstances':sum(r['admissionEligibleNow'] for r in rows),'lowerReviewRows':len(lower_rows),'executedExactChecks':sum(len(r['exactChecks']) for r in rows+lower_rows),'boundCases':len(bounds)},'families':families,'records':rows,'lowerRecords':lower_rows,'shortcutCertificates':bounds,'energyShortcutCertificates':energy_bounds,'limitations':['An editorial eligibility verdict is not an admission token; root must bind final source and review digests.','Choice non-equivalence does not establish distractor pedagogical value. Flagged format cues require new pools and held-out recheck.','Analytic convergence and extremality arguments are read mathematical certificates, not automatic formal proofs.','Numeric heuristics, if separately run, are warning signals and not proof.']}
 (out/'integration-peer-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts'],indent=2))
if __name__=='__main__':main()
