"""Source-bound private previews of the independently reviewed integral batch.

No registry, import, or activation is performed. Stable destination IDs allow
the complete effective option pools to be screened before admission.
"""
from pathlib import Path
import hashlib,json,sys
from .contract import ROOT,canonical,normalize
P=ROOT/'scripts/bank/quality/integration';D=ROOT/'docs/bank/problem-quality/integration'
def read(p):return json.loads(p.read_text())
def rows(p):return list(map(json.loads,p.read_text().splitlines()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rawsha(r):return hashlib.sha256(canonical(r).encode()).hexdigest()
def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier private stages')
 oldpath=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl'
 assert sha(oldpath)=='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677'
 originals={r['problemId']:r for r in rows(oldpath) if r['topic']=='integration'}
 old_report=D/'integration-peer-review.json';oldreview=read(old_report);oldpeer={r['problemId']:r for r in oldreview['records']};lowerpeer={r['rawSHA256']:r for r in oldreview['lowerRecords']}
 lower_report=D/'integration-lower-delivery-review.json';lower=read(lower_report);capacity=lower['perItemCapacityPlan'];byid={r['problemIdOrPendingKey']:r for r in capacity};byraw={r['sourceRawHash']:r for r in capacity}
 option_report=D/'integration-option-peer-v2.json';optionpeer={r['rawSHA256']:r for r in read(option_report)['records']}
 advanced_report=ROOT/'docs/bank/problem-quality/new-integration-peer-v2.json';advancedpeer={r['rawSha256']:r for r in read(advanced_report)['results']}
 lowerfixpeer={r['rawHash']:r for r in lower['new16AndTwoOverlayReview']['records']}
 repairs=rows(P/'integration-repairs.jsonl');repairfamilies={r['familyId'] for r in repairs}
 batch=[]
 for r in rows(P/'integration-extensions.jsonl'):
  if r['familyId'] not in repairfamilies and not r['familyId'].endswith('accumulation-from-derivative'):batch.append(('integration-extensions',r,r['parameters']['extension']))
 batch += [('integration-repairs',r,r['instanceIndex']) for r in repairs]
 batch += [('integration-options',r,r['instanceIndex']) for r in rows(P/'integration-option-repairs-v2.jsonl')]
 batch += [('integration-historical',r,r['instanceIndex']) for r in rows(P/'historical-candidates.jsonl')]
 batch += [('integration-new',r,r['instanceIndex']) for r in rows(P/'advanced/candidates.jsonl')]
 batch += [('integration-lower-guarded',r,r['parameters'].get('extension',r['parameters'].get('instance'))) for r in rows(ROOT/'scripts/bank/quality/ode-mv/frozen/integration-lower-revisions.jsonl')]
 assert len(batch)==350
 domains={}
 for module,r,i in batch:domains.setdefault((module,r['familyId']),[]).append(i)
 entries={};records=[];failures=[];bindings=[]
 for module,r,i in batch:
  h=rawsha(r);fid=r['familyId'];previous=r.get('previous');nearest='This is a separately checked finite fluency case of the existing construction; no new independent idea is claimed.'
  if module=='integration-new':
   peer=advancedpeer[h];assert peer['passed'] and peer['sixLiteralChoicePairsDistinct'] and peer['contentHash']==r['contentHash'];report=advanced_report;level=peer['difficultyRecommended'];route=peer['easiestOptionsVisibleRoute'];key=peer['normalizedLineageKey'];group=r['pedagogy']['relatedIdeaGroupId'];author='source_research';reviewer='root-independent-review';nearest=r['nearestNeighbor']
  elif module=='integration-options':
   peer=optionpeer[h];assert peer['exactFourChoiceNonEquivalence'] and peer['exactCorrectAnswer'] and previous['sourceContentHash']==peer['sourceContentHash'];report=option_report;level=r['difficulty'];prior=oldpeer[previous['problemId']];route=prior['easiestVisibleRoute']+' Final common-form options independently rechecked; per-index elementary shortcuts determine the stated level.';group=prior['reviewedGroup'];key=byid[previous['problemId']]['normalizedLineageKey'];author='root';reviewer='source_research-independent-peer'
  elif module=='integration-historical':
   peer=oldpeer[previous['problemId']];assert peer['sourceContentHash']==previous['sourceContentHash'] and peer['exactChecks'];report=old_report;level=peer['difficultyRecommended'];route=peer['easiestVisibleRoute'];group=peer['reviewedGroup'];key=byid[previous['problemId']]['normalizedLineageKey'];author='root';reviewer='source_research-independent-peer';nearest='The prior independently reviewed family remains the same mathematical task; this revision changes classification and supplies the already reviewed concrete explanation.'
  elif module=='integration-lower-guarded':
   peer=lowerfixpeer[h];report=lower_report;level=peer['recommendedDifficulty'];route=r.get('review',{}).get('easiestOptionsVisibleRoute',r['pedagogy']['difficultyRationale']);group=r['pedagogy']['relatedIdeaGroupId'];plan=byraw.get(h)
   if plan is None:
    assert fid=='m3-integration-easy-accumulation-from-derivative' and r['review']['presentationOnly']
    plan=byid['new:'+fid+':m:'+str(r['parameters']['m'])]
   key=plan['normalizedLineageKey'];author='root-original-lower';reviewer='integration_research-independent-peer';nearest=r.get('review',{}).get('nearestNeighbor',nearest)
   if r.get('admission',{}).get('previous'):
    p=r['admission']['previous'];previous={'problemId':p['problemId'],'revision':p['problemRevision'],'sourceContentHash':p['contentHash'],'semanticHash':p['semanticHash'],'meaningChanged':p['meaningChanged']}
  else:
   peer=lowerpeer[h];assert peer['mathematicalResult']=='passes independent exact checks' and peer['exactChecks'];report=old_report;level=peer['difficultyRecommended'];route=r['pedagogy']['difficultyRationale']+' '+(' '.join(peer['easiestVisibleRouteNotes']) or 'Independent finite mathematical and literal-choice review confirms this fluency route.');group=r['pedagogy']['relatedIdeaGroupId'];key=byraw[h]['normalizedLineageKey'];author='root';reviewer='source_research-independent-peer'
  rid='quality-review:'+module+':'+fid+':'+str(i)
  e={'reviewId':rid,'module':module,'familyId':fid,'index':i,'rawSha256':h,'verifier':'finite-source-reconstruction-and-independent-integral-review-v1','finiteDomain':{'indices':sorted(domains[(module,fid)])},'review':{'status':'independently-reviewed','author':author,'reviewer':reviewer,'report':str(report.relative_to(ROOT)),'reportSha256':sha(report),'centralDecision':route,'nearestNeighbor':nearest,'easiestOptionsVisibleRoute':route,'difficultyRationale':route,'difficulty':level,'qualifiedOlympiad':level=='olympiad','relatedIdeaGroupId':group,'normalizedLineageKey':key,'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64}}
  if previous:
   e['previous']=previous;assert originals[previous['problemId']]['contentHash']==previous['sourceContentHash']
   if previous.get('meaningChanged'):e['review']['semanticChangeReason']=previous['semanticChangeReason']
  try:
   record=normalize(r,e);records.append(record);entries[rid]=e;bindings.append({'reviewId':rid,'rawSha256':h,'sourceReport':e['review']['report'],'sourceReportSha256':e['review']['reportSha256'],'problemId':record['problemId'],'contentHash':record['contentHash'],'difficulty':level,'normalizedLineageKey':key})
  except Exception as error:failures.append({'reviewId':rid,'error':str(error)})
 priorids={e['previous']['problemId'] for e in entries.values() if e.get('previous')}
 retained=[r for pid,r in originals.items() if pid not in priorids and r['familyId']!='io3-chebyshev-absolute']
 effective=retained+records
 assert len({r['problemId'] for r in effective})==len(effective)
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n');(out/'source-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
 (out/'retained-originals.jsonl').write_text(''.join(canonical(r)+'\n' for r in retained));(out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n' for r in effective))
 result={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),'failures':failures,'knownChebyshevClueExcluded':8,'imported':0,'active':0}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main(sys.argv[1])
