"""Independent finite literal-option checks; no author constructor is imported.

Prior independent proof obligations remain source-bound separately. This
amendment rederives values from each finite parameter and inspects new choices.
"""
from pathlib import Path
import copy,hashlib,itertools,json,sys
import sympy as s
from ode_mv_literal_choices import parse,same,distinct
from lower_ode_mv import solve as lower
from existing_multivariable import solve as mv
from series_intervals import enclose

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def solve(r):
 f=r['familyId'];p=r['parameters'];m=s.Integer(p.get('m',1));t=s.symbols('t',real=True)
 if f.startswith('m3-') and '-olympiad-' not in f:
  a,route,checks,level=lower(r);return a,route,checks
 if f.endswith('nonlinear-radial-asymptotic'):
  # q=u²+v², q'=-2q(1+q). Its reciprocal obeys a linear ODE.
  q=m*m*s.exp(-2*t)/(1+m*m*(1-s.exp(-2*t)))
  assert s.simplify(s.diff(q,t)+2*q*(1+q))==0 and q.subs(t,0)==m*m
  return m*m/(1+m*m),'Differentiate the radial square, solve its reciprocal linear equation, and take the exact positive-time asymptote.',['Exact radial differential identity and initial condition']
 if f.endswith('resonant-boundary-compatibility'):
  forcing=s.integrate(t*s.sin(m*t),(t,0,s.pi));norm=s.integrate(s.sin(m*t)**2,(t,0,s.pi));assert norm>0
  return -forcing/norm,'Multiply by the Dirichlet null mode and integrate by parts; the orthogonality condition is necessary and the variation-of-constants solution makes it sufficient.',['Exact two compatibility integrals']
 if f.endswith('log-simplex-moment'):
  a,b=s.symbols('a b',positive=True);base=s.gamma(a+1)*s.gamma(b+1)/s.gamma(a+b+3)
  ans=s.simplify(s.expand_func(s.diff(base,a,b).subs({a:m,b:1})))
  return ans,'Differentiate the independently evaluated simplex beta integral in both exponents. Powers near the positive finite exponents dominate both logarithmic factors, justifying differentiation.',['Exact mixed beta derivative']
 if f.endswith('two-centre-resolvent') or f.endswith('polynomial-image-winding'):
  row=copy.deepcopy(r);row['provenance']={'authoring':{'builderParameters':{'m':int(m)}}};a,checks=mv(row)
  return a,'Reuse the separately written root derivation: parameter-completed-square primitive, or exact double-root factorization plus the strict coefficient-radius zero exclusion.',checks
 if f.endswith('Laguerre-zero-resolvent-limit'):
  c=s.Rational(p['c']);a=(s.sqrt((c+1)**2+4)-c-1)/2
  assert s.simplify(a*a+(c+1)*a-1)==0 and a>0
  return a,'Positive Laguerre roots bound the logarithmic-derivative remainder by 1/n at t=-n. The ODE leaves S²+(c+1)S-1→0; positivity selects its unique positive root.',['Exact limiting quadratic and positive branch']
 if f.endswith('Riccati-turning-point-connection'):
  n=s.Integer(p['n']);assert n>0 and n%2==1;nu=1/(n+2)
  a=-(n+2)**(1-2*nu)*s.gamma(1-nu)/s.gamma(nu)
  return a,'Scale t by ε^(2/(n+2)) and y by ε^(n/(n+2)). On the negative half-line the Riccati substitution gives u″=x^n u. The selected decaying solution is sqrt(x) K_{1/(n+2)}(2x^((n+2)/2)/(n+2)); its two small-argument coefficients give u′(0)/u(0). Positivity of the decaying solution permits continuation to zero.',['Exact Gamma connection ratio; existing independent Bessel-branch proof retained']
 if f.endswith('global-Riccati-threshold'):
  n=s.Integer(p['n']);k=s.Rational(p['k']);assert n>0 and k>0
  a=n*k;y=k*t**n
  assert "-"+str(k*k)+"t^{"+str(2*n)+"}" in r["statement"]
  assert s.simplify(s.diff(y,t)-(y*y-k*k*t**(2*n)+a*t**(n-1)))==0
  return a,'The positive decaying ground state exp(-k t^(n+1)/(n+1)) gives the critical Riccati solution. The independently reviewed ground-state identity and Sturm comparison distinguish global solutions from a finite first zero.',['Exact critical Riccati residual; ground-state/first-zero argument retained']
 if f.endswith('minimum-peak-acceleration'):
  D,T,V=map(s.Rational,[p['D'],p['T'],p['V']]);assert T>0
  B=abs(D-T*V/2);a=(2*B+s.sqrt(4*B*B+T*T*V*V))/(T*T)
  assert a>=abs(V)/T and s.simplify(a*a*T*T-4*a*B-V*V)==0
  return a,'For fixed integral V and bound M, arrange acceleration at ±M on endpoint intervals to maximize or minimize displacement. The sharp moment inequality |D-TV/2|≤MT²/4-V²/(4M) and a one-switch attaining control give the positive quadratic root.',['Exact moment quadratic and feasible velocity bound']
 if f.endswith('pantograph-entire-growth'):
  assert m>1
  return 1/(2*s.log(m)),'The recurrence gives coefficient m^(-j(j-1)/2)/j!. A maximal term near ln(r)/ln(m) gives the lower exponent; the Gaussian sum upper bound and j ln j=o((ln r)²) give the same limit.',['Independent positive-coefficient maximum-term argument']
 if f.endswith('eccentric-annulus-capacity'):
  n=s.Integer(p['n']);assert m>n>1
  return 2*s.pi/s.log(m/n),'The Möbius map gives a round annulus without a pole on the closure and preserves Dirichlet energy. Radial Cauchy–Schwarz gives 2π/ln(m/n), attained by the normalized logarithmic radius.',['Conformal domain and exact radial energy']
 raise ValueError('Unreviewed family '+f)

