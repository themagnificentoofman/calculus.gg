"""Independent finite answer and editorial review of the 19 retained M3 groups.

Solve from the displayed task and parameters first. Frozen constructors are used
only afterward to bind their expression choices to the immutable literal TeX;
their answer field is not the mathematical oracle. Analytic arguments below are
reviewed mathematics, not machine proofs or human certification.
"""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/bank'))
x,z=s.symbols('x z',real=True)

REVIEWS={
 'implicit-series-inversion':('hard','Solve the quadratic for the branch vanishing at zero; a binomial expansion gives the requested coefficient. Lagrange inversion is optional.'),
 'iterated-Mobius':('hard','Compose the two-by-two fractional-linear matrix and use its determinant-one derivative. Four through eleven iterations add computation, not another decision.'),
 'exponential-partition-coefficient':('hard','Expand exp(x/(1-x)) to the finite requested order, or use its first-order differential recurrence. No partition theorem is required.'),
 'noncommuting-operator':('medium','Differentiate the displayed exponential once: it is an eigenfunction of L with eigenvalue one. Every iterate has value one.'),
 'interpolation-derivative':('olympiad','Construct (x+1)P(x)-1, use its prescribed zeros and its value at minus one, then differentiate. The rational remainder supplies the central reframing.'),
 'nonlinear-recursion-rate':('olympiad','Prove monotone decay to zero and choose the reciprocal power whose successive increments tend to a nonzero constant; Cesaro averaging gives the scale.'),
 'Laplace-degenerate-endpoint':('hard','One power rescaling gives the increasing-cutoff Gamma integral directly. Same difficulty and global idea as the integration boundary-asymptotic construction.'),
 'irrational-rotation-correlation':('olympiad','Establish equidistribution using geometric sums, then integrate the correlated, piecewise quadratic product across its wrap point.'),
 'Newton-double-exponential-rate':('olympiad','Find the cross ratio that conjugates the Newton map to squaring and control the remaining root-limit factor; mere convergence is insufficient.'),
 'recurrence-Hankel-growth':('olympiad','The dominant roots cancel in the adjacent two-by-two determinant. Derive its exact first-order determinant recurrence and positivity before taking roots.'),
 'Dirichlet-endpoint-trace':('olympiad','Recognize the odd Dirichlet kernel and its two endpoint traces; justify the Fourier boundary value instead of applying ordinary oscillatory cancellation.'),
 'monic-minimax-rate':('olympiad','Prove a matching Chebyshev upper bound and alternating-node lower bound; interval length is a pure scaling and contributes one advanced lineage.'),
 'binomial-moving-threshold':('hard','Identify a fair-binomial distribution and standardize its moving threshold in the central limit theorem. The displayed error function requires only the normal-CDF conversion.'),
 'coupon-coverage-window':('olympiad','Use empty-box inclusion-exclusion, pass fixed factorial moments to the exponential law, and sandwich the alternating partial sums before removing the truncation.'),
 'gcd-pair-density':('olympiad','Use Mobius inversion with a summable tail to establish the coprime density. Prescribing a different fixed gcd is a pure lattice scaling: one advanced lineage.'),
 'sharp-endpoint-derivative':('olympiad','Prove the sharp endpoint bound from alternating interpolation weights and exhibit a Chebyshev extremizer; the degree changes the actual extremal polynomial.'),
 'cyclic-determinant-second-derivative':('olympiad','Count two-deleted principal minors of the cycle Laplacian, including path lengths; a general determinant formula alone does not resolve the zero mode.'),
 'oscillatory-regularity-pair':('olympiad','Separate existence of a derivative at zero from continuity there; induction identifies the leading oscillatory term, and phase sequences show sharp failure.'),
 'newton-iteration-jet':('olympiad','Track the first nonzero local error through three compositions. Only the quadratic coefficient enters, so the eight power parameters share one advanced coefficient-scaling lineage.'),
}

