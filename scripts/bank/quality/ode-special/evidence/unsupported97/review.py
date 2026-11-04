"""Independent literal mathematical review of the97 previously unsupported menus."""
from pathlib import Path
import json,hashlib,re,itertools
import sympy as s
from literal_special import parse,alpha,B
from special_intervals import certificate,enclose
P=Path(__file__).resolve().parent
H=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
R=s.Rational;pi=s.pi

def zero(expr):return s.simplify(s.expand_log(s.expand_func(expr),force=True))==0

def bessel_cert(expr):
 u=s.Symbol('u',positive=True);e=s.cancel((expr/B).subs(alpha**2,u+4));num,den=s.fraction(e);poly=s.Poly(num,u);coeff=poly.all_coeffs();assert den.is_positive is True or all(c>0 for c in s.Poly(den,u).all_coeffs())
 if all(c>=0 for c in coeff) and any(c>0 for c in coeff):sign='positive'
 elif all(c<=0 for c in coeff) and any(c<0 for c in coeff):sign='negative'
 elif all(c==0 for c in coeff):sign='zero'
 else:raise AssertionError(('Bessel sign not certified',e))
 return {'sign':sign,'route':'Divide by positive J_(nu+1)(alpha)^2; put u=alpha^2-4>0; exact polynomial coefficients have one strict sign.','polynomial':s.srepr(num),'denominator':s.srepr(den)}

def elliptic_cert(expr,p):
 q=s.Symbol('q',positive=True);v=s.expand(expr.subs({s.elliptic_e(p):1,s.elliptic_e(p*p):q},simultaneous=True));assert not v.has(s.elliptic_e)
 a=s.simplify(v.subs(q,1));b=s.simplify(v.subs(q,s.sqrt(1+p)))
 ca={'sign':'zero','lower':'0','upper':'0'} if zero(a) else certificate(a);cb={'sign':'zero','lower':'0','upper':'0'} if zero(b) else certificate(b)
 signs={ca['sign'],cb['sign']}
 if signs<={'positive','zero'} and 'positive'in signs:sign='positive'
 elif signs<={'negative','zero'} and 'negative'in signs:sign='negative'
 elif signs=={'zero'} and zero(v):sign='zero'
 else:raise AssertionError(('Elliptic ratio endpoints do not separate',v,ca,cb))
 return {'sign':sign,'route':'Divide by E(p)>0. Strict pointwise integrand comparison gives 1<E(p^2)/E(p)<sqrt(1+p); the difference is affine in that ratio.','p':str(p),'ratioPolynomial':s.srepr(v),'lowerEndpoint':ca,'upperEndpoint':cb}

