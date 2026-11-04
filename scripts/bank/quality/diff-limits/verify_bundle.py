"""Execute every isolated finite constructor and reject changed records."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,time,hashlib,sys
import runtime
BASE=Path(__file__).resolve().parent
joins=json.loads((BASE/'source-joins.json').read_text())['records'];started=time.monotonic()
def run(route):
 out=[]
 for q in [q for q in joins if q['route']==route]:
  try:
   r=runtime.build(route,q['familyId'],q['index']);h=hashlib.sha256(runtime.canonical(r).encode()).hexdigest();assert h==q['rawSha256'];bad=dict(r);bad['statement']+=' ';assert not runtime.verify(route,bad,q['index']);out.append({'route':route,'familyId':q['familyId'],'index':q['index'],'rawSha256':h,'passed':True,'alteredRecordRejected':True})
  except Exception as e:out.append({'route':route,'familyId':q['familyId'],'index':q['index'],'passed':False,'error':repr(e)})
  if len(out)%40==0:print(route,len(out),flush=True)
 return out
results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for task in as_completed([pool.submit(run,route) for route in sorted({q['route'] for q in joins})]):results+=task.result()
runtime.close()
for args in [('unknown','x',0),(joins[0]['route'],'unknown',0),(joins[0]['route'],joins[0]['familyId'],True)]:
 try:runtime.build(*args);raise AssertionError('Invalid domain accepted')
 except ValueError:pass
report={'records':len(results),'passed':sum(r['passed'] for r in results),'failures':[r for r in results if not r['passed']],'results':results,'seconds':time.monotonic()-started,'sourceJoinsSha256':hashlib.sha256((BASE/'source-joins.json').read_bytes()).hexdigest(),'invalidDomainRequestsRejected':3,'scope':'Executed author finite checks and byte-exact source reconstruction; independent mathematical/editorial evidence is separately bound in review-manifest.'}
(BASE/'reconstruction-report.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='results'});sys.exit(bool(report['failures']))
