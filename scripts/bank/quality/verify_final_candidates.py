"""Reconstruct each final candidate before replacing the admission registry."""
import hashlib,importlib,json,time
from pathlib import Path
from .contract import ROOT,canonical,normalize,bound_file,bind_supplemental_reports,MODULES
from . import finite_runtime,bundle_runtime

def main():
 stage=ROOT/'.bank-data/quality/final-candidates-v1';out=stage/'reconstruction.json'
 if out.exists():raise ValueError('Preserve prior reconstruction evidence')
 entries=json.loads((stage/'admission-candidates.json').read_text());records=[json.loads(s)for s in (stage/'canonical-candidates.jsonl').read_text().splitlines()]
 results=[];errors=[];start=time.time()
 for i,p in enumerate(records):
  rid=p['provenance']['authoring']['reviewId'];e=entries[rid]
  try:
   for prefix in ['report','optionAudit']:bound_file(e['review'][prefix if prefix=='report'else'optionAuditReport'],e['review'][prefix+'Sha256'])
   bind_supplemental_reports(e)
   if e.get('adaptation'):bound_file(e['adaptation']['sourceRegister'],e['adaptation']['sourceRegisterSha256'])
   assert type(e['index'])is int and e['index']in e['finiteDomain']['indices']
   route=e['module']
   if route in MODULES:
    module=importlib.import_module(MODULES[route]);raw=module.build(e['familyId'],e['index']);assert module.verify(raw)is True
   elif route in finite_runtime.ROUTES:raw=finite_runtime.build(route,e['familyId'],e['index'])
   else:raw=bundle_runtime.build(route,e['familyId'],e['index'])
   q=normalize(raw,e);assert canonical(q)==canonical(p),'Final canonical reconstruction mismatch'
   results.append({'reviewId':rid,'problemId':p['problemId'],'revision':p['problemRevision'],'contentHash':p['contentHash'],'passed':True})
  except Exception as ex:
   errors.append({'reviewId':rid,'error':str(ex)});print(json.dumps(errors[-1]),flush=True)
  if (i+1)%50==0:print(json.dumps({'checked':i+1,'passed':len(results),'errors':len(errors),'seconds':round(time.time()-start)}),flush=True)
 report={'status':'reconstructed'if not errors else'blocked','inputSha256':hashlib.sha256((stage/'canonical-candidates.jsonl').read_bytes()).hexdigest(),'admissionSha256':hashlib.sha256((stage/'admission-candidates.json').read_bytes()).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':results,'errors':errors,'seconds':time.time()-start,'imported':0,'active':0}
 out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':len(results),'errors':len(errors),'seconds':round(time.time()-start)}));assert not errors
if __name__=='__main__':main()
