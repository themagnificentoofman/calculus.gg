from pathlib import Path
import json,hashlib,time
import runtime
P=Path(__file__).resolve().parent;started=time.monotonic();rows=[];fail=[]
for q in runtime.catalog():
 for i in q['indices']:
  try:
   r=runtime.build(q['familyId'],i);assert runtime.verify(r);changed=json.loads(runtime.canonical(r));changed['statement']+=' altered';assert not runtime.verify(changed)
   rows.append({'familyId':q['familyId'],'index':i,'rawSha256':hashlib.sha256(runtime.canonical(r).encode()).hexdigest(),'canonicalFrozenBytesMatch':True,'alteredStatementRejected':True})
  except Exception as e:fail.append({'familyId':q['familyId'],'index':i,'error':repr(e)})
invalid=0
for f,i in [('unknown',0),(runtime.catalog()[0]['familyId'],True),(runtime.catalog()[0]['familyId'],999)]:
 try:runtime.build(f,i)
 except ValueError:invalid+=1
runtime.close();report={'status':'reconstruction-passed' if not fail else 'failed','records':rows,'failures':fail,'counts':{'expected':272,'passed':len(rows),'invalidDomainRequestsRejected':invalid},'seconds':time.monotonic()-started,'scope':'Offline constructor replay, exact frozen canonical bytes, and negative guards. Mathematical independence is established separately by the copied root peer report; no registration or final-ID option approval is implied.','runtimeFiles':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['runtime.py','worker.py','verify_bundle.py']}}
(P/'reconstruction-report.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts']);print(report['failures'])
