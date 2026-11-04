"""Independent mathematics and identity checks for unchanged-task old revisions."""
from pathlib import Path
import json,re,sys,hashlib,itertools
import sympy as s
from verify_new import derive,H,parse as narrow_parse
P=Path(__file__).resolve().parent;SOURCE=Path(sys.argv[1]).parent if len(sys.argv)>1 else P.parents[1]/'differentiation-limits/lower-v2';x=s.symbols('x',real=True)
def parse(q):
 if r'\operatorname{erf}' in q:
  # Closed finite grammar: rational combination of erf at literal real arguments.
  z=q.replace(r'\operatorname{erf}', ' ERF ')
  import literal_numeric_extended as parser
  source=Path(parser.__file__).read_text().replace("'atanh'}","'atanh','ERF'}").replace("'atanh':s.atanh}","'atanh':s.atanh,'ERF':s.erf}")
  ns={};exec(compile(source,'reviewer-erf-grammar','exec'),ns);return ns['parse'](z)
 return narrow_parse(q)
def advanced(r):
 f=r['familyId'].split('-olympiad-',1)[1];z=r['statement'];checks=[]
 def integer(pattern):
  h=re.search(pattern,z);assert h,(f,pattern,z);return int(h[1])
 if f=='Gaussian-moment-derivative':
  m=integer(r'F\^\{\((\d+)\)\}');A=(-1)**(m-1)*s.factorial(m-1)*s.factorial(m);route='The mth right parameter derivative of ln(1+at) at zero is(−1)^(m−1)(m−1)! t^m. The exponential moment is m!, with polynomial-exponential domination.'
 elif f=='cyclic-determinant-second-derivative':
  n=integer(r'1\\le i,j\\le (\d+)');M=s.Matrix(n,n,lambda i,j:2+x if i==j else -1 if(i-j)%n in [1,n-1] else 0);poly=s.expand(M.det());A=2*poly.coeff(x,2);route='Compute the finite cycle determinant independently as a polynomial and take twice its quadratic coefficient.';checks=[{'description':'Independent finite determinant polynomial','polynomial':str(poly)}]
 elif f=='envelope-derivative':
  m=integer(r'\\(?:log|ln)\{\\left\((\d+)');A=s.Integer(m);route='The minimizer is t=ln(m) at the displayed input. Strict convexity gives uniqueness; the envelope derivative is2(x−t)=m.'
 elif f=='global-inverse-curvature':
  m=integer(r'f\(x\)\+(\d+)');A=s.Rational(4,27*m);route='The defining increasing positive-coordinate map has inverse second derivative m f/(f+m)^3. Maximize this rational function over positive f; its unique maximum occurs at f=m/2.'
 elif f=='implicit-series-inversion':
  m=integer(r'y\^\{\((\d+)\)\}');A=s.factorial(m)*s.catalan(m);route='Solve the quadratic branch vanishing at zero and read its Catalan coefficient, then multiply by the derivative factorial.'
 elif f=='exponential-partition-coefficient':
  m=integer(r'\{d\^\{(\d+)\}\}');poly=s.series(s.exp(x/(1-x)),x,0,m+1).removeO();A=s.factorial(m)*poly.coeff(x,m);route='Expand the displayed exponential to the finite requested order; no combinatorial label is used as the oracle.'
 elif f=='interpolation-derivative':
  m=integer(r'j=0,\\ldots,(\d+)');poly=s.interpolate([(j,s.Rational(1,j+1)) for j in range(m+1)],x);A=s.diff(poly,x).subs(x,0);route='Interpolate the literal rational node data independently, then differentiate at zero. The rational-remainder identity explains the conceptual shortcut.'
 elif f=='iterated-Mobius':
  m=integer(r'\\circ (\d+)');M=s.Matrix([[1,1],[1,2]])**m;A=1/M[1,1]**2;route='Compose the two-by-two fractional-linear matrix; determinant1 gives the derivative at zero.'
 elif f=='newton-iteration-jet':
  m=integer(r'x\^\{(\d+)\}');A=s.factorial(8)*s.Rational(m-1,2)**7;N=x-(x**m-1)/(m*x**(m-1));c=s.diff(N,x,2).subs(x,1)/2;assert c==s.Rational(m-1,2);route='The Newton map has local error c h² with c=(m−1)/2. Three compositions give leading error c^7 h^8, so multiply by8!.'
 elif f=='noncommuting-operator':A=s.Integer(1);route='The supplied function exp(−x²+x) is an eigenfunction of D+2x with eigenvalue1; all iterates have value1 at zero.'
 elif f=='root-of-unity-filter':
  order=integer(r'F\^\{\((\d+)\)\}');A=s.Integer(3 if order%3==0 else 0);route='The three exponential frequencies are the cube roots of unity. Their powers sum to3 when the order is divisible by3 and to zero otherwise.'
 elif f=='sharp-endpoint-derivative':
  m=integer(r'at most\s*\}(\d+)');A=s.Integer(m*m);assert s.diff(s.chebyshevt(m,x),x).subs(x,1)==A;route='The pinned independent signed-interpolation-weight proof gives the endpoint Markov bound m²; the Chebyshev polynomial derivative independently verifies attainment.'
 elif f=='Laplace-degenerate-endpoint':
  m=integer(r'e\^\{-nx\^\{(\d+)\}');A=s.gamma(s.Rational(1,m))/m;route='Substitute u=n x^m. The increasing transformed cutoff gives the displayed positive Gamma integral divided by m.'
 elif f=='binomial-moving-threshold':
  h=re.search(r'n/2\+(.*?)\\sqrt n',z);assert h,z;a=parse(h[1]);A=(1+s.erf(s.sqrt(2)*a))/2;route='Use a fair binomial variable with mean n/2 and standard deviation sqrt(n)/2. The literal threshold standardizes to2a; floor errors vanish and the normal CDF gives the stated erf value.'
 elif f=='central-binomial-shift':
  m=integer(r'\\binom\{2n\}\{n\+(\d+)\}');A=m*m/s.sqrt(s.pi);route='Expand the finite shifted-to-central binomial ratio through order1/n, whose deficit coefficient is m², then use the central-binomial square-root asymptotic.'
 elif f=='nonlinear-recursion-rate':
  m=integer(r'a_n\^\{(\d+)\}');A=s.Integer(m)**(-s.Rational(1,m));route='Monotonicity forces the positive recurrence to zero. Its reciprocal mth power has increments tending to m; Cesaro averaging gives the normalized limit.'
 elif f=='product-Euler-correction':
  m=integer(r'\\frac\{(\d+)j\}\{n\^2\}');A=s.Rational(m,2)-s.Rational(m*m,6);route='Expand ln(1+u) to second order uniformly for0≤u≤m/n. Exact sums of j and j² give the coefficient; the summed cubic remainder vanishes after multiplication by n.'
 else:raise ValueError(f)
 return {'answer':s.simplify(A),'route':route,'conditions':'The finite source task and its hypotheses are unchanged. The route states any nonalgebraic theorem or interchange needed; existing pinned independent proof evidence is retained separately.','checks':checks}
