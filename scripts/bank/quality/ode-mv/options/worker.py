from pathlib import Path
import json,hashlib,sys,traceback
P=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'copy-manifest.json').read_text())
for f,q in manifest['copiedFiles'].items():assert digest(P/f)==q['sha256'],f
for f,h in manifest['createdAssets'].items():assert digest(P/f)==h,f
sys.path.insert(0,str(P/'sources'));import ode_mv_option_repairs as author
expected={(r['familyId'],r['instanceIndex']):r for r in map(json.loads,(P/'frozen/candidates.jsonl').read_text().splitlines())}
joins={(r['familyId'],r['index']):r for r in json.loads((P/'source-joins.json').read_text())}
for line in sys.stdin:
 try:
  q=json.loads(line);key=(q['family'],q['index']);assert type(q['index'])is int and key in expected
  row=author.build(*key);assert canonical(row)==canonical(expected[key]);assert hashlib.sha256(canonical(row).encode()).hexdigest()==joins[key]['rawSha256'];assert author.verify(row)is True
  print(canonical({'record':row,'verified':True}),flush=True)
 except Exception as exc:print(canonical({'error':type(exc).__name__+': '+str(exc)}),flush=True)
