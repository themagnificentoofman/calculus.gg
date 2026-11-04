"""Build private canonical previews; never registers or approves their admission.

Source-bound peer rows and family routes must match every raw item. The option
screen runs against these final stable IDs before the real review registry can
be updated. Its eventual report digest changes content hashes, not IDs/choices.
"""
from pathlib import Path
import hashlib,json,sys
from .contract import canonical,normalize,ROOT
BASE=ROOT/'scripts/bank/quality/series/bundles'
DOC=ROOT/'docs/bank/problem-quality/series'
INPUTS=[('series-advanced','advanced','advanced-candidates.jsonl'),('series-capacity','capacity','capacity-candidates.jsonl'),('series-hankel','hankel','hankel-candidates.jsonl'),('series-revisions','existing','revision-candidates.jsonl'),('series-lower','existing','lower-extensions.jsonl')]
def file_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw_hash(p):return hashlib.sha256(canonical(p).encode()).hexdigest()
def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve previous preview batches')
 report_path=DOC/'series-peer-final.json';report=json.loads(report_path.read_text());routes={r['familyId']:r for r in json.loads((DOC/'series-review-route-map.json').read_text())['families']}
 peer={r['rawHash']:(r,report_path) for r in report['records']}
 lower_path=DOC/'series-lower-peer-final.json'
 if lower_path.exists():
  lower=json.loads(lower_path.read_text());routes.update({r['familyId']:r for r in lower['families']})
  peer.update({r['rawHash']:(r,lower_path) for r in lower['records'] if r.get('mathematicsPassed')is True and not r.get('presentationBlocker')})
 entries={};records=[];failures=[];unreviewed=[]
 for module,folder,name in INPUTS:
  for raw in map(json.loads,(BASE/folder/name).read_text().splitlines()):
   sha=raw_hash(raw);binding=peer.get(sha)
   if not binding:unreviewed.append({'module':module,'familyId':raw['familyId'],'index':raw['instanceIndex'],'rawSha256':sha});continue
   reviewed,path=binding;route=routes[raw['familyId']];fid=raw['familyId'];index=raw['instanceIndex'];rid='quality-review:'+module+':'+fid+':'+str(index)
   assert reviewed['contentHash']==raw['contentHash'] and reviewed['familyId']==fid and reviewed['instanceIndex']==index
   if route.get('coveredRawHashes'):assert sha in route['coveredRawHashes']
   entry={'reviewId':rid,'module':module,'familyId':fid,'index':index,'rawSha256':sha,'verifier':'isolated-finite-reconstruction-and-independent-peer-v1','finiteDomain':{'indices':raw['finiteInstanceIndices']},'review':{'status':'independently-reviewed','author':'source_research','reviewer':'integration_research-independent-peer','report':str(path.relative_to(ROOT)),'reportSha256':file_hash(path),'centralDecision':reviewed.get('centralDecision',route['easiestOptionsVisibleRoute']),'nearestNeighbor':route['nearestNeighbor'],'easiestOptionsVisibleRoute':route['easiestOptionsVisibleRoute'],'difficultyRationale':route['difficultyRationale'],'difficulty':reviewed['recommendedDifficulty'],'qualifiedOlympiad':reviewed.get('qualifiedOlympiad',False),'relatedIdeaGroupId':reviewed['relatedIdeaGroupId'],'normalizedLineageKey':reviewed['normalizedLineageKey'],'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64}}
   if raw.get('revisionOf'):
    prior=raw['revisionOf'];entry['previous']={'problemId':prior['problemId'],'revision':prior['problemRevision'],'sourceContentHash':prior['sourceContentHash'],'semanticHash':raw['lineage']['ancestorSemanticHash'],'meaningChanged':False}
   try:
    record=normalize(raw,entry);records.append(record);entries[rid]=entry
   except Exception as e:failures.append({'module':module,'familyId':fid,'index':index,'rawSha256':sha,'error':str(e)})
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records))
 (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
 summary={'status':'private-previews-not-admitted','records':len(records),'failures':failures,'unreviewed':unreviewed,'registryChanged':False,'imported':0,'active':0,'note':'Source mathematics/editorial bindings checked. Final canonical-ID option audit, actual isolated reconstruction of every item, and explicit registry binding remain required.'}
 (out/'report.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'records':len(records),'failures':len(failures),'unreviewed':len(unreviewed),'admitted':0}))
if __name__=='__main__':main(sys.argv[1])
