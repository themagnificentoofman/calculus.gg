from pathlib import Path
import json,hashlib,copy,tempfile,shutil,subprocess,sys,importlib.util
P=Path(__file__).resolve().parent
H=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
fh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run_checks(sample=False):
 spec=importlib.util.spec_from_file_location('portable_integration_algebraic_runtime',P/'runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
 raw={H(r):r for r in map(json.loads,(P/'sources/combined-candidates.jsonl').read_text().splitlines())};joins=json.loads((P/'source-joins.json').read_text());records=[]
 if sample:
  selected={}
  for j in joins:selected.setdefault((j['route'],j['familyId']),j)
  joins=list(selected.values())
 for j in joins:
  r=runtime.build(j['route'],j['familyId'],j['index']);assert H(r)==j['rawHash']and r==raw[j['rawHash']];assert runtime.verify(j['route'],r)is True
  changed=copy.deepcopy(r);changed['statement']+='x';assert runtime.verify(j['route'],changed)is False
  # Returned mutable objects must not mutate cached reconstruction evidence.
  r['statement']+='x';assert runtime.build(j['route'],j['familyId'],j['index'])==raw[j['rawHash']]
  records.append({'route':j['route'],'familyId':j['familyId'],'index':j['index'],'rawHash':j['rawHash'],'exactReconstruction':True,'changedStatementRejected':True,'cacheMutationIsolated':True})
 invalid=[('unknown','x',0),('main55','x',0),('main55','io3-bernoulli-product',999),('main55','io3-bernoulli-product',True)]
 for args in invalid:
  try:runtime.build(*args)
  except ValueError:pass
  else:raise AssertionError(args)
 runtime.close();return {'records':records,'counts':{'checked':len(records),'exactReconstruction':len(records),'changedStatementRejected':len(records),'cacheMutationIsolated':len(records),'invalidRequestsRejected':len(invalid)},'copiedSourcesSha256':{f:q['sha256']for f,q in json.loads((P/'copy-manifest.json').read_text())['copiedFiles'].items()}}
if __name__=='__main__':
 if '--relocated-smoke'in sys.argv:
  report=run_checks(True);print(json.dumps({'counts':report['counts'],'runtimeDirectory':str(P)}));raise SystemExit
 report=run_checks();assert report['counts']['checked']==58;(P/'reconstruction-report.json').write_text(json.dumps(report,indent=2)+'\n')
 with tempfile.TemporaryDirectory(prefix='cn-integration-algebraic-')as temp:
  target=Path(temp)/'asset';shutil.copytree(P,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'));done=subprocess.run([sys.executable,'-B',str(target/'verify_bundle.py'),'--relocated-smoke'],text=True,capture_output=True,check=True,cwd=temp);smoke=json.loads(done.stdout);assert smoke['counts']['checked']==13
  portability={'status':'passed','scope':'One source-bound reconstruction per route/family (13 route-family combinations,12 unique families) in a relocated temporary bundle with the same isolated-worker API. All58 are covered by the original-location full reconstruction report.','counts':smoke['counts'],'stdout':smoke,'stderr':done.stderr,'noAbsoluteRuntimeDependency':'All reconstruction inputs and code are relative to the copied bundle; absolute paths in provenance/evidence are documentary.'}
 (P/'portability-report.json').write_text(json.dumps(portability,indent=2)+'\n');print(report['counts']);print('relocated',portability['counts'])