def solve(p):
 fid=p['familyId'];slug=fid.split('-olympiad-',1)[1];m=s.Integer(p['provenance']['authoring']['builderParameters']['m']);checks=[]
 def ck(label,a,b):
  assert equal(a,b),(slug,m,label,a,b)
  checks.append({'description':label,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
 if slug=='implicit-series-inversion':
  branch=(1-2*x-s.sqrt(1-4*x))/(2*x)
  answer=s.factorial(m)*s.series(branch,x,0,int(m)+1).removeO().coeff(x,m)
  ck('Chosen algebraic branch satisfies the equation',branch-x*(1+branch)**2,0)
 elif slug=='iterated-Mobius':
  M=s.Matrix([[1,1],[1,2]])**int(m);answer=1/M[1,1]**2
  ck('Composition matrix determinant',M.det(),1)
 elif slug=='exponential-partition-coefficient':
  # Independently propagate (1-x)^2 F prime=F with F(0)=1.
  a=[s.Integer(1)]
  for k in range(int(m)):
   a.append(((2*k+1)*a[k]-(k-1)*a[k-1] if k else a[0])/(k+1))
  answer=s.factorial(m)*a[int(m)]
  ck('Derivative differential equation',s.diff(s.exp(x/(1-x)),x)*(1-x)**2,s.exp(x/(1-x)))
 elif slug=='noncommuting-operator':
  g=s.exp(-x*x+x);ck('The literal function is an eigenfunction',s.diff(g,x)+2*x*g,g);answer=s.Integer(1)
 elif slug=='interpolation-derivative':
  # Direct interpolation is independent of the author's rational-remainder proof.
  P=s.interpolate([(j,s.Rational(1,j+1)) for j in range(int(m)+1)],x);answer=s.diff(P,x).subs(x,0)
  ck('Rational interpolation nodes',s.Tuple(*(P.subs(x,j) for j in range(int(m)+1))),s.Tuple(*(s.Rational(1,j+1) for j in range(int(m)+1))))
 elif slug=='nonlinear-recursion-rate':
  b=s.symbols('b',positive=True);answer=m**(-1/m)
  ck('Reciprocal-power increment at infinity',s.limit(b*(s.exp(m/b)-1),b,s.oo),m)
 elif slug=='Laplace-degenerate-endpoint':answer=s.gamma(1/m)/m
 elif slug=='irrational-rotation-correlation':
  a=1/(m+1);answer=s.integrate(x*(x+a),(x,0,1-a))+s.integrate(x*(x+a-1),(x,1-a,1))
 elif slug=='Newton-double-exponential-rate':
  root=s.sqrt(2);N=(x+2/x)/2;answer=(m-root)/(m+root)
  ck('Exact cross-ratio conjugacy',(N-root)/(N+root),((x-root)/(x+root))**2)
 elif slug=='recurrence-Hankel-growth':
  trace=2*m+1;det=m*m+m-1;a,b,c,d=s.symbols('a b c d');answer=det
  ck('Adjacent determinant recurrence',b*(trace*(trace*b-det*a)-det*b)-(trace*b-det*a)**2,det*(a*(trace*b-det*a)-b*b))
  ck('Positive initial determinant',2*(trace*trace-2*det)-trace*trace,5)
 elif slug=='Dirichlet-endpoint-trace':answer=s.pi**(m+1)/2
 elif slug=='monic-minimax-rate':answer=m/2
 elif slug=='binomial-moving-threshold':answer=(1+s.erf(m/(2*s.sqrt(2))))/2
 elif slug=='coupon-coverage-window':answer=s.exp(-1/m)
 elif slug=='gcd-pair-density':answer=6/(m*m*s.pi*s.pi)
 elif slug=='sharp-endpoint-derivative':
  answer=m*m;T=s.chebyshevt(m,x);ck('Endpoint derivative of an attaining polynomial',s.diff(T,x).subs(x,1),answer)
 elif slug=='cyclic-determinant-second-derivative':
  n=int(m);L=s.Matrix(n,n,lambda i,j:2 if i==j else -1 if (i-j)%n in [1,n-1] else 0)
  cp=L.charpoly(z);answer=2*(-1)**n*cp.nth(2)
  ck('Cycle zero row sum',L*s.ones(n,1),s.zeros(n,1))
 elif slug=='oscillatory-regularity-pair':
  power=2*m+2;answer=s.Tuple(m+1,m)
  # Track the leading sin/cos power under differentiation; its coefficient
  # never vanishes. Difference quotients establish r, continuity establishes s.
  g=x**power*s.sin(1/x)
  for j in range(int(m)+1):g=s.diff(g,x)
  assert s.expand(g).has(s.sin(1/x),s.cos(1/x));checks.append({'description':'Exact differentiation through the sharp continuity threshold','result':'executed symbolic differentiation','order':int(m)+1})
 elif slug=='newton-iteration-jet':
  N=x-(x**m-1)/(m*x**(m-1));c=s.diff(N,x,2).subs(x,1)/2
  ck('Fixed point and zero first derivative',s.Tuple(N.subs(x,1),s.diff(N,x).subs(x,1)),s.Tuple(1,0))
  # Direct composition of truncated polynomials through degree eight.
  jet=s.series(N.subs(x,1+z)-1,z,0,9).removeO();value=z
  def truncate(poly):return sum(v*z**e[0] for e,v in s.Poly(s.expand(poly),z).terms() if e[0]<=8)
  for _ in range(3):
   power=s.Integer(1);total=s.Integer(0)
   for k in range(1,9):
    power=truncate(power*value);total+=jet.coeff(z,k)*power
   value=truncate(total)
  answer=s.factorial(8)*s.expand(value).coeff(z,8);ck('No lower error survives',s.Tuple(*(s.expand(value).coeff(z,k) for k in range(1,8))),s.Tuple(*([0]*7)))
 else:raise ValueError(slug)
 return answer,checks

def equal(a,b):
 if isinstance(a,(s.Tuple,tuple,list)) or isinstance(b,(s.Tuple,tuple,list)):
  return len(a)==len(b) and all(equal(c,d) for c,d in zip(a,b))
 if isinstance(a,s.MatrixBase):return a==b
 return s.simplify(s.expand_func(a-b))==0

def source_choice_values(p):
 # Source is only a literal-choice expression binding after independent solve.
 import content_pipeline as c
 mod=c.module_for(p['familyId']);m=s.Integer(p['provenance']['authoring']['builderParameters']['m'])
 family=next(v for v in mod.FAMILIES if v['familyId']==p['familyId']) if isinstance(mod.FAMILIES,list) else mod.FAMILIES[p['familyId']]
 if hasattr(mod,'CHECKS'):
  token=mod.CHECKS.set([])
  try:raw=family['build'](m)
  finally:mod.CHECKS.reset(token)
 else:raw=family['build'](m)
 values=[raw['answer']]+[v for v,_ in raw.get('options',raw.get('wrongs',raw.get('pool',[])))]
 latex=getattr(mod,'L',getattr(mod,'latex',None));result=[]
 for ch in p['choices']:
  matches=[v for v in values if latex(v)==ch['math']]
  assert matches,('unbound literal choice',p['familyId'],ch['math'])
  result.append(matches[0])
 return result

def main(inp,out):
 data=Path(inp).read_bytes();rows=[json.loads(l) for l in data.splitlines()];results=[]
 for p in rows:
  slug=p['familyId'].split('-olympiad-',1)[1];level,route=REVIEWS[slug]
  if slug=='cyclic-determinant-second-derivative' and p['parameters']['instance']==0:level='hard';route='The four-by-four literal determinant factors directly into x(x+2)^2(x+4); its second coefficient is a routine calculation.'
  try:
   answer,checks=solve(p);values=source_choice_values(p)
   matches=[i for i,v in enumerate(values) if equal(v,answer)]
   assert len(matches)==1 and p['choices'][matches[0]]['choiceId']==p['answerChoiceId'],('answer mismatch',answer)
   assert all(not equal(a,b) for a,b in itertools.combinations(values,2))
   alias=p['problemId']
   if slug in ['newton-iteration-jet','monic-minimax-rate','gcd-pair-density']:alias=p['familyId']+':normalized'
   results.append({'problemId':p['problemId'],'sourceContentHash':p['contentHash'],'semanticHash':p['semanticHash'],'familyId':p['familyId'],'index':p['parameters']['instance'],'passed':True,'independentAnswer':s.srepr(answer),'checks':checks,'difficultyRecommended':level,'qualifiedOlympiad':level=='olympiad','easiestOptionsVisibleRoute':route,'normalizedLineageKey':alias,'admission':'Mathematics and editorial verdict only; any unresolved option-screen defects still block admission.'})
  except Exception as e:results.append({'problemId':p['problemId'],'familyId':p['familyId'],'index':p['parameters']['instance'],'passed':False,'error':str(e)})
 report={'reviewer':'root-independent-review','author':'frozen-M3-content','artifactSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(rows),'passed':sum(r['passed'] for r in results),'reviewScope':'Independent finite answers, literal expression-choice binding, pairwise exact inequivalence and options-visible editorial routes. Existing proof certificates subsequently inspected; not a fully blind review, formal proof or human certification. Full option-screen dispositions remain required.','results':results}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));return report['passed']==len(rows)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
