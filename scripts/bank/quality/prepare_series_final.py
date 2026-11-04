"""Final-ID private staging with the independently repaired negative-binomial pool."""
from pathlib import Path
import hashlib,json,sys
from .contract import ROOT,canonical,normalize
from .series.options.runtime import build
from .prepare_series import INPUTS,BASE

def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve previous stage')
 source=ROOT/'.bank-data/quality/series-previews-v3';entries=json.loads((source/'admission-previews.json').read_text());originals=[json.loads(x) for x in (source/'canonical-previews.jsonl').read_text().splitlines()];raw={}
 for module,folder,name in INPUTS:
  for r in map(json.loads,(BASE/folder/name).read_text().splitlines()):raw[(module,r['familyId'],r['instanceIndex'])]=r
 selected={rid:e for rid,e in entries.items() if e['familyId']!='m3-series-medium-negative-binomial'}
 report=ROOT/'scripts/bank/quality/series/options/negative-binomial-option-peer-review.json'
 for i in range(10):
  r=build('m3-series-medium-negative-binomial',i);module='series-options';rid='quality-review:'+module+':'+r['familyId']+':'+str(i);raw[(module,r['familyId'],i)]=r
  route='Recognize the triple geometric-convolution coefficient or differentiate the geometric sum twice; evaluate at the stated ratio. Comparable misconception fractions include a competing rational cube. Medium.'
  e={'reviewId':rid,'module':module,'familyId':r['familyId'],'index':i,'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'verifier':'guarded-source-reconstruction-and-independent-exact-option-review-v2','finiteDomain':{'indices':list(range(10))},'review':{'status':'independently-reviewed','author':'integration_research','reviewer':'source_research-independent-peer','report':str(report.relative_to(ROOT)),'reportSha256':hashlib.sha256(report.read_bytes()).hexdigest(),'centralDecision':route,'nearestNeighbor':'Negative-binomial coefficient counts triple convolution; it is distinct from a single geometric tail or a quadratic weighted sum without this combinatorial interpretation.','easiestOptionsVisibleRoute':route,'difficultyRationale':route,'difficulty':'medium','qualifiedOlympiad':False,'relatedIdeaGroupId':r['pedagogy']['relatedIdeaGroupId'],'normalizedLineageKey':r['lineage']['normalizedLineageKey'],'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64}}
  if r.get('previous'):e['previous']=r['previous']
  selected[rid]=e
 records=[];errors=[]
 for rid,e in selected.items():
  try:records.append(normalize(raw[(e['module'],e['familyId'],e['index'])],e))
  except Exception as ex:errors.append({'reviewId':rid,'error':str(ex)})
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(out/'admission-previews.json').write_text(json.dumps(selected,indent=2)+'\n')
 prior_ids={r['problemId'] for r in originals};effective=[json.loads(x) for x in (source/'effective-option-input.jsonl').read_text().splitlines()];effective=[r for r in effective if r['problemId'] not in prior_ids and r['familyId']!='m3-series-medium-negative-binomial']+records
 assert len({r['problemId'] for r in effective})==len(effective)
 projected=[{k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']} for r in effective]
 (out/'effective-option-input.jsonl').write_text(''.join(canonical(r)+'\n' for r in projected));(out/'report.json').write_text(json.dumps({'status':'private-not-admitted','records':len(records),'effectiveSeriesRecords':len(effective),'errors':errors,'newImmutableOptionRevisions':8,'repairedUnpublishedExtensions':2,'imported':0,'active':0},indent=2)+'\n');print(len(records),'private candidates;',len(effective),'effective records;',len(errors),'errors')
if __name__=='__main__':main(sys.argv[1])
