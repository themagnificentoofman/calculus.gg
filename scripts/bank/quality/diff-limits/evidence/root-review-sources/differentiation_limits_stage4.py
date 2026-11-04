"""Independent finite derivations for stage04; presentation/level verdicts are separate.

This consumes the frozen artifact, not the author's constructor or answer field.
Analytic limit and sharpness arguments are identified explicitly as arguments,
not claimed to be machine proofs.
"""
from differentiation_limits_stage1 import independently_solve as previous
import hashlib,itertools,json,math,sys
from pathlib import Path
import sympy as s
import mpmath as mp
x,t,u,h=s.symbols('x t u h',real=True)

def solve(p):
 f=p['familyId'];c=p['parameters']['case'];e=[]
 if f.endswith('critical-level-absolute-integral'):
  R=s.prod(x-r for r in c['roots']);w=s.sympify(c['weight'],locals={'x':x});lo,hi=c['bounds'];answer=0
  for r in c['roots']:
   assert lo<=r<=hi and s.diff(R,x).subs(x,r)!=0
   sides=1 if r in [lo,hi] else 2
   answer+=2*sides*w.subs(x,r)/abs(s.diff(R,x).subs(x,r))
  e=['Differentiate the absolute value by bounded difference quotients. Each inverse branch of R near a simple zero gives its own weighted sublevel length; endpoints have one branch.']
 elif f.endswith('moment-hankel-vandermonde'):
  a,b,r=c['a'],c['b'],c['r']
  moment=lambda k:s.factorial(a+k-1)*s.factorial(b-1)/s.factorial(a+b+k-1)
  determinant=s.Matrix(r,r,lambda i,j:moment(i+j)).det()
  # Selberg at exponent one independently checks the multi-integral; the
  # author's proof uses determinant antisymmetrization instead.
  integral=s.prod(s.factorial(a+j-1)*s.factorial(b+j-1)*s.factorial(j+1)/s.factorial(a+b+r+j-2) for j in range(r))
  answer=s.cancel(determinant/integral)
  assert answer==1/s.factorial(r)
  e=['Exact moment determinant compared with the independent beta/Selberg product at Vandermonde exponent two.', 'Stage04 statement omits parentheses around the weight: intended mathematics checked, statement blocked pending correction.']
 elif f.endswith('tree-resistance-sensitivity'):
  n=c['vertices'];total=0;selected_total=0
  for indices in itertools.combinations(range(len(c['edges'])),n-1):
   parents=list(range(n))
   def root(v):
    while parents[v]!=v:v=parents[v]
    return v
   weight=1;valid=True
   for j in indices:
    a,b,w=c['edges'][j];ra,rb=root(a),root(b)
    if ra==rb:valid=False;break
    parents[ra]=rb;weight*=c['at'] if j==c['selected'] else w
   if valid:
    total+=weight
    if c['selected'] in indices:selected_total+=weight
  assert total>0;answer=s.Rational(selected_total,total*c['at'])
  e=['Enumerate all edge subsets, reject cycles, and sum actual spanning-tree weights and their derivatives. No Laplacian inverse or authored resistance oracle.']
 elif f.endswith('sharp-landau-bound'):
  M,N=s.Rational(c['M']),s.Rational(c['N']);assert M>0 and N>0
  answer=s.sqrt(2*M*N)
  assert s.simplify(s.integrate(answer-N*t,(t,0,s.sqrt(2*M/N)))-M)==0
  e=['Two-sided Taylor remainder gives M/t+Nt/2, minimized at sqrt(2M/N). A bounded parabolic spline and positive mollification approach equality.', 'All budget pairs are exact rescalings and provide one normalized mathematical lineage.']
 elif f.endswith('dyadic-log-product'):
  b=c['b'];assert b>1;answer=-1/(2*s.log(b))
  e=['Split at floor(log_b(1/t)); the pre-cutoff logarithms are an arithmetic sum with bounded total remainder, and the post-cutoff geometric tail is uniformly bounded.']
 elif f.endswith('lipschitz-mass-concentration'):
  power=c['p'];sides=2 if c['side']=='zero-endpoints' else 1;assert power>0
  answer=(s.Rational(power+1,sides))**s.Rational(1,power+1)
  M=s.symbols('M',positive=True);assert s.integrate((M-t)**power,(t,0,M))==M**(power+1)/(power+1)
  e=['Integrate the forced cone below a maximum. Fixed zero endpoints require two full sides for large n; otherwise a boundary cone is sharp. Explicit cones attain the limiting bound.']
 elif f.endswith('discrete-volterra-norm'):
  answer=4*s.Integer(c['a'])**2/s.pi**2
  for n in [2,3,7]:
   A=mp.matrix([[min(i,j)+1 for j in range(n)] for i in range(n)])
   eigen=mp.eigsy(A,eigvals_only=True)[n-1,0]
   assert abs(eigen-1/(4*mp.sin(mp.pi/(4*n+2))**2))<1e-10
  e=['Independently form the cumulative-sum Gram matrix and verify its largest eigenvalue for several sizes. Inverting gives the Dirichlet/Neumann difference equation and its half-grid phase.', 'Scale/offset changes share one normalized capacity lineage.']
 elif f.endswith('peano-kernel-sharp-error'):
  q=s.Rational(c['q']);a=q*(1-q);assert 0<a<q<s.Rational(1,2)
  # Apply the actual error functional to the hinge (x-t)+. This constructs
  # the kernel directly from the displayed quadrature, rather than its answer.
  K=[(1-t)**2/2-((a-t)+(1-a-t))/2,(1-t)**2/2-(1-a-t)/2,(1-t)**2/2]
  intervals=[(0,a,K[0],1),(a,q,K[1],1),(q,1-q,K[1],-1),(1-q,1-a,K[1],1),(1-a,1,K[2],1)]
  answer=sum(sign*s.integrate(k,(t,lo,hi)) for lo,hi,k,sign in intervals)
  assert s.simplify(K[1].subs(t,q))==0
  e=['Apply the error functional directly to an affine hinge, locate both middle sign changes, and integrate its absolute kernel. Continuous approximations to its sign establish the supremum.']
 elif f.endswith('sturm-hurwitz-critical-count'):
  m,N=c['m'],c['N'];assert 1<=m<=N;answer=s.Integer(2*m)
  e=['A product of half-angle sine factors matching fewer than 2m sign changes would be a lower-frequency trigonometric polynomial with positive inner product against f prime, contradicting orthogonality. The pure lowest-frequency cosine attains 2m.']
 elif f.endswith('dense-corner-series-derivative'):
  a,lam=s.Rational(c['a']),s.Rational(c['lam']);assert 0<a<1 and 0<lam<s.Rational(1,2) and a.q%2==1
  period=int(s.n_order(2,int(a.q)));correction=0
  for j in range(1,period+1):
   # Count odd grid points strictly below a directly, instead of using the
   # constructor's floor formula. The residual after its linear growth repeats.
   left=sum(bool(s.Rational(k,2**j)<a) for k in range(1,2**j,2))
   coefficient=2*left-2**(j-1)
   correction+=(coefficient-(a-s.Rational(1,2))*2**j)*lam**j
  answer=(a-s.Rational(1,2))*2*lam/(1-2*lam)+correction/(1-lam**period)
  e=['Directly count signs of the odd dyadic corners over one modular period. Split off the linear count and sum the periodic correction geometrically. Summable Lipschitz constants justify differentiating at every nondyadic evaluation point.']
 elif f.endswith('singular-implicit-branches'):
  roots=c['roots'];assert len(roots)==len(set(roots))==3
  P=s.prod(u-r for r in roots);Q=sum(v*u**j for j,v in enumerate(c['Q']));values=[]
  z=s.symbols('z')
  for r in roots:
   # Substitute y=r*x+z*x^2 into the homogeneous cubic plus quartic and
   # solve its first nonzero coefficient, independently of implicit derivatives.
   coeff=s.expand(P.subs(u,r+z*x)+x*Q.subs(u,r+z*x)).coeff(x,1)
   zz=s.solve(coeff,z);assert len(zz)==1;values.append(2*zz[0])
  answer=sum(v*v for v in values)
  e=['Power-series substitution into each simple tangent direction gives the quadratic coefficient; simple tangent roots ensure precisely three analytic branches.']
 elif f.endswith('root-moment-extremum'):
  N,S,lo,hi=c['N'],s.Rational(c['S']),s.Rational(c['lo']),s.Rational(c['hi']);assert N*lo<=S<=N*hi
  vertices=[]
  for ends in itertools.product([lo,hi],repeat=N-1):
   remaining=S-sum(ends)
   if lo<=remaining<=hi:vertices.append((*ends,remaining))
  assert vertices;best=max(vertices,key=lambda v:sum(z*z for z in v));polynomial=s.prod(1+v*x for v in best)
  answer=s.diff(polynomial,x,2).subs(x,0);assert s.diff(polynomial,x).subs(x,0)==S
  e=['Enumerate every box-simplex vertex, maximize its square moment, and independently differentiate the attaining root product. Convexity places a maximum at such a vertex.']
 elif f.endswith('green-kernel-spectrum'):
  L=s.Rational(c['length']);k=c['ordinal'];wave=(2*k-1)*s.pi/(2*L) if c['boundary']=='mixed' else k*s.pi/L;answer=wave**2
  mode=s.sin(wave*t);kernel1=t;kernel2=x
  if c['boundary']=='dirichlet':kernel1-=x*t/L;kernel2-=x*t/L
  integral=s.integrate(kernel1*mode,(t,0,x))+s.integrate(kernel2*mode,(t,x,L))
  assert s.simplify(answer*integral-s.sin(wave*x))==0
  e=['Recover the second-order ODE and its endpoint conditions; order its positive frequencies. Direct split-kernel integration independently verifies the claimed eigenmode in the original equation.']
 elif f.endswith('stationary-phase-root-geometry'):
  R=s.prod(x-r for r in c['roots']);w=s.sympify(c['weight'],locals={'x':x});lo,hi=c['bounds'];coefficient=0
  for r in c['roots']:
   assert lo<=r<=hi and s.diff(R,x).subs(x,r)!=0
   coefficient+=(s.Rational(1,2) if r in [lo,hi] else 1)*w.subs(x,r)/abs(s.diff(R,x).subs(x,r))
  answer=s.sqrt(s.pi/2)*coefficient
  e=['On each stated neighborhood substitute the local inverse of R, with absolute Jacobian. A damped Gaussian and oscillatory tail estimate give the Fresnel constant; endpoint half-neighborhoods contribute half. Nonstationary pieces vanish after square-root normalization.']
 elif f.endswith('quadratic-gauss-magnitude'):
  repeat,residue=c['a'],c['r'];answer=s.sqrt(repeat*(2 if residue==0 else 0 if residue==2 else 1))
  for n in [1,2,4]:
   m=4*n+residue
   value=sum(mp.exp(2j*mp.pi*k*k/m) for k in range(m))
   expected=m*(2 if residue==0 else 0 if residue==2 else 1)
   assert abs(abs(value)**2-expected)<1e-8
  e=['Square the complete quadratic sum and use character orthogonality; only shifts with m dividing 2h survive. The exact surviving phases give all three parity cases. Numeric small-modulus checks are supplementary.']
 elif f.endswith('reinforced-urn-distribution'):
  a,b,q=c['a'],c['b'],s.Rational(c['q']);assert a>0 and b>0 and 0<q<1
  density=s.factorial(a+b-1)/s.factorial(a-1)/s.factorial(b-1)*t**(a-1)*(1-t)**(b-1)
  answer=s.integrate(density,(t,q,1));assert s.integrate(density,(t,0,1))==1
  # Independent finite urn transition law checks the exchangeable count law.
  probs=[s.Integer(1)]
  for n in range(8):
   nxt=[s.Integer(0)]*(n+2)
   for k,v in enumerate(probs):nxt[k]+=v*s.Rational(b+n-k,a+b+n);nxt[k+1]+=v*s.Rational(a+k,a+b+n)
   probs=nxt
  for k,v in enumerate(probs):assert v==s.binomial(8,k)*s.rf(a,k)*s.rf(b,8-k)/s.rf(a+b,8)
  e=['Compute the limiting beta density and its exact tail integral; separately evolve the finite urn Markov chain and compare its count law. Factorial ratios and endpoint integral bounds justify convergence.']
 elif f.endswith('matrix-commutator-limit'):
  a,b=s.Rational(c['a']),s.Rational(c['b']);U=s.eye(2);V=s.eye(2);U[0,1]=a*h;V[1,0]=b*h
  C=U*V*U.inv()*V.inv();assert C.subs(h,0)==s.eye(2) and s.diff(C,h).subs(h,0)==s.zeros(2)
  B=s.diff(C,h,2).subs(h,0)/2;answer=s.exp(B)[0,0]
  e=['Multiply the four actual shear matrices, check cancellation of the linear term, and take the matrix exponential of the quadratic coefficient. The logarithm remainder times n is O(n^-1/2).']
 elif f.endswith('hilbert-determinant-rate'):
  alpha,L=s.Rational(c['alpha']),s.Rational(c['length']);assert alpha>0 and L>0
  for n in [2,3,5]:
   H=s.Matrix(n,n,lambda i,j:L**(i+j+alpha)/(i+j+alpha));expected=L**(n*(n-1)+alpha*n)*s.prod(s.factorial(j)**2 for j in range(n))/s.prod(i+j+alpha for i in range(n) for j in range(n))
   assert s.simplify(H.det()-expected)==0
  numerator=2*s.integrate((1-u)*s.log(u),(u,0,1));denominator=s.integrate(s.integrate(s.log(u+t),(u,0,1)),(t,0,1))
  answer=s.simplify(L*s.exp(numerator-denominator));assert answer==L/4
  e=['Independently compute finite moment determinants and verify the Cauchy product. Exact logarithmic energy integrals determine the n-squared rate; truncation controls the integrable corner singularity and fixed alpha shift.']
 elif f.endswith('singular-riemann-renormalization'):
  power=c['p']-1;poly=s.cancel(((1-u)**power-1)/u);assert s.Poly(poly,u)
  answer=s.EulerGamma+s.integrate(poly,(u,0,1))
  e=['Subtract the harmonic sum exactly; its remaining quotient is a polynomial, so ordinary Riemann-sum convergence applies even at zero.']
 else:return previous(p)
 return s.simplify(answer),e

def main(path,out):
 data=Path(path).read_bytes();rows=json.loads(data);results=[]
 for p in rows:
  try:
   answer,evidence=solve(p);values=[s.sympify(v['expression']) for v in p['choices']]
   matches=[i for i,v in enumerate(values) if s.simplify(v-answer)==0]
   assert len(matches)==1 and p['choices'][matches[0]]['choiceId']==p['answerChoiceId'],str(answer)
   assert all(s.simplify(a-b)!=0 for a,b in itertools.combinations(values,2))
   results.append({'familyId':p['familyId'],'instance':p['parameters']['instance'],'passed':True,'independentAnswer':s.srepr(answer),'checks':evidence})
  except Exception as error:results.append({'familyId':p['familyId'],'instance':p['parameters']['instance'],'passed':False,'error':str(error)})
 report={'reviewer':'root-independent-review','author':'coverage_research','sourceArtifactSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(results),'passed':sum(r['passed'] for r in results),'results':results,'admission':'No admission conferred. Stage04 Hankel statements need semantic correction; domain/lineage/options-visible editorial dispositions are separate. AI review, not human or formal certification.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));return all(r['passed'] for r in results)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
