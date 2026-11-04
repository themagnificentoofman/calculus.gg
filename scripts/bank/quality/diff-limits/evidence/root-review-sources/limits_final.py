"""Independent rederivation of104 final cases not in the separate163-case review."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from differentiation_limits_stage4 import solve
from limits_literal_choices import parse,same
from limits_intervals import enclose
def separate(a,b):
 difference=s.simplify(s.expand_func(a-b)).replace(lambda v:v.func in [s.sinh,s.cosh],lambda v:v.rewrite(s.exp))
 lo,hi=enclose(difference);assert lo>0 or hi<0,(a,b,lo,hi)
 return {"lower":str(lo),"upper":str(hi)}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def main(source,mapping,out):
 data=Path(source).read_bytes();maps=Path(mapping).read_bytes();scope=json.loads(maps)
 assert hashlib.sha256(data).hexdigest()==scope['stage14SHA256'];keys={(r['familyId'],r['instance']):r for r in scope['records']}
 rows=[r for r in json.loads(data) if (r['familyId'],r['parameters']['instance'])in keys];assert len(rows)==104
 records=[]
 for r in rows:
  try:
   assert hashlib.sha256(canonical(r).encode()).hexdigest()==keys[(r['familyId'],r['parameters']['instance'])]['finalRawHash']
   answer,checks=solve(r);vals=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(vals) if same(v,answer)]
   assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],('Answer mismatch',answer,matches)
   pairs=[separate(a.replace(lambda v:v.func in [s.sinh,s.cosh],lambda v:v.rewrite(s.exp)),b.replace(lambda v:v.func in [s.sinh,s.cosh],lambda v:v.rewrite(s.exp))) for a,b in itertools.combinations(vals,2)]
   records.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'independentAnswer':str(answer),'checks':checks,'sixLiteralPairEnclosures':pairs,'passed':True})
  except Exception as e:records.append({'familyId':r['familyId'],'index':r['parameters']['instance'],'passed':False,'error':repr(e)})
  if len(records)%20==0:print(json.dumps({'reviewed':len(records),'failed':sum(not v['passed']for v in records)}),flush=True)
 deps=['limits_final.py','limits_literal_choices.py','limits_intervals.py','series_intervals.py','rational_intervals.py','differentiation_limits_stage1.py','differentiation_limits_stage4.py']
 report={'author':'coverage_research','reviewer':'root','inputSha256':hashlib.sha256(data).hexdigest(),'mappingSha256':hashlib.sha256(maps).hexdigest(),'reviewSources':{f:hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest()for f in deps},'instances':len(rows),'passed':sum(r['passed']for r in records),'records':records,'scope':'Prior separately written derivations rerun on every final finite case; literal four choices independently parsed and all six pairs separated by exact rational enclosures. No author expressions are answer or inequality oracles. Analytic arguments and supplementary small numerical checks retain their stated scope; no formal or human certification. Final admission/option screening remains separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['instances','passed']}));return report['instances']==report['passed']
if __name__=='__main__':sys.exit(0 if main(*sys.argv[1:]) else 1)
