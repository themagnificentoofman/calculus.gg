"""Join the independent 272 and 97 option repairs to the actual private pool."""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readlines(p):return list(map(json.loads,p.read_text().splitlines()))
def main(previous_stage,output,mode='ordinary'):
 assert mode in ['ordinary','special']
 stage,out=Path(previous_stage),Path(output);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier preview stage')
 base=readlines(stage/'canonical-previews.jsonl');retained=readlines(stage/'retained-originals.jsonl')
 effective={r['problemId']:r for r in retained+base}
 entries=json.loads((stage/'admission-previews.json').read_text())
 byid={r['problemId']:entries[r['provenance']['authoring']['reviewId']]for r in base}
 p=ROOT/('scripts/bank/quality/ode-mv/options'if mode=='ordinary'else'scripts/bank/quality/ode-special');d=ROOT/('scripts/bank/quality/diff-limits'if mode=='ordinary'else'scripts/bank/quality/ode-special')
 joins=json.loads((p/'source-joins.json').read_text())
 if mode=='special':joins=joins['records']
 additional=[r for r in json.loads((d/'source-joins.json').read_text())['records']if r['route']=='ode-mv-additional-options']if mode=='ordinary'else[]
 review_manifest={r['rawSha256']:r for r in json.loads((d/'review-manifest.json').read_text())['records']}
 source_rows=readlines(p/'frozen/candidates.jsonl')+readlines(d/'additional-options/candidates.jsonl')if mode=='ordinary'else readlines(p/'constructors/candidates.jsonl')
 raws={hashlib.sha256(canonical(r).encode()).hexdigest():r for r in source_rows}
 results,failures,replacements=[],[],[]
 for j in joins+additional:
  h=j['rawSha256'];raw=raws[h];prior_id=raw['sourcePreview']['problemId'];old=effective[prior_id]
  assert old['contentHash']==raw['sourcePreview']['sourceContentHash'],prior_id
  assert old['semanticHash']==raw['sourcePreview']['semanticHash'],prior_id
  prior_entry=byid.get(prior_id)
  route=j.get('route','ode-mv-options');rid='quality-review:'+route+':'+j['familyId']+':'+str(j['index'])
  if route=='ode-mv-options':
   evidence=p/j['independentPeerReport'];assert sha(evidence)==j['independentPeerSha256']
   supplement=p/'source-joins.json'
  else:
   rm=review_manifest[h];assert rm['status']=='independently-reviewed'
   evidence=d/rm['evidence']['file'];supplement=d/'review-manifest.json'
  route_description=raw.get('review',{}).get('easiestOptionsVisibleRoute') or (prior_entry['review']['easiestOptionsVisibleRoute']if prior_entry else old['pedagogy']['difficultyRationale'])
  review=copy.deepcopy(prior_entry['review'])if prior_entry else {
   'status':'independently-reviewed','author':'coverage-and-integration-research','reviewer':'root-independent-finite-derivations',
   'nearestNeighbor':'Same independently reviewed construction and exposure lineage; repaired choices add no new mathematical idea.',
   'relatedIdeaGroupId':old['pedagogy']['relatedIdeaGroupId'],'normalizedLineageKey':old['semanticHash'],
   'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64}
  level=j.get('difficulty',old['difficulty'])
  review.update({'report':str(evidence.relative_to(ROOT)),'reportSha256':sha(evidence),
   'centralDecision':route_description,'easiestOptionsVisibleRoute':route_description,'difficultyRationale':route_description,
   'difficulty':level,'qualifiedOlympiad':level=='olympiad'})
  e={'reviewId':rid,'module':route,'familyId':j['familyId'],'index':j['index'],'rawSha256':h,
   'finiteDomain':{'indices':raw['finiteInstanceIndices']},'review':review,
   'verifier':'independent-finite-answer-and-six-literal-outward-rational-inequalities-v1',
   'supplementalReports':[{'path':str(supplement.relative_to(ROOT)),'sha256':sha(supplement),
                          'purpose':'Exact finite source, independent peer and prior identity joins.'}]}
  if raw.get('previous'):
   e['previous']=copy.deepcopy(raw['previous'])
   if prior_entry:
    assert all(v==prior_entry['previous'].get(k)for k,v in e['previous'].items()),prior_id
    e['previous']=copy.deepcopy(prior_entry['previous'])
   if e['previous']['meaningChanged']:
    e['review']['semanticChangeReason']=raw.get('review',{}).get('semanticChangeReason') or prior_entry['review']['semanticChangeReason']
  try:
   record=normalize(raw,e);results.append(record);entries[rid]=e
   if prior_entry:entries.pop(prior_entry['reviewId'])
   replacements.append({'oldPreviewProblemId':prior_id,'problemId':record['problemId'],'problemRevision':record['problemRevision'],
    'rawSha256':h,'canonicalConstruction':old['pedagogy']['constructionId'],'sameMathematicalTask':True,'previous':e.get('previous')})
  except Exception as error:failures.append({'reviewId':rid,'error':str(error)})
 replaced={r['oldPreviewProblemId']for r in replacements};assert len(replaced)==len(replacements)
 records=[r for r in base if r['problemId']not in replaced]+results
 retained=[r for r in retained if r['problemId']not in replaced];effective=retained+records
 assert len({r['problemId']for r in effective})==len(effective)
 for name,rows in [('canonical-previews',records),('retained-originals',retained)]:
  (out/(name+'.jsonl')).write_text(''.join(canonical(r)+'\n'for r in rows))
 (out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n')
 (out/'replacement-joins.json').write_text(json.dumps(replacements,indent=2)+'\n')
 (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k]for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n'for r in effective))
 report={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),
  'optionOverlays':len(results),'failures':failures,'pending':'Final actual-ID family/form review and central admission.'if mode=='special'else'Remaining special-function repairs and final actual-ID family/form review; central admission.','imported':0,'active':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({**report,'failures':len(failures)}))
 assert not failures and len(results)==(369 if mode=='ordinary' else 17) and len(effective)==1531
if __name__=='__main__':main(*sys.argv[1:])
