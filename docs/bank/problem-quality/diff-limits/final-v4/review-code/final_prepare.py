"""Bind an effective final D/L stage to the frozen 1405-task lineage.

This writes a new report directory only. It never edits central admission,
source constructors, published records, retired identities, or app code.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,sys
P=Path(__file__).resolve().parent
ROOT=next((a for a in P.parents if(a/'scripts/bank/AGENTS.md').is_file()),P.parents[2]/'problem-quality')
RESEARCH=P.parent
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canon(v).encode()).hexdigest()
def filehash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readlines(p):return list(map(json.loads,p.read_text().splitlines()))
def norm(text):return re.sub(r'\\log(?!\s*_)',lambda _:r'\ln',text)
def menu(row):return sorted((c['choiceId'],norm(c['math']))for c in row['choices']),norm(next(c['math']for c in row['choices']if c['choiceId']==row['answerChoiceId']))
def main():
 stage=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
 if out.exists():raise ValueError('Use a new final report directory')
 base=ROOT/'.bank-data/quality/diff-limits-previews-v2'
 lineagepath=ROOT/'scripts/bank/quality/diff-limits/lineage-dispositions.json'
 lineage=json.loads(lineagepath.read_text());original={r['problemId']:r for r in lineage['instances']if r['kind']=='original-record'};new={r['rawHash']:r for r in lineage['instances']if r['kind']!='original-record'}
 oldadmit=json.loads((base/'admission-previews.json').read_text());base_records={};base_map={}
 for name in ['canonical-previews.jsonl','retained-originals.jsonl']:
  for r in readlines(base/name):
   base_records[r['problemId']]=r
   if name.startswith('retained'):l=original[r['problemId']]
   else:
    e=oldadmit[r['provenance']['authoring']['reviewId']]
    l=original[e['previous']['problemId']]if e.get('previous')else new[e['rawSha256']]
   base_map[r['problemId']]=l
 prior_join=json.loads((P/'source-id-joins.json').read_text());screen_family={r['actualProblemId']:r['reviewedConstructionFamilyId']for r in prior_join['records']}
 assert len(base_map)==1405 and set(base_map)==set(screen_family)
 overlays={};overlayartifacts={}
 classification_path=ROOT/'scripts/bank/quality/limits-options/recurrence-classification/classification-amendments.json'
 classification=json.loads(classification_path.read_text())
 amendments={e['rawSha256']:e for e in classification['entries']}
 assert len(amendments)==10
 for name in ['rational-sequence-options-v1','recurrence-options-v1']:
  directory=ROOT/'scripts/bank/quality/limits-options'/('rational'if name.startswith('rational')else'recurrence');manifest=json.loads((directory/'delivery-manifest.json').read_text())
  for f,h in manifest.get('frozenArtifacts',manifest.get('files')).items():assert filehash(directory/f)==h,(name,f)
  overlayartifacts[name]={'manifestSha256':filehash(directory/'delivery-manifest.json'),'candidatesSha256':filehash(directory/'candidates.jsonl')}
  for r in readlines(directory/'candidates.jsonl'):
   assert r['sourcePreview']['problemId']in base_records
   overlays[digest(r)]={'bundle':name,'raw':r}
 # Root's separate immutable adapter applies the approved classification
 # amendment without rewriting the frozen ten-menu author snapshot.
 runtimepath=ROOT/'scripts/bank/quality/late_runtime.py'
 spec=importlib.util.spec_from_file_location('final_dl_late_runtime',runtimepath);runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
 peerpath=ROOT/'docs/bank/problem-quality/recurrence-option-peer-v2.json';peer=json.loads(peerpath.read_text())
 assert filehash(peerpath)=='897dbc48f5d20553863cd5ad86f81f767581f97832dab95e3d419aa1e09b77e7'
 assert len(peer['records'])==10 and all(r['passed']for r in peer['records'])
 for e in peer['records']:
  raw=runtime.build('limits-recurrence-options',e['familyId'],e['index']);assert digest(raw)==e['rawSha256']and runtime.verify('limits-recurrence-options',raw)
  oldsha=raw['reviewedDifficultyChange']['sourceRawSha256'];assert oldsha in amendments and oldsha in overlays
  overlays[digest(raw)]={'bundle':'recurrence-options-v1-plus-approved-medium-v2','raw':raw};amendments[digest(raw)]=amendments[oldsha]
 overlayartifacts['recurrence-classification-runtime-v2']={'runtimeSha256':filehash(runtimepath),'peerPath':str(peerpath.relative_to(ROOT)),'peerSha256':filehash(peerpath)}
 rationalpeerpath=ROOT/'docs/bank/problem-quality/rational-sequence-option-peer-v1.json';rationalpeer=json.loads(rationalpeerpath.read_text())
 assert filehash(rationalpeerpath)=='a94f0d1fce6bfe81f81d942ff8f4ae72fc9fdb6f9043867d7fcf3f8809982ba0'
 assert len(rationalpeer['records'])==10 and all(r['passed']and r['rawSha256']in overlays for r in rationalpeer['records'])
 overlayartifacts['rational-independent-peer']={'peerPath':str(rationalpeerpath.relative_to(ROOT)),'peerSha256':filehash(rationalpeerpath)}
 actual={r['problemId']:r for n in ['canonical-previews.jsonl','retained-originals.jsonl']for r in readlines(stage/n)}
 effective=readlines(stage/'effective-option-input.jsonl');admit=json.loads((stage/'admission-previews.json').read_text())
 assert len(effective)==1405 and set(actual)=={r['problemId']for r in effective}
 groupmap=[];joins=[];construction=[];used=set();changed=0
 for display in effective:
  r=actual[display['problemId']];rid=r.get('provenance',{}).get('authoring',{}).get('reviewId');e=admit.get(rid);repair=overlays.get(e['rawSha256'])if e else None
  oldid=repair['raw']['sourcePreview']['problemId']if repair else r['problemId']
  assert oldid in base_records and oldid not in used,(r['problemId'],oldid)
  used.add(oldid);old=base_records[oldid];l=base_map[oldid]
  amendment=amendments.get(e['rawSha256'])if e else None
  expected_level=amendment['recommendedDifficulty']if amendment else l['recommendedDifficulty']
  assert r['topic']==l['topic']and r['difficulty']==expected_level,(r['problemId'],r['difficulty'],expected_level)
  assert norm(r['statement'])==norm(old['statement'])
  assert menu(display)==menu(r)
  if repair:
   assert menu(r)==menu(repair['raw']);changed+=1
   status='independently-reviewed-repaired-menu';reason=repair['bundle']
  else:
   assert menu(r)==menu(old),(r['problemId'],'unreviewed option change')
   status='same-reviewed-menu';reason='unchanged-options-after-serving-natural-log-normalization'
  m={'problemId':r['problemId'],'problemRevision':r['problemRevision'],'contentHash':r['contentHash'],'semanticHash':r['semanticHash'],'topic':r['topic'],'familyId':r['familyId'],
   'canonicalConstruction':l['constructionFamilyId'],'relatedIdeaGroupId':l['relatedIdeaGroupId'],'structuralSignature':l['structuralSignature'],'primaryTechnique':amendment['primaryTechnique']if amendment else l['primaryTechnique'],
   'servedPrimaryTechnique':r['pedagogy']['primaryTechnique'],'centralDecision':amendment['centralDecision']if amendment else l['centralDecision'],'normalizedTaskKey':l['normalizedTaskKey'],'qualifiedOlympiad':l['qualifiedOlympiad'],
   'recommendedDifficulty':expected_level,'sourceRecommendedDifficulty':l['recommendedDifficulty'],'classificationAmendmentSha256':filehash(classification_path)if amendment else None,'normalizationReason':l.get('normalizationReason'),'sourceV2ProblemId':oldid,'sourceLineageKind':l['kind'],'sourceLineageRawHash':l.get('rawHash'),
   'sourceLineageProblemId':l.get('problemId'),'reviewedScreenConstructionId':screen_family[oldid],'mathReviewReport':r.get('validation',{}).get('evidence',{}).get('independentReviewReport'),
   'mathReviewReportSha256':r.get('validation',{}).get('evidence',{}).get('independentReviewReportSha256'),'menuStatus':status,'menuSource':reason}
  groupmap.append(m);construction.append({**display,'familyId':screen_family[oldid]})
  joins.append({'problemId':r['problemId'],'contentHash':r['contentHash'],'sourceV2ProblemId':oldid,'sameProblemId':r['problemId']==oldid,'sameServedOptionsAndAnswer':menu(r)==menu(old),'menuSource':reason,'sourceV2CanonicalHash':digest(old),'destinationCanonicalHash':digest(r),'sourceLineageHash':digest(l)})
 assert used==set(base_map)and changed==20
 itemdispositions=json.loads((base/'item-dispositions.json').read_text());retired=itemdispositions['retiredProblemIds']
 assert len(retired)==47 and not(set(retired)&set(actual))
 summary={}
 for topic in ['differentiation','limits']:
  rows=[r for r in groupmap if r['topic']==topic];q=[r for r in rows if r['qualifiedOlympiad']]
  assert all((r['recommendedDifficulty']=='olympiad')==r['qualifiedOlympiad']for r in rows)
  summary[topic]={'records':len(rows),'levels':dict(collections.Counter(r['recommendedDifficulty']for r in rows)),'qualifiedRecords':len(q),'qualifiedIdeaGroups':len({r['relatedIdeaGroupId']for r in q}),'qualifiedNormalizedTasks':len({r['normalizedTaskKey']for r in q})}
 assert summary['differentiation']['qualifiedIdeaGroups']==30 and summary['differentiation']['qualifiedNormalizedTasks']==244
 assert summary['limits']['qualifiedIdeaGroups']==30 and summary['limits']['qualifiedNormalizedTasks']==241
 out.mkdir()
 for name,rows in [('construction-option-input.jsonl',construction),('storage-option-input.jsonl',effective),('normalized-record-map.jsonl',groupmap)]:
  (out/name).write_text(''.join(canon(r)+'\n'for r in rows))
 baseline=[{k:r.get(k)for k in ['problemId','familyId','topic','constructionFamilyId','relatedIdeaGroupId','structuralSignature','primaryTechnique','centralDecision','normalizedTaskKey','normalizationReason','qualifiedOlympiad','recommendedDifficulty','disposition']}for r in original.values()]
 (out/'baseline-original-lineage-map.json').write_text(json.dumps({'sourceSha256':filehash(lineagepath),'records':baseline},indent=2)+'\n')
 report={'schemaVersion':1,'sourceStage':str(stage),'sourceArtifacts':{name:filehash(stage/name)for name in ['canonical-previews.jsonl','retained-originals.jsonl','effective-option-input.jsonl','admission-previews.json']},'lineageSha256':filehash(lineagepath),'overlayArtifacts':overlayartifacts,
  'counts':{'records':len(groupmap),'storageFamilies':len({r['familyId']for r in groupmap}),'canonicalConstructions':len({r['canonicalConstruction']for r in groupmap}),'screenConstructions':len({r['familyId']for r in construction}),'sameServedMenus':sum(r['sameServedOptionsAndAnswer']for r in joins),'repairedMenus':changed,'retiredIdentities':len(retired)},
  'qualificationSummary':summary,'classificationAmendmentSha256':filehash(classification_path),'demotions':[r['problemId']for r in groupmap if r['sourceRecommendedDifficulty']!=r['recommendedDifficulty']],'retiredProblemIds':retired,'excludedReviewedRecords':itemdispositions['excludedReviewedRecords'],'records':joins,'limitations':'This exact source/group join preserves reviewed qualification and menu scope and applies only the ten source-bound recurrence demotions. It does not replace the frozen finite mathematical reviews, the independent two-repair reviews, the final-ID option dispositions, or the global release evaluator.'}
 (out/'source-and-lineage-joins.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'out':str(out),'counts':report['counts'],'qualificationSummary':summary}))
if __name__=='__main__':main()
