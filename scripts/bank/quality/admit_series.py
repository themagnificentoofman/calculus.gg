"""Admit only the exact independently reviewed, screened finite series batch.
This is a local admission operation, not an import or release activation.
"""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
from . import bundle_runtime
from .series.options import runtime as options

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stage=ROOT/'.bank-data/quality/series-previews-v4';doc=ROOT/'docs/bank/problem-quality/series';report=doc/'final-option-review.json';review=json.loads(report.read_text())
 for name,digest in review['inputs'].items():assert sha(stage/name)==digest,(name,'Changed reviewed input')
 assert len(review['records'])==705 and len(review['families'])==78 and review.get('answerForms')
 entries=json.loads((stage/'admission-previews.json').read_text());previews={r['provenance']['authoring']['reviewId']:r for r in map(json.loads,(stage/'canonical-previews.jsonl').read_text().splitlines())}
 out=ROOT/'.bank-data/quality/series-admitted.jsonl'
 if out.exists():raise ValueError('Preserve prior admitted output')
 records=[];destinations=[]
 for rid,e in entries.items():
  e['review']['optionAuditReport']=str(report.relative_to(ROOT));e['review']['optionAuditSha256']=sha(report)
  raw=options.build(e['familyId'],e['index']) if e['module']=='series-options' else bundle_runtime.build(e['module'],e['familyId'],e['index'])
  if e['module']=='series-options':assert options.verify(raw)
  assert hashlib.sha256(canonical(raw).encode()).hexdigest()==e['rawSha256']
  r=normalize(raw,e);prior=previews[rid]
  for field in ['problemId','problemRevision','familyId','semanticHash','statement','choices','answerChoiceId','solutionSteps','pedagogy']:assert r[field]==prior[field],(rid,field)
  e['contentHash']=r['contentHash'];records.append(r);destinations.append({'reviewId':rid,'problemId':r['problemId'],'revision':r['problemRevision'],'rawSha256':e['rawSha256'],'reviewedPreviewHash':prior['contentHash'],'admittedContentHash':r['contentHash'],'publicContentUnchanged':True})
  if len(records)%100==0:print(json.dumps({'reconstructedAndBound':len(records)}),flush=True)
 assert len(records)==455
 registry_path=ROOT/'scripts/bank/quality/reviewed.json';registry=json.loads(registry_path.read_text());backup=ROOT/'.bank-data/quality/registry-before-series.json';assert not backup.exists();backup.write_text(registry_path.read_text())
 manifest={'status':'locally-admitted-pending-real-pipeline-verification','records':455,'mathematics':'All finite raw records reconstructed using frozen sources, with independent exact raw report bindings and reviewed final option pools.','newlyImported':0,'active':0,'destinations':destinations}
 destination=doc/'admission-destinations.json';destination.write_text(json.dumps(manifest,indent=2)+'\n')
 paths=[ROOT/'scripts/bank/quality/contract.py',ROOT/'scripts/bank/quality/adapt.mjs',ROOT/'scripts/bank/quality/bundle_runtime.py',ROOT/'scripts/bank/quality/bundle_worker.py',ROOT/'scripts/bank/quality/option-audit.mjs',ROOT/'scripts/bank/quality/admit_series.py']
 for folder in ['advanced','capacity','hankel','existing']:
  paths += [p for p in (ROOT/'scripts/bank/quality/series/bundles'/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.json','.jsonl'] and '__pycache__' not in p.parts]
 paths += [p for p in (ROOT/'scripts/bank/quality/series/options').iterdir() if p.suffix in ['.py','.json']]
 paths += [p for p in doc.iterdir() if p.suffix in ['.json','.jsonl','.py']]
 for p in paths:registry['sourceDigests'][str(p.relative_to(ROOT))]=sha(p)
 registry['items'].update(entries)
 presentation_path=ROOT/'lib/server/solution-reviews/quality.json';presentation=json.loads(presentation_path.read_text());(ROOT/'.bank-data/quality/presentation-before-series.json').write_text(presentation_path.read_text())
 for r in records:presentation[r['problemId']+'@'+str(r['problemRevision'])]={'sourceContentHash':r['contentHash'],'revision':r['problemRevision'],'familyId':r['familyId'],'auditId':r['provenance']['authoring']['reviewId']}
 out.write_text(''.join(canonical(r)+'\n' for r in records));registry_path.write_text(json.dumps(registry,indent=2)+'\n');presentation_path.write_text(json.dumps(presentation,indent=2)+'\n');print(json.dumps({'locallyRegistered':455,'registryItems':len(registry['items']),'pipelineVerificationRequired':True,'imported':0,'active':0}))
if __name__=='__main__':main()
