"""55 source-bound option overlays; frozen tasks, proofs, and exposure identities.

A sole mathematical +/- pair can be hidden by logarithm identities or expanded
sums. Each menu contains two genuinely different magnitudes and both signs.
The second magnitude is a stated integration error, never an arbitrary offset.
"""
from pathlib import Path
from functools import lru_cache
import json,hashlib,re,itertools
import sympy as s
from literal_numeric import parse
P=Path(__file__).resolve().parent
VERSION='quality-integration-algebraic-sign-pairs-v1'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tex(v):return s.latex(s.factor_terms(v)).replace(r'\log',r'\ln')
def equal(a,b):return s.simplify(s.expand_log(a-b,force=True))==0
@lru_cache(None)
def inputs():return [json.loads(l) for l in (P/'inputs.jsonl').read_text().splitlines()]
@lru_cache(None)
def baseline():return {r['problemId']:r for r in map(json.loads,(P/'baseline-inputs.jsonl').read_text().splitlines())}
@lru_cache(None)
def presentations():return json.loads((P/'current-presentations.json').read_text())
def key(r):
 f=r['familyId'];z=r['statement']
 if f.startswith('io3-') or f.endswith(('odd-even','signed-area')):return r['parameters']['instance']
 if f.endswith(('parts-log','exponential-rate','log-recognition','exponential-trig','partial-fractions','mixed-log-endpoints','half-angle-quadratic','reciprocal-quartic')):
  if f.endswith('parts-log'):m=int(re.search(r'\\int_\{1\}\^\{(\d+)\}',z)[1])
  elif f.endswith('exponential-rate'):m=int(re.search(r'e\^\{(\d+) x\}',z)[1])
  elif f.endswith('log-recognition'):m=int(re.search(r'x \+ (\d+)',z)[1])
  elif f.endswith('exponential-trig'):m=int(re.search(r'\\cos\{\\left\((\d+) x',z)[1])
  elif f.endswith('partial-fractions'):m=int(re.findall(r'x \+ (\d+)',z)[-1])
  elif f.endswith('mixed-log-endpoints'):m=int(re.search(r'x\^\{(\d+)\}',z)[1])
  elif f.endswith('half-angle-quadratic'):m=int(re.search(r'1\+(\d+)\\sin',z)[1])
  else:m=int(s.sqrt(s.Integer(re.findall(r'x\^\{2\} \+ (\d+)',z)[-1])))
  return m-4
 raise ValueError(f)
@lru_cache(None)
def indexed():
 d={(r['familyId'],key(r)):r for r in inputs()};assert len(d)==55;return d

