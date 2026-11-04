"""Independent literal-statement oracle for184 differentiation/limits additions.
No author constructors or answerExpression are imported or used to derive results.
"""
from pathlib import Path
import json,re,hashlib,sys,itertools
import sympy as s
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent));from literal_numeric_extended import parse as base_parse
x,t,h=s.symbols('x t h',positive=True)
def parse(q):
 if q in [r'\infty',r'-\infty']:return s.oo if q==r'\infty' else -s.oo
 if 'i' in q and r'\left(1 + i\right)' in q:
  return (1+s.I)**int(re.search(r'\^\{(\d+)\}',q)[1])
 return base_parse(q)
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def derive(r):
 f=r['familyId'];z=r['statement'].replace(r'\operatorname{atan}',r'\arctan');checks=[];condition='All differentiations and finite arithmetic take place at the explicitly stated real point; the displayed denominators are nonzero.';m=None
 def get(pattern,group=1):
  q=re.search(pattern,z);assert q,(f,pattern,z);return q[group]
 def integer(pattern):return int(get(pattern))
 def ck(name,a,b):
  assert s.simplify(s.expand_complex(a-b))==0,(name,a,b);checks.append({'description':name,'left':s.srepr(a),'right':s.srepr(b),'exact':True})
 if f.startswith('q2-repair-'):
  if f.endswith('accumulation-derivative'):
   p=integer(r't\^\{(\d+)\}');a=integer(r'\\int_0\^\{(\d+)x\^2\}');A=2*a*(a**p+1);expr=(a*x*x)**p+1;ck('FTC derivative at the concrete upper endpoint', (expr*2*a*x).subs(x,1),A);route='FTC plus chain derivative of the moving quadratic endpoint.'
  elif f.endswith('rational-sequence-shift'):
   q=re.search(r'\\frac\{(\d+)n\+1\}\{(\d+)n\+2\}\\right\)\^\{(\d+)\}',z);assert q,z;a,b,p=map(int,q.groups());A=s.Rational(a,b)**p;route='Divide numerator and denominator by n and then use continuity of a fixed integer power.'
  elif f.endswith('factorial-ratio-fixed-shift'):
   k=integer(r'\(n\+(\d+)\)!');c=integer(r'\((\d+)n\)\^');assert integer(r'\^\{(\d+)\}')==k;A=s.Rational(1,c)**k;route='Cancel the factorials into k factors; divide each factor by cn and take the finite product.'
  elif f.endswith('root-test-scale'):
   q=re.search(r'\\left\((\d+)\^n n\^\{(-?\d+)\}',z);assert q,z;a,p=map(int,q.groups());A=s.Integer(a);route='Take logarithms; the fixed power contributes p ln(n)/n, which tends to zero.'
  elif f.endswith('two-sided-square-root'):
   q=re.search(r'\\sqrt\{(\d+)x\^2\+(\d+)x\^4\}\}\{(\d+)x\}',z);assert q,z;a,b,c=map(int,q.groups());sign=1 if r'0^{+}' in z else -1;assert r'0^{+}' in z or r'0^{-}' in z;A=sign*s.sqrt(a)/c;route='Factor x² under the square root, retain |x|, and use the stated one-sided sign.';condition='The radicand is nonnegative near zero because both displayed coefficients are positive. The one-sided direction fixes |x|/x.'
  else:raise ValueError(f)
 elif '-differentiation-' in f:
  if f.endswith('chain-data'):
   a=integer(r'g\\prime\(0\)=(\d+)');b=integer(r'f\\prime\(1\)=(\d+)');A=s.Integer(a*b);route='Chain rule at the explicitly supplied inner image.'
  elif f.endswith('derivative-definition'):
   m=integer(r'\(1\+h\)\^\{(\d+)\}');A=s.Integer(m);ck('Derivative from polynomial difference quotient',s.limit(((1+h)**m-1)/h,h,0),A);route='Recognize the derivative of the integer power at1.'
  elif f.endswith('implicit-circle'):
   m=integer(r'\(1,(\d+)\)');A=-s.Rational(1,m);route='Implicit differentiation gives y′=−x/y on the nonzero-height branch.'
  elif f.endswith('inverse-slope'):
   m=integer(r'f\\prime\(2\)=(\d+)');A=s.Rational(1,m);route='Differentiate the local inverse identity; the supplied derivative is nonzero.'
  elif f.endswith('linearization'):
   v=integer(r'x=(\d+)');m=int(s.sqrt(v));assert m*m==v;A=m+s.Rational(1,2*m);route='Use the square-root derivative1/(2m) at m² and the unit input increment.'
  elif f.endswith('matching-piecewise-slopes'):
   m=integer(r'cases\}(\d+)x');A=s.Integer(m);route='Continuity already holds at zero; match the two one-sided first derivatives.'
  elif f.endswith('minimum-from-sign'):
   m=integer(r'\(x-(\d+)\)\.');A=s.Integer(1 if r'=-(x+1)' in z else m);assert m>1;route='Track the derivative sign at the two positive simple roots; only the larger root changes from negative to positive.'
  elif f.endswith('parametric-slope'):
   m=integer(r't=(\d+)');A=s.Rational(3*m,2);ck('Parametric first derivative', (s.diff(t**3,t)/s.diff(t*t,t)).subs(t,m),A);route='Divide dy/dt by the nonzero dx/dt.'
  elif f.endswith('product-data'):
   a=integer(r'f\(0\)=(\d+)');b=integer(r'f\\prime\(0\)=(\d+)');c=integer(r'g\(0\)=(\d+)');d=integer(r'g\\prime\(0\)=(\d+)');A=s.Integer(b*c+a*d);route='Use both terms in the product rule with the supplied values.'
  elif f.endswith('related-area-rate'):
   m=integer(r'r=(\d+)');rate=integer(r'\{dr\}\{dt\}=(\d+)');A=2*s.pi*m*rate;route='Differentiate the area with respect to radius and multiply by the given radial velocity.'
  elif f.endswith('tangent-intercept'):
   m=integer(r'x\^\{(\d+)\}');A=s.Integer(1-m);route='The tangent has slope m through(1,1), so its vertical intercept is1−m.'
  elif f.endswith('complex-exponential-derivative'):
   m=integer(r'\{d\^\{(\d+)\}\}');A=s.re(s.expand((1+s.I)**m));ck('Separate direct real derivative',s.diff(s.exp(x)*s.cos(x),x,m).subs(x,0),A);route='Take the real part of(1+i)^m, or use the two-component derivative recurrence.'
  elif f.endswith('curvature-parametric'):
   m=integer(r'\\kappa\((\d+)\)');A=2/(1+4*s.Integer(m)**2)**s.Rational(3,2);route='Evaluate |x′y″−y′x″|/(x′²+y′²)^(3/2) for the regular plane curve.'
  elif f.endswith('high-order-rational'):
   m=integer(r'\{d\^\{(\d+)\}\}');A=s.factorial(m)*s.fibonacci(m+1);ck('Independent series coefficient',s.diff(1/(1-x-x*x),x,m).subs(x,0),A);route='The coefficients of1/(1−x−x²) satisfy the Fibonacci recurrence; multiply the required coefficient by m!.'
  elif f.endswith('implicit-inverse-exponential'):
   m=integer(r'y\((\d+) e');A=-(m+2)*s.exp(-2*m)/(m+1)**3;F=t*s.exp(t);ck('Second derivative of inverse',(-s.diff(F,t,2)/s.diff(F,t)**3).subs(t,m),A);route='Twice differentiate the local inverse of t exp(t), using its nonzero first derivative.'
  elif f.endswith('implicit-second'):
   m=integer(r'\(1,(\d+)\)');v=-s.Rational(m+2,2*m+1);A=-s.Rational(2)*(1+v+v*v)/(2*m+1);route='Differentiate the implicit quadratic twice; substitute the first slope before solving for the second derivative.'
  elif f.endswith('leibniz-high-order'):
   m=integer(r'\{d\^\{(\d+)\}\}');A=s.Integer(m*(m-1));ck('Leibniz coefficient at zero',s.diff(x*x*s.exp(x),x,m).subs(x,0),A);route='Only the term differentiating x² twice survives at zero.'
  elif f.endswith('log-power-second'):
   m=integer(r'x\^\{(\d+) x\}');A=s.Integer(m*m+m);ck('Logarithmic second derivative',s.diff(s.exp(m*x*s.log(x)),x,2).subs(x,1),A);route='Write the positive-base power as an exponential and differentiate its logarithm twice.'
  elif f.endswith('log-product'):
   denominators=[int(q) for q in re.findall(r'\\frac\{x\}\{(\d+)\}',z)];assert sorted(denominators)==list(range(2,max(denominators)+1));m=max(denominators);A=s.harmonic(m)**2-s.harmonic(m,2);poly=s.prod(1+x/j for j in range(1,m+1));ck('Finite product coefficient',s.expand(poly).coeff(x,2)*2,A);route='Select two distinct linear factors; the ordered reciprocal-pair sum is H_m²−H_m^(2).'
  elif f.endswith('moving-endpoint-parameter-second'):
   m=integer(r'x\^\{(\d+)\}');F=(s.exp(x**(m+1))-s.exp(x*x))/x;A=s.diff(F,x,2).subs(x,1);route='Integrate the defining exponential explicitly for x>0, then differentiate that expression twice at1.'
  elif f.endswith('multiplicity-shortcut'):
   m=integer(r'\{d\^\{(\d+)\}\}');A=s.factorial(m)*s.E;ck('Coefficient about the zero of order m',s.diff((x-1)**m*s.exp(x),x,m).subs(x,1),A);route='All Leibniz terms except the one removing the full zero of order m vanish at1.'
  elif f.endswith('nested-power-third'):
   m=integer(r'e\^\{(\d+) x\^\{2\}');A=s.Integer(1+6*m);ck('Cubic coefficient of the exponential',s.diff(s.exp(m*x*x+x),x,3).subs(x,0),A);route='Extract the cubic coefficient from the product exp(x)exp(mx²).'
  elif f.endswith('trigonometric-power-coefficient'):
   m=integer(r'\\sin\^\{(-?\d+)\}');order=integer(r'\{d\^\{(\d+)\}\}');assert order==m+2;A=-s.Rational(m,6)*s.factorial(m+2);route='In(sin x)^m=x^m(1−mx²/6+O(x⁴)), select the requested coefficient and multiply by its factorial.'
  elif f.endswith('implicit-product'):
   m=integer(r'\(1,(\d+)\)');A=-s.Rational(m,1+2*m);route='Differentiate xy+y² with respect to x and isolate the slope.'
  elif f.endswith('inverse-second'):
   m=integer(r'f\\prime\(0\)=(\d+)');b=integer(r'f\\prime\\prime\(0\)=(\d+)');A=-s.Rational(b,m**3);route='Differentiate the local inverse identity twice.'
  elif f.endswith('inverse-tangent-composition'):
   m=integer(r'\\arctan\{\\left\(x\^\{(\d+)\}');A=s.Rational(m,2);ck('Arctangent chain derivative',s.diff(s.atan(x**m),x).subs(x,1),A);route='Apply the chain rule to the arctangent and evaluate at1.'
  elif f.endswith('logarithmic-power'):
   m=integer(r'x\^\{(\d+) x\}');A=s.Integer(m);ck('Logarithmic power derivative',s.diff(s.exp(m*x*s.log(x)),x).subs(x,1),A);route='Differentiate x raised to a variable exponent using its logarithm.'
  elif f.endswith('moving-integral-endpoints'):
   m=integer(r'\\int_x\^\{(\d+)x\}');A=s.Integer(m-1);ck('Endpoint differentiation',s.diff(s.exp(m*x)-s.exp(x),x).subs(x,0),A);route='Apply the fundamental theorem at both moving endpoints.'
  elif f.endswith('nested-exponential'):
   m=integer(r'\\sin\{\\left\((\d+) x');A=s.Integer(m);ck('Nested chain derivative',s.diff(s.exp(s.sin(m*x)),x).subs(x,0),A);route='Use the two chain-rule factors at zero.'
  elif f.endswith('normal-line'):
   m=integer(r'x\^\{(\d+)\}');A=-s.Rational(1,m);route='Find the nonzero tangent slope, then take its negative reciprocal.'
  elif f.endswith('optimization-product'):
   m=integer(r'x\\le (\d+)');A=s.Rational(m,3);g=x*(m-x)**2;ck('Interior critical point',s.diff(g,x).subs(x,A),0);assert g.subs(x,A)>0;route='Differentiate, compare the one interior critical point with the zero endpoint values.'
  elif f.endswith('parametric-second'):
   k=integer(r'y=t\^\{(\d+)\}');A=s.Rational(k*(k-2),4);ck('Second parametric derivative',(s.diff(s.diff(t**k,t)/s.diff(t*t,t),t)/s.diff(t*t,t)).subs(t,1),A);route='Divide by dx/dt after each differentiation, not just the first.'
  elif f.endswith('piecewise-second-match'):
   m=integer(r'e\^\{(\d+)x\}');A=s.Rational(m*m,2);route='Value and first derivative already match; match the left second derivative m² with2a.'
  elif f.endswith('product-exp'):
   m=integer(r'\\left\(x\^\{(\d+)\}');A=(m+1)*s.E;ck('Product derivative',s.diff(x**m*s.exp(x),x).subs(x,1),A);route='Use both product-rule terms at1.'
  elif f.endswith('quotient-log'):
   m=integer(r'x \+ (\d+)');A=s.Rational(1,m+1);ck('Logarithmic quotient derivative',s.diff(s.log(x)/(x+m),x).subs(x,1),A);route='Differentiate the quotient; the undifferentiated logarithm vanishes at1.'
  else:raise ValueError(f)
 else:
  condition='The limit uses exactly the displayed one-sided or integer-sequence domain. Any logarithm or real power is defined on the stated positive neighborhood.'
  if f.endswith('exponential-standard') or f.endswith('exponential-cancellation') or f.endswith('exponential-variable-power'):
   m=integer(r'e\^\{(\d+) x\}') if 'variable-power' not in f else integer(r'\\left\((\d+) x \+ 1');A=s.Integer(m) if f.endswith('exponential-standard') else s.Rational(m*m,2) if f.endswith('exponential-cancellation') else s.exp(m);route='Use the exponential Taylor expansion, or the logarithm for the variable power.'
  elif f.endswith('floor-at-infinity'):
   m=integer(r'\\lfloor (\d+)x');A=s.Integer(m);route='Squeeze the floor between mx−1 and mx, then divide by positive x.'
  elif f.endswith('geometric-sequence'):
   m=integer(r'\\left\[(\d+)\+');A=s.Integer(m);route='The displayed ratio has magnitude strictly below1, so its integer powers vanish.'
  elif f.endswith('logarithm-standard'):
   m=integer(r'\\left\((\d+) x \+ 1');A=s.Integer(m);route='Apply ln(1+u)/u→1 with the displayed linear substitution.'
  elif f.endswith('one-sided-absolute'):
   m=integer(r'- (\d+) x');A=s.Integer(1-m);route='On the explicitly positive side, |x|=x exactly.'
  elif f.endswith('oscillatory-squeeze'):
   m=integer(r'\\left\((\d+)\+');A=s.Integer(m);route='Bound the oscillatory term by its positive vanishing power.'
  elif f.endswith('piecewise-continuity'):
   m=integer(r'cases\}(\d+)x');A=s.Integer(m);route='Match the left value m+1 to the right value a+1.'
  elif f.endswith('radical-rationalization'):
   m=integer(r'\} - (\d+)\}');A=s.Rational(1,2*m);route='Multiply by the conjugate and evaluate the resulting positive denominator.'
  elif f.endswith('rational-infinity'):
   m=integer(r'\\frac\{(\d+) x\^');A=s.Integer(m);route='Divide by the highest common power of x.'
  elif f.endswith('removable-power'):
   m=integer(r'x\^\{(\d+)\}');A=s.Integer(m);route='Factor the power difference into a finite geometric sum.'
  elif f.endswith('trigonometric-ratio'):
   m=integer(r'\\sin\{\\left\((\d+) x');A=s.Integer(m);route='Use the standard sine ratio at zero twice.'
  elif f.endswith('Gamma-finite-shift-correction'):
   ns=[int(q) for q in re.findall(r'x \+ (\d+)',z)];assert sorted(ns)==list(range(1,max(ns)+1));A=-sum(ns);route='Divide each finite factor by x; the first reciprocal-product coefficient is minus the sum of its shifts.'
  elif f.endswith('Lp-maximum-limit'):
   m=integer(r'x\^\{(\d+)\}');A=s.Rational(m,m+1)**m/(m+1);route='The positive continuous function has maximum at m/(m+1); upper and neighborhood lower bounds prove convergence of its Lp norm to that maximum.'
  elif f.endswith('Riemann-sum'):
   m=integer(r'n\+(\d+)j');A=s.log(m+1)/m;route='Recognize a Riemann sum for1/(1+mx) on[0,1].'
  elif f.endswith('Stolz-power-sum'):
   m=integer(r'j\^\{(\d+)\}');A=s.Rational(1,m+1);route='Normalize as the Riemann sum of x^m, or apply Stolz to successive differences.'
  elif f.endswith('boundary-moment'):
   m=integer(r'\(1\+x\)\^\{(\d+)\}');A=s.Integer(2)**m;route='Expand the fixed binomial polynomial; each term n/(n+j+1) tends to1 in this finite sum.'
  elif f.endswith('log-exponential-second-scale'):
   m=integer(r'\\left\((\d+) x \+ 1');A=-s.Rational(m*m,2);route='Expand the logarithm through the quadratic term, then exponentiate the remaining first-order correction.'
  elif f.endswith('log-phase-average-limsup'):
   m=integer(r'\\cos\((\d+)\\ln k\)');A=1/s.sqrt(1+m*m);route='Compare the sum with the integral of t^(im), whose normalized leading term is n^(im)/(1+im). The error is O(log n/n), and integer n approach every desired log phase.'
  elif f.endswith('log-sum-integral'):
   m=integer(r'\\frac\{(\d+)j\}\{n\}');A=s.exp(s.Rational(m+1,m)*s.log(m+1)-1);route='Take logarithms and evaluate the Riemann integral of ln(1+mx), then exponentiate.'
  elif f.endswith('oscillatory-regularity-threshold'):
   m=integer(r'1/x\^\{(\d+)\}');A=s.Integer(m+1);route='The differentiated oscillatory term has magnitude x^(alpha−m−1); its exponent must be strictly positive, with phase subsequences ruling out equality and smaller exponents.'
  elif f.endswith('recurrence-limit'):
   a=integer(r'\\sqrt\{(\d+)\+a_n\}');A=(1+s.sqrt(1+4*a))/2;route='Inductively bound the monotone sequence by the positive fixed point, then pass to its continuous recurrence.'
  elif f.endswith('supremum-pointwise-mismatch'):
   m=integer(r'x\^\{(\d+)n\}');A=(m-1)*s.Integer(m)**(-s.Rational(m,m-1));route='The substitution y=x^n is onto[0,1] for every n; maximize y−y^m exactly.'
  elif f.endswith('trig-power-limit'):
   m=integer(r'\\sin\{\\left\((\d+) x');A=s.exp(-s.Rational(m*m-1,6));route='Use the cubic sine expansion, then the logarithm of the variable power.'
  elif f.endswith('floor-integer-approach'):
   m=integer(r'\\frac\{(\d+) ');below=r'\sin' in z.split(r'\frac{',1)[1].split('}{',1)[0];A=s.Integer(m-1 if below else m);route='Use sin(x)<x for positive small x: the displayed quotient approaches the integer from below or above exactly as its numerator and denominator specify.'
  elif f.endswith('implicit-inverse-increment'):
   m=integer(r't\^3\+(\d+)t');A=s.Rational(1,m+3);route='The real cubic is strictly increasing with nonzero derivative at1; apply the inverse derivative rule.'
  elif f.endswith('infinity-root-difference'):
   m=integer(r'\+ (\d+) x');A=s.Rational(m,2);route='Rationalize and divide the denominator by positive x.'
  elif f.endswith('log-power-decay'):
   m=integer(r'\^\{(\d+)\}');A=s.Integer(0) if r'\frac' in z else s.oo;route='Set t=ln x. Dividing a fixed power by exp(t) gives zero; multiplying by exp(t) gives positive infinity, as displayed.'
  elif f.endswith('nested-log-ratio'):
   m=integer(r'\\sin\{\\left\((\d+) x');A=s.Integer(m);route='Multiply the standard log and sine ratios with their exact inner scaling.'
  elif f.endswith('second-order-trig'):
   m=integer(r'\\cos\{\\left\((\d+) x');A=s.Rational(m*m,2);route='Use the quadratic cosine expansion, or the half-angle sine identity.'
  elif f.endswith('small-power-log'):
   m=integer(r'\\sqrt\[(\d+)\]');A=-s.oo if r'\frac' in z else s.Integer(0);route='Set t=−ln x. The displayed product gives−t exp(−t/m)→0; the displayed quotient gives−t exp(t/m)→−infinity.'
  else:raise ValueError(f)
 return {'answer':s.simplify(A),'checks':checks,'route':route,'conditions':condition}
