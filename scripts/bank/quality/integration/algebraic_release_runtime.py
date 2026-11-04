"""Exact conclusion supplement over the immutable 58-menu package."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,importlib.util,json
P=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def bundle():
 spec=importlib.util.spec_from_file_location('quality_integration_algebraic_bundle_runtime',P/'algebraic-options/runtime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
@lru_cache(None)
def amendments():return json.loads((P/'algebraic-conclusion-amendments.json').read_text())
def catalog():return bundle().catalog()
def supplement(raw,route,family,index):
 patch=amendments()['items'].get(route+':'+family+':'+str(index))
 if patch:
  assert digest(raw)==patch['sourceRawSha256'] and raw['solutionSteps'][-1]==patch['oldConclusion']
  assert patch['exactIdentity'] and patch['newConclusion']==next(c['math']for c in raw['choices']if c['choiceId']==raw['answerChoiceId'])
  raw=copy.deepcopy(raw);raw['solutionSteps'].append(patch['newConclusion']);raw.pop('contentHash',None);raw['contentHash']=digest(raw)
  assert digest(raw)==patch['destinationRawSha256']
 return raw
def build(route,family,index):return supplement(bundle().build(route,family,index),route,family,index)
def verify(route,record,index):return canonical(record)==canonical(build(route,record['familyId'],index))
def close():bundle().close()
