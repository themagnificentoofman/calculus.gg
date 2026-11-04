"""Independent review of the two frozen source adaptations, without importing their builder."""
import hashlib,json,math,sys
from fractions import Fraction
from pathlib import Path
import sympy as s

def review(path):
 data=Path(path).read_bytes();rows=[json.loads(line) for line in data.splitlines()];results=[]
 assert len(rows)==2
 for p in rows:
  choices=p['choices'];assert len(choices)==4 and len({c['math'] for c in choices})==4
  chosen=next(c['math'] for c in choices if c['choiceId']==p['answerChoiceId'])
  if p['familyId'].endswith('gaussian-truncation'):
   # Build the first omitted integrated coefficient recursively, rather than
   # taking the constructor's answer or its factorial computation as an oracle.
   coefficient=Fraction(1);bounds=[]
   for n in range(9):
    if n:coefficient/=n
    bounds.append(coefficient/(2*n+1))
   passing=[n for n in range(1,9) if bounds[n]<Fraction(1,10000)]
   assert min(passing)==7 and chosen=='7'
   assert all(bounds[n+1]<bounds[n] for n in range(8))
   assert {c['math'] for c in choices}=={'5','6','7','8'}
   checks=['Exact recursive omitted-term magnitudes give the least certified count 7.',
    'Uniform convergence on [0,1] permits integration; decreasing magnitudes tending to zero give the alternating remainder bound.',
    'All four counts are distinct and the question explicitly asks for the first passing bound, not actual quadrature error.']
   route='Compute the consecutive omitted bounds at six and seven, then use monotonicity. Medium: theorem applicability and indexing are the challenge.'
  else:
   x=s.symbols('x');answer=s.diff(2*s.exp(-x*x)/s.sqrt(s.pi),x,6).subs(x,0)/math.factorial(7)
   assert s.simplify(answer+1/(21*s.sqrt(s.pi)))==0
   assert chosen==r'\left(-\frac1{21\sqrt\pi},\ \infty\right)'
   n=s.symbols('n',integer=True,positive=True)
   assert s.limit(x*x*(2*n+1)/((n+1)*(2*n+3)),n,s.oo)==0
   checks=['Six derivatives of the defining derivative, divided by 7!, give -1/(21 sqrt(pi)).',
    'The successive nonzero-term ratio tends to zero for every fixed x; radius infinity.',
    'Each alternative changes exactly one coefficient sign, integration factor, or radius; all are inequivalent.']
   route='Integrate the exponential Taylor series and identify its seventh-power coefficient; the radius follows from factorial growth. Medium.'
  results.append({'familyId':p['familyId'],'passed':True,'checks':checks,'easiestOptionsVisibleRoute':route,
   'optionDisposition':'Single purposeful item: no held-out statistical claim is possible. All options manually compared; shuffled production order retained. No stable family rule can be inferred from this one-item family.'})
 return {'author':'source_research','reviewer':'root-independent-review','status':'independently-reviewed','sourceArtifactSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'limitations':'Independent AI mathematical/editorial review with exact finite computations and stated analytic arguments; not human certification, formal proof, or player calibration.'}
if __name__=='__main__':
 report=review(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'independentlyVerified':len(report['results']),'status':report['status']}))
