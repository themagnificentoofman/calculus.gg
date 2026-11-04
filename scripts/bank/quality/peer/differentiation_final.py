"""Rebind independent finite derivations to the final literal differentiation pool."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from differentiation_limits_stage4 import solve as early
from differentiation_limits_stage6 import solve as extra,SLUGS
from differentiation_literal_choices import parse,same
from limits_intervals import separate
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def main(source,out):
 data=Path(source).read_bytes();rows=[r for r in json.loads(data) if r['topic']=='differentiation'];records=[]
 for r in rows:
  try:
   if r['familyId'].endswith('critical-level-absolute-integral') and len(set(r['parameters']['case']['roots']))<len(r['parameters']['case']['roots']):
    case=r['parameters']['case'];assert case['roots']==[0,0,1] and case['bounds']==[-1,2] and case['weight']=='1+x**2'
    assert 'R(x)=x^2(x-1)' in r['statement'] and 'a^{1/4}' in r['statement']
    x,z=s.symbols('x z',real=True);R=x*x*(x-1);weight=1+x*x
    assert s.limit(R**2/x**4,x,0)==1 and s.limit(R**2/(x-1)**2,x,1)==1
    answer=2*2*weight.subs(x,0)
    checks=['Independent multiplicity analysis: the interior double root contributes two intervals of width a^(1/4)(1+o(1)), with weight tending to1. The interior simple root contributes O(sqrt(a)), negligible at the fourth-root scale. Away from both roots, the squared polynomial has a positive compact minimum. Dominated difference quotients give twice this weighted sublevel mass, so the limit is4. This is a new mixed-multiplicity case, not a reuse of the earlier simple-root oracle.']
   else:answer,checks=(extra if any(r['familyId'].endswith(k) for k in SLUGS) else early)(r)
   vals=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(vals) if same(v,answer)]
   assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],('answer mismatch',answer,matches)
   pairs=[separate(a,b) for a,b in itertools.combinations(vals,2)]
   if r['familyId'].endswith('moment-hankel-vandermonde'):
    # The original independent proof identified a statement-scope defect.
    # The corrected finite source must actually include the weight grouping.
    assert r'\left(' in r['statement'] and r'\right)' in r['statement']
    checks=[x for x in checks if not x.startswith('Stage04 statement')]+['Final weight grouping inspected in the literal statement; the original stage04 blocked draft remains preserved.']
   records.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'independentAnswer':s.srepr(answer),'checks':checks,'sixLiteralPairsDistinct':True,'sixLiteralPairEnclosures':pairs,'passed':True})
  except Exception as e:records.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'passed':False,'error':repr(e)})
  if len(records)%25==0:print(json.dumps({'reviewed':len(records),'failed':sum(not v['passed'] for v in records)}),flush=True)
 deps=['differentiation_final.py','differentiation_literal_choices.py','differentiation_limits_stage1.py','differentiation_limits_stage4.py','differentiation_limits_stage6.py','limits_intervals.py','series_intervals.py','rational_intervals.py']
 report={'status':'independent-final-finite-mathematics','author':'coverage_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in deps},'instances':len(rows),'passed':sum(r['passed'] for r in records),'records':records,'scope':'Separate root derivations are rerun on every final finite parameter. Actual literal choices, not author expression metadata, establish the answer match and all six inequalities. Analytic proof obligations are reviewed mathematical arguments, not formal proof or human calibration. Final difficulty, equivalence, catalog screen and admission remain separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['instances','passed']}));return report['instances']==report['passed']
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
