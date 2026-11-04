"""Join the reviewed integration identities without counting scalar copies twice."""
from pathlib import Path
import collections,hashlib,json,sys
from .contract import ROOT,canonical
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return list(map(json.loads,p.read_text().splitlines()))
def main(stage,output):
 stage,out=Path(stage),Path(output)
 if out.exists():raise ValueError('Preserve prior group map')
 doc=ROOT/'docs/bank/problem-quality/integration'
 peer=json.loads((doc/'integration-peer-review.json').read_text())
 old={r['problemId']:r for r in peer['records']}
 normal={r['problemId']:r for r in json.loads((doc/'integration-normalized-capacity.json').read_text())['records']}
 entries=json.loads((stage/'admission-previews.json').read_text())
 records=lines(stage/'canonical-previews.jsonl')+lines(stage/'retained-originals.jsonl')
 result=[];groups=collections.defaultdict(set);raw_counts=collections.Counter()
 for r in records:
  e=entries.get(r.get('provenance',{}).get('authoring',{}).get('reviewId'))
  meta=r['pedagogy'];historical=old.get(r['problemId']);qualified=r['difficulty']=='olympiad'
  if e:
   review=e['review'];assert review['difficulty']==r['difficulty'] and review['qualifiedOlympiad']==qualified
   group=review['relatedIdeaGroupId'];key=review['normalizedLineageKey'];decision=review['centralDecision']
   proof={'path':review['report'],'sha256':review['reportSha256']}
   assert sha(ROOT/proof['path'])==proof['sha256']
  elif qualified:
   assert historical and historical['olympiadMethodQualified'] and historical['difficultyRecommended']=='olympiad'
   group=historical['reviewedGroup'];key=normal[r['problemId']]['equivalenceKey'];decision=historical['easiestVisibleRoute']
   proof={'path':str((doc/'integration-peer-review.json').relative_to(ROOT)),'sha256':sha(doc/'integration-peer-review.json')}
  else:
   group=meta['relatedIdeaGroupId'];key=r['problemId'];decision=meta['difficultyRationale']
   proof={'path':str((doc/'final-option-review-v5.json').relative_to(ROOT)),'sha256':sha(doc/'final-option-review-v5.json'),
          'scope':'Unchanged retained lower-level source; frozen finite mathematics and current presentation review are preserved. No new advanced idea or instance normalization is inferred from the option screen.'}
  result.append({'problemId':r['problemId'],'revision':r['problemRevision'],'contentHash':r['contentHash'],
   'semanticHash':r['semanticHash'],'familyId':r['familyId'],'canonicalConstruction':meta['constructionId'],
   'relatedIdeaGroupId':group,'structuralSignature':meta['structuralSignature'],'primaryTechnique':meta['primaryTechnique'],
   'centralDecision':decision,'normalizedTaskKey':key,'qualifiedOlympiad':qualified,'recommendedDifficulty':r['difficulty'],
   'independentEvidence':proof,'previous':e.get('previous')if e else None})
  raw_counts[r['difficulty']]+=1
  if qualified:groups[group].add(key)
 assert len(result)==766 and len(groups)==30 and sum(map(len,groups.values()))==244
 files=[stage/'canonical-previews.jsonl',stage/'retained-originals.jsonl',stage/'admission-previews.json',doc/'integration-peer-review.json',doc/'integration-normalized-capacity.json',Path(__file__)]
 out.write_text(json.dumps({'status':'source-bound-reviewed-integration-group-map','records':result,
  'inputs':{str(p.resolve()):sha(p)for p in files},'rawCounts':dict(raw_counts),'qualifiedOlympiadGroups':len(groups),
  'normalizedOlympiadInstances':sum(map(len,groups.values())),
  'scope':'Joins exact published-source reviews and independently checked candidate review plans. No new group or capacity credit for an option repair. Cross-topic related-idea reconciliation and real selector horizon remain separate gates.'},indent=2)+'\n')
 print(json.dumps({'records':len(result),'rawCounts':dict(raw_counts),'advancedGroups':len(groups),'advancedNormalized':sum(map(len,groups.values()))}))
if __name__=='__main__':main(*sys.argv[1:])
