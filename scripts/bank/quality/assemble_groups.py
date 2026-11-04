"""One reviewed vocabulary and conservative task lineage for both selector runs."""
from pathlib import Path
import collections,hashlib,json
from .contract import ROOT,canonical
DOC=ROOT/'docs/bank/problem-quality';STAGE=ROOT/'.bank-data/quality/final-candidates-v1'
def read(p):return json.loads(p.read_text())
def lines(p):return list(map(json.loads,p.read_text().splitlines()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=STAGE/'group-definitions.json'
 if out.exists():raise ValueError('Preserve previous group definitions')
 sources={}
 def bound(p):sources[str(p.resolve())]=sha(p);return read(p)
 final=bound(STAGE/'source-definitions.json');original_definitions={r['problemId']:r for r in final}
 baseline_path=ROOT.parent/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl'
 sources[str(baseline_path)]=sha(baseline_path);baseline=lines(baseline_path)
 assert len(baseline)==2504 and len(final)==4407
 candidates=lines(STAGE/'canonical-candidates.jsonl');retained=lines(STAGE/'retained-originals.jsonl');current={r['problemId']:r for r in candidates+retained}
 review=bound(DOC/'cross-topic-grouping-audit-v1/cross-topic-grouping-audit.json')
 methods=bound(DOC/'cross-topic-grouping-audit-v1/cross-topic-method-aliases.json');spell=bound(DOC/'cross-topic-grouping-audit-v1/global-spelling-aliases.json')
 for artifact in review['sourceArtifacts'].values():assert sha(ROOT/artifact['path'])==artifact['sha256']
 final_byid={r['problemId']:r for r in final};related={};method_by_id={};structure_by_id={}
 for a in review['relatedIdeaAliases']:
  for alias in a['sourceAliases']:
   if alias in related:assert related[alias]==a['canonicalRelatedIdeaGroupId']
   related[alias]=a['canonicalRelatedIdeaGroupId']
 def plan(rows,key,field,target):
  for a in rows:
   for record in a['sourceRecords']:
    m=final_byid[record['problemId']];assert m.get('reviewedPreviewContentHash',m['contentHash'])==record['contentHash']
    assert m[field]in a['sourceAliases'],(record['problemId'],field,m[field])
    target[record['problemId']]=a[key]
 plan(review['primaryMethodAliases'],'canonicalPrimaryTechnique','primaryTechnique',method_by_id)
 plan(review['structuralAliases'],'canonicalStructuralSignature','structuralSignature',structure_by_id)
 # The narrow cross-topic primary-method audit intentionally follows the
 # family-specific vocabulary repair; it never rewrites generic labels globally.
 for a in methods['aliases']:
  for record in a['sourceRecords']:
   m=final_byid[record['problemId']];assert m.get('reviewedPreviewContentHash',m['contentHash'])==record['contentHash']
   assert record['after']==a['canonicalPrimaryTechnique'];method_by_id[record['problemId']]=record['after']
 corrections=methods['preservedOwnerMethodCorrection']['exactSourceRecords']
 peer=bound(DOC/'control-energy-peer.json');assert peer['passed'] and len(corrections)==3
 for record in corrections:
  m=final_byid[record['problemId']];assert m['recommendedDifficulty']=='hard' and m.get('reviewedPreviewContentHash',m['contentHash'])==record['contentHash']
  method_by_id[record['problemId']]='Cauchy-Schwarz-and-cubic-trial-bounds'
 spelling={a['sourceAlias']:a['canonicalSpelling']for a in spell['aliases']}
 def vocabulary(m,apply_id=True):
  m=dict(m);pid=m['problemId'];m['relatedIdeaGroupId']=related.get(m['relatedIdeaGroupId'],m['relatedIdeaGroupId'])
  if apply_id:
   m['primaryTechnique']=method_by_id.get(pid,m['primaryTechnique']);m['structuralSignature']=structure_by_id.get(pid,m['structuralSignature'])
  m['primaryTechnique']=spelling.get(m['primaryTechnique'],m['primaryTechnique']);return m
 final=[vocabulary(m)for m in final];final_byid={r['problemId']:r for r in final}
 dl={r['problemId']:r for r in bound(DOC/'diff-limits/final-v4/baseline-original-lineage-map.json')['records']}
 integration=bound(DOC/'integration/integration-peer-review.json');ip={r['problemId']:r for r in integration['records']}
 inn={r['problemId']:r for r in bound(DOC/'integration/integration-normalized-capacity.json')['records']}
 ode_normal={r['problemId']:r for r in bound(ROOT/'scripts/bank/quality/ode-mv/sources/retained-normalization.json')['records']}
 mv_peer={r['problemId']:r for r in bound(DOC/'existing-multivariable-peer.json')['results']}
 ode_baseline={r['problemId']:r for r in bound(DOC/'ode-mv/baseline-original-v3/descriptor-map.json')['records']}
 series_map=DOC/'series/original-baseline-reconciliation-v1/normalized-record-map.jsonl';sources[str(series_map)]=sha(series_map)
 series_baseline={r['problemId']:r for r in lines(series_map)}
 semantic=collections.defaultdict(list)
 for m in final:semantic[m['semanticHash']].append(m)
 baseline_def=[];qualification=collections.Counter()
 for p in baseline:
  pid=p['problemId'];meta=p['pedagogy'];m={'problemId':pid,'revision':p['problemRevision'],'contentHash':p['contentHash'],'semanticHash':p['semanticHash'],'familyId':p['familyId'],'topic':p['topic'],'constructionFamilyId':p['familyId'],'relatedIdeaGroupId':meta['relatedIdeaGroupId'],'structuralSignature':meta['structuralSignature'],'primaryTechnique':meta['primaryTechnique'],'centralDecision':meta['difficultyRationale'],'normalizedTaskKey':pid,'qualifiedOlympiad':False,'recommendedDifficulty':p['difficulty'],'qualificationScope':'Historical metadata only; no unproved advanced credit.'}
  matches=semantic[p['semanticHash']]
  if matches:
   keys={r['normalizedTaskKey']for r in matches};assert len(keys)==1,(pid,'Ambiguous reviewed normalized keys')
   m['normalizedTaskKey']=next(iter(keys))
   constructions={r.get('canonicalConstruction',r.get('constructionFamilyId'))for r in matches};assert len(constructions)==1
   m['constructionFamilyId']=next(iter(constructions))
  if pid in dl:m.update(dl[pid]);m['qualificationScope']='Exact original D/L final lineage/disposition review.'
  if pid in inn:m['normalizedTaskKey']=inn[pid]['equivalenceKey']
  if pid in ip:
   a=ip[pid];assert a['sourceContentHash']==p['contentHash'];m.update(relatedIdeaGroupId=a['reviewedGroup'],qualifiedOlympiad=a['olympiadMethodQualified'] and a['admissionEligibleNow'],recommendedDifficulty=a['difficultyRecommended'],centralDecision=a['easiestVisibleRoute'],qualificationScope='Original literal integration review, including current original-menu eligibility; repaired choices do not confer earlier qualification.')
  if pid in ode_normal:m['normalizedTaskKey']=ode_normal[pid]['normalizedLineageKey']
  if pid in mv_peer:
   a=mv_peer[pid];assert a['sourceContentHash']==p['contentHash'];m.update(qualifiedOlympiad=a['qualifiedOlympiad'],recommendedDifficulty=a['difficultyRecommended'],centralDecision=a['easiestOptionsVisibleRoute'],qualificationScope='Original literal multivariable independent route review.')
  if pid in ode_baseline:
   a=ode_baseline[pid];assert a['contentHash']==p['contentHash'];m.update(a);m['qualificationScope']=a['reviewEvidenceKind']
  if pid in series_baseline:
   a=series_baseline[pid];assert a['contentHash']==p['contentHash'];m.update(a);m['qualificationScope']=a['qualificationStatus']
  exact=final_byid.get(pid)
  if exact and exact['contentHash']==p['contentHash']:
   for field in ['relatedIdeaGroupId','structuralSignature','primaryTechnique','centralDecision','normalizedTaskKey']:m[field]=exact[field]
   if pid not in dl and pid not in ode_baseline and pid not in series_baseline and pid not in ip:
    m['qualifiedOlympiad']=exact['qualifiedOlympiad'];m['recommendedDifficulty']=exact['recommendedDifficulty'];m['qualificationScope']='Unchanged canonical record in final exact-source topic review.'
  # For a revised task, metadata aliases transfer only when the mathematical
  # semantic identity and prior named method still match a reviewed route.
  use_id=bool(exact and exact['semanticHash']==p['semanticHash'] and meta['primaryTechnique']in {exact['primaryTechnique'],final_byid[pid].get('servedPrimaryTechnique'),original_definitions[pid]['primaryTechnique']})
  m=vocabulary(m,use_id);baseline_def.append(m);qualification[m['qualificationScope']]+=1
 # Union established task keys and historical identity. Revisions never erase
 # exposure, and source-normalized scalar classes remain conservative aliases.
 parent={}
 def find(x):
  parent.setdefault(x,x)
  if parent[x]!=x:parent[x]=find(parent[x])
  return parent[x]
 def union(a,b):
  a,b=find(a),find(b)
  if a!=b:parent[b]=a
 for m in baseline_def+final:union('id:'+m['problemId'],'key:'+m['normalizedTaskKey'])
 components=collections.defaultdict(set)
 for m in baseline_def+final:components[find('id:'+m['problemId'])].add(m['problemId'])
 old_ids={p['problemId']for p in baseline};representatives={k:min(ids,key=lambda pid:(pid not in old_ids,pid))for k,ids in components.items()}
 items={pid:representatives[find('id:'+pid)]for ids in components.values()for pid in ids}
 fields=['relatedIdeaGroupId','structuralSignature','primaryTechnique','centralDecision','qualifiedOlympiad','recommendedDifficulty','qualificationScope']
 families={};item_defs={}
 for role,inventory in [('baseline',baseline_def),('candidate',final)]:
  for m in inventory:
   family=m['familyId'];d={k:m[k]for k in fields if k in m};d['constructionFamilyId']=m.get('canonicalConstruction',m.get('constructionFamilyId',family))
   families.setdefault(family,{**d,'qualifiedOlympiad':False})
   d['sourceContentHash']=m['contentHash'];d['sourceFamily']=family
   key=m['problemId']+'@'+str(m.get('revision',m.get('problemRevision')))
   prior=item_defs.get(key)
   if prior:assert prior['sourceContentHash']==d['sourceContentHash']
   d['qualificationByRole']={**(prior.get('qualificationByRole',{})if prior else{}),role:{'qualifiedOlympiad':m['qualifiedOlympiad'],'scope':m.get('qualificationScope','Final independently reviewed task and effective-family option context.')}}
   item_defs[key]=d
 legacy=bound(ROOT/'lib/bank/legacy-features.json')
 for family,v in legacy.items():families[family]={'constructionFamilyId':family,'relatedIdeaGroupId':v['idea'],'structuralSignature':v['structure'],'primaryTechnique':spelling.get(v['technique'],v['technique']),'centralDecision':'Original finite fluency construction; historical integrity retained. No qualified advanced credit without current independent admission.','qualifiedOlympiad':False}
 # One family has one real construction, even if particular options lower the
 # appropriate method or difficulty. Item-level metadata remains explicit.
 family_lineage={}
 for m in baseline_def+final:
  f=m['familyId'];c=m.get('canonicalConstruction',m.get('constructionFamilyId',f))
  if f in family_lineage:assert family_lineage[f]==c,(f,family_lineage[f],c)
  family_lineage[f]=c
 capacity={}
 for topic in sorted({m['topic']for m in final}):
  for level in ['easy','medium','hard','olympiad']:
   pool=[m for m in final if m['topic']==topic and m['recommendedDifficulty']==level];byfamily=collections.defaultdict(set)
   for m in pool:byfamily[m.get('canonicalConstruction',m.get('constructionFamilyId',m['familyId']))].add(items[m['problemId']])
   h=10 if level=='olympiad'else 5;effective=sum(min(len(v),2*h)for v in byfamily.values())
   capacity[topic+'/'+level]={'rawItems':len(pool),'normalizedTasks':len({items[m['problemId']]for m in pool}),'constructionFamilies':len(byfamily),'relatedIdeas':len({m['relatedIdeaGroupId']for m in pool}),'qualifiedIdeas':len({m['relatedIdeaGroupId']for m in pool if m['qualifiedOlympiad']}),'capEffective':effective,'necessary':20*h,'headroom':effective/(20*h)}
 result={'status':'independently-reviewed','sourceArtifacts':sources,'families':families,'items':items,'itemDefinitions':item_defs,'qualificationEvidenceScope':dict(qualification),'candidateCapacity':capacity,'historicalIntegrity':'Original baseline canonical records and selector source remain unchanged. Shared reviewed descriptor definitions apply to both evaluations. Historical-only records without complete current independent advanced review receive no qualified-idea credit.','crossTopicScope':'No new exact/scaled cross-topic equivalence or merged construction inferred from shared methods/related ideas.'}
 out.write_text(json.dumps(result,indent=2)+'\n')
 (STAGE/'lineage-policy.json').write_text(json.dumps({'lineage':[{'problemId':p,'lineageId':l}for p,l in sorted(items.items())if p!=l],'familyLineage':[{'familyId':f,'constructionId':c}for f,c in sorted(family_lineage.items())if f!=c]},indent=2)+'\n')
 (STAGE/'resolved-definitions.json').write_text(json.dumps(final,indent=2)+'\n')
 print(json.dumps({'families':len(families),'exactRevisionDefinitions':len(item_defs),'normalizedAliasRows':sum(p!=l for p,l in items.items()),'candidateCapacity':capacity},indent=2))
if __name__=='__main__':main()