def solve(r):
 f=r['familyId'];z=r['statement'];checks=[];t=s.symbols('t',real=True)
 def hit(pattern):
  q=re.search(pattern,z);assert q,(f,pattern,z);return q
 def ck(label,a,b=0):assert zero(a-b),(label,a,b);checks.append({'description':label,'left':s.srepr(a),'right':s.srepr(b),'passed':True})
 special=None
 if f.endswith('Bessel-zero-normalization'):
  nu=int(hit(r'J_\{(\d+)\}')[1]);j=int(hit(r'alpha be the \}(\d+)')[1]);assert 0<=nu<=4 and j in[1,2]
  # Verify the displayed Bessel normalization identity formally, eliminating y'' by its ODE.
  y=s.Function('y')(t);F=(t*t*s.diff(y,t)**2+(t*t-nu*nu)*y*y)/2;res=s.diff(F,t).subs(s.diff(y,t,2),-s.diff(y,t)/t-(1-nu*nu/t**2)*y);ck('ODE normalization derivative',res,t*y*y)
  expected=B/2;special=('bessel',None);route='Bessel ODE boundary identity and derivative recurrence give J_(nu+1)(alpha)^2/2. Positive zeros exceed2 by the alternating defining series; the adjacent-order value is nonzero by ODE uniqueness.'
  domains=['nu is a nonnegative integer; root ordinal is1 or2.','All J orders occurring in choices are nu+1 and covered by the displayed series.','For0<z<=2, after factoring the leading positive monomial, the alternating series is positive: for nu>=1 the first pair is positive; for nu=0 at z2 the next pair1/4−1/36 is strictly positive. Thus every positive root alpha>2.','If J_nu(alpha)=J_(nu+1)(alpha)=0, the derivative recurrence gives J_nu prime(alpha)=0; regular ODE uniqueness contradicts the nonzero defining series. Hence B>0.']
 elif f.endswith('Gaussian-trigonometric-nodal-length'):
  n=int(hit(r'cos\((\d+)y\)')[1]);assert 2<=n<=11;p=1-R(1,n*n);expected=2*s.sqrt(2)*pi*n*s.elliptic_e(p);special=('elliptic',p)
  route='At each point F has variance2 and is independent of its Gaussian gradient. Kac–Rice gives density1/(2sqrt(pi)) times the mean anisotropic gradient norm; radial-angle integration gives total2sqrt(2)pi*n*E(1−1/n²).'
  domains=['Both actual parameters p and p² lie strictly between0and1, so all displayed elliptic integrals use the stated real parameter convention.','E(p)>0. The ratio of the two integrands lies strictly between1and sqrt(1+p) away from endpoints; integration preserves the strict ratio bounds.','Nondegenerate value-gradient joint Gaussian density and smooth finite trigonometric field justify the Kac–Rice first moment; the existing full theorem certificate is retained separately.'];checks.append({'description':'Parameter and normalization arithmetic','n':n,'p':str(p),'variance':2,'area':'4*pi^2','passed':bool(0<p*p<p<1)})
 elif f.endswith('schwarzian-ivp'):
  m=int(hit(r'y\\prime\(0\)=(\d+)')[1]);Y=s.tanh(m*t);dy=s.diff(Y,t);ck('Schwarzian equation',s.diff(Y,t,3)/dy-R(3,2)*(s.diff(Y,t,2)/dy)**2,-2*m*m);ck('Initial slope',dy.subs(t,0),m);expected=s.tanh(m);route='Set p=y″/y′ to obtain a Riccati equation with p(0)=0; its solution integrates to tanh(mt).';domains=['m is a positive displayed integer; cosh(mt)>0 on the real axis, so y prime is positive.','All tanh choices are real. Every displayed tan integer is certified away from its cosine zeros by outward rational bounds.']
 elif f.endswith('darboux-oscillator'):
  m=int(s.sqrt(int(hit(r'y\\prime\\prime\+\((\d+)\+')[1])));h=s.symbols('h',real=True);Y=m*s.sin(m*t)+h*s.cos(m*t);D=lambda q:s.diff(q,t)+(1-h*h)*s.diff(q,h);ck('Independent Darboux residual',s.expand(D(D(Y))+(m*m+2*(1-h*h))*Y),0);ck('Initial slope',D(Y).subs({t:0,h:0}),m*m+1);expected=s.sqrt(2)*(m+s.tanh(pi/(4*m)))/2;route='The explicit Darboux-transformed oscillator solves the equation and both initial data; evaluate at the displayed quarter phase.';domains=['m>0, all hyperbolic functions have real arguments, and cosh is nonzero. The statement defines sech as1/cosh.']
 elif f.endswith('Green-kernel-square-trace'):
  a=s.sqrt(int(hit(r'-G_\{tt\}\+(\d+)G')[1]));v=s.symbols('v',positive=True);trace=(v*s.coth(v)-1)/(2*v*v);expected=s.coth(a)/(4*a**3)+1/(4*a*a*s.sinh(a)**2)-1/(2*a**4);ck('Derivative of resolvent trace',(-s.diff(trace,v)/(2*v)).subs(v,a),expected);route='The explicit positive Dirichlet Green kernel has resolvent trace(a*coth(a)−1)/(2a²); differentiating the resolvent parameter gives its square trace.';domains=['a is a positive integer1..10; sinh(a)>0.','All scalar menu functions are finite real. The true integral is strictly positive because its nonzero real kernel is squared.']
 elif f.endswith('squared-log-disk'):
  m=int(hit(r'1-x/(\d+)')[1]);q=R(1,m*m);expected=pi*(s.polylog(2,q)-(m*m-1)*s.log(1-q)-1)/2;k=s.symbols('k',positive=True);ck('Series coefficient decomposition',1/(k*k*(k+1)),1/k**2-1/k+1/(k+1));route='Expand the real logarithmic Fourier series, use angular orthogonality, integrate radial powers, and sum1/[k²(k+1)] by the displayed exact decomposition.';domains=['q=1/m² lies in(0,1); the Li2 series converges absolutely and every logarithm has positive argument.','The Fourier series is uniformly convergent on the unit disk because1/m<1, allowing termwise integration; the integral is strictly positive.']
 elif f.endswith('confocal-distance-integral'):
  cap=int(hit(r'r_\+\+r_-\\le(\d+)')[1]);a=R(cap,2);angular=pi if r'\le\sqrt{2}' in z else 2*pi/3;expected=angular*s.acosh(a);route='Elliptic coordinates give Jacobian r_plus*r_minus, which cancels the denominator. The radial coordinate ranges0..acosh(cap/2), and the displayed difference bound gives angular measure pi or2pi/3.';domains=['cap/2 is an integer2..6; arccosh has its real principal value.','The alternative arcsinh arguments are also positive real numbers; no branch ambiguity.','Coordinate degeneracy on the focal segment has planar measure zero; the canceled integral is finite.']
 elif f.endswith('spherical-triangle-vector-area'):
  h=hit(r'C=\\frac\{\((\d+),(\d+),(\d+)\)\}');a,b,c=map(s.Integer,h.groups());rr=s.sqrt(a*a+b*b+c*c);expected=pi/4-a*s.acos(b/rr)/(2*s.sqrt(a*a+c*c))-b*s.acos(a/rr)/(2*s.sqrt(b*b+c*c));route='By Stokes, integral n_z dS is one half of the z component of the boundary cross-product integral. Each oriented short great-circle arc contributes its angle times its unit normal.';domains=['All three coordinates are strictly positive, selecting the positive-octant short-arc triangle.','Every arccos argument lies in(0,1), and every arctan argument is positive; principal real branches are unambiguous.','Despite the family name, the requested z-weighted integral is scalar, not a vector or tuple.'];checks.append({'description':'Arc normal denominators and acos domains','passed':bool(a>0 and b>0 and c>0 and a/rr<1 and b/rr<1)})
 elif f.endswith('disk-to-annulus-optimal-transport'):
  h=hit(r'\\quad (.*?)\\le \|Y\|\^2\\le');a2=parse(h[1]);a=s.sqrt(a2);assert 0<a2;expected=1+a2-(2+a2)*s.sqrt(1+a2)/2+a2*a2*s.asinh(1/a)/2;u=s.symbols('u',positive=True);F=((2*u+a2)*s.sqrt(u*(u+a2))-a2*a2*s.asinh(s.sqrt(u)/a))/4;ck('Radial coupling primitive derivative',s.diff(F,u),s.sqrt(u*(u+a2)));route='Align angles, then use increasing radial-quantile coupling to maximize the product of radii. The remaining integral is the independently differentiated primitive.';domains=['a² is the displayed positive inner squared radius; the outer squared radius is a²+1.','All arcsinh arguments are positive; its real logarithmic definition is explicitly supplied.','Layer-cake rearrangement proves global optimality among all joint distributions with the prescribed marginals.']
 elif f.endswith('nonlinear-damping-Melnikov-bound'):
  m=int(hit(r'1\+x\^\{(\d+)\}')[1])//2;u=s.symbols('u',real=True);damping=R(4,3)+2**(m+1)*s.integrate(u*u*(1-u*u)**m,(u,-1,1));expected=damping*s.cosh(pi/2)/(s.sqrt(2)*pi);route='Insert the homoclinic sqrt(2)*sech(t), compute damping by u=tanh(t), and integrate the forcing term by parts. Its Fourier coefficient is sqrt(2)*pi/cosh(pi/2), so simple zeros require amplitude above the damping-to-coefficient ratio.';domains=['m is a positive integer1..10; all damping integrals are absolutely convergent.','The forcing phase is real and the threshold is an infimum; at equality the zero is not simple.','All displayed sinh/cosh arguments are pi/2, finite positive, and no Gamma function is used in any choice.'];checks.append({'description':'Independent exact polynomial damping integral','value':str(damping),'passed':bool(damping>0)})
 elif f.endswith('Gaussian-wedge'):
  m=int(hit(r'\\pi\}\{(\d+)\}|\\pi/(\d+)')[1] or hit(r'\\pi\}\{(\d+)\}|\\pi/(\d+)')[2]);expected=(m-1)*pi/(2*m*s.sin(pi/m));route='Whiten the positive quadratic form; its quadrant becomes a wedge of angle pi−pi/m, with Jacobian1/sin(pi/m). Radial integration contributes one half.';domains=['m>1 gives0<pi/m<pi, so the Gaussian quadratic form is positive definite and sin(pi/m)>0.'];checks.append({'description':'Whitening determinant and angle domain','m':m,'passed':m>1})
 else:raise KeyError(f)
 return expected,special,route,domains,checks

