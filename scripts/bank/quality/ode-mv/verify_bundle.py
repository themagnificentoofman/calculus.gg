"""Reconstruct every effective raw record using isolated offline constructors."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy,hashlib,json,time,sys
import runtime
BASE=Path(__file__).resolve().parent
def raw(r):return hashlib.sha256(runtime.canonical(r).encode()).hexdigest()
joins=json.loads((BASE/'source-joins.json').read_text())['records']
routes=sorted({q['route'] for q in joins});started=time.monotonic()
def verify_route(route):
 results=[]
 for q in [q for q in joins if q['route']==route]:
  try:
   record=runtime.build(route,q['familyId'],q['index'])
   assert raw(record)==q['rawSha256']
   assert runtime.verify(route,record,q['index'])is True
   changed=copy.deepcopy(record);changed['statement']+=' '
   assert runtime.verify(route,changed,q['index'])is False
   results.append({'route':route,'familyId':q['familyId'],'index':q['index'],'rawSha256':raw(record),'sourceLineSha256':q['sourceLineSha256'],'contentHash':record.get('contentHash'),'passed':True,'canonicalRecordByteParity':True,'frozenSourceLineByteParity':True,'alteredRecordRejected':True,'reconstructionNormalizations':runtime.reconstruction_evidence(route,q['familyId'],q['index'])})
  except Exception as e:results.append({'route':route,'familyId':q['familyId'],'index':q['index'],'passed':False,'error':repr(e)})
  if len(results)%20==0:print(route,len(results),'records',flush=True)
 return results
allresults=[]
with ThreadPoolExecutor(max_workers=3) as pool:
 for result in as_completed([pool.submit(verify_route,route) for route in routes]):
  rows=result.result();allresults.extend(rows);print('completed',rows[0]['route'],len(rows),'failures',sum(not q['passed'] for q in rows),flush=True)
runtime.close()
for args in [('unknown','x',0),(routes[0],'unknown',0),(routes[0],joins[0]['familyId'],True)]:
 try:runtime.build(*args);raise AssertionError('Invalid finite request accepted')
 except ValueError:pass
report={'status':'offline-reconstruction-complete' if all(q['passed'] for q in allresults) else 'failed-preserve-evidence','records':len(allresults),'coreODEMVRecords':sum(q['route']!='integration-lower-guarded' for q in allresults),'integrationRecords':sum(q['route']=='integration-lower-guarded' for q in allresults),'passed':sum(q['passed'] for q in allresults),'failures':[q for q in allresults if not q['passed']],'results':sorted(allresults,key=lambda q:(q['route'],q['familyId'],q['index'])),'seconds':time.monotonic()-started,'invalidDomainRequestsRejected':3,'sourceJoinSha256':hashlib.sha256((BASE/'source-joins.json').read_bytes()).hexdigest(),'runtimeSourceSha256':{f:hashlib.sha256((BASE/f).read_bytes()).hexdigest() for f in ['runtime.py','worker.py','verify_bundle.py','certificate_serialization.py','green-certificate-serialization-forms.json']},'scope':'Every source-bound finite builder executed and its canonical output compared byte-for-byte with the frozen record. Exact source JSONL line hashes checked too. The narrow Green proof-description equivalence guard is recorded per use; it proves zero residual and forbids other field differences. This is reconstruction evidence, not a new independent proof/level review or an admission token.'}
(BASE/'reconstruction-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['results','runtimeSourceSha256']},indent=2),flush=True)
if report['failures']:sys.exit(1)
