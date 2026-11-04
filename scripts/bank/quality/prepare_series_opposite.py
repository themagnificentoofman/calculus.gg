"""Replace the exact44 private/source pools and preserve all other destinations."""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
P=ROOT/'scripts/bank/quality/series/opposite'
def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve previous stage')
 registry=json.loads((ROOT/'scripts/bank/quality/reviewed.json').read_text());admitted=list(map(json.loads,(ROOT/'.bank-data/quality/series-admitted.jsonl').read_text().splitlines()));oldbyid={r['problemId']:r for r in admitted};originals={r['problemId']:r for r in map(json.loads,(P/'frozen/source-records.jsonl').read_text().splitlines())};raws=list(map(json.loads,(P/'candidates.jsonl').read_text().splitlines()));report=ROOT/'docs/bank/problem-quality/series/opposite-pair-peer-v1.json'
 entries={r['provenance']['authoring']['reviewId']:copy.deepcopy(registry['items'][r['provenance']['authoring']['reviewId']]) for r in admitted if r['problemId']not in originals};records=[r for r in admitted if r['problemId']not in originals];assert len(records)==427
 replacement=[]
 for raw in raws:
  pid=raw['sourcePreview']['problemId'];source=originals[pid];old=oldbyid.get(pid);index=raw['instanceIndex'];fid=raw['familyId'];rid='quality-review:series-opposite-options:'+fid+':'+str(index)
  if old:review=copy.deepcopy(registry['items'][old['provenance']['authoring']['reviewId']]['review'])
  else:
   route='Evaluate the finite alternating binomial sum by the degree-order finite difference.' if fid.endswith('binomial-alternating-difference') else 'Expand the finite binomial sum as a beta integral and evaluate its integer endpoint parameters.'
   review={'centralDecision':route,'nearestNeighbor':'Existing finite generating-function fluency, with no new independent construction or idea claimed.','easiestOptionsVisibleRoute':route,'difficultyRationale':route+' Hard finite-sum fluency.','difficulty':'hard','qualifiedOlympiad':False,'relatedIdeaGroupId':raw['pedagogy']['relatedIdeaGroupId'],'normalizedLineageKey':'historical:'+pid}
  review.update({'status':'independently-reviewed','author':'source_research','reviewer':'root-independent-literal-option-review','report':str(report.relative_to(ROOT)),'reportSha256':hashlib.sha256(report.read_bytes()).hexdigest(),'optionAuditReport':'PRIVATE-PENDING-UPDATED-COMPLETE-POOL-SCREEN','optionAuditSha256':'0'*64})
  e={'reviewId':rid,'module':'series-opposite-options','familyId':fid,'index':index,'rawSha256':hashlib.sha256(canonical(raw).encode()).hexdigest(),'verifier':'guarded-reconstruction-and-independent-rational-option-enclosures-v1','finiteDomain':{'indices':raw['finiteInstanceIndices']},'review':review}
  if raw.get('previous'):e['previous']=raw['previous']
  record=normalize(raw,e);entries[rid]=e;records.append(record);replacement.append(record)
 prior=list(map(json.loads,(ROOT/'.bank-data/quality/series-previews-v4/effective-option-input.jsonl').read_text().splitlines()));effective=[r for r in prior if r['problemId']not in originals]+[{k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']} for r in replacement]
 assert len(records)==471 and len(effective)==705 and len({r['problemId'] for r in effective})==705
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n');(out/'effective-option-input.jsonl').write_text(''.join(canonical(r)+'\n' for r in effective));(out/'report.json').write_text(json.dumps({'status':'private-not-admitted','records':471,'unchangedEarlierDestinations':427,'repairedPools':44,'baselineRevisionsInPatch':32,'replacedUnpublishedIDs':12,'effectiveSeriesIncludingPilot':705,'imported':0,'active':0},indent=2)+'\n');print('471 private destinations;427 unchanged;44 exact patched pools;705 effective records')
if __name__=='__main__':main(sys.argv[1])