def main():
 out=[];errors=[]
 for q in json.loads((P/'inputs.json').read_text()):
  r=q['activeMenu'];key={'problemId':q['sourceCanonical']['problemId'],'familyId':r['familyId'],'instance':r['parameters']['instance']}
  try:
   vals=[parse(c['math']) for c in r['choices']];expected,special,route,domains,checks=solve(r);answer=next(v for c,v in zip(r['choices'],vals) if c['choiceId']==r['answerChoiceId']);assert zero(answer-expected),('Independent answer mismatch',answer,expected)
   def certify(v):
    if zero(v):return {'sign':'zero','route':'exact symbolic identity'}
    if special and special[0]=='bessel':return bessel_cert(v)
    if special and special[0]=='elliptic':return elliptic_cert(v,special[1])
    return certificate(v)
   pairs=[];opposites=[]
   for i,j in itertools.combinations(range(4),2):
    c=certify(vals[i]-vals[j]);assert c['sign']in['positive','negative'],('Choice equality or unproved distinction',i,j,c);sm=certify(vals[i]+vals[j]);assert sm['sign']!='unresolved',('Unresolved opposite comparison',i,j,sm)
    pairs.append({'choiceIds':[r['choices'][i]['choiceId'],r['choices'][j]['choiceId']],'difference':c,'sum':sm})
    if sm['sign']=='zero':opposites.append([r['choices'][i]['choiceId'],r['choices'][j]['choiceId']])
   out.append({**key,'sourceCanonicalContentHash':q['sourceCanonical']['contentHash'],'sourceCanonicalRawHash':q['sourceCanonicalHash'],'activePresentationRawHash':H(r),'presentationBinding':q['presentationBinding'],'scalarDisposition':'scalar; family-specific literal verification performed','independentAnswer':s.srepr(expected),'answerMatches':True,'pairCertificates':pairs,'mathematicalOppositePairs':opposites,'oppositePairContainsCorrect':any(r['answerChoiceId'] in p for p in opposites),'publicFunctionDomains':domains,'correctTaskRoute':route,'independentChecks':checks,'priorProofBinding':{'validationHash':H(q['sourceCanonical']['validation']),'authorRawHash':q['sourceCanonical']['provenance']['authoring'].get('rawSha256'),'scope':'Earlier full task proofs retained; this review independently derives the selected scalar answer and all literal distinctions.'},'status':'confirmed-singleton-opposite-pair-blocker' if len(opposites)==1 else 'literal-mathematics-and-domains-passed'})
  except Exception as e:errors.append({**key,'error':repr(e)})
 (P/'review-results.json').write_text(json.dumps({'records':out,'errors':errors,'counts':{'requested':97,'completed':len(out),'pairDistinctions':6*len(out),'oppositeSumChecks':6*len(out),'blockers':sum(r['status'].startswith('confirmed') for r in out),'errors':len(errors)}},indent=2)+'\n');print('completed',len(out),'errors',errors,'blockers',sum(r['status'].startswith('confirmed') for r in out))
if __name__=='__main__':main()
