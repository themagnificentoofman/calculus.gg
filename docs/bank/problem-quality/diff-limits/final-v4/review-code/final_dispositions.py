"""Resolve bounded final-ID flags with exact joins and explicit finite notes."""
from pathlib import Path
import collections,hashlib,json,sys
P=Path(__file__).resolve().parent
def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=Path(sys.argv[1]).resolve();target=out/'final-option-dispositions.json'
 if target.exists():raise ValueError('Never overwrite an existing disposition report')
 mapping=list(map(json.loads,(out/'normalized-record-map.jsonl').read_text().splitlines()));byid={r['problemId']:r for r in mapping}
 source=json.loads((out/'source-and-lineage-joins.json').read_text());notes=json.loads((P/'manual-dispositions.json').read_text())
 construction=json.loads((out/'construction-option-audit.json').read_text());storage=json.loads((out/'storage-option-audit.json').read_text())
 assert construction['records']==storage['records']==1405
 findings=[];unknown=[]
 def disposition(name,group,kind):
  ids=group['trainingIds']+group['heldoutIds'];assert len(ids)==group['items']and len(set(ids))==len(ids)
  rows=[byid[i]for i in ids];screen_names={r['reviewedScreenConstructionId']for r in rows};manual=[]
  if kind!='answer-form':
   assert len(screen_names)==1,(kind,name,screen_names)
   screen_name=next(iter(screen_names))
   if screen_name in notes['notes']:manual.append(notes['notes'][screen_name])
  else:screen_name=None
  flags=[]
  for flag in group['flags']:
   score=next(r for r in group['results']if r['rule']==flag['rule']);rule=flag['rule']
   if rule.startswith('shuffled-position-'):explanation=notes['shuffleDisposition'];decision='retain-with-fresh-serving-shuffle-and-disclosed-finite-position-flag'
   elif kind=='storage-family':
    pooled=construction['families'][screen_name]
    explanation=notes['storageAliasDisposition'];decision='retain-under-complete-construction-disposition'
    if any(not f['rule'].startswith('shuffled-position-')for f in pooled['flags'])and screen_name not in notes['notes']:unknown.append((kind,name,rule,'unresolved pooled flag'))
   elif screen_name in notes['notes']:
    explanation=notes['notes'][screen_name];decision='retain-under-explicit-literal-menu-and-source-proof-disposition'
   else:
    explanation='Unresolved new nonposition flag: requires explicit finite editorial review.';decision='pending';unknown.append((kind,name,rule))
   flags.append({'rule':rule,'training':score['training'],'heldout':score['heldout'],'decision':decision,'explanation':explanation})
  if not flags:manual.append(notes['noFlagDisposition'])
  if kind=='storage-family':manual.append(notes['storageAliasDisposition'])
  if kind=='construction'and group['items']==1 and screen_name not in notes['notes']:unknown.append((kind,name,'singleton lacks explicit note'))
  return {'groupId':name,'kind':kind,'items':group['items'],'actualProblemIds':ids,'canonicalConstructions':sorted({r['canonicalConstruction']for r in rows}),
   'levels':dict(collections.Counter(r['recommendedDifficulty']for r in rows)),'qualifiedOlympiadRecords':sum(r['qualifiedOlympiad']for r in rows),'limitedSample':group['limitedSample'],
   'selectedUsingTrainingOnly':group['selectedUsingTrainingOnly'],'flags':flags,'finiteEditorialNotes':manual,'status':'local-source-bound-review-disposition-complete'if all(f['decision']!='pending'for f in flags)else'pending',
   'proofScope':'Existing finite source-bound mathematical/option reviews and canonical verification are carried forward through the exact source joins; only the two ten-menu repairs and the ten-item classification amendment are new work in this final asset review. This is not a fresh independent solve of all 1405 tasks.'}
 for name,g in storage['families'].items():findings.append(disposition(name,g,'storage-family'))
 for name,g in construction['families'].items():findings.append(disposition(name,g,'construction'))
 for name,g in construction['answerForms'].items():findings.append(disposition(name,g,'answer-form'))
 report={'schemaVersion':1,'status':'pending-explicit-findings'if unknown else'complete-local-final-ID-dispositions-pending-root-admission-and-release-gates','records':1405,
  'counts':{'storageFamilies':len(storage['families']),'constructions':len(construction['families']),'answerForms':len(construction['answerForms']),'groupsWithFlags':sum(bool(r['flags'])for r in findings),'unresolvedFindings':len(unknown)},
  'artifacts':{name:fh(out/name)for name in ['construction-option-input.jsonl','storage-option-input.jsonl','construction-option-audit.json','storage-option-audit.json','normalized-record-map.jsonl','source-and-lineage-joins.json']},
  'manualDispositionSourceSha256':fh(P/'manual-dispositions.json'),'qualifiedCapacity':source['qualificationSummary'],'retirementsPreserved':source['retiredProblemIds'],'classificationDemotions':source['demotions'],
  'independentRepairReviews':{k:v for k,v in source['overlayArtifacts'].items()if'peerPath'in v},'findings':findings,'unresolved':unknown,'limitations':['Final canonical IDs and served-normalized expressions are screened; this does not cover hypothetical future content or all possible classifiers.','Parser non-applicability is not mathematical equality/inequality evidence. Prior analytic and exact-pair reports retain that role.','All finite sample sizes, flags and singleton limitations are disclosed; shuffled positions are handled by production shuffle, not ID or seed changes.','The new default-off Experimental legacy selection policy is owned by root; inclusion in this reviewed inventory does not grant default eligibility.','The two repairs and recurrence demotion have exact-source independent owner reviews. Central admission, historical preservation, UI, and the global release evaluator remain separate gates.']}
 target.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'counts':report['counts'],'status':report['status'],'unresolved':unknown}))
if __name__=='__main__':main()