def catalog():return [{'familyId':f,'indices':sorted(i for ff,i in indexed() if ff==f),'newIndependentIdeas':0} for f in sorted({r['familyId'] for r in inputs()})]
def derive(r):
 f=r['familyId'];z=r['statement'];i=key(r);ordinal=sorted(j for ff,j in indexed() if ff==f).index(i);low=ordinal%2==0;x=s.symbols('x',positive=True);checks=[]
 def ck(name,lhs,rhs):
  assert equal(lhs,rhs),(name,lhs,rhs);checks.append({'description':name,'left':s.srepr(lhs),'right':s.srepr(rhs),'result':'exact equality'})
 params={'sourceInstance':r['parameters']['instance'],'reviewIndex':i}
 if f=='io3-bernoulli-product':
  n,m=map(int,re.findall(r'B_\{(\d+)\}',z));p=s.bernoulli(n,x)*s.bernoulli(m,x);A=s.integrate(s.expand(p),(x,0,1));formula=(-1)**(n-1)*s.factorial(n)*s.factorial(m)*s.bernoulli(n+m)/s.factorial(n+m);ck('Polynomial integral agrees with endpoint-jump formula',A,formula)
  factor=s.Integer(n);B=A/factor if low else A*factor;why='Omit the first derivative multiplier in the Bernoulli integration-by-parts recurrence' if low else 'Apply the first Bernoulli derivative multiplier twice';params.update(n=n,m=m)
  route='Extract the finite Bernoulli polynomials from the given generating series, then integrate their product; an endpoint-jump recurrence gives an alternative.';conditions='All integrands are explicitly finite polynomials on[0,1]. The chosen degrees are positive integers. The generating-function convention fixes B1(x)=x−1/2.'
 elif f=='io3-jensen-radius':
  b=s.Integer(re.search(r'- (\d+) \\cos',z)[1]);c=parse(re.search(r'\\ln\{\\left\((.*?) - ',z)[1]);r0=b/2;assert r0>1;ck('Squared-modulus constant coefficient',c,r0*r0+1);A=4*s.pi*s.log(r0);B=A/2 if low else 2*A;why='Use log modulus instead of log squared modulus' if low else 'Count both conjugate logarithm series twice';params.update(radius=str(r0))
  route='Factor the positive trigonometric expression as r²|1−e^(ix)/r|² and integrate the absolutely convergent logarithmic Fourier series.';conditions='r>1 makes the logarithmic power series uniformly absolutely convergent on the integration circle; every nonconstant Fourier mode integrates to zero. The real logarithm argument is positive.'
 elif f.endswith('exponential-rate'):
  m=s.Integer(i+4);A=(s.exp(m)-1)/m;B=A/m if low else A*m;why='Apply the exponential-rate primitive denominator twice' if low else 'Omit the exponential-rate primitive denominator';ck('Exponential primitive derivative',s.diff(s.exp(m*x)/m,x),s.exp(m*x));params.update(m=int(m));route='Evaluate the exponential primitive at both displayed endpoints.';conditions='The integrand is continuous on[0,1] and the rate is positive.'
 elif f.endswith('log-recognition'):
  m=s.Integer(i+4);A=s.log((m+1)/m);B=s.log((m+2)/(m+1)) if low else s.log((m+2)/m);why='Shift both primitive evaluation endpoints one unit right' if low else 'Use2 instead of1 as the upper endpoint';ck('Log primitive derivative',s.diff(s.log(x+m),x),1/(x+m));params.update(m=int(m));route='Evaluate ln(x+m) at1 and0.';conditions='x+m>0 throughout[0,1], so the real logarithm primitive is valid.'
 elif f.endswith('odd-even'):
  assert r'\frac{\pi}{8}' in z and 'x^{3}' in z;a=s.pi/8;A=s.simplify(2*s.sin(a));B=A/2;why='Integrate the even cosine only over the positive half interval';ck('Odd cubic cancels',s.integrate(x**3,(x,-a,a)),0);ck('Cosine symmetric integral',s.integrate(s.cos(x),(x,-a,a)),A);params.update(halfWidth='pi/8');route='Cancel the odd cubic and double the cosine integral over the positive half interval.';conditions='Both summands are continuous on the symmetric compact interval.'
 elif f.endswith('signed-area'):
  a,b=map(s.Integer,re.search(r'\\int_\{(\d+)\}\^\{(\d+)\}',z).groups());body=re.search(r'\^\{\d+\}(.*?)\\,',z)[1].strip();pol=x-5 if body=='x - 5' else 20-2*x if body=='20 - 2 x' else None;assert pol is not None;root=s.solve(pol,x)[0];assert a<root<b;A=s.integrate(pol,(x,a,b));L=s.integrate(pol,(x,a,root));R=s.integrate(pol,(x,root,b));B=abs(L)+abs(R);ck('Signed component sum',L+R,A);why='Add the unsigned triangular areas instead of their oriented difference';params.update(lower=int(a),upper=int(b),slope=int(s.diff(pol,x)),intercept=int(pol.subs(x,0)));route='Evaluate the linear primitive or subtract the two triangular signed areas.';conditions='The displayed affine function changes sign once inside the compact interval. The task asks for the oriented integral, not unsigned area.'
 elif f.endswith('parts-log'):
  m=s.Integer(i+4);A=m*s.log(m)-m+1;B=m*s.log(m)-m-1 if low else m*s.log(m)+m-1;why='Subtract+1 instead of the lower primitive value−1' if low else 'Reverse the integration-by-parts subtraction';ck('Integration-by-parts primitive derivative',s.diff(x*s.log(x)-x,x),s.log(x));params.update(m=int(m));route='Integrate by parts once and evaluate x ln x−x at the two positive endpoints.';conditions='The logarithm is continuously differentiable on[1,m], with m>1.'
 elif f.endswith('partial-fractions'):
  m=s.Integer(i+4);A=s.log(2*m/(m+1))/(m-1);B=A/(m-1) if low else A*(m-1);why='Apply the partial-fraction coefficient a second time' if low else 'Omit the partial-fraction coefficient';ck('Partial-fraction decomposition',(1/(x+1)-1/(x+m))/(m-1),1/((x+1)*(x+m)));params.update(m=int(m));route='Subtract the two linear reciprocal terms, integrate their logarithms, and preserve the endpoint ratio.';conditions='Both linear factors are positive on[0,1], and m≠1.'
 elif f.endswith('exponential-trig'):
  m=s.Integer(i+4);E=s.exp(2*s.pi)-1;A=E/(m*m+1);B=E/(m+1)**2 if low else E/(m*m);why='Replace the complex modulus sqrt(1+m²) by1+m when solving the two primitive coefficients' if low else 'Omit the real-exponential contribution1 in the coefficient denominator';F=s.exp(x)*(s.cos(m*x)+m*s.sin(m*x))/(1+m*m);ck('Two-coefficient exponential-trigonometric primitive',s.diff(F,x),s.exp(x)*s.cos(m*x));ck('Integer-frequency endpoints',F.subs(x,2*s.pi)-F.subs(x,0),A);params.update(m=int(m));route='Solve the two primitive coefficients for e^x cos(mx), then use the integer-frequency endpoints.';conditions='m is an integer, so sine vanishes and cosine equals1 at both endpoints. All functions are continuous.'
 elif f.endswith('reciprocal-quartic'):
  m=s.Integer(i+4);A=s.pi/(2*m*(m+1));B=A/m if low else A*m;why='Apply the second quadratic scale factor twice' if low else 'Omit the second quadratic scale factor';ck('Quadratic partial fractions',(1/(x*x+1)-1/(x*x+m*m))/(m*m-1),1/((x*x+1)*(x*x+m*m)));ck('Two half-line arctangent integrals',(s.pi/2-s.pi/(2*m))/(m*m-1),A);params.update(m=int(m));route='Split the two quadratic factors and evaluate each positive half-line arctangent integral.';conditions='m>1; the rational integrand is bounded near0 and O(x^-4) at infinity. Both quadratic factors are positive.'
 elif f.endswith('mixed-log-endpoints'):
  m=s.Integer(i+4);n=m+1;A=s.harmonic(n)/n**2+(s.harmonic(n,2)-s.pi**2/6)/n;B=A/2 if low else A*2;why='Divide the mixed Taylor coefficient by2 as if both derivatives used the same variable' if low else 'Add both orders of the same mixed derivative as separate terms';k=s.symbols('k',positive=True);ck('Shifted reciprocal-square sum decomposition',1/(k*(n+k)**2),(1/k-1/(k+n))/n**2-1/(n*(k+n)**2));params.update(m=int(m));route='Expand−ln(1−x) into its nonnegative series, integrate x^m(−ln x) termwise, and telescope the resulting shifted reciprocal-square sum.';conditions='On0<x<1 both negative logarithms are positive, so Tonelli justifies the interchange. The resulting sum converges and equals H_n/n²−(zeta(2)−H_n^(2))/n, n=m+1.'
 elif f.endswith('half-angle-quadratic'):
  m=s.Integer(i+4);d=s.sqrt(m*m-1);F=s.log((x+m-d)/(x+m+d))/d;A=F.subs(x,1)-F.subs(x,0);B=A/2 if low else A*2;why='Omit the factor2 in the tangent-half-angle Jacobian' if low else 'Apply the factor2 tangent-half-angle Jacobian twice';ck('Transformed rational primitive derivative',s.diff(F,x),2/(x*x+2*m*x+1));params.update(m=int(m));route='Set t=tan(x/2), integrate2/(t²+2mt+1) from0 to1, and evaluate its real logarithm primitive.';conditions='m>1; d=sqrt(m²−1)<m. Both logarithm numerator and denominator are positive for0≤t≤1. The original denominator is positive on[0,pi/2].'
 else:raise ValueError(f)
 A=s.expand(A);B=s.expand(B);assert not equal(A,0) and not equal(B,0) and not equal(A,B) and not equal(A,-B)
 original=parse(next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']));ck('Literal old answer equals separately derived integral',original,A)
 return dict(answer=A,alternative=B,misconception=why,parameters=params,checks=checks,route=route,conditions=conditions)
@lru_cache(None)
def build(fid,index):
 if type(index)is not int or (fid,index) not in indexed():raise ValueError('Outside the source-bound finite55 domain')
 old=indexed()[fid,index];d=derive(old);A,B=d['answer'],d['alternative'];vals=[A,-A,B,-B];whys=['correct','Reverse the oriented integral or final sign',d['misconception'],d['misconception']+' and reverse the final sign'];choices=[]
 for v,why in zip(vals,whys):choices.append({'choiceId':'ch_'+H(s.srepr(v))[:16],'math':tex(v),'expression':s.srepr(v),'misconception':why})
 parsed=[parse(c['math']) for c in choices]
 for a,b in itertools.combinations(parsed,2):assert not equal(a,b) and s.N(abs(a-b),30)>0
 assert sum(equal(a,-b) for a,b in itertools.combinations(parsed,2))==2
 display=presentations()[old['problemId']];assert display['sourceContentHash']==old['contentHash'] and display['revision']==old['problemRevision']
 src={'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':H(old),'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')}
 row={'familyId':fid,'topic':'integration','difficulty':old['difficulty'],'instanceIndex':index,'parameters':d['parameters'],'finiteInstanceIndices':next(c['indices'] for c in catalog() if c['familyId']==fid),'statement':display['statement'],'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':display['steps'],'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':src,'sourcePresentation':{'sha256':fh(P/'current-presentations.json'),'entryHash':H(display),'solutionQuality':display.get('solutionQuality')},'review':{'status':'candidate-awaiting-independent-peer-and-final-id-options','newIndependentIdeas':0,'meaningChanged':False,'preservePreviousLineage':True,'easiestOptionsVisibleRoute':d['route'],'optionRepairReason':'The previous menu had a single exact opposite pair after algebraic/logarithmic simplification. The revised menu has two competing opposite pairs, with a concrete integration error defining its second nonzero magnitude.','analyticConditions':d['conditions']},'verificationEvidence':d['checks'],'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[])}
 b=baseline().get(old['problemId'])
 if b:row['previous']={'problemId':b['problemId'],'revision':b['problemRevision'],'sourceContentHash':b['contentHash'],'semanticHash':b['semanticHash'],'meaningChanged':False}
 else:row['replacesPrivateProblemId']=old['problemId']
 row['contentHash']=H(row);return row

def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=[build(q['familyId'],i) for q in catalog() for i in q['indices']];assert len(rows)==55
 out=P/'candidates.jsonl';out.write_text(''.join(canonical(r)+'\n' for r in rows));evidence=[]
 for r in rows:
  v=[parse(c['math']) for c in r['choices']];evidence.append({'rawHash':H(r),'contentHash':r['contentHash'],'familyId':r['familyId'],'index':r['instanceIndex'],'sourcePreview':r['sourcePreview'],'previous':r.get('previous'),'replacesPrivateProblemId':r.get('replacesPrivateProblemId'),'checks':r['verificationEvidence'],'sixLiteralPairsDistinct':True,'oppositePairs':2,'correctNumericRank':1+sum(bool(s.N(q-v[0],30)<0) for q in v),'sourcePresentation':r['sourcePresentation'],'recommendedDifficulty':r['difficulty'],'easiestOptionsVisibleRoute':r['review']['easiestOptionsVisibleRoute']})
 report={'status':'all55-author-checks-passed-independent-peer-pending','records':evidence,'counts':{'records':55,'baselineRevisions':sum('previous'in r for r in rows),'privateReplacements':sum('replacesPrivateProblemId'in r for r in rows),'literalPairInequalities':330,'exactChecks':sum(len(r['checks']) for r in evidence)},'sourceSha256':{f:fh(P/f) for f in ['options.py','literal_numeric.py','inputs.jsonl','baseline-inputs.jsonl','current-presentations.json','presentation-source-manifest.json','candidates.jsonl']},'limitation':'Author exact checks do not replace separate peer review or the final actual-ID whole-family options screen. Nonzero numerical comparisons supplement exact symbolic identity and the displayed analytic conditions.'}
 (P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts'])
