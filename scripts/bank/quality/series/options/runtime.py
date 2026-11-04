"""Guarded immutable negative-binomial option revisions; no published edits."""
from pathlib import Path
import copy,hashlib,json
from . import series_option_disposition as recipe
P=Path(__file__).resolve().parent
FID='m3-series-medium-negative-binomial'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def build(fid,index):
 if fid!=FID or type(index)is not int or index not in range(10):raise ValueError('Outside independently reviewed option repair domain')
 originals=json.loads((P/'guarded-inputs.json').read_text());guards=json.loads((P/'series-negative-binomial-repair-guards.json').read_text());pid=next(k for k,g in guards.items() if g['m']==index+4);old=originals[pid]
 patch=recipe.build_patch(old);assert recipe.verify_patch(patch,old)
 peers=json.loads((P/'negative-binomial-option-peer-review.json').read_text())['records'];peer=next(v for v in peers if v['problemId']==pid)
 assert peer['sourceRawHash']==recipe.raw(old) and peer['patchSHA256']==hashlib.sha256(canonical(patch).encode()).hexdigest() and peer['pairwiseInequivalences']==6 and peer['correctSoleRationalCube']is False
 overlays=json.loads((P/'prior-presentation-reviews.json').read_text());overlay=overlays.get(pid)
 if overlay:assert overlay['sourceContentHash']==old['contentHash'] and overlay['revision']==old['problemRevision']
 raw={'familyId':fid,'topic':'series','difficulty':'medium','instanceIndex':index,'parameters':{'m':index+4},'finiteInstanceIndices':list(range(10)),'statement':overlay.get('statement',old['statement']) if overlay else old['statement'],'choices':patch['choices'],'answerChoiceId':patch['answerChoiceId'],'solutionSteps':overlay['steps'] if overlay else old['solutionSteps'],'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'source':{'kind':'independently-authored','thirdPartyProblemAdapted':False,'attribution':'Original Calculus Ninja content. Exact prior task and reviewed worked solution with independently reviewed misconception choices.'},'constructorVersion':'quality-series-negative-binomial-options-v2','verificationEvidence':[{'kind':'source-bound-independent-option-review','report':'negative-binomial-option-peer-review.json','sourceRawHash':peer['sourceRawHash'],'patchSHA256':peer['patchSHA256'],'allSixPairsDistinct':True,'competingRationalCubes':2}],'lineage':{'ancestorSemanticHash':old['semanticHash'],'normalizedLineageKey':'negative-binomial-geometric-ratio:'+str(index+4)}}
 if overlay:raw['previous']={'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':False}
 raw['contentHash']=hashlib.sha256(canonical(raw).encode()).hexdigest();return raw

def verify(raw):return canonical(raw)==canonical(build(raw['familyId'],raw['instanceIndex']))