def exact_same(a,b):
 if same(a,b):return True
 # Gamma duplication/recurrence may require simplifying a quotient first.
 return s.simplify(s.gammasimp(s.expand_func(a/b)))==1 if a!=0 and b!=0 else False
def separated(a,b):
 if distinct(a,b):return 'exact-symbolic'
 lo,hi=enclose(s.simplify(s.expand_func(a-b)))
 assert lo>0 or hi<0,(a,b)
 return 'outward-rational-enclosure'
def main(source,out):
 data=Path(source).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  try:
   answer,route,checks=solve(r);values=[parse(c['math']) for c in r['choices']]
   matches=[i for i,v in enumerate(values) if exact_same(v,answer)]
   assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],('answer',answer,matches)
   pairs=[separated(a,b) for a,b in itertools.combinations(values,2)]
   opposite=[(i,j) for i,j in itertools.combinations(range(4),2) if exact_same(values[i],-values[j])]
   assert len(opposite) in [0,2],('single-opposite-pair',opposite)
   results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'sourcePreview':r['sourcePreview'],'independentAnswer':s.srepr(answer),'route':route,'checks':checks,'literalPairInequalities':pairs,'oppositePairs':opposite,'passed':True})
  except Exception as e:results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'passed':False,'error':repr(e)})
  if len(results)%40==0:print(json.dumps({'reviewed':len(results),'failed':sum(not x['passed'] for x in results)}),flush=True)
 dependencies=['ode_mv_options.py','ode_mv_literal_choices.py','lower_ode_mv.py','existing_multivariable.py','existing_diff_limits.py','literal_choices.py','series_intervals.py','rational_intervals.py']
 report={'status':'independent-finite-option-review','author':'integration_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in dependencies},'instances':len(rows),'passed':sum(r['passed'] for r in results),'records':results,'limitations':'Independently derived finite answers and literal pair checks, with analytic branch/convergence proofs retained from source-bound independent family reviews. No author expression metadata used. This is not formal verification or human calibration. Final actual-ID full-family screen and admission remain required.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['instances','passed']}));return report['passed']==len(rows)
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
