"""Guarded final series choice revisions, pending complete-pool admission."""
from pathlib import Path
from functools import lru_cache
import atexit,copy,hashlib,json,subprocess,sys
P=Path(__file__).resolve().parent
WORKER=None;CACHE={}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def inputs():
 originals={r['problemId']:r for r in map(json.loads,(P/'frozen/source-records.jsonl').read_text().splitlines())};guards=json.loads((P/'lineage-guards.json').read_text());peers={r['problemId']:r for r in json.loads((P/'independent-peer.json').read_text())['records']};overlays=json.loads((P/'historical-presentations.json').read_text());return originals,guards,peers,overlays
def close():
 if WORKER and WORKER.poll()is None:WORKER.terminate()
atexit.register(close)
def catalog():
 _,guards,_,_=inputs()
 return [{'familyId':fid,'indices':sorted(g['index'] for g in guards.values() if g['familyId']==fid)} for fid in sorted({g['familyId'] for g in guards.values()})]
def build(fid,index):
 global WORKER
 if type(index)is not int:raise ValueError('Integer index required')
 if (fid,index)in CACHE:return copy.deepcopy(CACHE[(fid,index)])
 originals,guards,peers,overlays=inputs();matches=[pid for pid,g in guards.items() if g['familyId']==fid and g['index']==index]
 if len(matches)!=1:raise ValueError('Outside reviewed opposite-pair revision domain')
 pid=matches[0];old=originals[pid];guard=guards[pid];peer=peers[pid];assert digest(old)==guard['sourceRawHash']==peer['sourceRawHash'] and old['contentHash']==guard['sourceContentHash']==peer['sourceContentHash']
 if WORKER is None:WORKER=subprocess.Popen([sys.executable,'-B',str(P/'worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 WORKER.stdin.write(canonical({'problemId':pid})+'\n');WORKER.stdin.flush();answer=json.loads(WORKER.stdout.readline())
 if answer.get('error'):raise ValueError(answer['error'])
 patch=answer['patch'];assert answer['verified'] and digest(patch)==peer['patchSha256'] and peer['sixLiteralPairInequalities'] and peer['unchangedReviewedCorrectValue']
 overlay=overlays.get(pid)
 if overlay:assert overlay['sourceContentHash']==old['contentHash'] and overlay['revision']==old['problemRevision']
 row={k:copy.deepcopy(old[k]) for k in ['familyId','topic','difficulty','assumptions','pedagogy']}
 row.update({'instanceIndex':index,'parameters':{'instance':index},'finiteInstanceIndices':next(c['indices'] for c in catalog() if c['familyId']==fid),'statement':overlay.get('statement',old['statement']) if overlay else old['statement'],'solutionSteps':overlay['steps'] if overlay else old['solutionSteps'],'choices':patch['choices'],'answerChoiceId':patch['answerChoiceId'],'constructorVersion':'quality-series-opposite-pair-revisions-v1','sourcePreview':{'problemId':pid,'sourceContentHash':old['contentHash'],'sourceRawHash':digest(old)},'verificationEvidence':[{'kind':'independent-literal-choice-enclosures','patchSha256':peer['patchSha256'],'sixDistinctPairs':True,'correctReviewedValueUnchanged':True}],'provenance':{'kind':'original','theoremReferenceURLs':old.get('provenance',{}).get('authoring',{}).get('theoremReferenceURLs',[])}})
 if guard.get('previous'):row['previous']=guard['previous']
 else:row['replacesPrivateProblemId']=pid
 row['contentHash']=digest(row);CACHE[(fid,index)]=row;return copy.deepcopy(row)
def verify(row):return canonical(row)==canonical(build(row['familyId'],row['instanceIndex']))
if __name__=='__main__':
 rows=[build(f['familyId'],i) for f in catalog() for i in f['indices']];Path(sys.argv[1]).write_text(''.join(canonical(r)+'\n' for r in rows));print(json.dumps({'reconstructed':len(rows),'independentLiteralPairs':6*len(rows),'imported':0,'active':0}))
