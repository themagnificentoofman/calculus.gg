"""Portable verification of original-source descriptor and qualification joins."""
from pathlib import Path
from collections import Counter
import hashlib,json
P=Path(__file__).resolve().parent
def read(name):return json.loads((P/name).read_text())
def lines(name):return [json.loads(x)for x in(P/name).read_text().splitlines()]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read('artifact-manifest.json')
for name,h in manifest['files'].items():assert sha(P/name)==h,name
for r in read('evidence-source-bindings.json')['files']:assert sha(P/r['localPath'])==r['sha256']
base=read('descriptor-map.json');original={r['problemId']:r for r in lines('original-published-rows.jsonl')};assert len(original)==len(base['records'])==768
assert base['originalPublishedSubsetSha256']==sha(P/'original-published-rows.jsonl')
final={r['problemId']:r for r in read('final-lineage-extract.json')['records']};mv={r['problemId']:r for r in read('evidence/original-multivariable-peer.json')['results']};ode={r['problemId']:r for r in read('evidence/original-ode-route-peer.json')['records']};normal={r['problemId']:r for r in read('evidence/retained-normalization.json')['records']}
for table in[mv,ode,normal]:
 for pid,r in table.items():assert original[pid]['contentHash']==r['sourceContentHash']
for r in base['records']:
 old=original[r['problemId']];assert r['sourceRawSha256']==digest(old)and r['sourceContentHash']==old['contentHash'];assert r['publishedDifficulty']==old['difficulty'];assert r['publishedLiteralChoicesHash']==digest(old['choices'])
 f=final[r['finalLineage']['problemId']];same=old['semanticHash']==f['semanticHash'];assert same==r['finalLineage']['sameSemanticTask'];assert not r['finalLineage']['qualificationInheritedFromFinalMenu'];assert r['newIndependentIdeaCredit']==0
 if same:assert r['normalizedTaskKey']==f['normalizedTaskKey']
 else:assert r['normalizedTaskKey']=='original-published-task:'+old['problemId']
 if r['qualifiedOlympiad']:
  assert r['publishedDifficulty']=='olympiad' and not r['knownOriginalMenuFindings']
  if r['problemId']in mv:assert mv[r['problemId']]['qualifiedOlympiad']
  else:assert ode[r['problemId']]['proposedDifficulty']=='olympiad'
 if r['publishedDifficulty']=='olympiad':assert r['reviewedDifficulty']in['hard','olympiad']
checks=read('unchanged-menu-revision-bindings.json')['records'];assert len(checks)==168
for c in checks:
 old=original[c['problemId']];rs=lines('evidence/'+Path(c['revisionFile']).name);r=rs[c['recordIndex']];assert digest(r)==c['revisionRawSha256'];assert r['admission']['previous']['contentHash']==old['contentHash'];assert r['choices']==old['choices']and r['answerChoiceId']==old['answerChoiceId']
qualified=[r for r in base['records']if r['qualifiedOlympiad']]
assert len(qualified)==85
assert len({r['normalizedTaskKey']for r in qualified})==74
assert len({r['relatedIdeaGroupId']for r in qualified})==11
assert sum(r['finalLineage']['sameSemanticTask']for r in base['records'])==736
assert sum(bool(r['knownOriginalMenuFindings'])for r in base['records'])==3
print(json.dumps({'status':'passed','originalRecords':768,'exactOriginalPeerRows':144,'exactOriginalNormalizationRows':144,'unchangedOriginalMenuRevisions':168,'effectiveQualifiedRecords':85,'qualifiedNormalizedItems':74,'qualifiedIdeaGroups':11,'semanticChangedLowerOriginalsWithoutBackTransfer':32}))
