"""Twelve purposeful MV Hard calculations after honest lower-level demotions.
Same six constructions, zero new ideas. Prior finite constructors remain frozen.
"""
from pathlib import Path
import copy,json,hashlib
from common import Registry,H
import extensions_v2 as corrected
P=Path(__file__).resolve().parent
SLUGS=['quadratic-eigenconstraint','ellipsoid-inertia','nonlinear-Jacobian','simplex-beta','surface-flux-graph','Gaussian-precision']
reg=Registry('multivariable')
for slug in SLUGS:
 fid='m3-multivariable-hard-'+slug;meta=copy.copy(corrected.reg.families[fid]);meta['finiteParameters']=[{'m':14},{'m':15}];reg.families[fid]=meta
def catalog():return reg.catalog()
def build(fid,index):
 r=reg.build(fid,index);r['constructorVersion']='quality-mv-hard-headroom-v1'
 r['review'].update(newIndependentIdeas=0,recommendedDifficulty='hard',qualifiedOlympiadCandidate=False,relatedIdeaGroupId=r['relatedIdeaGroupId'],normalizedLineageKey=fid+':finite-fluency-m:'+str(r['parameters']['m']),normalizedLineageReason='A new displayed numerical calculation in the same retained Hard construction; the parameter changes the actual finite computation. No extra idea group or harder level is claimed.',scope='Two finite m14/15 cases after six other former Hard constructions were honestly demoted. Exact independent solution routes are reused on the new finite inputs; final independent literal review is separately bound.')
 r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r
def all_candidates():
 for f in catalog():
  for i in range(f['instanceCount']):yield build(f['familyId'],i)
def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False
if __name__=='__main__':
 rows=list(all_candidates());assert len(rows)==12
 tmp=P/'hard-headroom-candidates.jsonl.tmp';tmp.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows));tmp.replace(P/'hard-headroom-candidates.jsonl')
 (P/'hard-headroom-verification.json').write_text(json.dumps({'records':12,'families':6,'newIndependentIdeas':0,'executedChecks':sum(len(r['verificationEvidence']) for r in rows),'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['hard_headroom.py','extensions_v2.py','extensions.py','baseline_support.py','common.py','presentation.py']},'artifactSha256':hashlib.sha256((P/'hard-headroom-candidates.jsonl').read_bytes()).hexdigest(),'status':'candidate-awaiting-final-independent-finite-review'},indent=2)+'\n');print('12 MV Hard headroom cases')
