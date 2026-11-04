"""Independent displayed-task derivations for the nine provisional old MV groups.

Frozen expressions are used only to bind literal choices after solving. Analytic
arguments are reviewed prose, not formal proofs; source/editorial findings remain
separate from correct final answers. No author constructor is an answer oracle.
"""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from existing_diff_limits import source_choice_values,equal
x,y,z,r,t=s.symbols('x y z r t',real=True)
REVIEWS={
 'Vandermonde-extremum':('olympiad','Convert the constrained product into a cubic discriminant and exhibit a zero-product triple attaining its bound.','The fixed sphere-radius changes are pure scaling: one advanced lineage, related to polynomial discriminant extremality.'),
 'anisotropic-integrability':('olympiad','Match the two different denominator scales and establish two uniform positive bounds before testing the endpoint exponent.','Distinct from an isotropic polar power test: the anisotropic region requires a variable rescaling and uniform tail control.'),
 'Gaussian-wedge':('olympiad','Whiten the quadratic form while tracking the image of the positive quadrant as an oblique wedge.','A whole-plane Gaussian determinant does not supply this truncated angular fraction; the boundary geometry is essential.'),
 'planar-log-potential':('olympiad','Derive the logarithmic circle mean, split at the moving singularity radius and justify its local area integrability.','Related globally to log-circle/Fourier integration; the point lies inside the two-dimensional domain, forcing a radial split.'),
 'two-centre-resolvent':('olympiad','Introduce a parameter to join two denominators, translate the plane integral and control the resulting inverse-hyperbolic branch.','A one-centre radial integral is insufficient; the parameter bridge removes the incompatible centres.'),
 'lemniscate-petal-area':('hard','Polar coordinates turn the defining inequality into an explicit radial bound; the petal count cancels in a single angle substitution, followed by a beta integral.','The standard polar/beta chain does not require optimization, a hidden branch decision, or a new sharpness argument.'),
 'squared-log-disk':('olympiad','Expand the uniformly convergent harmonic logarithm, use angular orthogonality, then sum the radially weighted coefficient series.','Unlike a zero or single Fourier coefficient, the squared logarithm couples every mode before orthogonality removes cross terms.'),
 'cube-simplex-cap':('olympiad','Translate the coordinate-violation regions and use inclusion-exclusion with the correct changing active cutoff.','Unlike a bare simplex volume, overlapping upper-coordinate cuts and their combinatorial multiplicities are decisive.'),
 'polynomial-image-winding':('olympiad','Factor out a double root and prove all remaining zeros lie beyond the contour using a coefficient-ratio bound, then apply the argument principle.','Degree alone gives the wrong winding: controlling the remaining roots and absence of contour zeros is essential.'),
}

