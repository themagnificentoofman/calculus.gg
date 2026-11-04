"""Eight immutable presentations: reorder whole terms, keep every value."""
from pathlib import Path
import copy,hashlib,json
P=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def build(family,index):
 if family!='m3-series-olympiad-lattice-resolvent'or type(index)is not int or index not in range(8):raise ValueError('Outside exact lattice domain')
 proposal=json.loads((P/'proposal.json').read_text());patch=next(r for r in proposal['records']if r['sourceInstanceIndex']==index)
 originals={r['problemId']:r for r in map(json.loads,(P/'source-records.jsonl').read_text().splitlines())};old=originals[patch['sourcePreview']['problemId']]
 assert digest(old)==patch['sourceCanonicalSHA256']and old['contentHash']==patch['sourcePreview']['contentHash']
 raw={k:copy.deepcopy(old[k])for k in ['familyId','topic','difficulty','assumptions','pedagogy']}
 raw.update({'constructorVersion':'lattice-complete-term-order-v1','instanceIndex':index,'finiteInstanceIndices':list(range(8)),'parameters':{'instance':index},
  'statement':patch['statement'],'solutionSteps':patch['solutionSteps'],'choices':patch['choices'],'answerChoiceId':patch['answerChoiceId'],
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old)},
  'provenance':{'kind':'original','theoremReferenceURLs':[]},'review':{'meaningChanged':False,'newIndependentIdeas':0,'presentationOnly':True}})
 raw['contentHash']=digest(raw);return raw
def verify(raw):return canonical(raw)==canonical(build(raw['familyId'],raw['instanceIndex']))
