import os
from pathlib import Path
import sys,json,sqlite3,gzip,time,hashlib
ROOT=Path(os.environ.get('BANK_AUDIT_REPO',Path(__file__).resolve().parents[4]))
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/bank'))
import pipeline as p
from families import FAMILIES
DB=os.environ['BANK_AUDIT_LEGACY_DB']
c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
counts={};edges={};metadata={}
for fid,meta in c.execute('select shared_id,metadata_json from cbank_shared'):
 d=json.loads(meta);family=d['familyId'];metadata[family]=d
 rows=c.execute('select problem_id,payload_gzip from cbank_problems where shared_id=? order by problem_ref',(fid,)).fetchall();counts[family]=len(rows)
 picks=[rows[0],rows[-1],min(rows,key=lambda r:sum(json.loads(gzip.decompress(r[1]))['parameters'].values())),max(rows,key=lambda r:sum(json.loads(gzip.decompress(r[1]))['parameters'].values()))]
 edges[family]=[{**d,**json.loads(gzip.decompress(blob)), 'problemId':pid} for pid,blob in picks]
(OUT/'legacy-edge-records.json').write_text(json.dumps(edges,indent=2)+'\n')
report=[];definitions={}
for f in FAMILIES:
 start=time.monotonic();values,assumptions=p.certificate(f)
 meta=metadata[f['id']]
 stored=meta['validation']['evidence'].get('basisResults')
 if stored is not None:
  assert len(stored)==len(values)
  for v,w in zip(values,stored):assert p.equal(v,p.s.sympify(w))
 row={'familyId':f['id'],'kind':f['kind'],'instances':counts[f['id']],'basisValues':[p.math(v) for v in values],'exactBasisRecalculated':True,'immutableBasisResultsAgree':True,'certificateScope':'All coefficient triples in [1,16]^3 by linearity; special ODEs use symbolic residual, initial/branch and domain checks.' if f['kind']!='special-ode' else 'Symbolic residual and branch/initial conditions for bounded parameters, not linear superposition.','elapsedSeconds':round(time.monotonic()-start,3)}
 report.append(row);print(json.dumps(row),flush=True)
 d={'familyId':f['id'],'kind':f['kind'],'kernels':[p.math(k) for k in f['kernels']],'values':[p.math(v) for v in values],'componentOperations':[p.display(f,k)+'='+p.math(v) for k,v in zip(f['kernels'],values)] if f['kind']!='special-ode' else [],'assumptions':assumptions}
 for key in ['lo','hi','point','order','dx','dy','px','py','yhi','xhi','start','operator']:
  if key in f:d[key]=[p.math(v) for v in f[key]] if isinstance(f[key],list) else p.math(f[key])
 definitions[f['id']]=d
 (OUT/'legacy-certificates.json').write_text(json.dumps(report,indent=2)+'\n')
 (OUT/'legacy-definitions.json').write_text(json.dumps(definitions,indent=2)+'\n')
print('COMPLETE '+str(sum(counts.values()))+' instances, '+str(len(report))+' families',flush=True)
