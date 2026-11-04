"""Reconcile unchanged equivalence keys with explicit options-visible levels."""
from pathlib import Path
import argparse,collections,hashlib,json
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def recalculate(ledger,records,changes):
 old={(r['familyId'],r['instanceIndex']):r for r in ledger['recordNormalizedKeys']}
 families={r['familyId']:r for r in ledger['families']};byid={r['problemId']:r for r in changes};rows=[]
 for r in records:
  k=(r['familyId'],r['parameters']['instance']);prior=old[k];change=byid.get(r['problemId']);level=change['recommendedDifficulty']if change else prior['difficulty'];family=families[r['familyId']]
  rows.append({'problemId':r['problemId'],'sourceContentHash':r['contentHash'],'familyId':r['familyId'],'instanceIndex':k[1],'previousReviewedDifficulty':prior['difficulty'],'reviewedDifficulty':level,'normalizedKey':prior['normalizedKey'],'normalizationReason':prior['normalizationReason'],'reviewedGroup':family['reviewedGroup'],'globalRelatedGroup':family['globalRelatedGroup'],'difficultyChanged':level!=prior['difficulty'],'difficultyEvidence':change})
 assert len(old)==len(rows)==705 and len({(r['familyId'],r['instanceIndex'])for r in rows})==705
 counts={}
 for level in ['easy','medium','hard','olympiad']:
  sub=[r for r in rows if r['reviewedDifficulty']==level];fs={r['familyId']for r in sub};groups={r['reviewedGroup']for r in sub};normalized={r['normalizedKey']for r in sub};perfamily={f:len({r['normalizedKey']for r in sub if r['familyId']==f})for f in fs}
  counts[level]={'rawItems':len(sub),'normalizedMeaningfulItems':len(normalized),'constructionFamilies':len(fs),'topicLocalGroups':len(groups),'fiveRoundCapacityUnderFamilyCap2':sum(min(n,10)for n in perfamily.values()),'twoRoundCapacityUnderFamilyCap2':sum(min(n,4)for n in perfamily.values()),'normalizedItemsPerFamily':dict(sorted(perfamily.items()))}
 return {'status':'reconciled-exact-finite-review-no-admission','records':705,'beforeCounts':ledger['counts'],'afterCounts':counts,'recordsEvidence':rows,'qualifiedOlympiadGroupDeficitFrom30':max(0,30-counts['olympiad']['topicLocalGroups']),'olympiadNormalizedDeficitFrom240':max(0,240-counts['olympiad']['normalizedMeaningfulItems']),'scope':'Prior normalized keys and groups are preserved exactly; only independently reviewed finite-level changes are applied. Arithmetic capacity is necessary but is not a rerun of the selector/session horizon. Mixed global group equivalence remains the parent policy.','humanReviewed':False,'formalProof':False,'admitted':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--ledger',type=Path,required=True);ap.add_argument('--records',type=Path,required=True);ap.add_argument('--changes',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=recalculate(json.loads(a.ledger.read_text()),list(map(json.loads,a.records.read_text().splitlines())),json.loads(a.changes.read_text()));out['inputs']={str(p):sha(p)for p in [a.ledger,a.records,a.changes]};a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{q:v for q,v in x.items()if q!='normalizedItemsPerFamily'}for k,x in out['afterCounts'].items()}))
