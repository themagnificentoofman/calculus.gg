"""Verify the97 added records and preserve the completed1069 reconstruction."""
from pathlib import Path
import json,hashlib,time
import runtime
B=Path(__file__).resolve().parent
joins=json.loads((B/'source-joins.json').read_text())['records'];index={(j['route'],j['familyId'],j['index']):j for j in joins};old=json.loads((B/'reconstruction-1069.json').read_text());assert old['passed']==1069 and not old['failures'];out=[]
for row in old['results']:
 assert row['passed'];q=index[(row['route'],row['familyId'],row['index'])];assert row['rawSha256']==q['rawSha256'];out.append(row)
for q in joins:
 if q['route']!='ode-mv-additional-options':continue
 r=runtime.build(q['route'],q['familyId'],q['index']);h=hashlib.sha256(runtime.canonical(r).encode()).hexdigest();assert h==q['rawSha256'];changed=dict(r);changed['statement']+=' ';assert not runtime.verify(q['route'],changed,q['index']);out.append({'route':q['route'],'familyId':q['familyId'],'index':q['index'],'rawSha256':h,'passed':True,'alteredRecordRejected':True})
runtime.require_reviews();runtime.close();assert len(out)==1166
report={'records':1166,'passed':1166,'failures':[],'results':out,'sourceJoinsSha256':hashlib.sha256((B/'source-joins.json').read_bytes()).hexdigest(),'evidenceReuse':{'previous1069ReportSha256':hashlib.sha256((B/'reconstruction-1069.json').read_bytes()).hexdigest(),'allPreviousRawJoinsIdentical':True,'additional97Executed':True},'scope':'All1166 constructor records reconstructed exactly. The unchanged1069 retain their completed execution evidence; only97 new menu-route constructors are executed here. Every altered record is rejected. Independent peer review remains separate and is complete for all1166 exact raw hashes.'}
(B/'reconstruction-report.json').write_text(json.dumps(report,indent=2)+'\n');print({'records':len(out),'passed':len(out),'pendingPeerJoins':0})
