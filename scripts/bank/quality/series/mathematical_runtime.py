"""Compose exact option patches with the captured current reviewed presentation."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,json
from .mathematical import runtime as bundle
P=Path(__file__).resolve().parent/'mathematical'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def changes():return {r['problemId']:r for r in json.loads((P/'difficulty-changes.json').read_text())}
def catalog():return bundle.catalog()
def build(route,family,index):
 patch=bundle.build(route,family,index);assert bundle.verify(route,patch,index)
 old=bundle.source(route,family,index);j=bundle.review(route,family,index)
 presentation=bundle.presentation(route,family,index)
 assert old['contentHash']==patch['sourceContentHash'] and digest(old)==patch['sourceRawSHA256']
 assert not j['statementMeaningChanged'] and not j['answerChanged'] and j['preserveSemanticLineage']
 row={k:copy.deepcopy(old[k])for k in ['familyId','topic','assumptions','pedagogy']}
 row.update({'difficulty':j['reviewedDifficulty'],'parameters':{'instance':index},'instanceIndex':index,
  'finiteInstanceIndices':next(c['indices']for c in catalog()if c['route']==route and c['familyId']==family),
  'statement':presentation['statement'],'solutionSteps':presentation['solutionSteps'],
  'choices':patch['choices'],'answerChoiceId':patch['answerChoiceId'],
  'constructorVersion':'quality-series-mathematical-options-v1','sourcePreview':copy.deepcopy(j['sourcePreview']),
  'verificationEvidence':[{'kind':'independently-checked-literal-option-patch','patchSha256':digest(patch),'review':j['independentReview'],'correctValueAndMeaningUnchanged':True}],
  'provenance':{'kind':'original','theoremReferenceURLs':old.get('provenance',{}).get('authoring',{}).get('theoremReferenceURLs',[])}})
 previous=j.get('baselinePrevious')
 if previous:row['previous']={'problemId':previous['problemId'],'revision':previous['problemRevision'],'sourceContentHash':previous['contentHash'],'semanticHash':previous['semanticHash'],'meaningChanged':False}
 else:row['replacesPrivateProblemId']=old['problemId']
 if old['problemId']in changes():row['reviewedDifficultyChange']=copy.deepcopy(changes()[old['problemId']])
 row['contentHash']=digest(row);return row
def verify(route,record,index):return canonical(record)==canonical(build(route,record['familyId'],index))
def close():bundle.close()
