"""Independent80-menu review, including branch-aware arctangent inequalities."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,re,sys
import sympy as s
from ode_mv_literal_choices import parse as simple,same
from rational_intervals import PI,add,mul,power
from limits_intervals import enclose as ordinary
from series_intervals import rounded
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def parse(t):return simple(t.replace(r'\operatorname{atan}',r'\arctan').replace(r'\log',r'\ln'))
def atan(q):
 q=Q(int(q.p),int(q.q))
 if q<0:return mul((Q(-1),)*2,atan(s.Rational(-q.numerator,q.denominator)))
 if q==1:return mul((Q(1,4),)*2,PI)
 if q>1:return add(mul((Q(1,2),)*2,PI),mul((Q(-1),)*2,atan(s.Rational(q.denominator,q.numerator))))
 assert 0<=q<Q(1,2),'Unreviewed arctangent range'
 total=sum(((-1)**k*q**(2*k+1)/Q(2*k+1)for k in range(65)),Q(0));next_term=-q**131/Q(131)
 return min(total,total+next_term),max(total,total+next_term)
def bounds(v):
 if v.func==s.atan:assert v.args[0].is_Rational;return atan(v.args[0])
 if v.is_Add:
  a=(Q(0),)*2
  for x in v.args:a=rounded(add(a,bounds(x)))
  return a
 if v.is_Mul:
  a=(Q(1),)*2
  for x in v.args:a=rounded(mul(a,bounds(x)))
  return a
 if v.is_Pow and v.exp.is_Integer:return rounded(power(bounds(v.base),int(v.exp)))
 return ordinary(v)
def answer_of(r,old):
 f=r['familyId'];t=old['statement'];index=r['instanceIndex'];m=s.Integer(4+index)
 if f.endswith('geometric-tail'):
  assert re.search(r'\\sum_\{k='+str(m)+r'\}',t)
  return m**(1-m)/(m-1),'Evaluate the geometric tail from its stated first index; the common ratio is1/m.'
 if f.endswith('rational-telescope')or f.endswith('cubic-telescope'):
  assert re.search(r'k\s*\+\s*'+str(m)+r'\b',t)
  return (1/(2*m*(m+1)) if f.endswith('cubic-telescope')else 1/m),'Subtract consecutive reciprocal factors; the finite partial sum has an explicit endpoint remainder tending to zero. Cubic factors contribute an additional factor one half.'
 if f.endswith('borderline-exponential-comparison'):
  assert 'e^{'+str(m)+'k}'in t and '1-'+str(m)+'/k'in t
  return s.Integer(1),'The logarithm of the non-power factor is m k+k² ln(1−m/k)=−m²/2+O(1/k). Its positive finite limit gives limit comparison with k^(−p), whose exact convergence threshold is1.'
 if f.endswith('floor-geometric-count'):
  assert 'k/'+str(m)in t
  return 2/(s.Integer(2)**m-1),'Write floor(k/m) as the number of positive multiples of m at most k. Tonelli sums the nonnegative geometric tails, giving2/(2^m−1).'
 if f.endswith('alternating-error'):
  assert re.search(r'through\s*\}'+str(m)+r'\b',t)
  return 1/(m+1),'The alternating-series bound is the positive magnitude of the first omitted term, indexed m+1.'
 if f.endswith('integral-tail-bound'):
  assert r'\int_{'+str(m)+'}'in t
  return 1/(2*m*m),'Integrate the displayed decreasing power x^(−3) from the stated endpoint to infinity.'
 if f.endswith('theta-dual-moment'):
  assert 'M('+str(m)+')'in t
  return 1/(2*s.pi*m),'Poisson summation for the Gaussian gives Θ(a)=a^(−1/2)Θ(1/a). Differentiate on a compact positive-a interval, justified by uniform Gaussian tails. With Θ′=−πM, rearrangement gives the literal numerator Θ(a)/(2πa).'
 if f.endswith('telescoping-arctan'):
  assert re.search(r'\\sum_\{k='+str(m)+r'\}',t)
  return s.pi/2-s.atan(m),'For positive integer k, atan(k+1)−atan(k) lies in(0,π/2) and has tangent1/(k²+k+1). Thus it equals the displayed summand on the principal real branch. Telescoping and atan(k)→π/2 give the answer; exact alternating bounds distinguish the revised omission choices.'
 raise ValueError('Unreviewed family '+f)
def main(folder,out):
 p=Path(folder);data=(p/'bracket-option-patches.json').read_bytes();sourcebytes=(p/'full-source-records.jsonl').read_bytes();originals={r['problemId']:r for r in map(json.loads,sourcebytes.splitlines())};results=[]
 for r in json.loads(data):
  old=originals[r['problemId']];assert hashlib.sha256(canonical(old).encode()).hexdigest()==r['sourceRawSHA256'] and old['contentHash']==r['sourceContentHash']
  a,route=answer_of(r,old);vals=[parse(c['math'])for c in r['choices']];matches=[i for i,v in enumerate(vals)if same(v,a)];assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
  assert next(c for c in old['choices']if c['choiceId']==old['answerChoiceId'])==r['choices'][matches[0]]
  cert=[]
  for x,y in itertools.combinations(vals,2):
   lo,hi=bounds(x-y);assert lo>0 or hi<0,('Unseparated options',r['problemId'],x,y);cert.append({'lower':str(lo),'upper':str(hi)})
  results.append({'problemId':r['problemId'],'familyId':r['familyId'],'index':r['instanceIndex'],'sourceRawSHA256':r['sourceRawSHA256'],'patchSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'independentAnswer':s.srepr(a),'correctLiteralChoiceUnchanged':True,'sixLiteralPairEnclosures':cert,'route':route,'passed':True})
 deps=['series_bracket_patch.py','ode_mv_literal_choices.py','limits_intervals.py','series_intervals.py','rational_intervals.py'];report={'author':'source_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'originalsSha256':hashlib.sha256(sourcebytes).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()for f in deps},'instances':len(results),'literalPairInequalities':6*len(results),'records':results,'scope':'Finite literal statements independently solved; all corrected choices separately parsed and certified distinct by outward rational bounds. The arctangent subtraction identity includes its real range; no heuristic non-equality result is used. Final actual-ID full-family review and admission remain separate. Not a formal proof assistant or human calibration.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'instances':len(results),'pairs':6*len(results),'passed':True}))
if __name__=='__main__':main(*sys.argv[1:])
