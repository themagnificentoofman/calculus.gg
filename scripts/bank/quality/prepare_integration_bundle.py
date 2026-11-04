"""Actual-ID private previews of the frozen468 integration package.

No admission registry, published source, or database is changed.
"""
from pathlib import Path
import copy,hashlib,json,sys
from .contract import ROOT,canonical,normalize
from .integration import release_runtime
P=ROOT/'scripts/bank/quality/integration/bundle'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier preview stage')
 joins=json.loads((P/'source-joins.json').read_text())['records'];sources={};domains={}
 for j in joins:
  if j['sourceFile']not in sources:sources[j['sourceFile']]=list(map(json.loads,(P/j['sourceFile']).read_text().splitlines()))
  domains.setdefault((j['route'],j['familyId']),[]).append(j['index'])
 records=[];entries={};failures=[]
 for j in joins:
  raw=sources[j['sourceFile']][j['sourceLine']-1];assert hashlib.sha256(canonical(raw).encode()).hexdigest()==j['rawSha256']
  amendment=release_runtime.amendments()['items'].get(j['route']+':'+j['familyId']+':'+str(j['index']))
  if amendment:raw=release_runtime.build(j['route'],j['familyId'],j['index'])
  rawhash=hashlib.sha256(canonical(raw).encode()).hexdigest()
  review=copy.deepcopy(j['reviewPlan']);path=P/review['report'];assert sha(path)==review['reportSha256'];review['report']=str(path.relative_to(ROOT))
  review.update({'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64})
  if j['route']=='integration-hilbert':
   # Shared related idea with the discrete Hilbert-Schur family. This does
   # not collapse distinct parameter shapes or the different constructions.
   review['relatedIdeaGroupId']='hilbert-schur-sharpness'
  rid='quality-review:'+j['route']+':'+j['familyId']+':'+str(j['index'])
  e={'reviewId':rid,'module':j['route'],'familyId':j['familyId'],'index':j['index'],'rawSha256':rawhash,'verifier':'isolated-finite-reconstruction-and-independent-integration-review-v1','finiteDomain':{'indices':sorted(domains[(j['route'],j['familyId'])])},'review':review}
  if amendment:
   ap=P.parent/'conclusion-amendments.json';e['supplementalReports']=[{'path':str(ap.relative_to(ROOT)),'sha256':sha(ap),'purpose':'Exact source-bound logarithmic identity and final conclusion presentation.'}]
  if j.get('previous'):e['previous']=j['previous']
  try:records.append(normalize(raw,e));entries[rid]=e
  except Exception as err:failures.append({'reviewId':rid,'error':str(err)})
 oldpath=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl';assert sha(oldpath)=='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677'
 previous={e['previous']['problemId'] for e in entries.values() if e.get('previous')}
 retired={'io3-chebyshev-absolute'}
 retained=[r for r in map(json.loads,oldpath.read_text().splitlines()) if r['topic']=='integration' and r['problemId']not in previous and r['familyId']not in retired]
 effective=retained+records;assert len({r['problemId'] for r in effective})==len(effective)
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n');(out/'retained-originals.jsonl').write_text(''.join(canonical(r)+'\n' for r in retained))
 (out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n' for r in effective))
 report={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),'failures':failures,'sourceJoinsSha256':sha(P/'source-joins.json'),'pending':'Actual-ID full-family clue review, final normalized coverage and admission.','imported':0,'active':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert not failures
if __name__=='__main__':main(sys.argv[1])
