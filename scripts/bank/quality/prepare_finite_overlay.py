"""Join a separately reviewed finite overlay without changing prior stage files."""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
from .finite_runtime import build
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return list(map(json.loads,p.read_text().splitlines()))
def main(previous_stage,output,route,raw_path,peer_path):
 stage,out,raw_path,peer_path=map(Path,[previous_stage,output,raw_path,peer_path]);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve previous stage')
 base=lines(stage/'canonical-previews.jsonl');retained=lines(stage/'retained-originals.jsonl')
 current={r['problemId']:r for r in base+retained};entries=json.loads((stage/'admission-previews.json').read_text())
 byid={r['problemId']:entries[r['provenance']['authoring']['reviewId']]for r in base}
 peer=json.loads(peer_path.read_text());assert peer['inputSha256']==sha(raw_path)
 checked={r['rawSha256']:r for r in peer['records']};results=[];replacements=[]
 for raw in lines(raw_path):
  h=hashlib.sha256(canonical(raw).encode()).hexdigest();assert checked[h]['passed']
  index=raw['instanceIndex'];family=raw['familyId'];old=current[raw['sourcePreview']['problemId']]
  assert old['contentHash']==raw['sourcePreview']['sourceContentHash'] and old['semanticHash']==raw['sourcePreview']['semanticHash']
  assert canonical(raw)==canonical(build(route,family,index))
  previous_entry=byid.get(old['problemId'])
  if previous_entry:
   review=copy.deepcopy(previous_entry['review'])
   prior_reports=copy.deepcopy(previous_entry.get('supplementalReports',[]))+[{'path':review['report'],'sha256':review['reportSha256'],'purpose':'Preserve the prior independently reviewed complete task derivation and finite-domain review.'}]
  else:
   assert checked[h].get('completeTaskReviewed') or route=='limits-recurrence-options','Retained source needs a complete independent derivation'
   review={'status':'independently-reviewed','author':peer.get('author','finite-content-author'),'reviewer':'root-independent-owner',
    'centralDecision':raw['review'].get('centralDecision',raw['review']['easiestOptionsVisibleRoute']),
    'nearestNeighbor':'Same reviewed mathematical task and historical exposure; this amendment adds no idea.',
    'easiestOptionsVisibleRoute':raw['review']['easiestOptionsVisibleRoute'],
    'difficultyRationale':raw['review'].get('difficultyRationale',raw['review']['easiestOptionsVisibleRoute']),
    'relatedIdeaGroupId':raw['review'].get('relatedIdeaGroupId',old['pedagogy']['relatedIdeaGroupId']),
    'normalizedLineageKey':raw['review'].get('normalizedLineageKey',old['problemId'])}
   prior_reports=[]
  review.update({'report':str(peer_path.resolve().relative_to(ROOT)),'reportSha256':sha(peer_path),
   'easiestOptionsVisibleRoute':raw['review'].get('easiestOptionsVisibleRoute',review['easiestOptionsVisibleRoute']),
   'difficulty':raw['difficulty'],'qualifiedOlympiad':raw['difficulty']=='olympiad',
   'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64})
  review['difficultyRationale']=raw['review'].get('difficultyRationale',review['easiestOptionsVisibleRoute'])
  rid='quality-review:'+route+':'+family+':'+str(index)
  e={'reviewId':rid,'module':route,'familyId':family,'index':index,'rawSha256':h,
   'verifier':'independent-literal-finite-derivation-and-all-choice-pair-inequalities-v1',
   'finiteDomain':{'indices':raw['finiteInstanceIndices']},'review':review,'supplementalReports':prior_reports}
  if previous_entry and previous_entry.get('previous'):e['previous']=copy.deepcopy(previous_entry['previous'])
  if not previous_entry:
   e['previous']={'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':False}
  if raw.get('previous'):
   if e.get('previous'):assert e['previous']==raw['previous']
   else:e['previous']=copy.deepcopy(raw['previous'])
  if e.get('previous',{}).get('meaningChanged'):assert e['review'].get('semanticChangeReason')
  record=normalize(raw,e)
  if previous_entry:entries.pop(previous_entry['reviewId'])
  entries[rid]=e;results.append(record)
  replacements.append({'oldPreviewProblemId':old['problemId'],'problemId':record['problemId'],'revision':record['problemRevision'],
   'rawSha256':h,'canonicalConstruction':old['pedagogy']['constructionId'],'normalizedTaskKey':review['normalizedLineageKey'],
   'relatedIdeaGroupId':review['relatedIdeaGroupId'],'recommendedDifficulty':record['difficulty'],'sameMathematicalTask':True})
 replaced={r['oldPreviewProblemId']for r in replacements};records=[r for r in base if r['problemId']not in replaced]+results
 retained=[r for r in retained if r['problemId']not in replaced]
 effective=records+retained;assert len({r['problemId']for r in effective})==len(current)==len(effective)
 for name,rows in [('canonical-previews',records),('retained-originals',retained)]:
  (out/(name+'.jsonl')).write_text(''.join(canonical(r)+'\n'for r in rows))
 (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
 (out/'replacement-joins.json').write_text(json.dumps(replacements,indent=2)+'\n')
 (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k]for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n'for r in effective))
 report={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),
  'overlayRecords':len(results),'route':route,'independentPeerSha256':sha(peer_path),'pending':'Final served-option dispositions, classification and source admission.','imported':0,'active':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(*sys.argv[1:])
