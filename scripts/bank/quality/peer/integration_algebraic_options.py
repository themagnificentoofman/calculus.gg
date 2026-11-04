"""Independent integral derivations and exact inequalities for the final58 menus."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,sys
import sympy as s
from differentiation_literal_choices import parse,same
from limits_intervals import enclose as ordinary
from series_intervals import enclose as series,rounded
from rational_intervals import add,mul,power
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def bounds(v):
 if v.func==s.sin:return series(s.cos(s.pi/2-v.args[0],evaluate=False))
 if v.is_Add:
  a=(Q(0),)*2
  for t in v.args:a=rounded(add(a,bounds(t)))
  return a
 if v.is_Mul:
  a=(Q(1),)*2
  for t in v.args:a=rounded(mul(a,bounds(t)))
  return a
 if v.is_Pow and v.exp.is_Integer:return rounded(power(bounds(v.base),int(v.exp)))
 return ordinary(v)
def solve(r):
 f=r['familyId'];p=r['parameters'];m=s.Integer(p.get('m',1));x=s.symbols('x',real=True)
 if f=='io3-bernoulli-product':
  n=s.Integer(p['n']);polys=[s.Integer(1)]
  for j in range(1,int(max(m,n))+1):
   primitive=s.integrate(j*polys[-1],x);polys.append(s.expand(primitive-s.integrate(primitive,(x,0,1))))
  return s.integrate(s.expand(polys[int(m)]*polys[int(n)]),(x,0,1)),'The displayed generating function implies B0=1, Bn′=n B(n−1), and zero integral for n≥1. Reconstruct the finite polynomials recursively with these conditions, then integrate the exact product coefficient by coefficient.'
 if f=='io3-jensen-radius':
  R=s.Rational(p['radius']);assert R>1
  return 4*s.pi*s.log(R),'Factor the positive logarithm argument as R²|1−e^(ix)/R|². The uniformly convergent real logarithm Fourier series has zero circular mean; the constant term integrates to4π ln R.'
 if f.endswith('exponential-rate'):return (s.exp(m)-1)/m,'Differentiate e^(m x)/m and evaluate both stated endpoints.'
 if f.endswith('log-recognition'):return s.log((m+1)/m),'The positive affine denominator has logarithmic primitive; evaluate at0 and1 using the real quotient identity.'
 if f.endswith('odd-even'):
  h=s.sympify(p['halfWidth'],locals={'pi':s.pi}) if 'halfWidth'in p else s.pi/s.Integer(p['denominator']);assert 0<h<s.pi
  return 2*s.sin(h),'The cubic integrates to zero by oddness over the symmetric bounds. Cosine is even and has sine primitive, giving2sin(half-width).'
 if f.endswith('signed-area'):
  a,b,lo,hi=map(s.Rational,[p['slope'],p['intercept'],p['lower'],p['upper']]);assert lo<hi
  return s.integrate(a*x+b,(x,lo,hi)),'Integrate the actual revised affine integrand over its concrete endpoints; retain signed, rather than absolute, area.'
 if f.endswith('half-angle-quadratic'):
  d=s.sqrt(m*m-1);G=s.log((x+m-d)/(x+m+d))/d;assert m>1 and s.simplify(s.diff(G,x)-2/(x*x+2*m*x+1))==0
  return G.subs(x,1)-G.subs(x,0),'Set t=tan(x/2), with endpoints0 and1. The positive quadratic factors as(t+m−sqrt(m²−1))(t+m+sqrt(m²−1)); integrate its partial fractions. Every real logarithm argument is positive throughout the interval.'
 if f.endswith('mixed-log-endpoints'):
  n=m+1
  return s.harmonic(n)/n**2-(s.pi**2/6-s.harmonic(n,2))/n,'Expand−ln(1−x) in its nonnegative power series and use Tonelli with−x^m ln x. Integrating each logarithmic moment gives1/[k(k+m+1)²]; exact partial fractions leave the two displayed finite harmonic tails.'
 if f.endswith('reciprocal-quartic'):return s.pi/(2*m*(m+1)),'Subtract the two quadratic reciprocal kernels with coefficient1/(m²−1), then use their complete positive-half-line arctangent integrals.'
 if f.endswith('exponential-trig'):
  F=s.exp(x)*(s.cos(m*x)+m*s.sin(m*x))/(1+m*m);assert s.simplify(s.diff(F,x)-s.exp(x)*s.cos(m*x))==0
  return (s.exp(2*s.pi)-1)/(1+m*m),'Differentiate the independently constructed exponential-trigonometric primitive; evaluate at0 and2π using the integer frequency.'
 if f.endswith('partial-fractions'):return s.log(2*m/(m+1))/(m-1),'The kernel is(1/(x+1)−1/(x+m))/(m−1). Both denominators are positive; their exact logarithmic endpoint difference gives the answer.'
 if f.endswith('parts-log'):return m*s.log(m)-m+1,'Integration by parts gives x ln x−x; subtract its value−1 at the lower endpoint.'
 raise ValueError('Unreviewed family '+f)
def equal(a,b):return same(a,b) or s.simplify(s.expand_log(a-b,force=True))==0
def main(source,out):
 data=Path(source).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  try:
   answer,route=solve(r);values=[parse(c['math'])for c in r['choices']];matches=[i for i,v in enumerate(values)if equal(v,answer)];assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],('answer mismatch',answer,matches)
   pairs=[]
   for a,b in itertools.combinations(values,2):
    lo,hi=bounds(s.expand_func(a-b));assert lo>0 or hi<0,('Unseparated literal pair',a,b);pairs.append({'lower':str(lo),'upper':str(hi)})
   opposite=[(i,j)for i,j in itertools.combinations(range(4),2)if equal(values[i],-values[j])];assert len(opposite)==2
   results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'independentAnswer':s.srepr(answer),'route':route,'sixLiteralPairEnclosures':pairs,'oppositePairs':opposite,'passed':True})
  except Exception as e:results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'passed':False,'error':repr(e)})
  if len(results)%10==0:print(json.dumps({'reviewed':len(results),'failed':sum(not v['passed']for v in results)}),flush=True)
 deps=['integration_algebraic_options.py','differentiation_literal_choices.py','limits_intervals.py','series_intervals.py','rational_intervals.py'];report={'author':'integration_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()for f in deps},'instances':len(rows),'passed':sum(r['passed']for r in results),'records':results,'scope':'Independent literal integral derivations and six exact outward-rational pair inequalities per finite item. No author constructor or answer-expression oracle. Real logarithm domains and analytic convergence arguments are explicitly identified. Final history/source joins, canonical-ID screen and admission remain separate. Not formal or human certification.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['instances','passed']}));return report['instances']==report['passed']
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
