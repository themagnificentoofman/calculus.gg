"""Separate finite oracle for the97 stage05/06 additions, without author imports."""
from pathlib import Path
import hashlib,itertools,json,math,sys
import sympy as s
x,t,h=s.symbols('x t h',real=True)
SLUGS=['abel-density-recovery','laplace-moment-sharp-third','periodic-shift-derivative-bound','lorentzian-derivative-zero-window','chebyshev-edge-derivative-correction','singular-reparametrized-wronskian','hermite-inverse-gap-moment','cosine-equation-regularity','commuting-parabolic-jet']
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def truncate(p,n):return s.Add(*(v*x**k[0] for k,v in s.Poly(s.expand(p),x).terms() if k[0]<=n))
def solve(p):
 c=p['parameters']['case'];slug=next(k for k in SLUGS if p['familyId'].endswith(k));checks=[]
 if slug=='abel-density-recovery':
  density=sum(s.Integer(v)*x**j for j,v in enumerate(c['coefficients']));at=s.Rational(c['at']);assert 0<at<1
  # Beta moments are evaluated by u=sin(theta)^2 and integration by parts.
  moments=[s.Rational(2)]
  for j in range(1,len(c['coefficients'])):moments.append(s.cancel(moments[-1]*2*j/(2*j+1)))
  transform=sum(v*moments[j]*x**s.Rational(2*j+1,2) for j,v in enumerate(c['coefficients']))
  assert s.latex(transform) in p['statement']
  answer=s.diff(density,x).subs(x,at)
  checks=['Independent beta-moment recurrence reconstructs the literal right-hand side; derivative of recovered polynomial evaluated exactly. Composing two Abel kernels gives pi times the primitive by absolute Fubini, proving injectivity for continuous densities.']
 elif slug=='laplace-moment-sharp-third':
  a,b=s.Rational(c['a']),s.Rational(c['b']);q=(a-b)/(1-a);w=(1-a)/(1-q);assert 0<q<1 and 0<w<1
  assert s.simplify(w*q+(1-w)-a)==0 and s.simplify(w*q*q+(1-w)-b)==0
  dual=s.expand((1-t)*(t-q)**2+t**3);bound=sum(v*{0:1,1:a,2:b}[k[0]] for k,v in s.Poly(dual,t).terms());answer=w*q**3+1-w;assert s.simplify(bound-answer)==0
  checks=['An independently constructed two-atom probability measure satisfies both moments. The nonnegative polynomial(1-t)(t-q)^2 bounds every competing third moment and vanishes on both atoms, proving exact attainment. Compact support justifies differentiating the Laplace transform.']
 elif slug=='periodic-shift-derivative-bound':
  e,o=c['even'],c['odd'];assert e%2==0 and o%2==1 and math.gcd(e,o)==1
  A=s.Rational(e*e+o*o,2);B=s.Rational(o*o-e*e,2);answer=s.sqrt(e*e+o*o)
  f=(e*s.sin(e*x)+o*s.sin(o*x))/answer
  assert s.simplify(s.diff(f,x,2)+A*f-B*f.subs(x,x+s.pi))==0
  assert s.integrate(s.expand_trig(f*f),(x,0,2*s.pi))==s.pi and s.simplify(s.diff(f,x).subs(x,0)-answer)==0
  checks=['Split f into the plus/minus eigenspaces of translation by pi. Each solves its own constant-coefficient oscillator; periodicity restricts to the two stated frequencies. Orthogonal coefficient norm gives Cauchy-Schwarz; exact residual, normalization and attaining derivative checked.']
 elif slug=='lorentzian-derivative-zero-window':
  n,q,a,b=c['order'],c['q'],c['a'],c['b'];assert 0<a<b<q
  answer=s.Integer(sum(a*(n+1)<j*q<b*(n+1) for j in range(1,n+1)))
  # Check pole expression against differentiating the real rational function.
  real=s.cancel(s.diff(1/(1+x*x),x,n));poles=(-1)**n*s.factorial(n)/(2*s.I)*((x-s.I)**(-n-1)-(x+s.I)**(-n-1));assert s.cancel(real-poles)==0
  checks=['Direct rational differentiation independently agrees with the complex-pole expression. Cotangent maps the real line bijectively to0<theta<pi; zeros occur at j*pi/(n+1). Strict integer inequalities count the specified open interval, including endpoint exclusions.']
 elif slug=='chebyshev-edge-derivative-correction':
  a=s.pi*s.Rational(c['phase']);theta=a*h+a**3*h**3/24
  assert s.series(s.cos(theta)-(1-a*a*h*h/2),h,0,6).removeO()==0
  quotient=s.series(s.sin(s.expand(theta/h))/(s.sin(theta)/h),h,0,3).removeO();answer=s.expand(quotient).coeff(h,2)
  checks=['Conjugate the recurrence to angle doubling. Independent series division of sin(theta/h)/(sin(theta)/h), with h=2^-n, recovers the correction. The inverse-cosine remainder and nonzero fixed phase justify the division and limit.']
 elif slug=='singular-reparametrized-wronskian':
  r,h0=c['r'],c['h'];g=x**h0+x**(h0+1);N=r*(r-1)//2
  # Composition derivatives are lower triangular in derivatives with respect
  # to g; their diagonal entries are(g prime)^i. The remaining determinant is
  # a nonzero Vandermonde in1..r, not a numeric determinant guess.
  V=s.det(s.Matrix(r,r,lambda i,j:s.Integer(j+1)**i));assert V!=0
  lead=s.Poly(s.diff(g,x)**N,x);answer=s.Integer(min(k[0] for k,v in lead.terms() if v))
  assert answer==(h0-1)*N
  checks=['Triangular chain-rule change of derivative basis separates(g prime)^(r(r-1)/2), an exponential with nonzero value at zero, and a checked nonzero Vandermonde. The first exponent of the exact polynomial factor gives the order.']
 elif slug=='hermite-inverse-gap-moment':
  n,q=c['n'],c['q'];coeff={n:s.Integer(1),n-1:s.Integer(0)}
  for j in range(n-2,-1,-1):coeff[j]=s.cancel(-(j+2)*(j+1)*coeff[j+2]/(2*(n-j)))
  P=sum(v*x**j for j,v in coeff.items());assert s.expand(s.diff(P,x,2)-2*x*s.diff(P,x)+2*n*P)==0
  assert s.gcd(P,s.diff(P,x))==1
  # Root power sums from multiplication by x in Q[x]/(P), rather than the
  # author's Newton recurrence or tabulated Hermite moments.
  C=s.zeros(n)
  for j in range(n-1):C[j+1,j]=1
  for j in range(n):C[j,n-1]=-coeff[j]
  answer=s.cancel(((2*n-2)*s.trace(C**(2*q))-s.trace(C**(2*q+2)))/3)
  checks=['Solve the displayed differential equation coefficient by coefficient and check its residual and square-free gcd. At a root, logarithmic derivatives and the differentiated ODE give sum inverse-square gaps=(2n−2−r²)/3. Independent companion-matrix traces supply the needed root moments.']
 elif slug=='cosine-equation-regularity':
  answer=s.log(2)**2;assert s.simplify(s.cosh(s.log(2)).rewrite(s.exp))==s.Rational(5,4)
  checks=['Evenness follows from x=0. Integrating the functional equation in y on a small symmetric interval expresses f as an integral of translates divided by a nonzero constant; bootstrap continuity to smoothness. Twice differentiating yields f second=c f with f(0)=1,f prime(0)=0. f(1)=5/4 excludes the cosine/constant branches and gives sqrt(c)=ln2. One normalized item, not scalar variants.']
 else:
  n,r=c['order'],c['r'];F=x+x*x+c['b']*x**3+c['c']*x**4;G=x
  for _ in range(r):G=truncate(G+G*G+c['b']*G**3+c['c']*G**4,n+1)
  answer=s.factorial(n)*s.expand(G).coeff(x,n);assert s.expand(G).coeff(x,2)==r
  assert truncate(F.subs(x,G)-G.subs(x,F),n+1)==0
  # Direct commutation coefficients recover the unique finite jet separately.
  jet=x+r*x*x
  for k in range(3,n+1):
   z=s.Symbol('z');trial=jet+z*x**k
   equation=truncate(F.subs(x,trial)-trial.subs(x,F),k+1).coeff(x,k+1)
   value=s.solve(equation,z);assert len(value)==1;jet+=value[0]*x**k
  assert s.expand(jet).coeff(x,n)*s.factorial(n)==answer
  checks=['Truncated polynomial iteration supplies an analytic commuting witness. Separately solve successive commutation coefficients to determine the unique requested jet. The leading difference at order k produces a nonzero factor k−2; no full analytic-centralizer theorem is needed.']
 return s.simplify(answer),checks

def main(path,out):
 data=Path(path).read_bytes();rows=[r for r in json.loads(data) if any(r['familyId'].endswith(k) for k in SLUGS)];results=[]
 for r in rows:
  try:
   answer,checks=solve(r);values=[s.sympify(c['expression']) for c in r['choices']];matches=[j for j,v in enumerate(values) if s.simplify(v-answer)==0]
   assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
   assert all(s.simplify(a-b).equals(0)is False for a,b in itertools.combinations(values,2))
   results.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'independentAnswer':s.srepr(answer),'checks':checks,'allSixChoicePairsDistinct':True,'passed':True})
  except Exception as e:results.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'passed':False,'error':str(e)})
 report={'reviewer':'root-independent-review','author':'coverage_research','sourceArtifactSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(rows),'passed':sum(r['passed'] for r in results),'results':results,'scope':'Sample statements solved before reading proofs. No author constructor imported. All finite answers independently derived and six expression-pairs checked. Analytic arguments are AI mathematical review, not formal/human certification. Literal notation fixes, option-form review and final source binding remain separate; no admission conferred.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));return report['passed']==len(rows)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
