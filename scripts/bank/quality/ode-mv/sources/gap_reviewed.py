"""Versioned portable adapter for the reviewed six ODE plus one MV additions."""
from pathlib import Path
import json,hashlib
from common import H
import ode_gap,mv_gap
P=Path(__file__).resolve().parent
REG={f['familyId']:r for r in (ode_gap.reg,mv_gap.reg) for f in r.catalog()}
def catalog():return [f for r in (ode_gap.reg,mv_gap.reg) for f in r.catalog()]
def build(fid,index):
 r=REG[fid].build(fid,index);source_hash=r['contentHash']
 r['constructorVersion']='quality-ode-mv-gap-v1'
 r['review'].update(recommendedDifficulty=r['difficulty'],qualifiedOlympiadCandidate=r['difficulty']=='olympiad',relatedIdeaGroupId=r['relatedIdeaGroupId'],sourceBeforeMetadataOverlayContentHash=source_hash,normalizedLineageKey='q4-meaningful:'+fid+':'+H(r['parameters'])[:24],normalizedLineageInvariants=r['parameters'],normalizedLineageReason='The finite parameter changes a nonlinear contact/forcing degree, a spectral aspect ratio, or a geometric frequency ratio; no two listed cases differ only by an outside amplitude/time/coordinate scale.',normalizationScope='Conservative advanced meaningful-headroom qualification; zero extra idea groups for parameter changes.',status='source-bound-candidate-awaiting-final-admission')
 r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r
def all_candidates():
 for f in catalog():
  for i in range(f['instanceCount']):yield build(f['familyId'],i)
def verify(record):
 try:return record==build(record['familyId'],record['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=list(all_candidates());assert len(rows)==70
 temp=P/'gap-reviewed-candidates.jsonl.tmp';temp.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows));temp.replace(P/'gap-reviewed-candidates.jsonl')
 (P/'gap-reviewed-verification.json').write_text(json.dumps({'records':len(rows),'executedChecks':sum(len(r['verificationEvidence']) for r in rows),'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['common.py','ode_gap.py','mv_gap.py','gap_reviewed.py']},'artifactSha256':hashlib.sha256((P/'gap-reviewed-candidates.jsonl').read_bytes()).hexdigest(),'status':'candidate-not-admission'},indent=2)+'\n');print(len(rows),'versioned candidates')
