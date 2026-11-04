"""Finite source-bound option repairs. No frozen constructors are changed.
Author finite checks are separate from independent peer and final-ID screening.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,itertools,re
import sympy as s
from literal_numeric_extended import parse
P=Path(__file__).resolve().parent;VERSION='quality-ode-mv-option-repairs-v4'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(s.factor_terms(v)).replace(r'\log',r'\ln')
@lru_cache(None)
def inputs():return [json.loads(l) for l in(P/'ode-mv-option-complete-preview-inputs.jsonl').read_text().splitlines()],{r['problemId']:r for r in map(json.loads,(P/'ode-mv-option-complete-baseline-inputs.jsonl').read_text().splitlines())},json.loads((P/'ode-mv-option-complete-current-presentations.json').read_text())

def derive(r):
 f=r['familyId'];z=r['statement'];x,t=s.symbols('x t',positive=True);checks=[];pars={};pool=None;display=None
 def match(pattern):
  q=re.search(pattern,z);assert q,(f,pattern,z);return q
 def ck(name,a,b):
  assert s.simplify(s.expand_func(a-b))==0,(name,a,b);checks.append({'description':name,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
 if f.endswith('Green-circulation'):
  rad2=s.Integer(match(r'x\^2\+y\^2=(\d+)')[1]);m=int(s.sqrt(rad2));assert m*m==rad2;i=m-4;A=2*s.pi*rad2;B=A/2 if i%2==0 else 2*A;why='Omit one of the two curl derivatives' if i%2==0 else 'Count the curl derivative contributions twice';route='The circle and counterclockwise orientation give curl2 times disk area.'
 elif f.endswith('divergence-flux'):
  rad2=s.Integer(match(r'z\^2=(\d+)')[1]);m=int(s.sqrt(rad2));assert m*m==rad2;i=m-4;A=4*s.pi*m**3;B=A/2 if i%2==0 else 2*A;why='Integrate only one hemisphere' if i%2==0 else 'Count the sphere volume twice';route='Use divergence3 and the stated ball volume.';bcoef=2 if i%2==0 else 8;display=[rf'4\pi\,{m}^{{3}}',rf'-4\pi\,{m}^{{3}}',rf'{bcoef}\pi\,{m}^{{3}}',rf'-{bcoef}\pi\,{m}^{{3}}']
 elif f.endswith('implicit-surface-partial'):
  m=int(match(r'z\(1,1\)=(\d+)')[1]);i=m-4;A=-s.Rational(1,m);B=2*A if i%2==0 else A/2;why='Retain the numerator derivative factor two after canceling only the denominator factor' if i%2==0 else 'Retain the denominator derivative factor two after canceling only the numerator factor';route='Differentiate the constraint with y fixed: z_x=−x/z, then substitute the specified branch value.'
 elif f.endswith('surface-flux-graph'):
  m=int(match(r'\\frac\{1\}\{(\d+)\}')[1]);i=m-4;A=s.pi*(2*m+1)/(2*m*m);B=s.pi*(2*m-1)/(2*m*m) if i%2==0 else s.pi*(2*m+3)/(2*m*m);why='Reverse the radial contribution to the graph area vector' if i%2==0 else 'Count an extra radial contribution in the graph area vector';rho=s.symbols('rho',positive=True);ck('Upward graph flux radial integral',s.integrate(2*s.pi*(1+rho*rho)*rho,(rho,0,1/s.sqrt(m))),A);route='Form the upward graph area vector; its dot product with the field is1+r², then integrate over the disk.'
 elif f.endswith('two-centre-resolvent'):
  m=int(match(r'\(x-(\d+)\)')[1]);i=m-4;A=4*s.pi*s.atanh(s.Integer(m)/s.sqrt(m*m+4))/(m*s.sqrt(m*m+4));B=2*A if i%2==0 else A/2;why='Double the symmetric parameter interval twice' if i%2==0 else 'Integrate only one half of the symmetric parameter interval';route='Use the positive Feynman parameter identity, complete the translated square, and evaluate the radial integral followed by its inverse-hyperbolic parameter integral.'
 elif f.endswith('polynomial-image-winding'):
  m=int(match(r'P\(z\)=z\^\{(\d+)\}')[1]);i=m-4;A=4*s.pi;B=2*s.pi if i%2==0 else 8*s.pi;why='Count the enclosed double root only once' if i%2==0 else 'Count the enclosed double root twice';route='Factor the polynomial into a double root and a positive decreasing-coefficient factor, exclude the latter zeros from the input circle, then apply the argument principle.'
 elif f.endswith('rate-identification'):
  m=int(match(r'e\^\{(\d+)t\}')[1]);i=m-4;A=s.Integer(m);B=s.Rational(m,2) if i%2==0 else s.Integer(2*m);why='Apply an extra factor one half to the chain-rule coefficient' if i%2==0 else 'Count the chain-rule coefficient twice';ck('Exponential logarithmic derivative',s.diff(s.exp(m*t),t)/s.exp(m*t),A);route='Differentiate the supplied exponential and divide by the nonzero function.'
 elif f.endswith('phase-line-stability'):
  m=int(s.sqrt(s.Integer(match(r'y\^2-(\d+)')[1])));i=m-4;A=-s.Integer(m);B=-s.Integer(m*m) if i%2==0 else -s.Rational(m,2);why='Fail to take the square root when locating the equilibrium' if i%2==0 else 'Divide the equilibrium root by two';ck('Selected equilibrium',A*A-m*m,0);assert 2*A<0;route='Solve the quadratic equilibrium equation and use the derivative sign to choose the attracting root.'
 elif f.endswith('oscillator-initial-data'):
  m=int(match(r'y\(0\)=(\d+)')[1]);b=int(match(r'y\\prime\(0\)=(\d+)')[1]);i=m-4;A=s.Integer(b);B=s.Integer(m) if i%2==0 else s.Integer(m+b);why='Exchange the two initial coefficients' if i%2==0 else 'Add both basis coefficients at the quarter-period point';ck('Oscillator evaluation',m*s.cos(s.pi/2)+b*s.sin(s.pi/2),A);route='Identify the cosine and sine coefficients from the initial data and evaluate at a quarter period.'
 elif f.endswith('exact-curve'):
  m=int(match(r'y\(1\)=(\d+)')[1]);i=m-4;A=s.sqrt(m*m+m+1);B=s.sqrt(m*m+1) if i%2==0 else s.sqrt(m*m+2*m+2);why='Omit the mixed term from the initial potential value' if i%2==0 else 'Count the mixed and independent-square initial terms twice';ck('Positive intersection root',A*A,m*m+m+1);route='Recognize the total derivative of t²+ty+y², preserve its initial value, then select the required positive intercept.'
 elif f.endswith('distinct-characteristic-roots'):
  m=int(match(r'\+(\d+)y=0')[1]);i=m-4;A=s.exp(m)-s.E;B=s.exp(m-1)-s.E if i%2==0 else s.exp(m+1)-s.E;why='Use the fast characteristic exponent one unit too small' if i%2==0 else 'Use the fast characteristic exponent one unit too large';Y=s.exp(m*t)-s.exp(t);ck('Characteristic ODE residual',s.diff(Y,t,2)-(m+1)*s.diff(Y,t)+m*Y,0);ck('Initial derivative',s.diff(Y,t).subs(t,0),m-1);route='Factor the two characteristic roots and impose the initial cancellation and derivative data.'
 elif f.endswith('euler-cauchy-resonance'):
  m=int(match(r'e\^\{\\frac\{1\}\{(\d+)\}\}')[1]);i=m-4;A=s.exp(s.Rational(2,m))/(2*m*m);B=2*A if i%2==0 else A/2;why='Omit the repeated-integration factor one half' if i%2==0 else 'Apply the repeated-integration factor one half twice';Y=t*t*s.log(t)**2/2;ck('Euler equation residual',t*t*s.diff(Y,t,2)-3*t*s.diff(Y,t)+4*Y,t*t);route='Set s=ln t and factor out t²; the remaining equation is w″=1 with two zero initial data.'
 elif f.endswith('mixed-boundary-spectrum'):
  m=int(match(r'y\\prime\((\d+)\)=0')[1]);i=m-4;A=s.pi**2/(4*m*m);B=4*A if i%2==0 else A/4;why='Use two Dirichlet endpoints instead of the mixed boundary conditions' if i%2==0 else 'Double the interval length in the first mixed mode';ck('First mixed mode derivative endpoint',s.cos(m*s.sqrt(A)),0);route='Exclude nonpositive spectral parameters and choose the first zero of the cosine derivative boundary factor.'
 elif f.endswith('global-Riccati-threshold'):
  hit=match(r'y\^2-(\d+)t\^\{(\d+)\}');k=s.sqrt(s.Integer(hit[1]));n=int(hit[2])//2;assert 2*n==int(hit[2]);i=r['parameters']['instance'];A=k*n;B=k*(n-1) if i%2==0 else k*(n+1);why='Lower the derivative power coefficient by one' if i%2==0 else 'Raise the derivative power coefficient by one';pars={'n':n,'k':str(k)};q=k*t**n;ck('Threshold comparison polynomial equation',s.diff(q,t),q*q-k*k*t**(2*n)+A*t**(n-1));route='Find the comparison polynomial and prove both the global lower/upper barriers and the superquadratic escape above its threshold.'
 elif f.endswith('eccentric-annulus-capacity'):
  h=re.findall(r'\\frac1\{(\d+)\}',z);assert len(h)==2;(m,n)=map(int,h);i=r['parameters']['instance'];R=s.Rational(m,n);A=2*s.pi/s.log(R);pars={'m':m,'n':n};menus=[(s.Rational(1,2),1,4),(1,4,8)];coeffs=menus[i%2];why='';pool=[(s.sympify(c)*s.pi/s.log(R),{s.Rational(1,2):'Apply the angular symmetry reduction twice',1:'Omit the angular factor two',4:'Count the two symmetric half-annuli twice',8:'Count both angular reductions twice'}[s.sympify(c)]) for c in coeffs];route='Use conformal invariance of Dirichlet energy, prove the sharp radial Cauchy–Schwarz bound, and construct its attaining logarithmic potential.'
 elif f.endswith('Laguerre-zero-resolvent-limit'):
  c=parse(match(r'tP_n\\prime\\prime\+\((.*?)n\+1-t\)')[1]);i=r['parameters']['instance'];A=(s.sqrt((c+1)**2+4)-c-1)/2;q=int(2*c+2);bq=q-1 if i%2==0 else q+1;B=(s.sqrt(bq*bq+16)-bq)/4;why='Lose one half of the shifted logarithmic-derivative coefficient' if i%2==0 else 'Count an extra one half in the shifted logarithmic-derivative coefficient';pars={'c':str(c)};ck('Limit resolvent quadratic',A*A+(c+1)*A,1);assert A>0 and B>0;display=[rf'\frac{{\sqrt{{{q*q+16}}}-{q}}}{{4}}',rf'-\frac{{\sqrt{{{q*q+16}}}-{q}}}{{4}}',rf'\frac{{\sqrt{{{bq*bq+16}}}-{bq}}}{{4}}',rf'-\frac{{\sqrt{{{bq*bq+16}}}-{bq}}}{{4}}'];route='Prove positivity of the polynomial roots, control the differentiated resolvent error at a negative argument, and select the positive algebraic limit branch.'
 elif f.endswith('Riccati-turning-point-connection'):
  n=int(match(r'\\prime=t\^\{(\d+)\}')[1]);i=r['parameters']['instance'];nu=s.Rational(1,n+2);A=-(n+2)**(1-2*nu)*s.gamma(1-nu)/s.gamma(nu);B=2*A if i%2==0 else A/2;why='Count the two connection coefficients twice' if i%2==0 else 'Lose one of the two connection coefficients';pars={'n':n};ck('Gamma recurrence connection identity',-(n+2)**(-2*nu)*s.gamma(1-nu)/s.gamma(1+nu),A);route='Scale the turning point, linearize Riccati, select the recessive modified-Bessel branch, and match its two leading powers.'
 elif f.endswith('path-dependent-directional'):
  m=int(match(r'x\^\{(\d+)\}')[1]);i=m-4;A=s.Rational(1,2);B=s.Integer(1) if i%2==0 else s.Rational(1,4);why='Keep only one of the two equal denominator terms' if i%2==0 else 'Count both denominator terms twice';ck('Literal supplied path substitution',x**m*x**m/(x**(2*m)+x**(2*m)),A);route='Insert the explicitly given curve; the expression is the constant one half along it.'
 elif f.endswith('step-forcing'):
  m=int(match(r',\\\\(\d+),')[1]);i=m-4;A=s.Integer(2*m);B=s.Integer(m) if i%2==0 else s.Integer(4*m);why='Return the forcing amplitude instead of the peak step response' if i%2==0 else 'Count the constant and cosine parts twice';Y=m*(1-s.cos(t-1));ck('Shifted oscillator forcing',s.diff(Y,t,2)+Y,m);ck('Shifted oscillator evaluation',Y.subs(t,1+s.pi),A);route='Solve the familiar forced oscillator after the switch using the two zero matching data.'
 elif f.endswith('wronskian-transport'):
  m=int(match(r'\\frac\{(\d+)\}t')[1]);i=m-4;A=s.Rational(1,2**m);pars={'m':m};poolvalues=[(A*A,'Apply the coefficient of the logarithmic derivative twice'),(2*A,'Lower the transported power by one'),(s.Rational(1,2*m),'Replace exponential transport by reciprocal linear scaling'),(A/2,'Raise the transported power by one')];pool=[poolvalues[j] for j in ([0,1,3] if i%2==0 else [0,1,2])];ck('Wronskian scalar transport',s.diff(t**(-m),t),-m/t*t**(-m));route='Differentiate the Wronskian; cancellation gives W′=−mW/t, then impose the normalization.'
 elif f.endswith('nonlinear-radial-asymptotic'):
  m=int(match(r'\(u\(0\),v\(0\)\) =?\(?')[0]) if False else int(match(r'\(u\(0\),v\(0\)\)\s*=\((\d+),0\)')[1]);i=m-4;A=s.Rational(m*m,m*m+1);pars={'m':m};poolvalues=[(s.Rational(m*m,2*m*m+1),'Count the nonlinear damping coefficient twice'),(s.Rational(m*m,3*m*m+1),'Count the nonlinear damping coefficient three times'),(s.Rational(2*m*m,m*m+2),'Keep only half the nonlinear damping coefficient'),(s.Rational(3*m*m,m*m+3),'Keep only one third of the nonlinear damping coefficient')];pool=[poolvalues[j] for j in ([0,1,2] if i%2==0 else [0,2,3])];E=m*m*s.exp(-2*t)/(m*m+1-m*m*s.exp(-2*t));ck('Radial energy evolution',s.diff(E,t),-2*E*(1+E));ck('Scaled energy limit',s.limit(s.exp(2*t)*E,t,s.oo),A);route='Differentiate the squared radius so the rotation cancels, solve its separable scalar equation, and extract the exponential coefficient.'
 elif f.endswith('resonant-boundary-compatibility'):
  m=int(match(r'\\sin\((\d+)t\)')[1]);i=m-4;A=s.Rational(2*(-1)**m,m);B=2*A if i%2==0 else A/2;why='Count the sine-squared average one half twice' if i%2==0 else 'Omit the sine-squared average one half';ck('Forcing compatibility moment',s.integrate((t+A*s.sin(m*t))*s.sin(m*t),(t,0,s.pi)),0);route='Integrate against the resonant sine mode or substitute a direct particular solution; use the endpoint condition to determine the forcing coefficient.'
 elif f.endswith('nonconservative-hole'):
  m=int(match(r'C\(t\)=\((\d+)\\cos')[1]);i=m-4;A=2*s.pi;B=s.pi if i%2==0 else 4*s.pi;why='Integrate only a half-turn of the circle parameter' if i%2==0 else 'Count the full angular traversal twice';route='Parametrize the supplied circle: radius factors cancel and the angular integrand is one.'
 elif f.endswith('nonlinear-energy-speed'):
  m=int(match(r'y\(0\)=(\d+)')[1]);i=m-4;A=s.Integer(m*m);B=A/4 if i%2==0 else 4*A;why='Read the stated amplitude as a peak-to-peak distance and halve it before squaring' if i%2==0 else 'Use the peak-to-peak distance as the initial amplitude before squaring';ck('Conserved energy at zero displacement',A*A,m**4);route='Multiply the equation by the velocity to conserve kinetic plus quartic potential energy, then maximize speed at zero displacement.'
 elif f.endswith('pantograph-entire-growth'):
  m=int(match(r'F\(z/(\d+)\)')[1]);i=r['parameters']['instance'];A=1/(2*s.log(m));coeffs=[s.Rational(1,8),s.Rational(1,4),1] if i%2==0 else [s.Rational(1,4),1,2];why='';pool=[(s.sympify(c)/s.log(m),{s.Rational(1,8):'Apply the quadratic exponent factor one half three times',s.Rational(1,4):'Apply the quadratic exponent factor one half twice',s.Integer(1):'Omit the quadratic exponent factor one half',s.Integer(2):'Double the quadratic exponent scale instead of halving it'}[s.sympify(c)]) for c in coeffs];route='Obtain the entire positive-coefficient series recursively and use its largest-term quadratic exponent with matching upper and lower growth bounds.'
 elif f.endswith('minimum-peak-acceleration'):
  h=match(r'x\(([^()]*)\)=([^=,]+),\\quad x\\prime\(([^()]*)\)=([^.]*)\.');T=parse(h[1]);D=parse(h[2]);assert parse(h[3])==T;V=parse(h[4]);i=r['parameters']['instance'];delta=2*D-V*T;A=(delta+s.sqrt(delta**2+T*T*V*V))/(T*T);pars={'T':str(T),'D':str(D),'V':str(V)};coeffs=[s.Rational(1,2),2,3] if i%2==0 else [s.Rational(1,4),s.Rational(1,2),2];pool=[]
  for c in coeffs:
   dd=2*c*D-V*T;value=(dd+s.sqrt(dd*dd+T*T*V*V))/(T*T);pool.append((value,{s.Rational(1,4):'Apply the triangular displacement factor one half twice too many times',s.Rational(1,2):'Apply an extra triangular displacement factor one half',s.Integer(2):'Count the required displacement twice',s.Integer(3):'Count the required displacement three times'}[s.sympify(c)]))
  ck('Sharp feasibility quadratic',T*T*A*A+(2*V*T-4*D)*A-V*V,0);assert T>0 and D>0 and delta>0;route='Maximize displacement under the fixed velocity integral with a saturated two-level acceleration, then solve its sharp feasibility quadratic.'
 elif f.endswith('log-simplex-moment'):
  m=int(match(r'x\^\{(\d+)\}')[1]);i=m-4;hm=s.harmonic(m);hn=s.harmonic(m+3);h2=s.harmonic(m+3,2);moment=s.factorial(m)/s.factorial(m+3);A=s.expand(moment*((hm-hn)*(1-hn)-s.pi**2/6+h2));B=2*A if i%2==0 else A/2;why='Apply the factor two for a repeated derivative to the mixed parameter derivative' if i%2==0 else 'Insert a symmetrization factor one half into the mixed parameter derivative';route='Differentiate the two-parameter simplex moment once in each exponent and evaluate the resulting digamma and trigamma differences.'
 else:raise ValueError(f)
 if not pars:pars={'m':m}
 A=s.simplify(A)
 if pool is None:
  B=s.simplify(B);assert s.simplify(B/A)>0 and s.simplify(B-A)!=0
  pool=[(-A,'Reverse the orientation, derivative, or selected branch sign'),(B,why),(-B,why+' and reverse the final sign')]
 original=parse(next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']));ck('Literal answer preserved and independently reconstructed',original,A)
 return {'index':i,'parameters':pars,'answer':A,'pool':pool,'display':display,'checks':checks,'route':route}
@lru_cache(None)
def indexed():return {(r['familyId'],derive(r)['index']):r for r in inputs()[0]}
def catalog():return [{'familyId':f,'indices':sorted(i for fid,i in indexed() if fid==f),'newIndependentIdeas':0} for f in sorted({f for f,i in indexed()})]
def build(f,i):
 if type(i)is not int or (f,i) not in indexed():raise ValueError('Outside frozen272 record domain')
 old=indexed()[(f,i)];d=derive(old);choices=[]
 for j,(v,why) in enumerate([(d['answer'],'correct'),*d['pool']]):
  v=s.simplify(v);math=d['display'][j] if d['display'] else tex(v);assert s.simplify(parse(math)-v)==0
  choices.append({'choiceId':'ch_'+H(s.srepr(v))[:16],'math':math,'expression':s.srepr(v),'misconception':why})
 vals=[parse(c['math']) for c in choices]
 for a,b in itertools.combinations(vals,2):assert s.simplify(a-b).equals(0)is False,(f,i,a,b)
 oldbase=inputs()[1].get(old['problemId']);display=inputs()[2][old['problemId']];assert display['sourceContentHash']==old['contentHash'] and display['revision']==old['problemRevision']
 steps=list(display['steps']);
 if steps[-1]!=choices[0]['math']:steps.append(choices[0]['math'])
 row={'familyId':f,'topic':old['topic'],'difficulty':old['difficulty'],'instanceIndex':i,'parameters':d['parameters'],'finiteInstanceIndices':next(c['indices'] for c in catalog() if c['familyId']==f),'statement':display['statement'],'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':steps,'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':H(old),'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')},'sourcePresentation':{'sha256':hashlib.sha256((P/'ode-mv-option-complete-current-presentations.json').read_bytes()).hexdigest(),'entryHash':H(display),'solutionQuality':display.get('solutionQuality')},'verificationEvidence':d['checks'],'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[]),'review':{'status':'candidate-awaiting-independent-peer-and-final-id-screen','meaningChanged':False,'preservePreviousLineage':True,'newIndependentIdeas':0,'easiestOptionsVisibleRoute':d['route'],'optionRepairReason':'Remove a replicated cross-choice sign coupling or display-form cue using exact authored misconceptions and common expression conventions; finite screening and mathematical peer review remain separate gates.'}}
 if oldbase:row['previous']={'problemId':oldbase['problemId'],'revision':oldbase['problemRevision'],'sourceContentHash':oldbase['contentHash'],'semanticHash':oldbase['semanticHash'],'meaningChanged':False}
 else:row['replacesPrivateProblemId']=old['problemId']
 row['contentHash']=H(row);return row
def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=[build(q['familyId'],i) for q in catalog() for i in q['indices']];assert len(rows)==272
 (P/'ode-mv-option-candidates-v4.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
 report={'status':'author-finite-checks-passed-awaiting-independent-peer-and-final-id-screen','records':[{'familyId':r['familyId'],'index':r['instanceIndex'],'rawHash':H(r),'contentHash':r['contentHash'],'sourcePreview':r['sourcePreview'],'sourcePresentation':r['sourcePresentation'],'previous':r.get('previous'),'replacesPrivateProblemId':r.get('replacesPrivateProblemId'),'literalChoicePairCount':6,'checks':r['verificationEvidence'],'easiestOptionsVisibleRoute':r['review']['easiestOptionsVisibleRoute'],'recommendedDifficulty':r['difficulty']} for r in rows],'counts':{'records':272,'families':27,'baselineRevisions':168,'unpublishedReplacements':104,'literalChoicePairs':1632,'exactChecks':sum(len(r['verificationEvidence']) for r in rows)},'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['ode_mv_option_repairs.py','literal_numeric_extended.py','ode-mv-option-complete-preview-inputs.jsonl','ode-mv-option-complete-baseline-inputs.jsonl','ode-mv-option-complete-current-presentations.json','ode-mv-option-complete-presentation-manifest.json','ode-mv-option-candidates-v4.jsonl']}}
 (P/'ode-mv-option-verification-v4.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts'])
