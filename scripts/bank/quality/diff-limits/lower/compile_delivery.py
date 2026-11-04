"""Compile exactly enumerated finite data and guard its portable runtime."""
from pathlib import Path
import sys,json,hashlib,copy
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE))
import generate,replacements,old_revisions
rows=[]
for name in ['extensions','replacements','old-revisions']:
 errors=BASE/(name+'-errors.json')
 if errors.exists():assert not json.loads(errors.read_text()),name
 rows+=json.loads((BASE/(name+'-candidates.json')).read_text())
catalog=generate.catalog()+replacements.catalog()+old_revisions.catalog()
assert len(rows)==sum(f['instanceCount'] for f in catalog)
assert len({(r['familyId'],r.get('problemId',r['parameters']['instance'])) for r in rows})==len(rows)
(BASE/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
(BASE/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
# Source-bound selected reconstruction of every constructor; all finite
# mathematical assertions were already executed by generation.
selected=[]
for f in catalog:
 if f.get('kind')=='immutable-revision':
  r=next(r for r in rows if r.get('problemId')==f['finiteDomain'][0]['problemId']);mod=old_revisions
 else:
  r=next(r for r in rows if r['familyId']==f['familyId'] and r['parameters']['instance']==0)
  mod=replacements if f['familyId'].startswith('q2-repair-') else generate
 assert mod.verify(r);selected.append({'familyId':f['familyId'],'instance':r['parameters']['instance'],'verified':True})
(BASE/'constructor-reproduction.json').write_text(json.dumps(selected,indent=2))
files=[p for p in BASE.rglob('*') if p.is_file() and (p.suffix=='.py' or p.name in ['admission.json','original-records.json','original-reviewed-presentation.json','parent-existing-review.json','candidates.json','catalog.json','constructor-reproduction.json']) and '__pycache__' not in str(p)]
manifest={'records':len(rows),'newItems':184,'immutableRevisions':len(rows)-184,'families':len(catalog),'finiteMathStatus':'All generated finite constructor and independent intermediate checks passed; no human or formal-proof claim.','selectedSourceReconstructions':len(selected),'files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
(BASE/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k!='files'}))
