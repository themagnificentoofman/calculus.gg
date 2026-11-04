"""Register only a completely reconstructed final finite inventory, locally."""
from pathlib import Path
import hashlib,json,shutil
from .contract import ROOT
STAGE=ROOT/'.bank-data/quality/final-candidates-v1';DOC=ROOT/'docs/bank/problem-quality/final-admission-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def main():
 check=read(STAGE/'reconstruction.json');entries=read(STAGE/'admission-candidates.json');records=[json.loads(s)for s in (STAGE/'canonical-candidates.jsonl').read_text().splitlines()]
 assert check['status']=='reconstructed'and not check['errors']and len(check['records'])==len(entries)==len(records)==3292
 assert check['inputSha256']==sha(STAGE/'canonical-candidates.jsonl')and check['admissionSha256']==sha(STAGE/'admission-candidates.json')
 assert check['verifierSha256']==sha(ROOT/'scripts/bank/quality/verify_final_candidates.py')
 destination=read(STAGE/'destination-binding.json')
 for path,digest in destination['sourceArtifacts'].items():assert sha(ROOT/path)==digest,path
 if DOC.exists():raise ValueError('Preserve earlier registration evidence')
 DOC.mkdir()
 for file in ['reconstruction.json','destination-binding.json','source-definitions.json']:shutil.copyfile(STAGE/file,DOC/file)
 registry_path=ROOT/'scripts/bank/quality/reviewed.json';presentation_path=ROOT/'lib/server/solution-reviews/quality.json'
 old=read(registry_path);shutil.copyfile(registry_path,DOC/'previous-local-registry.json');shutil.copyfile(presentation_path,DOC/'previous-local-presentation.json')
 changed=[]
 for path,digest in old['sourceDigests'].items():
  if sha(ROOT/path)!=digest:changed.append({'path':path,'previousSha256':digest,'currentSha256':sha(ROOT/path)})
 assert {r['path']for r in changed}=={'scripts/bank/quality/adapt.mjs','scripts/bank/quality/contract.py','scripts/bank/quality/option-audit.mjs'}
 amendment={'status':'source-rebinding-after-complete-independent-content-reviews-and-reconstruction','changedPreviouslyBoundCode':changed,'reason':{'scripts/bank/quality/adapt.mjs':'Exact-source editorial supplements for original provenance and all four misconception labels; no existing values silently overwritten. Actual finite final reconstruction preserves public mathematics.','scripts/bank/quality/contract.py':'Bound supplemental review files by exact digest; expanded explicit frozen runtime routes. Unknown/changed source still fails closed.','scripts/bank/quality/option-audit.mjs':'Stronger rational-power and opposite-pair clue diagnostics; final per-topic family/form reviews preserve and resolve their findings.'},'validation':['All3292 final canonical records rebuilt from frozen constructors and separate finite verifiers, with raw/report/destination hashes checked.','Independent mathematical reviews remain separately bound per item; this registry operation is not a new mathematical proof.','Regression coverage rejects spoofed editorial supplements, malformed legacy evidence and source changes.'],'imported':0,'active':0}
 write(DOC/'source-binding-amendment.json',amendment)
 # Bind all portable runtime/review files consumed by this finite release.
 paths=set(ROOT/p for p in old['sourceDigests'])
 runtime_root=ROOT/'scripts/bank/quality'
 runtime_entries={'adapt.mjs','contract.py','bundle_runtime.py','bundle_worker.py','finite_runtime.py','late_runtime.py','option-audit.mjs','editorial-technique-labels.json'}
 for folder in [runtime_root,DOC]:
  for p in folder.rglob('*'):
   if p.parent==runtime_root and p.name not in runtime_entries:continue
   if p.is_file()and p.suffix in {'.py','.mjs','.json','.jsonl'}and '__pycache__'not in p.parts and p.name!='reviewed.json':paths.add(p)
 for e in entries.values():
  paths.add(ROOT/e['review']['report']);paths.add(ROOT/e['review']['optionAuditReport'])
  for r in e.get('supplementalReports',[]):paths.add(ROOT/r['path'])
  e.setdefault('supplementalReports',[]).append({'path':str((DOC/'destination-binding.json').relative_to(ROOT)),'sha256':sha(DOC/'destination-binding.json'),'purpose':'Exact final destination join; public mathematics unchanged from final independently reviewed topic previews.'})
  assert len(e['supplementalReports'])<=16
 registry={'version':old['version'],'status':'independently-reviewed','sourceDigests':{str(p.relative_to(ROOT)):sha(p)for p in sorted(paths)},'items':entries}
 presentation=read(presentation_path)
 for p in records:presentation[p['problemId']+'@'+str(p['problemRevision'])]={'sourceContentHash':p['contentHash'],'revision':p['problemRevision'],'familyId':p['familyId'],'auditId':p['provenance']['authoring']['reviewId']}
 write(registry_path,registry);write(presentation_path,presentation)
 shutil.copyfile(STAGE/'canonical-candidates.jsonl',ROOT/'.bank-data/quality/final-admitted-v1.jsonl')
 print(json.dumps({'locallyRegistered':len(entries),'sourceFilesBound':len(paths),'recordsReconstructed':len(records),'imported':0,'active':0}))
if __name__=='__main__':main()
