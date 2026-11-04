"""Separate finite final-review layers; frozen author packages remain unchanged."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
from functools import lru_cache
P=Path(__file__).resolve().parent
ROUTES={'limits-recurrence-options':('limits-options/recurrence','repairs.py'),
 'ode-nonnormal-options':('ode-final/nonnormal-v2','repairs.py'),
 'ode-ground-options':('ode-final/ground-v4','repairs.py'),
 'mv-density-classification':('ode-final/density-v1','amendment.py')}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def package(route):
 folder,file=ROUTES[route];path=P/folder
 inventory=json.loads((path/'parent-copy-manifest.json').read_text())
 for entry in inventory['files']:assert hashlib.sha256((path/entry['path']).read_bytes()).hexdigest()==entry['sha256']
 spec=importlib.util.spec_from_file_location('late_'+route.replace('-','_'),path/file);module=importlib.util.module_from_spec(spec)
 sys.path.insert(0,str(path))
 try:spec.loader.exec_module(module)
 finally:sys.path.pop(0)
 return module,path

def build(route,family,index):
 if route not in ROUTES or type(index)is not int:raise ValueError('Unknown late finite review route')
 module,path=package(route);raw=module.build(family,index)
 frozen=[r for r in map(json.loads,(path/'candidates.jsonl').read_text().splitlines())if r['familyId']==family and r['instanceIndex']==index]
 assert len(frozen)==1 and canonical(frozen[0])==canonical(raw)
 verified=module.verify(raw);assert verified is True or isinstance(verified,dict)and verified.get('passed')is True
 if route=='limits-recurrence-options':
  amendment=P/'limits-options/recurrence-classification/classification-amendments.json'
  assert hashlib.sha256(amendment.read_bytes()).hexdigest()=='13caacadfb5597c4d6dabb183d95fe01a2b586d1fb83b238d02539cf4754dd2d'
  entry=next(e for e in json.loads(amendment.read_text())['entries']if e['familyId']==family and e['index']==index)
  assert entry['rawSha256']==digest(raw)
  raw=copy.deepcopy(raw);raw.pop('contentHash');raw['constructorVersion']='quality-recurrence-options-medium-v2';raw['difficulty']='medium'
  for k in ['easiestOptionsVisibleRoute','difficultyRationale','centralDecision']:raw['review'][k]=entry[k]
  raw['review']['qualifiedOlympiad']=False
  raw['pedagogy']['primaryTechnique']=entry['primaryTechnique'];raw['pedagogy']['difficultyRationale']=entry['difficultyRationale']
  raw['reviewedDifficultyChange']={'previousDifficulty':'hard','recommendedDifficulty':'medium','reason':entry['difficultyRationale'],'sourceRawSha256':entry['rawSha256']}
  raw['contentHash']=digest(raw)
 return raw

def verify(route,raw):return canonical(raw)==canonical(build(route,raw['familyId'],raw['instanceIndex']))
