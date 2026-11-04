"""Verify portable final snapshots and review joins without private stage access."""
from pathlib import Path
from collections import Counter
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
def read(p):return json.loads(p.read_text())
manifest=read(P/'artifact-manifest.json')
for name,h in manifest['files'].items():assert sha(P/name)==h,('file hash',name)
canonicalRows=lines(P/'sources/canonical-previews.jsonl');retained=lines(P/'sources/retained-originals.jsonl');assert len(canonicalRows)==1150 and len(retained)==381
rows=canonicalRows+retained;byid={r['problemId']:r for r in rows};assert len(rows)==len(byid)==1531
served=lines(P/'served-records.jsonl');servedById={r['problemId']:r for r in served};assert set(servedById)==set(byid)
gm=read(P/'group-map.json');maps={r['problemId']:r for r in gm['records']};assert set(maps)==set(byid) and not gm['unresolved']
for pid,r in byid.items():
 m=maps[pid];p=servedById[pid];assert m['sourceCanonicalRawHash']==digest(r);assert m['servedRawHash']==digest(p);assert m['servedChoiceMenuHash']==digest(p['choices'])
 assert all(m[k]==r[q]for k,q in [('revision','problemRevision'),('contentHash','contentHash'),('semanticHash','semanticHash'),('recommendedDifficulty','difficulty')]);assert m['newIndependentIdeas']==0
for topic,levels in gm['capacity'].items():
 for level,want in levels.items():
  rs=[r for r in maps.values()if r['topic']==topic and r['recommendedDifficulty']==level];unique={r['normalizedTaskKey']:r for r in rs};families=Counter(r['canonicalConstruction']for r in unique.values());cap=20 if level=='olympiad' else 10
  assert want['records']==len(rs)and want['normalizedItems']==len(unique)and want['capEffective']==sum(min(n,cap)for n in families.values())
  assert want['qualifiedIdeas']==len({r['relatedIdeaGroupId']for r in rs if r['qualifiedOlympiad']})
render=read(P/'render.json');assert render['status']=='passed'and not render['failures']and render['records']==1531
assert render['expressions']==sum(1+len(r['choices'])+len(r['solutionSteps'])for r in served)==15877
assert render['servedInputSha256']==sha(P/'served-records.jsonl')
for name,inp in [('raw-option-audit.json','raw-options.jsonl'),('served-option-audit.json','served-options.jsonl')]:
 a=read(P/name);assert a['records']==1531 and a['artifactSha256']==sha(P/inp);assert len(a['families'])==151 and sum(bool(v['flags'])for v in a['families'].values())==24
 assert all(not v['flags']for v in a['answerForms'].values())
dispositions=read(P/'family-form-dispositions.json');assert len(dispositions['families'])==151 and not dispositions['requiredActions'];assert dispositions['counts']['flaggedFamilies']==24
joins=read(P/'destination-joins.json')['records'];assert len(joins)==26 and len({r['problemId']for r in joins})==26
entries=read(P/'sources/admission-previews.json');source=read(P/'late-overlay/source-joins.json')['records'];sourceByRaw={r['rawSha256']:r for r in source};reviews=read(P/'late-overlay/review-manifest.json');assert reviews['counts']=={'records':26,'independentlyReviewed':26,'pending':0}
for j in joins:
 r=byid[j['problemId']];assert j['canonicalRawHash']==digest(r);assert j['revision']==r['problemRevision'];e=entries[j['reviewId']];assert e['rawSha256']==j['rawSha256']
 s=sourceByRaw[j['rawSha256']];raw=lines(P/'late-overlay'/s['sourceFile'])[s['sourceRecordIndex']];assert digest(raw)==j['rawSha256']
 old=next(r for r in lines(P/'late-overlay'/s['constructorFolder']/'source-records.jsonl')if r['problemId']==j['oldProblemId']);assert digest(old)==j['oldCanonicalRawHash'];assert old['contentHash']==j['oldContentHash']
 peer=j['independentReview'];f=P/'independent'/Path(peer['path']).name;assert sha(f)==peer['fileSha256'];q=read(f)['records'][peer['recordIndex']];assert q['passed']and q['rawSha256']==j['rawSha256']
 assert j['normalizedTaskKey']==maps[j['problemId']]['normalizedTaskKey']and j['newIndependentIdeas']==0
scalar=read(P/'scalar97-final-joins.json');assert scalar['counts']=={'records':97,'unchangedMenus':80,'repairedMenus':17,'unresolved':0}
for r in scalar['records']:assert r['passed']and r['pairDistinctions']==r['oppositeSumChecks']==6 and r['canonicalRawHash']==digest(byid[r['problemId']])
print(json.dumps({'status':'passed','files':len(manifest['files']),'records':1531,'exactLatePeerJoins':26,'scalarDispositions':97,'strictRenderedExpressions':15877,'flaggedFamiliesWithExplicitDispositions':24}))
