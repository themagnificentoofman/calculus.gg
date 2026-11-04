"""Independent literal finite review of the additional97 ODE/MV menus."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from ode_mv_literal_choices import parse,same
from lower_ode_mv import solve as lower
from limits_intervals import enclose
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def solve(r):
 f=r['familyId'];p=r['parameters'];m=s.Integer(p.get('m',1));t=s.symbols('t',real=True)
 if f.endswith('finite-blowup'):
  answer=(m+1)/m;y=1/(m+1-m*t);assert s.simplify(s.diff(y,t)-m*y*y)==0 and y.subs(t,0)==1/(m+1)
  return answer,'Differentiate the explicit reciprocal solution and locate its first future pole. The smooth vector field gives uniqueness up to that pole; the finite endpoint is(m+1)/m.'
 if f.startswith('m3-') and not f.endswith('simplex-log-partition'):
  a,route,checks,level=lower(r);return a,route+' '+str(checks)
 if f.endswith('simplex-log-partition'):
  assert m>3;weights=[1/m,2/m,1-3/m];answer=-sum(v*s.log(v) for v in weights)
  x,y=s.symbols('x y',real=True);F=s.log(1+s.exp(x)+s.exp(y))-(x+2*y)/m;point={x:s.log(1/(m-3)),y:s.log(2/(m-3))}
  assert all(s.simplify(s.diff(F,z).subs(point))==0 for z in [x,y])
  return answer,'The three positive softmax weights at the minimizer must be1/m,2/m,1−3/m. Weighted log-sum-exp convexity gives the global minimum; the finite critical point attains its Shannon entropy.'
 if f.endswith('bistable-front-speed'):
  k=s.Integer(p['k']);a=s.Rational(p['a']);assert k>0 and 0<a<1;Y=1/(1+s.exp(k*t));c=k*(1-2*a)
  assert s.simplify(s.diff(Y,t,2)+c*s.diff(Y,t)+2*k*k*Y*(1-Y)*(Y-a))==0
  return c,'The decreasing logistic profile has the stated two endpoint limits and satisfies the ODE exactly. For uniqueness put p(y)=−y′>0. It solves p′=c−f(y)/p; increasing c raises the slope near y=0 but lowers it near y=1. A first crossing between two such positive phase curves would have derivative difference c2−c1>0, contradicting crossing from above. Endpoint slopes follow the two linearized characteristic roots.'
 if f.endswith('logarithmic-relaxation-constant'):
  a=s.Integer(p['a']);b=1/s.Rational(p['b']);assert a>0 and b>0
  w=s.symbols('w',positive=True);assert s.simplify(s.diff(w-a*s.log(w+a),w)*(1+a/w))==1
  return b-a*s.log(b+a),'For w=1/y, w′=1+a/w and b denotes the reciprocal of the displayed initial value. Thus w(0)=b. Integrating gives w−a ln(w+a)=t+b−a ln(b+a). Bounds w≥b+t and w≤b+t+a ln((b+t)/b) imply w/t→1; subtracting t+a ln t yields the stated constant.'
 if f.endswith('spectral-potential-derivative'):
  L=s.Rational(p['ell']);n=s.Integer(p['n']);assert L>0 and n>0
  v=s.sin(n*s.pi*t/L);norm=s.integrate(v*v,(t,0,L));a=s.integrate(t*t*v*v,(t,0,L))/norm
  return s.simplify(a),'The unperturbed Dirichlet eigenvalue is simple. Differentiate the eigenvalue equation, multiply by the unperturbed sine eigenfunction and integrate by parts; the eigenfunction derivative terms cancel. Normalize its exact second spatial moment.'
 if f.endswith('Gaussian-entropy-variational'):
  a,b,c=map(s.Integer,[p['a'],p['b'],p['c']]);det=a*b-c*c;assert a>0 and det>0
  return -s.log(2*s.pi)-1-s.log(det)/2,'Relative entropy against the centered Gaussian with the given covariance is nonnegative, by z ln z−z+1≥0. The cross-entropy is fixed by the mean and covariance; the Gaussian itself attains equality. Its exact determinant and two-dimensional normalization give the minimum.'
 if f.endswith('optimizer-fourth-envelope-derivative'):
  a,b,c,p0,q=map(s.Integer,[p['a'],p['b'],p['c'],p['p'],p['q']]);A=s.Matrix([[a,c],[c,b]]);assert a>0 and A.det()>0;v=A.inv()*s.Matrix([p0,q]);answer=6*sum(w**4 for w in v)
  return s.simplify(answer),'The positive quadratic form plus coordinate quartics is strictly convex and coercive, so its critical point is the unique minimizer. The implicit-function theorem gives z=t A^(−1)b+O(t³). Stationarity cancels the unknown cubic displacement from the fourth-order objective coefficient, leaving one quarter the sum of the two fourth powers; multiply by4!.'
 raise ValueError('Unreviewed family '+f)
def main(source,out):
 data=Path(source).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  try:
   a,route=solve(r);values=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(values)if same(v,a)];assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],('answer mismatch',a,matches)
   pairs=[]
   for left,right in itertools.combinations(values,2):
    difference=s.simplify(s.expand_func(left-right)).replace(lambda v:v.func in [s.sinh,s.cosh],lambda v:v.rewrite(s.exp));lo,hi=enclose(difference);assert lo>0 or hi<0,('Unseparated choices',left,right)
    pairs.append({'lower':str(lo),'upper':str(hi)})
   opposite=[(i,j)for i,j in itertools.combinations(range(4),2)if same(values[i],-values[j])];assert len(opposite)in [0,2]
   results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'sourcePreview':r['sourcePreview'],'independentAnswer':s.srepr(a),'route':route,'sixLiteralPairEnclosures':pairs,'oppositePairs':opposite,'passed':True})
  except Exception as e:results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'passed':False,'error':repr(e)})
  if len(results)%20==0:print(json.dumps({'reviewed':len(results),'failed':sum(not v['passed']for v in results)}),flush=True)
 deps=['ode_mv_additional_options.py','ode_mv_literal_choices.py','lower_ode_mv.py','literal_choices.py','limits_intervals.py','series_intervals.py','rational_intervals.py'];report={'author':'coverage_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()for f in deps},'instances':len(rows),'passed':sum(r['passed']for r in results),'records':results,'scope':'Finite answers independently derived from the statements and all literal option pairs separated with outward rational intervals. No author constructor/answer expression is an oracle. Analytic arguments are mathematical review, not machine-checked formal proof or human calibration. Final source identity, classification and actual-ID screen remain separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['instances','passed']}));return report['instances']==report['passed']
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
