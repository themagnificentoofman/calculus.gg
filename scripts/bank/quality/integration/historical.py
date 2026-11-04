"""Immutable difficulty revisions of independently reviewed existing integrals.

The original source is reconstructed by its frozen verifier. Mathematical
content and options are unchanged; the separate peer report binds the exact
old identity, all finite answers, and options-visible classification.
"""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/bank'))
import content_pipeline
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def inputs():
 originals={(r['familyId'],r['parameters']['instance']):r for r in map(json.loads,(P/'historical-originals.jsonl').read_text().splitlines())}
 peers={r['problemId']:r for r in json.loads((ROOT/'docs/bank/problem-quality/integration/integration-peer-review.json').read_text())['records']}
 return originals,peers,json.loads((P/'historical-presentations.json').read_text())
def catalog():
 originals,_,_=inputs()
 return [{'familyId':fid,'indices':sorted(i for f,i in originals if f==fid),'newIndependentIdeas':0} for fid in sorted({f for f,_ in originals})]
def build(fid,index):
 originals,peers,presentations=inputs()
 if type(index)is not int or (fid,index)not in originals:raise ValueError('Outside reviewed historical finite domain')
 old=originals[(fid,index)];assert content_pipeline.verify(old)
 peer=peers[old['problemId']];overlay=presentations[old['problemId']]
 assert peer['sourceContentHash']==old['contentHash']==overlay['sourceContentHash'] and peer['semanticHash']==old['semanticHash']
 assert peer['difficultyRecommended']in ['easy','medium','hard'] and peer['exactChecks']
 # The peer's energy-bound finding blocks advanced classification, not the
 # legitimate bounding solution at its independently recommended Hard level.
 if peer['blockingOptionIssues']:
  assert fid=='io3-variational-energy' and index in [0,1,4] and peer['difficultyRecommended']=='hard'
  assert all('before counting this instance as Olympiad' in issue for issue in peer['blockingOptionIssues'])
 row={k:copy.deepcopy(old[k]) for k in ['familyId','topic','choices','answerChoiceId','assumptions','pedagogy']}
 row.update({'instanceIndex':index,'parameters':{'instance':index},'finiteInstanceIndices':next(f['indices'] for f in catalog() if f['familyId']==fid),'difficulty':peer['difficultyRecommended'],'statement':overlay.get('statement',old['statement']),'solutionSteps':overlay['steps'],'previous':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':False},'constructorVersion':'quality-integration-historical-dispositions-v1','provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring']['theoremReferenceURLs']},'verificationEvidence':peer['exactChecks'],'analyticCertificate':old['validation']['evidence']['analyticCertificate']})
 row['contentHash']=digest(row);return row
def verify(row):return canonical(row)==canonical(build(row['familyId'],row['instanceIndex']))
def all_candidates():
 for f in catalog():
  for i in f['indices']:yield build(f['familyId'],i)
if __name__=='__main__':
 rows=list(all_candidates());Path(sys.argv[1]).write_text(''.join(canonical(r)+'\n' for r in rows));print(json.dumps({'unchangedTaskDifficultyRevisions':len(rows)}))