if __name__=='__main__':
 source=Path(sys.argv[1]) if len(sys.argv)>1 else P.parents[1]/'differentiation-limits/lower-v2/candidates.json';allrows=json.loads(source.read_text());rows=[r for r in allrows if r['familyId'].startswith('q2-')];evidence=[];fail=[]
 for r in rows:
  try:
   d=derive(r);vals=[parse(c['math']) for c in r['choices']];idx=next(i for i,c in enumerate(r['choices']) if c['choiceId']==r['answerChoiceId']);assert vals[idx]==d['answer'] or s.simplify(s.expand_complex(vals[idx]-d['answer']))==0,(vals[idx],d['answer'])
   for a,b in itertools.combinations(vals,2):assert s.simplify(s.expand_complex(a-b)).equals(0)is False
   evidence.append({'familyId':r['familyId'],'instance':r['parameters']['instance'],'rawHash':H(r),'derivedAnswer':s.srepr(d['answer']),'literalAnswerMatched':True,'allSixLiteralPairsDistinct':True,'route':d['route'],'conditions':d['conditions'],'independentChecks':d['checks'],'difficulty':r['difficulty']})
  except Exception as e:fail.append({'familyId':r['familyId'],'instance':r['parameters']['instance'],'rawHash':H(r),'error':repr(e)})
 report={'sourcePath':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reviewerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':evidence,'failures':fail,'counts':{'attempted':len(rows),'passed':len(evidence),'failed':len(fail)},'scope':'Separate literal-statement answer routes and all literal choice pairs; no author constructors or answerExpression used. Proposed levels were visible, so this is statement/options-first rather than fully level-blind. Domain/proof arguments are explicit and separate from exact symbolic checks.'}
 (Path(sys.argv[2]) if len(sys.argv)>2 else P/'new-finite-review-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts']);print(json.dumps(fail,indent=2)[:10000])
