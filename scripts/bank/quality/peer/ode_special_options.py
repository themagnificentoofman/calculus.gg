"""Independent Green double integration and Bessel Sturm identity for 17 menus.

Only literal TeX is used for options. No author answer expression or constructor
is imported. Bessel inequalities use positive polynomial coefficients; Green
inequalities use outward rational exponential enclosures.
"""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,re,sys
import sympy as s
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application
from limits_intervals import enclose

B,alpha=s.symbols('B alpha',positive=True)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def literal(tex,order=None):
 v=tex
 if order is not None:
  expected=r'J^{2}_{'+str(order)+r'}\left(\alpha\right)'
  v=v.replace(expected,'B')
  assert 'J'not in v,tex
 for token in [r'\left',r'\right',r'\,',r'\!']:v=v.replace(token,'')
 v=v.replace(r'\alpha','alpha')
 v=re.sub(r'\\sinh\^\{2\}\{\((\d+)\s*\)\}',r'(sinh(\1))^{2}',v)
 v=v.replace(r'\coth',' coth ').replace(r'\sinh',' sinh ')
 def group(i):
  assert v[i]=='{',tex
  n=1;j=i+1
  while n:
   assert j<len(v),tex
   n+=(v[j]=='{')-(v[j]=='}');j+=1
  return v[i+1:j-1],j
 while r'\frac'in v:
  i=v.index(r'\frac');a,j=group(i+5);b,j=group(j)
  v=v[:i]+'(('+a+')/('+b+'))'+v[j:]
 v=v.replace('{','(').replace('}',')').replace('^','**')
 assert re.fullmatch(r'[A-Za-z0-9\s()+*/.\-]+',v),tex
 assert set(re.findall(r'[A-Za-z]+',v))<={'B','alpha','coth','sinh'},tex
 return parse_expr(v,local_dict={'B':B,'alpha':alpha,'coth':s.coth,'sinh':s.sinh},transformations=standard_transformations+(implicit_multiplication_application,))

def green_derivation():
 t,x,a=s.symbols('t x a',positive=True)
 left=s.sinh(a*t)*s.sinh(a*(1-x))/(a*s.sinh(a))
 right=s.sinh(a*x)*s.sinh(a*(1-t))/(a*s.sinh(a))
 assert s.simplify(-s.diff(left,t,2)+a*a*left)==0
 assert s.simplify((s.diff(right,t)-s.diff(left,t)).subs(t,x)+1)==0
 assert left.subs(t,0)==right.subs(t,1)==0
 inner=s.sinh(2*a*x)/(4*a)-x/2
 assert s.simplify(s.diff(inner,x)-s.sinh(a*x)**2)==0
 # Direct square integration over both symmetric triangles; no trace or
 # parameter differentiation from the authored solution is used here.
 integral=2*s.integrate(s.expand((s.sinh(a*(1-x))**2*inner).rewrite(s.exp)),(x,0,1))/(a*a*s.sinh(a)**2)
 closed=s.coth(a)/(4*a**3)+1/(4*a*a*s.sinh(a)**2)-1/(2*a**4)
 assert s.simplify((integral-closed).rewrite(s.exp))==0
 return a,closed

def bessel_derivation():
 k,n=s.symbols('k n',integer=True,positive=True)
 coefficient=lambda order,index:(-1)**index/(2**(2*index+order)*s.factorial(index)*s.factorial(index+order))
 assert s.simplify(2*k*coefficient(n,k)+coefficient(n+1,k-1))==0
 assert s.simplify(4*k*(k+n)*coefficient(n,k)+coefficient(n,k-1))==0
 r,l=s.symbols('r l',positive=True);u=s.Function('u')(r);v=s.Function('v')(r)
 L=lambda f:-s.diff(r*s.diff(f,r),r)+n*n*f/r
 W=r*(v*s.diff(u,r)-u*s.diff(v,r))
 assert s.expand(s.diff(W,r)-(u*L(v)-v*L(u)))==0
 return {
  'derivation':'Differentiate the Sturm equation in lambda for u(r)=J_nu(lambda*r). Lagrange identity gives [r(v*uprime-u*vprime)]_0^1=2lambda integral(r*u^2). The defining series makes the zero endpoint vanish. At a root, v(1)=Jprime(alpha), uprime(1)=alpha*Jprime(alpha); division gives integral=Jprime(alpha)^2/2=J_(nu+1)(alpha)^2/2.',
  'rootDomain':'For nu>=1 and0<z<=2, the normalized alternating series exceeds1-z²/[4(nu+1)]>=nu/(nu+1)>0. For nu=0 the first pair is positive for z<2; at z=2 the next pair1/4-1/36>0 and the remaining alternating tail is positive. Thus alpha>2. Coefficient ratios decrease, justifying each bound.',
  'positiveScale':'At alpha>0 the ODE is regular. A common zero of J_nu and J_(nu+1) would also have derivative zero by the coefficient-checked recurrence, contradicting uniqueness and the nonzero defining series. Hence B=J_(nu+1)(alpha)^2>0.',
  'exactCoefficientChecks':2,'lagrangeIdentityChecked':True,
 }

