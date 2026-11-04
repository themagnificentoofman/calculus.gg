from pathlib import Path
import sys,json,hashlib
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));import runtime
runtime.require_reviews();results=[]
for q in runtime.catalog():
 for i in q['indices']:
  r=runtime.build(q['route'],q['familyId'],i);assert runtime.verify(q['route'],r,i)
  results.append({'route':q['route'],'familyId':q['familyId'],'index':i,'rawSha256':hashlib.sha256(runtime.canonical(r).encode()).hexdigest(),'passed':True})
runtime.close();out={'status':'passed','records':results}
if len(sys.argv)>1:
 dest=Path(sys.argv[1]);assert not dest.exists(),'Preserve previous review output';dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'passed','instances':len(results)}))
