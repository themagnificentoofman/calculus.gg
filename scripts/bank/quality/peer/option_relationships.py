"""Exact parsed-scalar opposite-pair diagnostic; unsupported means unreviewed."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from ode_mv_literal_choices import parse,same
def main(source,out):
 data=Path(source).read_bytes();rows=list(map(json.loads,data.splitlines()));records=[]
 for r in rows:
  result={'problemId':r['problemId'],'familyId':r['familyId']}
  try:
   vals=[parse(c['math'].replace(r'\log',r'\ln')) for c in r['choices']]
   assert all(not isinstance(v,s.Tuple) and v.is_real is True and v.is_finite is True for v in vals),'Nonreal, nonfinite, tuple or unresolved domain'
   pairs=[(i,j) for i,j in itertools.combinations(range(4),2) if same(vals[i],-vals[j])]
   correct=next(i for i,c in enumerate(r['choices']) if c['choiceId']==r['answerChoiceId'])
   result.update({'status':'parsed-exact-real-scalar','oppositePairs':pairs,'pairedCorrect':any(correct in pair for pair in pairs)})
  except Exception as e:result.update({'status':'unsupported-needs-explicit-review','reason':str(e)})
  records.append(result)
  if len(records)%100==0:print(json.dumps({'reviewed':len(records)}),flush=True)
 report={'inputSha256':hashlib.sha256(data).hexdigest(),'reviewCodeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parserSha256':hashlib.sha256(Path(__file__).with_name('ode_mv_literal_choices.py').read_bytes()).hexdigest(),'records':records,'limitation':'A finite exact symbolic diagnostic, not a complete equivalence procedure. Every unsupported family needs explicit review. No author expression metadata is used.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'records':len(records),'unsupported':sum(r['status']!='parsed-exact-real-scalar' for r in records),'singlePairs':sum(len(r.get('oppositePairs',[]))==1 for r in records)}))
if __name__=='__main__':main(*sys.argv[1:])
