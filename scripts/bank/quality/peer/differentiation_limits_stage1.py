"""Separately implemented finite checks by the parent reviewer.

Input is the author's frozen candidate artifact, not a re-imported constructor.
Analytic applicability and options-visible difficulty are recorded separately.
No output from this script alone confers content admission.
"""
import hashlib,json,math,re,sys
from pathlib import Path
import sympy as s
x,t,z,L=s.symbols('x t z L')

def independently_solve(record):
 f=record['familyId'];c=record['parameters']['case'];evidence=[]
 if f.endswith('hilbert-representer-bound'):
  degree,order,point=c['N'],c['order'],s.Rational(c['point'])
  basis=[s.legendre(i,x) for i in range(degree+1)]
  derivative=[s.diff(p,x,order).subs(x,point) for p in basis]
  weights=[s.Rational(2*i+1,2) for i in range(degree+1)]
  value=sum(w*d*d for w,d in zip(weights,derivative))
  if c['side']=='zero-mean':value-=weights[0]*derivative[0]**2
  if c['side']=='zero-at-zero':
   kernel=sum(w*p.subs(x,0)**2 for w,p in zip(weights,basis))
   covariance=sum(w*d*p.subs(x,0) for w,d,p in zip(weights,derivative,basis))
   value-=covariance**2/kernel
  answer=s.sqrt(s.factor(value));evidence=['Legendre orthogonality and constrained functional projection, independent of the authored monomial Gram inversion.']
 elif f.endswith('eigenvalue-curvature'):
  a,b,coupling=map(s.Integer,c['off']);B=s.Matrix([[c['diagB'][0],a,b],[a,c['diagB'][1],coupling],[b,coupling,c['diagB'][2]]]);A=s.diag(*c['diag'])+t*B
  F=(L*s.eye(3)-A).det();at={L:c['diag'][c['j']],t:0};first=-s.diff(F,t).subs(at)/s.diff(F,L).subs(at)
  answer=-(s.diff(F,t,2)+2*s.diff(F,L,t)*first+s.diff(F,L,2)*first**2).subs(at)/s.diff(F,L).subs(at)
  assert s.diff(F,L).subs(at)!=0;evidence=['Implicitly differentiate the displayed characteristic determinant twice; simple-root denominator checked.']
 elif f.endswith('implicit-root-trace'):
  n,q=c['N'],c['q'];P=s.Poly(z**n-z-1,z);coefficients=P.all_coeffs();C=s.zeros(n)
  for i in range(1,n):C[i,i-1]=1
  for i in range(n):C[i,n-1]=-coefficients[n-i]
  assert s.expand(C.charpoly(z).as_expr()-P.as_expr())==0
  derivative=n*C**(n-1)-s.eye(n);assert derivative.det()!=0
  root_velocities=C**q*derivative.inv();answer=s.trace(root_velocities**2)
  evidence=['Trace of a rational function of the companion matrix; no explicit roots or interpolation-coefficient oracle.']
 elif f.endswith('log-derivative-root-count'):
  P=s.prod((x-r)**m for r,m in zip(c['roots'],c['mult']));Q=s.Poly(s.diff(P,x)-c['c']*P,x)
  answer=s.Integer(Q.count_roots(-s.oo,s.oo));evidence=['Exact Sturm root count of the complete derivative equation, retaining repeated-root solutions.']
 elif f.endswith('schwarz-pick-jet'):
  a,b=s.Rational(c['a']),s.Rational(c['c']);assert 0<a<1 and 0<b<1
  h=(b-z)/(1-b*z);fmap=(a+z*h)/(1+a*z*h)
  assert fmap.subs(z,0)==a and s.simplify(s.diff(fmap,z).subs(z,0)-(1-a*a)*b)==0
  answer=abs(s.diff(fmap,z,2).subs(z,0));assert s.simplify(answer-2*(1-a*a)*(1-b*b+a*b*b))==0
  evidence=['Differentiate the attaining Blaschke/Möbius map; Schwarz-Pick derivative disk gives the independently reviewed matching upper bound.']
 elif f.endswith('exponential-chebyshev-zero-bound'):
  assert len(set(c['rates']))==len(c['rates']) and all(d>=0 for d in c['degrees'])
  dimension=sum(d+1 for d in c['degrees']);answer=s.Integer(dimension-1)
  # The confluent Vandermonde product is nonzero; finite dimensionality and
  # repeated Rolle give upper bound, while homogeneous interpolation attains it.
  determinant=s.prod((c['rates'][j]-c['rates'][i])**((c['degrees'][i]+1)*(c['degrees'][j]+1)) for i in range(len(c['rates'])) for j in range(i+1,len(c['rates'])))
  assert determinant!=0;evidence=['Confluent Vandermonde product and dimension, plus independently reviewed weighted Rolle/attainment argument.']
 elif f.endswith('padic-digit-extrema'):
  prime=c['p'];assert s.isprime(prime)
  def valuation(n):
   total=0
   while n:n//=prime;total+=n
   return total
  for j in range(1,5):
   n=prime**j-1;assert valuation(prime*n)-prime*valuation(n)==(prime-1)*j
  answer=s.Integer(prime-1);evidence=['Factorial floor-sum valuation checked at extremal digit strings; digit-length upper bound supplies limsup.']
 elif f.endswith('pell-liminf'):
  d=c['d'];assert math.isqrt(d)**2!=d
  found=None
  for n in range(1,100000):
   m=math.isqrt(1+d*n*n)
   if m*m-d*n*n==1:found=(m,n);break
  assert found
  answer=1/(2*s.sqrt(d));evidence=['Independent search finds an exact Pell unit; its powers give an unbounded attaining subsequence. Integer norm supplies lower bound.']
 elif f.endswith('poisson-coefficient-limit'):
  exponent,j=c['a'],c['j'];rate=s.Rational(1,exponent+1);assert exponent>=1 and j>=0
  answer=s.exp(-rate)*rate**j/s.factorial(j)
  # A direct Bernoulli-convolution recurrence is independent of log generating
  # functions. Numerical agreement supplements, never proves, coefficient limit.
  n=800;prob=[1.0]+[0.0]*j
  for k in range(1,n+1):
   p=(k/n)**exponent/n
   for r in range(j,0,-1):prob[r]=prob[r]*(1-p)+prob[r-1]*p
   prob[0]*=1-p
  assert abs(prob[j]-float(answer))<.003
  evidence=['Finite probability convolution plus uniform-log remainder and Cauchy coefficient argument; numerical check is supplementary.']
 elif f.endswith('binomial-large-deviation'):
  p,a=s.Rational(c['p']),s.Rational(c['a']);assert 0<p<a<1
  answer=s.exp(-a*s.log(a/p)-(1-a)*s.log((1-a)/(1-p)))
  evidence=['Exact relative-entropy expression derived from Stirling of the largest tail term; monotone ratio and polynomial number of terms bound the tail.']
 elif f.endswith('nilpotent-matrix-asymptotics'):
  body=re.search(r'\\begin\{matrix\}(.*?)\\end\{matrix\}',record['statement']).group(1)
  A=s.Matrix([[s.Rational(v.strip()) for v in row.split('&')] for row in body.split('\\\\')])
  n=A.rows;lam=s.trace(A)/n;N=A-lam*s.eye(n);assert N**n==s.zeros(n)
  answer=(N**(n-1))[n-1,n-1]/(s.factorial(n-1)*lam**(n-1))
  evidence=['Parse actual displayed matrix, identify eigenvalue from trace, verify nilpotence, and evaluate highest binomial coefficient. Editorial fit: Hard.']
 elif f.endswith('divisor-hyperbola-constant'):
  omitted=c['a'];answer=2*s.EulerGamma-1-s.harmonic(omitted)
  for n in [10,97,1000]:
   m=math.isqrt(n);assert sum(n//k for k in range(1,n+1))==2*sum(n//k for k in range(1,m+1))-m*m
  evidence=['Exact lattice-hyperbola identity checked at square/non-square bounds; harmonic asymptotic and finite omitted block determine constant.']
 else:raise ValueError('Unreviewed family '+f)
 return s.simplify(answer),evidence

def main(input_path,output_path):
 content=Path(input_path).read_bytes();records=json.loads(content);results=[]
 for record in records:
  try:
   answer,evidence=independently_solve(record);values=[s.sympify(c['expression']) for c in record['choices']]
   matches=[i for i,v in enumerate(values) if s.simplify(v-answer)==0]
   assert len(matches)==1 and record['choices'][matches[0]]['choiceId']==record['answerChoiceId'],(answer,matches)
   results.append({'familyId':record['familyId'],'instance':record['parameters']['instance'],'passed':True,'independentAnswer':s.srepr(answer),'checks':evidence})
  except Exception as error:results.append({'familyId':record['familyId'],'instance':record['parameters']['instance'],'passed':False,'error':str(error)})
 report={'reviewer':'root-independent-review','author':'coverage_research','sourceArtifactSha256':hashlib.sha256(content).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(results),'passed':sum(r['passed'] for r in results),'results':results,'admission':'Separate editorial/option/render review required; not human or formal-proof certification.'}
 Path(output_path).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));return all(r['passed'] for r in results)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