if __name__=='__main__':
 allrows=json.loads((SOURCE/'candidates.json').read_text());rows=[r for r in allrows if 'problemId'in r];originals={r['problemId']:r for r in json.loads((SOURCE/'original-records.json').read_text())};evidence=[];fail=[]
 for r in rows:
  try:
   old=originals[r['problemId']];assert r['semanticHash']==old['semanticHash'];assert r['problemRevision']==old['problemRevision']+1;d=advanced(r) if '-olympiad-'in r['familyId'] else derive(r)
   vals=[parse(c['math']) for c in r['choices']];correct=vals[next(i for i,c in enumerate(r['choices']) if c['choiceId']==r['answerChoiceId'])];oldanswer=parse(next(c['math'] for c in old['choices'] if c['choiceId']==old['answerChoiceId']))
   assert correct==d['answer'] or s.simplify(s.expand_complex(correct-d['answer']))==0,(correct,d['answer'])
   assert oldanswer==correct or s.simplify(s.expand_complex(oldanswer-correct))==0
   for a,b in itertools.combinations(vals,2):assert s.simplify(s.expand_complex(a-b)).equals(0)is False
   evidence.append({'problemId':r['problemId'],'rawHash':H(r),'familyId':r['familyId'],'sourceContentHash':old['contentHash'],'sourceSemanticHash':old['semanticHash'],'semanticAndRevisionIdentityPreserved':True,'independentAnswer':s.srepr(d['answer']),'currentAndOriginalAnswerMatch':True,'sixLiteralPairsDistinct':True,'route':d['route'],'conditions':d['conditions'],'checks':d['checks'],'difficulty':r['difficulty']})
  except Exception as e:fail.append({'problemId':r['problemId'],'familyId':r['familyId'],'rawHash':H(r),'error':repr(e)})
 report={'sourcePath':str(SOURCE/'candidates.json'),'sourceSha256':hashlib.sha256((SOURCE/'candidates.json').read_bytes()).hexdigest(),'originalsSha256':hashlib.sha256((SOURCE/'original-records.json').read_bytes()).hexdigest(),'reviewerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':evidence,'failures':fail,'counts':{'attempted':len(rows),'passed':len(evidence),'failed':len(fail)},'scope':'Independent literal answer routes, baseline answer/semantic identity, and new literal option inequalities. No author constructors imported. Nonalgebraic arguments are stated; this is not formal or human certification.'}
 (Path(sys.argv[2]) if len(sys.argv)>2 else P/'existing-finite-review-v2.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts']);print(json.dumps(fail,indent=2)[:12000])
