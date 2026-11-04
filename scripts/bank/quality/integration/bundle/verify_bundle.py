"""Reproduce every finite raw record and rejection guard; no author flag bypass."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,collections,copy,hashlib,json,time
import runtime
BASE=Path(__file__).resolve().parent
def H(v):return hashlib.sha256(runtime.canonical(v).encode()).hexdigest()
def check_route(route,entries):
 results=[]
 for entry in entries:
  family,index=entry['familyId'],entry['index']
  try:
   record=runtime.build(route,family,index)
   assert H(record)==entry['rawSha256']
   assert runtime.verify(route,record,index)
   corrupt=copy.deepcopy(record);corrupt['statement']+='\\quad0=1';assert runtime.verify(route,corrupt,index)is False
   corrupt=copy.deepcopy(record);corrupt['choices'][0]['math']+='\\quad0=1';assert runtime.verify(route,corrupt,index)is False
   ev=runtime.reconstruction_evidence(route,family,index);assert ev['canonicalByteParity'] and ev['normalizations']==[]
   results.append({'route':route,'familyId':family,'index':index,'rawSha256':H(record),'sourceLineSha256':entry['sourceLineSha256'],'passed':True,'mutatedStatementRejected':True,'mutatedChoiceRejected':True})
  except Exception as error:results.append({'route':route,'familyId':family,'index':index,'passed':False,'error':type(error).__name__+': '+str(error)})
 print(json.dumps({'route':route,'records':len(results),'passed':sum(x['passed']for x in results)}),flush=True)
 return results

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,default=BASE/'reconstruction-report.json');ap.add_argument('--workers',type=int,default=3);args=ap.parse_args();started=time.monotonic()
 joins=json.loads((BASE/'source-joins.json').read_text())['records'];by=collections.defaultdict(list)
 for entry in joins:by[entry['route']].append(entry)
 result=[]
 with ThreadPoolExecutor(max_workers=args.workers)as pool:
  futures=[pool.submit(check_route,route,rows)for route,rows in by.items()]
  for f in as_completed(futures):result.extend(f.result())
 guards=[];first=joins[0]
 for route,family,index in [('missing',first['familyId'],first['index']),(first['route'],'missing',first['index']),(first['route'],first['familyId'],True),(first['route'],first['familyId'],-1),(first['route'],first['familyId'],999)]:
  try:runtime.build(route,family,index);guards.append(False)
  except ValueError:guards.append(True)
 runtime.close()
 final=list(map(json.loads,(BASE/'final-candidates.jsonl').read_text().splitlines()));assert [H(x)for x in final]==[x['rawSha256']for x in joins]
 report={'status':'passed'if all(r['passed']for r in result)and all(guards)else'failed','records':len(result),'passed':sum(r['passed']for r in result),'failed':sum(not r['passed']for r in result),'rejectionGuards':guards,'canonicalByteParity':all(r['passed']for r in result),'sourceLineParity':all(r['passed']for r in result),'serializationNormalizations':0,'seconds':round(time.monotonic()-started,3),'sourceManifestSha256':hashlib.sha256((BASE/'copy-manifest.json').read_bytes()).hexdigest(),'finalCandidatesSha256':hashlib.sha256((BASE/'final-candidates.jsonl').read_bytes()).hexdigest(),'scope':'Executed trusted finite constructors and exact frozen record equality, plus negative mutation checks. Does not replace the independently authored mathematical/analytic review evidence. No admission, registry or production writes.','recordsEvidence':sorted(result,key=lambda r:(r['route'],r['familyId'],r['index']))}
 args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='recordsEvidence'}));raise SystemExit(0 if report['status']=='passed'else 1)
if __name__=='__main__':main()