def bessel_sign(value):
 q=s.symbols('q',positive=True)
 quotient=s.cancel((value/B).subs(alpha**2,q+4))
 numerator,denominator=map(s.expand,s.fraction(quotient))
 nc=s.Poly(numerator,q).all_coeffs();dc=s.Poly(denominator,q).all_coeffs()
 assert all(c>=0 for c in dc)and any(c>0 for c in dc)
 sign=1 if all(c>=0 for c in nc)and any(c>0 for c in nc)else -1 if all(c<=0 for c in nc)and any(c<0 for c in nc)else 0
 assert sign or numerator==0,(value,quotient)
 return {'sign':sign,'positiveVariable':'q=alpha^2-4','numerator':str(numerator),'positiveDenominator':str(denominator)}

def main(source,output):
 source,output=Path(source),Path(output)
 if output.exists():raise ValueError('Preserve earlier report')
 parameter,green=green_derivation();bessel=bessel_derivation();records=[]
 for raw in map(json.loads,source.read_text().splitlines()):
  family=raw['familyId'];index=raw['instanceIndex'];is_bessel=family.endswith('Bessel-zero-normalization')
  if is_bessel:
   nu=int(re.search(r'J_\{(\d+)\}',raw['statement'])[1]);assert nu==raw['parameters']['nu'] and 0<=nu<=4
   vals=[literal(c['math'],nu+1)for c in raw['choices']];answer=B/2
   allowed={s.Integer(0),B/4,B,B/(2*alpha**2),B*alpha**2/2,B*alpha**2}
   assert all(v==answer or v in allowed for v in vals)
   certify=bessel_sign;route=bessel['derivation']
  else:
   assert family.endswith('Green-kernel-square-trace')
   a=s.sqrt(s.Integer(re.search(r'-G_\{tt\}\+(\d+)G',raw['statement'])[1]));assert a==s.Rational(raw['parameters']['a']) and a>0
   vals=[literal(c['math'])for c in raw['choices']];answer=green.subs(parameter,a)
   route='Explicitly verify the matched zero-boundary Green kernel and jump. Integrate its square first over0<t<s<1, using the elementary primitive of sinh², then double by symmetry. This independently yields the displayed hyperbolic expression.'
   def certify(v):
    v=s.cancel(v.rewrite(s.exp))
    if v==0:return {'sign':0,'lower':'0','upper':'0'}
    lo,hi=enclose(v);assert lo>0 or hi<0
    return {'sign':1 if lo>0 else -1,'lower':str(lo),'upper':str(hi)}
  correct=next(v for c,v in zip(raw['choices'],vals)if c['choiceId']==raw['answerChoiceId'])
  assert s.simplify((correct-answer).rewrite(s.exp))==0
  pairs=[];opposites=[]
  for i,j in itertools.combinations(range(4),2):
   difference=certify(vals[i]-vals[j]);assert difference['sign']!=0
   total=certify(vals[i]+vals[j]);pairs.append({'choiceIds':[raw['choices'][i]['choiceId'],raw['choices'][j]['choiceId']],'difference':difference,'sum':total})
   if total['sign']==0:opposites.append([i,j])
  assert len(opposites)in[0,2]
  records.append({'familyId':family,'index':index,'rawSha256':hashlib.sha256(canonical(raw).encode()).hexdigest(),'independentAnswer':str(answer),'route':route,'correctAnswerPassed':True,'literalPairCertificates':pairs,'mathematicalOppositePairs':opposites,'passed':True})
 assert len(records)==17
 dependencies=[Path(__file__),Path(__file__).with_name('limits_intervals.py'),Path(__file__).with_name('series_intervals.py'),Path(__file__).with_name('rational_intervals.py')]
 output.write_text(json.dumps({'author':'coverage_research','reviewer':'root','inputSha256':sha(source),'reviewSources':{p.name:sha(p)for p in dependencies},'instances':17,'pairInequalities':102,'oppositeSumChecks':102,'besselDomainArgument':bessel,'records':records,'scope':'Independent literal mathematics and domain review. Final family/form screen, classification, lineage and admission remain separate; no formal or human certification.'},indent=2)+'\n')
 print(json.dumps({'passed':len(records),'literalPairs':102,'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
