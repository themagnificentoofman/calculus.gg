"""Reproduce every authored finite integration candidate and its independent checks."""
from pathlib import Path
import json,hashlib
import integrals
from verify_integrals import verify
ROOT=Path(__file__).resolve().parent
def main():
 rows=[];reports=[];failures=[]
 for f in integrals.catalog():
  for i in f['finiteInstanceIndices']:
   try:r=integrals.build(f['familyId'],i);v=verify(r);rows.append(r);reports.append(v)
   except Exception as e:failures.append({'familyId':f['familyId'],'instanceIndex':i,'error':repr(e)})
 (ROOT/'candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 sources={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['integrals.py','common.py','verify_integrals.py','generate.py']}
 result={'status':'passed' if not failures else 'failed','families':len(integrals.catalog()),'instances':len(rows),'executedChecks':sum(r['executedCheckCount'] for r in reports),'sourceFiles':sources,'failures':failures,'results':reports,'humanReviewed':False,'formalProof':False}
 (ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'catalog.json').write_text(json.dumps(integrals.catalog(),indent=2)+'\n')
 first=[r for r in rows if r['instanceIndex']==0];blind=[{'sampleKey':'sample-'+str(j+1),'statement':r['statement'],'choices':[{'choiceId':c['choiceId'],'math':c['math']} for c in r['choices']]} for j,r in enumerate(first)]
 (ROOT/'first-samples.json').write_text(json.dumps(blind,indent=2)+'\n');(ROOT/'first-samples-private-map.json').write_text(json.dumps([{'sampleKey':'sample-'+str(j+1),'familyId':r['familyId'],'sourceContentHash':r['contentHash'],'answerChoiceId':r['answerChoiceId']} for j,r in enumerate(first)],indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['results','sourceFiles']}));return bool(failures)
if __name__=='__main__':raise SystemExit(main())
