"""Independent Taylor/Gamma-domain repair checks over six exact literal menus."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,re,sys
import sympy as s
from ode_mv_literal_choices import parse as simple,same
from series_intervals import loggamma,expq,loginterval,rounded,enclose as base
from rational_intervals import add,mul,power
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def parse(tex):
 tex=re.sub(r'\\Gamma\^\{(\d+)\}\\left\((.*?)\\right\)',lambda m:r'(\Gamma\left('+m[2]+r'\right))^{'+m[1]+'}',tex)
 return simple(tex)
def bounds(v):
 if v.func==s.gamma:
  a=v.args[0];assert a.is_Rational and a>0;lo,hi=loggamma(Q(int(a.p),int(a.q)));return expq(lo)[0],expq(hi)[1]
 if v.is_Add:
  a=(Q(0),)*2
  for t in v.args:a=rounded(add(a,bounds(t)))
  return a
 if v.is_Mul:
  a=(Q(1),)*2
  for t in v.args:a=rounded(mul(a,bounds(t)))
  return a
 if v.is_Pow:
  a,b=v.args
  if b.is_Integer:return rounded(power(bounds(a),int(b)))
  assert b.is_Rational and a.is_positive is True
  c=Q(int(b.p),int(b.q));lo,hi=mul((c,c),loginterval(bounds(a)));return expq(lo)[0],expq(hi)[1]
 return base(v)
def main(folder,out):
 p=Path(folder);patchbytes=(p/'option-patches.json').read_bytes();sourcebytes=(p/'full-source-records.jsonl').read_bytes();source={r['problemId']:r for r in map(json.loads,sourcebytes.splitlines())};results=[]
 for r in json.loads(patchbytes):
  old=source[r['problemId']];assert hashlib.sha256(canonical(old).encode()).hexdigest()==r['sourceRawSHA256'] and old['contentHash']==r['sourceContentHash']
  stmt=old['statement']
  if r['familyId'].endswith('taylor-coefficient-derivative'):
   n=int(re.search(r'a_\{(\d+)\}',stmt)[1]);coefficient=re.search(r'a_\{\d+\}=(.*?)\.',stmt)[1];answer=s.factorial(n)*parse(coefficient)
   assert 'f^{('+str(n)+')}(2)' in stmt
   route='Differentiate the convergent power series n times inside its convergence interval and evaluate at its center. Only the nth monomial survives, giving n! times the literal coefficient.'
  else:
   match=re.search(r'k\^\{\\frac\{(\d+)\}\{(\d+)\}\}',stmt);assert match;q=s.Rational(int(match[1]),int(match[2]));assert 0<q<1
   answer=s.gamma(1-q)**2/s.gamma(2-2*q)
   route='Rewrite as a Riemann sum for t^(-q)(1-t)^(-q). On any fixed interior interval convergence is ordinary; the two omitted tails are uniformly bounded by constants times cutoff^(1-q), tending to zero. The positive-argument beta integral gives Gamma(1-q)^2/Gamma(2-2q).'
  vals=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(vals)if same(v,answer)];assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
  correct=next(c for c in old['choices']if c['choiceId']==old['answerChoiceId']);assert correct==r['choices'][matches[0]] and old['answerChoiceId']==r['answerChoiceId']
  for v in vals:
   assert all(g.args[0].is_positive is True for g in v.atoms(s.gamma))
  paircert=[]
  for a,b in itertools.combinations(vals,2):
   lo,hi=bounds(s.expand_func(a-b));assert lo>0 or hi<0,('unseparated',a,b)
   paircert.append({'lower':str(lo),'upper':str(hi)})
  signs=[1 if bounds(v)[0]>0 else -1 if bounds(v)[1]<0 else 0 for v in vals];assert len(set(signs))==1 and 0 not in signs
  results.append({'problemId':r['problemId'],'familyId':r['familyId'],'index':r['instanceIndex'],'sourceRawSHA256':r['sourceRawSHA256'],'patchSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'independentAnswer':s.srepr(answer),'literalCorrectChoiceUnchanged':True,'allGammaArgumentsInStatedPositiveDomain':True,'sameCertifiedSignForAllChoices':signs[0],'sixLiteralPairEnclosures':paircert,'route':route,'passed':True})
 deps=['series_domain_patch.py','ode_mv_literal_choices.py','series_intervals.py','rational_intervals.py'];report={'author':'source_research','reviewer':'root','inputSha256':hashlib.sha256(patchbytes).hexdigest(),'originalsSha256':hashlib.sha256(sourcebytes).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()for f in deps},'records':results,'instances':len(results),'literalPairInequalities':6*len(results),'scope':'Independent literal-answer derivations, exact outward rational bounds and stated-domain inspection. Gamma enclosures use separately implemented positive-real log-Gamma recurrence and signed Stirling remainder. No author constructor, expression field or numerical oracle is used. Final family screen and admission remain separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'instances':len(results),'pairs':6*len(results),'passed':True}))
if __name__=='__main__':main(*sys.argv[1:])