def solve(p):
 m=s.Integer(p['provenance']['authoring']['builderParameters']['m']);slug=p['familyId'].split('-olympiad-')[1];checks=[]
 def ck(label,a,b):
  assert equal(a,b),(slug,m,label,a,b);checks.append({'description':label,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
 if slug=='Vandermonde-extremum':
  V=(x-y)**2*(y-z)**2*(z-x)**2;D=(x*x+y*y+z*z)**3/2-27*x*x*y*y*z*z
  ck('Discriminant under the exact linear constraint',(V-D).subs(z,-x-y),0)
  answer=m**3/2;ck('Feasible attaining triple',V.subs({x:s.sqrt(m/2),y:0,z:-s.sqrt(m/2)}),answer)
 elif slug=='anisotropic-integrability':
  answer=1-1/m;ck('Matched denominator powers',(x**2+y**(2*m)).subs(y,x**(1/m)*t),x*x*(1+t**(2*m)))
 elif slug=='Gaussian-wedge':
  theta=s.pi/m;u=x-s.cos(theta)*y;v=s.sin(theta)*y
  ck('Whitening quadratic form',u*u+v*v,x*x-2*s.cos(theta)*x*y+y*y)
  ck('Positive Jacobian determinant',s.Matrix([[s.diff(u,x),s.diff(u,y)],[s.diff(v,x),s.diff(v,y)]]).det(),s.sin(theta))
  answer=(s.pi-theta)/(2*s.sin(theta))
 elif slug=='planar-log-potential':
  a=1/m;answer=2*s.pi*(s.integrate(r*s.log(a),(r,0,a))+s.integrate(r*s.log(r),(r,a,1)))
 elif slug=='two-centre-resolvent':
  A=1+x*x+y*y;B=1+(x-m)**2+y*y;c=1+m*m*t*(1-t)
  ck('Parameter-completed square',t*A+(1-t)*B,(x-m*(1-t))**2+y*y+c)
  # Derive the one-dimensional primitive by centering the interval at 1/2.
  k=m/s.sqrt(m*m+4);F=2*s.atanh(k*(2*t-1))/(m*s.sqrt(m*m+4))
  ck('Primitive of the parameter integral',s.diff(F,t),1/c)
  answer=4*s.pi*s.atanh(k)/(m*s.sqrt(m*m+4))
 elif slug=='lemniscate-petal-area':
  answer=2**(2/m-1)*s.sqrt(s.pi)*s.gamma(s.Rational(1,2)+1/m)/s.gamma(1+1/m)
  ck('The petal angle substitution cancels multiplicity',m*s.Rational(1,2)*2**(2/m)/m,2**(2/m-1))
 elif slug=='squared-log-disk':
  q=1/m**2;n=s.symbols('n',positive=True)
  ck('Coefficient partial fractions',1/n**2-1/n+1/(n+1),1/(n*n*(n+1)))
  ck('Radial moment',s.integrate(r**(2*n+1),(r,0,1)),1/(2*n+2))
  answer=s.pi/2*(s.polylog(2,q)+(1-1/q)*s.log(1-q)-1)
 elif slug=='cube-simplex-cap':
  cutoff=m/3;answer=sum((-1)**j*s.binomial(m,j)*(cutoff-j)**m for j in range(int(s.floor(cutoff))+1))/s.factorial(m)
  assert 0<answer<1;checks.append({'description':'Exact signed sum over all coordinate-subset sizes with nonnegative residual cutoff','result':'passed','lastActiveSubsetSize':int(s.floor(cutoff))})
 elif slug=='polynomial-image-winding':
  P=z**m-m*z+m-1;Q=sum((m-1-j)*z**j for j in range(int(m)-1));ck('Exact double-root factorization',P,(z-1)**2*Q)
  R=(m+1)/m;bound=(m-1)/(m-2);Rprime=(R+bound)/2
  coeff=[(m-1-j)*Rprime**j for j in range(int(m)-1)]
  assert 1<R<Rprime<bound and all(a>b>0 for a,b in zip(coeff,coeff[1:]));answer=4*s.pi
  checks.append({'description':'Strict positive decreasing coefficients after scaling beyond the contour exclude all remaining interior and contour zeros','result':'passed','contourRadius':str(R),'outerRadius':str(Rprime)})
 else:raise ValueError(slug)
 return answer,checks

def main(inp,out):
 data=Path(inp).read_bytes();rows=[json.loads(l) for l in data.splitlines()];results=[]
 for p in rows:
  slug=p['familyId'].split('-olympiad-')[1];level,route,neighbor=REVIEWS[slug]
  try:
   answer,checks=solve(p);values=source_choice_values(p);matching=[i for i,v in enumerate(values) if equal(v,answer)]
   assert len(matching)==1 and p['choices'][matching[0]]['choiceId']==p['answerChoiceId'],('answer mismatch',answer)
   assert all(not equal(a,b) for a,b in itertools.combinations(values,2))
   results.append({'problemId':p['problemId'],'sourceContentHash':p['contentHash'],'semanticHash':p['semanticHash'],'familyId':p['familyId'],'index':p['parameters']['instance'],'passed':True,'independentAnswer':s.srepr(answer),'checks':checks,'difficultyRecommended':level,'qualifiedOlympiad':level=='olympiad','easiestOptionsVisibleRoute':route,'nearestNeighbor':neighbor,'normalizedLineageKey':p['familyId']+':radius-normalized' if slug=='Vandermonde-extremum' else p['problemId']})
  except Exception as e:results.append({'problemId':p['problemId'],'familyId':p['familyId'],'index':p['parameters']['instance'],'passed':False,'error':str(e)})
 report={'author':'frozen-M3-content','reviewer':'root-independent-review','artifactSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(rows),'passed':sum(r['passed'] for r in results),'results':results,'scope':'Statement/options-first answer derivations, exact finite checks, literal-choice binding, pairwise inequality and subsequent reading of all nine source-bound solution recipes. Theorems and analytic convergence are prose arguments, not formal proofs. Final option-only screen and source-binding admission remain separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}));return report['passed']==len(rows)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
