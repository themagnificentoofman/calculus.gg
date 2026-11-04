"""Guarded option-only repair of16 complete finite integration pools.

Two competing opposite-sign pairs remove the former lone-sign-pair clue. The
second magnitude is produced by an explicitly authored integration error.
Frozen source tasks/solutions are not changed; baseline-only revision identities
and unpublished preview identities are kept separate.
"""
from pathlib import Path
from functools import lru_cache
import json,hashlib,copy,re,itertools
import sympy as s
from literal_numeric import parse as _parse
def parse(value):return _parse(value.replace(r"\log",r"\ln"))
P=Path(__file__).resolve().parent;VERSION='quality-integration-competing-sign-pairs-v3'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(s.factor_terms(v)).replace(r'\log',r'\ln')
@lru_cache(None)
def inputs():
 previews=[json.loads(l) for l in(P/'integration-sign-preview-inputs.jsonl').read_text().splitlines()]
 baselines={r['problemId']:r for r in map(json.loads,(P/'integration-sign-baseline-inputs.jsonl').read_text().splitlines())}
 return previews,baselines

def literal_problem(r):
 f=r['familyId'];z=r['statement'];x=s.symbols('x',positive=True);checks=[]
 def ck(name,lhs,rhs):
  assert s.simplify(lhs-rhs)==0,(name,lhs,rhs);checks.append({'description':name,'left':s.srepr(lhs),'right':s.srepr(rhs),'result':'exact equality'})
 def match(pattern):
  q=re.search(pattern,z);assert q,(f,pattern,z);return q
 if f=='io3-fresnel':
  a=parse(match(r'\\cos\{\\left\((.*?)\\right\)')[1].replace(' x^{2}','').replace('x^{2}','1').strip());i=r['parameters']['instance'];A=s.sqrt(s.pi)/(2*s.sqrt(2*a));B=A*s.sqrt(2) if i%2==0 else A/s.sqrt(2)
  why='Omit the cosine projection of the rotated Gaussian' if i%2==0 else 'Apply the cosine projection twice to the rotated Gaussian'
  pars={'a':str(a),'instance':i};route='Regularize the oscillatory Gaussian, select the continuous square-root branch, and pass to the improper limit with a uniform tail bound.'
  conditions='a>0. Integration by parts gives a uniform O(1/(aR)) tail for the Gaussian-damped complex phase. The real part of the branch-continuous Gaussian limit gives the claimed positive Fresnel value.'
  ck('Positive coefficient and Fresnel square identity',A*A,s.pi/(8*a))
 elif f=='io3-reciprocal-quartic':
  c=s.Integer(match(r'x\^\{4\} \+ (\d+) x\^\{2\}')[1]);i=r['parameters']['instance'];A=s.pi/(2*s.sqrt(c+2));B=2*A if i%2==0 else A/2;why='Omit the factor two after adding the reciprocal substitutions' if i%2==0 else 'Divide by the reciprocal-pair averaging factor twice';pars={'quadraticCoefficient':int(c),'instance':i}
  u=x-1/x;ck('Reciprocal quadratic denominator', (x**4+c*x*x+1)/x**2,u*u+c+2)
  ck('Reciprocal substitution differential',s.diff(u,x),1+x**-2)
  route='Average the integral with its reciprocal substitution, then set u=x−1/x and integrate a Cauchy kernel on the real line.';conditions='The polynomial is positive for x>0 and c>0; the integrand is bounded at zero and decays as x^-4. The substitution is increasing onto the real line.'
 elif f=='io3-rodrigues-moment':
  power=int(match(r'x\^\{(\d+)\}')[1]);n=int(match(r'\\mathrm\{d\}\^\{(\d+)\}')[1]);i=r['parameters']['instance'];integrand=x**power*s.diff((x*x-1)**n,x,n);A=s.integrate(s.expand(integrand),(x,-1,1));B=2*A if i%2==0 else A/2;why='Double the even-interval reduction a second time' if i%2==0 else 'Use only the positive half of the even integral';pars={'power':power,'derivativeOrder':n,'instance':i}
  ck('Finite polynomial evaluation by primitive',s.integrate(integrand,x).subs(x,1)-s.integrate(integrand,x).subs(x,-1),A)
  ck('Even polynomial integrand',integrand.subs(x,-x),integrand)
  route='Expand the explicitly finite polynomial derivative and integrate its even terms, or integrate by parts repeatedly with vanishing endpoints.';conditions='All functions are polynomials on a compact interval. The Rodrigues polynomial has zeros of multiplicity n at both endpoints, so all earlier boundary terms vanish.'
 elif f=='io3-scaled-frullani':
  hits=re.findall(r'e\^\{- (?:(\d+) )?x\^\{(\d+)\}\}',z);assert len(hits)==2,(hits,z)
  a,p=s.Integer(hits[0][0] or 1),int(hits[0][1]);b,q=s.Integer(hits[1][0] or 1),int(hits[1][1]);assert p==q and b>a>0;i=r['parameters']['instance'];A=s.log(b/a)/p;B=p*A if i%2==0 else A/p;why='Omit the power-substitution Jacobian' if i%2==0 else 'Apply the power-substitution Jacobian twice';pars={'a':int(a),'b':int(b),'power':p,'instance':i}
  ck('Power change of logarithmic differential',s.diff(x**p,x)/(x**p),s.Integer(p)/x)
  route='Set t=x^p and express the exponential difference divided by t as an integral over its positive rate parameter.';conditions='a,b,p are positive and b>a. The parameter integrand is nonnegative, so Tonelli applies; the remaining parameter integral is ln(b/a).'
 else:
  if f.endswith('accumulation-from-derivative'):
   v0=s.Integer(match(r'F\(1\)=(\d+)')[1]);v1=s.Integer(match(r'F\(3\)=(\d+)')[1]);m=int(v0);i=m-4;A=v1-v0;B=v1+v0 if i%2==0 else v1-2*v0;why='Add endpoint values instead of subtracting' if i%2==0 else 'Subtract the lower endpoint value twice';pars={'leftValue':int(v0),'rightValue':int(v1),'m':m}
   ck('FTC endpoint difference',A,v1-v0);route='Apply the fundamental theorem to the two stated endpoint values.';conditions='The statement assumes continuous differentiability on the closed interval.'
  elif f.endswith('area-between-curves'):
   m=int(match(r'\\int_\{0\}\^\{(\d+)\}')[1]);i=m-4;A=s.Rational(m**3,6);B=s.Rational(m**3,4) if i%2==0 else s.Rational(m**3,8);why='Use the midpoint rectangle for the parabolic region' if i%2==0 else 'Replace the parabolic region by a triangle with its maximum height';pars={'m':m};ck('Polynomial area integral',s.integrate(m*x-x*x,(x,0,m)),A);route='Integrate the displayed quadratic between its zeros.';conditions='The polynomial is nonnegative throughout the stated compact interval.'
  elif f.endswith('rational-power-substitution'):
   m=int(match(r'\\right\)\^\{(\d+)\}')[1]);i=m-4;A=(1-s.Rational(2)**(1-m))/(m-1);den=m-2 if i%2==0 else m;B=(1-s.Rational(2)**(1-m))/den;why='Increment the denominator exponent by two in the primitive' if i%2==0 else 'Keep the old exponent in the primitive denominator';pars={'m':m};u=s.symbols('u',positive=True);ck('Power substitution primitive',s.diff((1-u**(1-m))/(m-1),u),u**(-m));route='Set u=1+x²; integrate u raised to the displayed negative integer power from1 to2.';conditions='m≥4; the denominator is positive and bounded away from zero on the compact interval.'
  elif f.endswith('trig-odd-power') or f.endswith('secant-square-substitution'):
   trig='cos' if f.endswith('trig-odd-power') else 'tan';m=int(match(r'\\'+trig+r'\^\{(\d+)\}')[1]);i=m-4;A=s.Rational(1,m+1);B=s.Rational(1,m) if i%2==0 else s.Rational(1,m+2);why='Fail to increment the power in the monomial primitive' if i%2==0 else 'Increment the monomial primitive exponent twice';pars={'m':m};ck('Unit monomial moment',s.integrate(x**m,(x,0,1)),A);route='Use cosine or tangent as the substitution variable and evaluate one monomial moment.';conditions='The stated interval gives substitution endpoints0 and1; cosine is nonzero throughout the secant-square interval.'
  elif f.endswith('inverse-tangent'):
   m=int(match(r'\\int_\{0\}\^\{(\d+)\}')[1]);i=m-4;assert str(m*m) in z;A=s.pi/(4*m);B=s.pi/4 if i%2==0 else s.pi/(4*m*m);why='Omit the scale Jacobian in the arctangent integral' if i%2==0 else 'Apply the scale Jacobian twice';pars={'m':m};ck('Arctangent primitive derivative',s.diff(s.atan(x/m)/m,x),1/(x*x+m*m));route='Scale x by the positive denominator parameter and evaluate arctan at1 and0.';conditions='The quadratic denominator is strictly positive throughout the interval.'
  elif f.endswith('nested-log'):
   m=int(match(r'\^\{e\^\{(\d+)\}\}')[1]);i=m-4;A=s.log(m);B=s.log(m+1) if i%2==0 else s.log(m-1);why='Take the logarithm of the sum of the transformed endpoints' if i%2==0 else 'Take the logarithm of the interval length instead of the endpoint ratio';pars={'m':m};ck('Nested-log primitive derivative',s.diff(s.log(s.log(x)),x),1/(x*s.log(x)));route='Set u=ln x and integrate1/u from1 to the displayed exponent.';conditions='x≥e, so both logarithms in the chosen primitive have positive arguments.'
  elif f.endswith('improper-exponential'):
   m=int(match(r'e\^\{- (\d+) x\}')[1]);i=m-4;A=s.Rational(1,m);B=s.Integer(m) if i%2==0 else s.Rational(1,m*m);why='Invert the reciprocal decay rate' if i%2==0 else 'Apply the decay-rate Jacobian twice';pars={'m':m};ck('Exponential primitive derivative',s.diff(-s.exp(-m*x)/m,x),s.exp(-m*x));ck('Decay endpoint',s.limit(s.exp(-m*x),x,s.oo),0);route='Evaluate an exponential primitive and its zero limit at infinity.';conditions='The displayed exponential decay rate is strictly positive.'
  elif f.endswith('moving-boundary-area'):
   upper=int(match(r'\\int_\{0\}\^\{(\d+)\}')[1]);m=int(s.sqrt(upper));assert m*m==upper;i=m-4;A=s.Rational(m**3,6);B=s.Rational(m**3,2) if i%2==0 else s.Rational(m**3,8);why='Keep only the area under the linear boundary' if i%2==0 else 'Replace the region by a triangle with its maximum height';pars={'m':m};ck('Difference of power primitives',s.integrate(s.sqrt(x)-x/m,(x,0,m*m)),A);route='Find the endpoint intersection already supplied, then subtract the two elementary power integrals.';conditions='The integrand is nonnegative on0≤x≤m² and continuous at both endpoints.'
  elif f.endswith('Frullani-rectangle'):
   m=int(match(r'e\^\{-(\d+)x\}')[1]);i=m-4;A=s.log(m);B=s.log(m+1) if i%2==0 else s.log(m-1);why='Take the logarithm of the sum of decay rates instead of their ratio' if i%2==0 else 'Take the logarithm of the difference of decay rates instead of their ratio';pars={'m':m};t=s.symbols('t',positive=True);ck('Positive rate-parameter representation',s.integrate(s.exp(-t*x),(t,1,m)),(s.exp(-x)-s.exp(-m*x))/x);route='Represent the exponential difference divided by x as a positive parameter integral, exchange order, and integrate1/t.';conditions='m>1; the auxiliary integrand is nonnegative, so Tonelli gives a justified exchange.'
  elif f.endswith('improper-rational-beta'):
   m=int(match(r'x\^\{(\d+)\}')[1]);i=m-4;A=s.Rational(1,m+1);B=s.Rational(1,m) if i%2==0 else s.Rational(1,m+2);why='Fail to increment the transformed monomial exponent' if i%2==0 else 'Increment the transformed monomial exponent twice';pars={'m':m};u=s.symbols('u',positive=True);ck('Fractional substitution with Jacobian',(x**m/(1+x)**(m+2)).subs(x,u/(1-u))/(1-u)**2,u**m);route='Set u=x/(1+x) and integrate the resulting monomial on[0,1].';conditions='m≥4; the integrand is integrable both near zero and at infinity.'
  elif f.endswith('logarithmic-moment'):
   m=int(match(r'x\^\{(\d+)\}')[1]);i=m-4;n=m+1;A=s.Rational(2,n**3);wrong_rate=m if i%2==0 else m+2;B=s.Rational(2,wrong_rate**3);why='Omit the exponential factor from dx after t=−ln x' if i%2==0 else 'Apply the exponential factor from dx twice';pars={'m':m,'rate':n,'wrongRate':wrong_rate};t=s.symbols('t',positive=True);prim=-s.exp(-n*t)*(t*t/n+2*t/s.Integer(n*n)+s.Rational(2,n**3));ck('Quadratic exponential moment primitive',s.diff(prim,t),t*t*s.exp(-n*t));ck('Moment lower endpoint',prim.subs(t,0),-A);ck('Moment upper endpoint',s.limit(prim,t,s.oo),0);route='Substitute t=−ln x and integrate the quadratic exponential moment twice by parts.';conditions='The rate m+1 is positive; polynomial times exponential boundary terms vanish.'
  else:raise ValueError(f)
 A=s.simplify(A);B=s.simplify(B);assert A>0 and B>0 and s.simplify(A-B)!=0
 original=parse(next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']));ck('Independent literal answer equals current answer',original,A)
 return {'index':i,'parameters':pars,'answer':A,'alternative':B,'misconception':why,'checks':checks,'route':route,'conditions':conditions}

@lru_cache(None)
def indexed():return {(r['familyId'],literal_problem(r)['index']):r for r in inputs()[0]}
def catalog():
 return [{'familyId':f,'indices':sorted(i for fid,i in indexed() if fid==f),'newIndependentIdeas':0} for f in sorted({f for f,i in indexed()})]
def build(fid,index):
 if type(index)is not int or (fid,index) not in indexed():raise ValueError('Outside the source-bound finite152 domain')
 old=indexed()[(fid,index)];d=literal_problem(old);A,B=d['answer'],d['alternative'];choices=[]
 for v,why in [(A,'correct'),(-A,'Reverse the oriented integral or final sign'),(B,d['misconception']),(-B,d['misconception']+' and reverse the final sign')]:
  v=s.simplify(v);choices.append({'choiceId':'ch_'+H(s.srepr(v))[:16],'math':tex(v),'expression':s.srepr(v),'misconception':why})
 values=[parse(c['math']) for c in choices]
 for u,v in itertools.combinations(values,2):assert s.simplify(u-v).equals(0)is False
 assert len([(i,j) for i,j in itertools.combinations(range(4),2) if s.simplify(values[i]+values[j])==0])==2
 baseline=inputs()[1].get(old['problemId']);sourcePreview={'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':H(old),'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')}
 previous=None if baseline is None else {'problemId':baseline['problemId'],'revision':baseline['problemRevision'],'sourceContentHash':baseline['contentHash'],'semanticHash':baseline['semanticHash'],'meaningChanged':False}
 presentations=json.loads((P/'integration-sign-current-presentations.json').read_text());display=presentations[old['problemId']];assert display['sourceContentHash']==old['contentHash'] and display['revision']==old['problemRevision']
 row={'familyId':fid,'topic':'integration','difficulty':old['difficulty'],'instanceIndex':index,'parameters':d['parameters'],'finiteInstanceIndices':next(c['indices'] for c in catalog() if c['familyId']==fid),'statement':display['statement'],'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':display['steps'],'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':sourcePreview,'sourcePresentation':{'sha256':hashlib.sha256((P/'integration-sign-current-presentations.json').read_bytes()).hexdigest(),'entryHash':H(display),'solutionQuality':display.get('solutionQuality')},'review':{'status':'candidate-awaiting-independent-peer-and-final-id-options','newIndependentIdeas':0,'meaningChanged':False,'preservePreviousLineage':True,'easiestOptionsVisibleRoute':d['route'],'optionRepairReason':'The prior single opposite-sign pair revealed the positive answer. Two competing sign pairs now leave two positive magnitudes, one produced by a concrete integration misconception. The two positive magnitude orders alternate within each finite family; sign knowledge alone cannot identify the answer.','analyticConditions':d['conditions']},'verificationEvidence':d['checks'],'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[])}
 if previous is not None:row['previous']=previous
 else:row['replacesPrivateProblemId']=old['problemId']
 row['contentHash']=H(row);return row

def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=[build(q['familyId'],i) for q in catalog() for i in q['indices']];assert len(rows)==152
 out=P/'integration-sign-option-candidates-v3.jsonl';out.write_text(''.join(canonical(r)+'\n' for r in rows))
 evidence=[]
 for r in rows:
  vals=[parse(c['math']) for c in r['choices']];evidence.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawHash':H(r),'contentHash':r['contentHash'],'sourcePreview':r['sourcePreview'],'previous':r.get('previous'),'replacesPrivateProblemId':r.get('replacesPrivateProblemId'),'checks':r['verificationEvidence'],'sixLiteralPairsDistinct':True,'oppositePairCount':2,'positiveCandidates':2,'correctMagnitudeRank':sum(bool(v<vals[0]) for v in vals)+1,'correctSignPairIsUnique':False,'easiestOptionsVisibleRoute':r['review']['easiestOptionsVisibleRoute'],'recommendedDifficulty':r['difficulty'],'currentGuardedPresentationPreserved':all(r[k]==json.loads((P/'integration-sign-current-presentations.json').read_text())[r['sourcePreview']['problemId']][dk] for k,dk in [('statement','statement'),('solutionSteps','steps')]),'sourcePresentation':r['sourcePresentation']})
 report={'status':'author-finite-checks-complete-independent-peer-pending','records':evidence,'counts':{'records':152,'baselineRevisions':128,'unpublishedReplacements':24,'literalPairInequalities':912,'exactChecks':sum(len(r['checks']) for r in evidence)},'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['integration_sign_options.py','integration-sign-preview-inputs.jsonl','integration-sign-baseline-inputs.jsonl','integration-sign-option-candidates-v3.jsonl','literal_numeric.py','integration-sign-current-presentations.json','integration-sign-presentation-source-manifest.json']},'standingRule':'Audit relations among choices, including opposite-sign pairs, in addition to each option alone. A nonnegative task with a unique ± pair can disclose its answer even when numeric rank, length, and format checks pass. Repairs must leave more than one sign-compatible candidate, use real misconception formulas, and preserve the original identity/semantic lineage.'}
 (P/'integration-sign-option-verification-v3.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts'])
