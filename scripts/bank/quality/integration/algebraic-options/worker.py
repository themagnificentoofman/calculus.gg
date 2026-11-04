from pathlib import Path
import json,hashlib,sys
P=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'copy-manifest.json').read_text())
for f,q in manifest['copiedFiles'].items():assert digest(P/f)==q['sha256'],f
for f,h in manifest['createdAssets'].items():assert digest(P/f)==h,f
for f,h in manifest.get('runtimeFiles',{}).items():assert digest(P/f)==h,f
sys.path.insert(0,str(P/'sources'));import options,odd_even_addendum
modules={'main55':options,'odd-even3':odd_even_addendum}
rows={q['rawHash']:q for q in json.loads((P/'source-joins.json').read_text())}
expected={}
for r in map(json.loads,(P/'sources/combined-candidates.jsonl').read_text().splitlines()):
 h=hashlib.sha256(canonical(r).encode()).hexdigest();q=rows[h];key=q['route'],r['familyId'],r['instanceIndex'];assert key not in expected;expected[key]=(r,q)
for line in sys.stdin:
 try:
  q=json.loads(line);key=q['route'],q['family'],q['index'];assert type(q['index'])is int and key in expected
  frozen,join=expected[key];author=modules[q['route']];row=author.build(q['family'],q['index']);assert canonical(row)==canonical(frozen);assert hashlib.sha256(canonical(row).encode()).hexdigest()==join['rawHash'];assert author.verify(row)is True
  print(canonical({'record':row,'verified':True}),flush=True)
 except Exception as exc:print(canonical({'error':type(exc).__name__+': '+str(exc)}),flush=True)
