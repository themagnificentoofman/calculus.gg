import sys,json,hashlib,importlib.util,time
from pathlib import Path
from reproduction_paths import source_repo,source_artifact
CONTENT=source_repo()/'scripts/bank/content';OUT=Path(__file__).parent;sys.path.insert(0,str(CONTENT))
def module(name):
 sp=importlib.util.spec_from_file_location('source_'+name,CONTENT/(name+'.py'));mo=importlib.util.module_from_spec(sp);sp.loader.exec_module(mo);return mo
mods={n:module(n) for n in ['coverage','ode','limits_additions','differentiation_additions','series_easy']}
route={}
for name,mo in mods.items():
 for f in mo.catalog():
  if name=='coverage' and f['topic']!='multivariable':continue
  if f['editorialStatus']!='admitted':continue
  route[f['familyId']]=name
bank=source_artifact();rows=[json.loads(l) for l in bank.read_text().splitlines()];assigned=[r for r in rows if r['familyId'] in route]
manifest={'artifact':str(bank),'artifactSha256':hashlib.sha256(bank.read_bytes()).hexdigest(),'families':route,'records':[{'problemId':r['problemId'],'familyId':r['familyId'],'contentHash':r['contentHash'],'parameters':r['parameters'],'builderParameters':r['provenance']['authoring']['builderParameters']} for r in assigned]};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
results=[]
for fid,name in route.items():
 tests=[]
 for r in [r for r in assigned if r['familyId']==fid]:
  try:
   raw=mods[name].build(fid,r['parameters']['instance']);correct=next(c['math'] for c in raw['choices'] if c['choiceId']==raw['answerChoiceId']);original=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']);assert correct==original,(correct,original)
   tests.append({'problemId':r['problemId'],'passed':True,'executedChecks':len(raw.get('automatedChecks',[]))})
  except Exception as e:tests.append({'problemId':r['problemId'],'passed':False,'error':repr(e)})
 results.append({'familyId':fid,'sourceModule':name,'records':tests});print(fid,sum(t['passed'] for t in tests),flush=True)
report={'artifactSha256':manifest['artifactSha256'],'familyCount':len(route),'recordCount':len(assigned),'results':results,'failures':[t for f in results for t in f['records'] if not t['passed']]};(OUT/'source-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('FINISHED',len(route),len(assigned),len(report['failures']))
