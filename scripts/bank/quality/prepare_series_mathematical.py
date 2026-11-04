"""Apply the 162 exact mathematical option patches and 13 honest demotions."""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
from .series import mathematical_runtime as runtime
P=ROOT/'scripts/bank/quality/series/mathematical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readlines(p):return list(map(json.loads,p.read_text().splitlines()))
def main(previous_stage,output):
 stage,out=Path(previous_stage),Path(output);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier preview stage')
 base=readlines(stage/'canonical-previews.jsonl');full={r['problemId']:r for r in readlines(P/'full-source-records.jsonl')}
 entries=json.loads((stage/'admission-previews.json').read_text())
 byid={r['problemId']:entries[r['provenance']['authoring']['reviewId']]for r in base}
 for r in base:assert canonical(r)==canonical(full[r['problemId']])
 joins=json.loads((P/'source-joins.json').read_text());results=[];replacements=[];failures=[]
 for j in joins:
  fid,i,local=j['familyId'],j['instanceIndex'],j['route'];raw=runtime.build(local,fid,i)
  old=full[j['sourcePreview']['problemId']];prior=byid.get(old['problemId'])
  route='series-mathematical-'+local;rid='quality-review:'+route+':'+fid+':'+str(i)
  evidence=P/j['independentReview']['path'];assert sha(evidence)==j['independentReview']['sha256']
  review=copy.deepcopy(prior['review'])if prior else {
   'status':'independently-reviewed','author':'source_research','reviewer':'root-and-integration-independent-review',
   'centralDecision':old['pedagogy']['difficultyRationale'],
   'nearestNeighbor':'Same independently reviewed series construction and exposure lineage; option repair adds no new idea.',
   'easiestOptionsVisibleRoute':old['pedagogy']['difficultyRationale'],'difficultyRationale':old['pedagogy']['difficultyRationale'],
   'relatedIdeaGroupId':old['pedagogy']['relatedIdeaGroupId']}
  review.update({'report':str(evidence.relative_to(ROOT)),'reportSha256':sha(evidence),
   'difficulty':j['reviewedDifficulty'],'qualifiedOlympiad':j['qualifiedOlympiad'],
   'normalizedLineageKey':j['normalizedLineageKey'],
   'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64})
  if raw.get('reviewedDifficultyChange'):
   reason=raw['reviewedDifficultyChange']['reason'];review.update({'easiestOptionsVisibleRoute':reason,'difficultyRationale':reason})
  e={'reviewId':rid,'module':route,'familyId':fid,'index':i,'rawSha256':hashlib.sha256(canonical(raw).encode()).hexdigest(),
   'verifier':'frozen-patch-reconstruction-and-independent-literal-choice-inequalities-v1',
   'finiteDomain':{'indices':raw['finiteInstanceIndices']},'review':review,
   'supplementalReports':[{'path':str((P/f).relative_to(ROOT)),'sha256':sha(P/f),'purpose':purpose}for f,purpose in[
    ('source-joins.json','Exact patch, independent proof, prior identity and normalized task joins.'),
    ('source-presentations.json','Capture the current exact-source statement and worked solution into the new revision.'),
    ('difficulty-changes.json','Independent per-index options-visible classifications and shortcut certificates.'),
   ]]}
  if raw.get('previous'):
   e['previous']=raw['previous']
   if prior and prior.get('previous'):assert all(v==prior['previous'].get(k)for k,v in e['previous'].items())
  try:
   r=normalize(raw,e);entries[rid]=e;results.append(r)
   if prior:entries.pop(prior['reviewId'])
   replacements.append({'oldPreviewProblemId':old['problemId'],'problemId':r['problemId'],'problemRevision':r['problemRevision'],
    'rawSha256':e['rawSha256'],'canonicalConstruction':old['pedagogy']['constructionId'],'normalizedLineageKey':j['normalizedLineageKey'],
    'difficulty':r['difficulty'],'qualifiedOlympiad':j['qualifiedOlympiad'],'presentationInherited':True,'sameMathematicalTask':True})
  except Exception as error:failures.append({'reviewId':rid,'error':str(error)})
 replaced={r['oldPreviewProblemId']for r in replacements};baseids={r['problemId']for r in base}
 records=[r for r in base if r['problemId']not in replaced]+results
 retained=[r for pid,r in full.items()if pid not in baseids|replaced];effective=retained+records
 assert len({r['problemId']for r in effective})==len(effective)
 for name,rows in [('canonical-previews',records),('retained-originals',retained)]:
  (out/(name+'.jsonl')).write_text(''.join(canonical(r)+'\n'for r in rows))
 (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
 (out/'replacement-joins.json').write_text(json.dumps(replacements,indent=2)+'\n')
 (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k]for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n'for r in effective))
 report={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),'optionOverlays':len(results),
  'failures':failures,'pending':'Final destination-ID option screen, current-presentation check, central admission and full release gates.','imported':0,'active':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({**report,'failures':len(failures)}))
 assert not failures and len(results)==162 and len(effective)==705
if __name__=='__main__':main(*sys.argv[1:])
