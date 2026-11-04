"""Private canonical previews of the frozen ODE/multivariable review assets.
No admission registry is written. Reconstruction, independent coverage joins,
and final effective-pool option dispositions remain separate required gates.
"""
from pathlib import Path
import hashlib,json,sys
from .contract import ROOT,canonical,normalize
P=ROOT/'scripts/bank/quality/ode-mv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if (out/'canonical-previews.jsonl').exists():raise ValueError('Preserve earlier stage')
 report=P/'source-joins.json';joins=[r for r in json.loads(report.read_text())['records'] if r['route'].startswith('ode-mv-')];sources={};domains={}
 for j in joins:
  f=j['sourceFile']
  if f not in sources:sources[f]=list(map(json.loads,(P/f).read_text().splitlines()))
  domains.setdefault((j['route'],j['familyId']),[]).append(j['index'])
 records=[];entries={};failures=[]
 for j in joins:
  raw=sources[j['sourceFile']][j['sourceLine']-1];h=hashlib.sha256(canonical(raw).encode()).hexdigest();assert h==j['rawSha256']
  plan=j['reviewPlan'];assert plan['reviewCoverage'];level=plan['recommendedDifficulty'];rid='quality-review:'+j['route']+':'+j['familyId']+':'+str(j['index'])
  route=raw.get('review',{}).get('easiestOptionsVisibleRoute') or next((v['easiestOptionsVisibleRoute'] for v in plan['reviewCoverage'] if v.get('easiestOptionsVisibleRoute')),raw['pedagogy']['difficultyRationale'])
  if j['familyId'].endswith('oscillator-minimum-control-energy') and j['index'] in [4,6,9]:route='Cauchy–Schwarz with one endpoint kernel gives a lower bound and the feasible cubic trajectory gives an upper bound. Exact rational enclosures show these two bounds isolate the literal correct choice. Hard.'
  nearest=raw.get('nearestNeighbor') or raw.get('review',{}).get('nearestNeighbor') or ('Same reviewed construction and exposure lineage; this finite revision adds no independent idea.' if j.get('previous') or not level=='olympiad' else 'The source-bound family proof and nearest-neighbor review are in the bundled independent coverage evidence; final catalog qualification remains a separate gate.')
  e={'reviewId':rid,'module':j['route'],'familyId':j['familyId'],'index':j['index'],'rawSha256':h,'verifier':'isolated-finite-reconstruction-and-independent-ODE-MV-review-v1','finiteDomain':{'indices':sorted(domains[(j['route'],j['familyId'])])},'review':{'status':'independently-reviewed','author':'integration_research','reviewer':'root-and-coverage-independent-reviews','report':str(report.relative_to(ROOT)),'reportSha256':sha(report),'centralDecision':route,'nearestNeighbor':nearest,'easiestOptionsVisibleRoute':route,'difficultyRationale':route,'difficulty':level,'qualifiedOlympiad':level=='olympiad' and plan['qualifiedOlympiadCandidate'],'relatedIdeaGroupId':plan['relatedIdeaGroupId'],'normalizedLineageKey':plan['normalizedLineageKey'],'optionAuditReport':'PRIVATE-PENDING-FINAL-ID-OPTION-SCREEN','optionAuditSha256':'0'*64}}
  if j.get('previous'):
   prior=j['previous'];e['previous']={'problemId':prior['problemId'],'revision':prior['problemRevision'],'sourceContentHash':prior['contentHash'],'semanticHash':prior['semanticHash'],'meaningChanged':prior['meaningChanged']}
   if prior['meaningChanged']:e['review']['semanticChangeReason']=raw['review']['semanticChangeReason']
  try:records.append(normalize(raw,e));entries[rid]=e
  except Exception as err:failures.append({'reviewId':rid,'error':str(err)})
 oldpath=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl';assert sha(oldpath)=='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677'
 priorids={e['previous']['problemId'] for e in entries.values() if e.get('previous')};retained=[r for r in map(json.loads,oldpath.read_text().splitlines()) if r['topic']in ['differential equations','multivariable'] and r['problemId']not in priorids];effective=retained+records
 assert len({r['problemId'] for r in effective})==len(effective)
 (out/'canonical-previews.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(out/'admission-previews.json').write_text(json.dumps(entries,indent=2)+'\n');(out/'retained-originals.jsonl').write_text(''.join(canonical(r)+'\n' for r in retained));(out/'effective-option-input.jsonl').write_text(''.join(canonical({k:r[k] for k in ['problemId','familyId','choices','answerChoiceId','pedagogy']})+'\n' for r in effective))
 result={'status':'private-not-admitted','records':len(records),'retained':len(retained),'effectiveRecords':len(effective),'failures':failures,'pending':'Final exact independent coverage/lineage joins, complete isolated reconstruction and final option dispositions; these private entries do not register admission.','imported':0,'active':0};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main(sys.argv[1])
