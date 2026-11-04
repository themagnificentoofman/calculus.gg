"""Reconstruct every patch and exercise exact guards, from any copied location."""
from pathlib import Path
import argparse,copy,hashlib,json
import runtime
BASE=Path(__file__).resolve().parent
def H(v):return hashlib.sha256(runtime.canonical(v).encode()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();checks=[];guard=0
 for item in runtime.catalog():
  for index in item['indices']:
   route=item['route'];family=item['familyId'];src=runtime.source(route,family,index);patch=runtime.build(route,family,index);assert runtime.supports(route,src)and runtime.verify(route,patch,index)
   j=runtime.review(route,family,index);peer=json.loads((BASE/j['independentReview']['path']).read_text());pr=next(r for r in peer['records']if r['problemId']==src['problemId']);assert H(pr)==j['independentReview']['recordSHA256'];assert pr.get('patchSHA256',pr.get('patchSha256'))==H(patch);assert pr['sourceRawSHA256']==H(src)and pr['passed']is True
   present=runtime.presentation(route,family,index);assert present['sourceContentHash']==src['contentHash']and present['statement']and present['solutionSteps']
   altered=copy.deepcopy(src);altered['statement']+=' ';assert not runtime.supports(route,altered);guard+=1
   altered=copy.deepcopy(patch);altered['choices'][0]['math']+=' ';assert not runtime.verify(route,altered,index);guard+=1
   altered=copy.deepcopy(src);altered['contentHash']='0'*64;assert not runtime.supports(route,altered);guard+=1
   checks.append({'route':route,'familyId':family,'index':index,'sourceCanonicalSHA256':H(src),'patchCanonicalSHA256':H(patch),'reconstructed':True})
 for route,family,index in [('missing','unknown',0),('domain-six','unknown',0),('domain-six','m3-series-easy-taylor-coefficient-derivative',1000)]:
  try:runtime.build(route,family,index)
  except ValueError:guard+=1
  else:raise AssertionError('Unknown finite key accepted')
 assert len(checks)==162
 out={'records':len(checks),'reconstructionFailures':0,'negativeGuardsPassed':guard,'recordsEvidence':checks,'scope':'Exact frozen reconstruction and supplied-source guards. Independent mathematical evidence and final classifications are separately bound in source-joins.json. No admission, import or deployment.'}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2)+'\n');runtime.close();print(json.dumps({'records':len(checks),'negativeGuardsPassed':guard}))
if __name__=='__main__':main()
