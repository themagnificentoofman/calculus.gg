"""Independent literal-answer and pair checks for repaired integral options.
No author constructor or author's expression metadata is imported.
"""
from pathlib import Path
import hashlib,itertools,json,re,sys
import sympy as s
from literal_choices import parse,same,distinct
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def solve(r):
 f=r['familyId'];p=r['parameters'];m=s.Integer(p.get('m',1));x=s.symbols('x',positive=True)
 if f=='io3-fresnel':
  a=s.Rational(p['a']);assert a>0;return s.sqrt(s.pi)/(2*s.sqrt(2*a)),'Scale the independently reviewed oscillatory Gaussian integral. Uniform integration-by-parts tail control identifies the ordinary improper limit with its Abel-regularized value.'
 if f=='io3-reciprocal-quartic':
  a=s.Integer(p['quadraticCoefficient']);assert a+2>0;return s.pi/(2*s.sqrt(a+2)),'Average the reciprocal substitution with the original integral; u=x−1/x reduces it to half an arctangent integral over the real line.'
 if f=='io3-rodrigues-moment':
  n=s.Integer(p['derivativeOrder']);power=s.Integer(p['power']);assert n>0 and power>=n
  assert 'x^{'+str(power)+'}' in r['statement'] and r'\mathrm{d}^{'+str(n)+'}' in r['statement']
  return s.integrate(s.expand(x**power*s.diff((x*x-1)**n,x,n)),(x,-1,1)),'Differentiate the literal finite polynomial and integrate its exact monomial coefficients; this independently checks the Rodrigues/endpoint derivation.'
 if f=='io3-scaled-frullani':
  a,b=s.Integer(p['a']),s.Integer(p['b']);q=s.Integer(p['power']);assert 0<a<b and q>0
  return s.log(b/a)/q,'The positive parameter rectangle (e^(−a u)−e^(−b u))/u=integral_a^b e^(−t u)dt permits Tonelli; u=x^q supplies the factor1/q.'
 if f.endswith('accumulation-from-derivative'):
  a,b=map(s.Integer,[p['leftValue'],p['rightValue']]);assert 'F(1)='+str(a)in r['statement'] and 'F(3)='+str(b)in r['statement'];return b-a,'Apply FTC to the explicitly stated endpoint data.'
 if f.endswith('area-between-curves'):return s.integrate(m*x-x*x,(x,0,m)),'Integrate the displayed nonnegative quadratic between its two zeros.'
 if f.endswith('Frullani-rectangle'):return s.log(m),'Tonelli on the positive exponential parameter rectangle gives integral_1^m dt/t.'
 if f.endswith('improper-rational-beta'):return 1/(m+1),'The increasing u=x/(1+x) substitution gives the monomial u^m on(0,1), with both improper endpoints convergent.'
 if f.endswith('logarithmic-moment'):return 2/(m+1)**3,'The substitution t=−ln(x) gives a quadratic exponential moment; two integrations by parts with vanishing boundary terms give2/(m+1)^3.'
 if f.endswith('improper-exponential'):return 1/m,'Evaluate the exponential primitive at zero and infinity; positive decay ensures convergence.'
 if f.endswith('inverse-tangent'):return s.pi/(4*m),'Scale x=m u; the upper limit becomes1 and the arctangent angle is pi/4.'
 if f.endswith('moving-boundary-area'):return s.integrate(s.sqrt(x)-x/m,(x,0,m*m)),'Integrate both explicit powers over the positive intersection interval[0,m²].'
 if f.endswith('nested-log'):return s.log(m),'Set u=ln(x); the endpoints are1 and m, so integrate1/u.'
 if f.endswith('rational-power-substitution'):return (1-s.Integer(2)**(1-m))/(m-1),'Set u=1+x²; integrate u^(−m) from1 to2 with the exact Jacobian.'
 if f.endswith('secant-square-substitution')or f.endswith('trig-odd-power'):return 1/(m+1),'A tangent or cosine substitution gives the same oriented monomial integral from0 to1.'
 raise ValueError('Unreviewed family '+f)
def main(source,out):
 data=Path(source).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  answer,route=solve(r);values=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(values) if same(v,answer)]
  assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],r['familyId']
  assert all(distinct(a,b) for a,b in itertools.combinations(values,2))
  pairs=[(i,j) for i,j in itertools.combinations(range(4),2) if same(values[i],-values[j])];assert len(pairs)==2
  assert sum(v.is_positive is True for v in values)==2 and sum(v.is_negative is True for v in values)==2
  results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'independentAnswer':s.srepr(answer),'sixLiteralPairsDistinct':True,'oppositePairs':pairs,'positiveCandidates':2,'negativeCandidates':2,'route':route,'passed':True})
 report={'status':'independent-finite-mathematics-passed','author':'integration_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'reviewCodeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'literalParserSha256':hashlib.sha256(Path(__file__).with_name('literal_choices.py').read_bytes()).hexdigest(),'records':results,'instances':len(results),'pairInequalities':6*len(results),'limitations':'Mathematical arguments and exact finite symbolic checks, not human certification or a formal proof assistant. Final combined stable-ID clue screen and source/presentation/lineage bindings remain admission gates.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'instances':len(results),'literalPairInequalities':6*len(results),'passed':True}))
if __name__=='__main__':main(*sys.argv[1:])
