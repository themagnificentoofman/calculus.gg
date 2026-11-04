from pathlib import Path
from collections import Counter
import copy,json,hashlib
P=Path(__file__).resolve().parent;BASE=P.parent/'final1531-v4';ROOT=P.parents[2]/'problem-quality';STAGE=ROOT/'.bank-data/quality/ode-mv-previews-v7'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x)for x in p.read_text().splitlines()]
prior=json.load(open(BASE/'group-map-v4.json'));priorMap={r['problemId']:r for r in prior['records']}
oldRows={r['problemId']:r for r in lines(ROOT/'.bank-data/quality/ode-mv-previews-v4/canonical-previews.jsonl')+lines(ROOT/'.bank-data/quality/ode-mv-previews-v4/retained-originals.jsonl')}
rows=lines(STAGE/'canonical-previews.jsonl')+lines(STAGE/'retained-originals.jsonl');served={r['problemId']:r for r in lines(P/'served-records.jsonl')};entries=json.load(open(STAGE/'admission-previews.json'))
joinStages=['ode-mv-previews-v5','ode-mv-previews-v6','ode-mv-previews-v7'];late={}
for stage in joinStages:
 for r in json.load(open(ROOT/'.bank-data/quality'/stage/'replacement-joins.json')):
  assert r['problemId']not in late
  late[r['problemId']]={**r,'joinStage':stage}
peerNames=['nonnormal-option-peer-v2.json','density-classification-peer-v1.json','ground-option-peer-v4.json'];peerExpected=['d2ceb7225fb848f2c608ab3469401a4c40284378e8683209f722c6b1b7b201eb','09c834e55395d6226768623f86c2d1b54305ce5a07d8e2e59f86a399cec42636','985040f6c79daf569cb3a74bdc3c5cb235885e7f3014b74c8450a6ebb6d9c41f'];peers={}
for name,expected in zip(peerNames,peerExpected):
 p=ROOT/'docs/bank/problem-quality'/name;assert sha(p)==expected
 for i,r in enumerate(json.load(open(p))['records']):
  assert r['passed'];assert len(r.get('literalPairs',r.get('literalPairDifferences',[])))==6
  peers[r['rawSha256']]={'path':str(p.relative_to(ROOT)),'fileSha256':expected,'recordIndex':i,'record':r}
assert len(late)==len(peers)==26
out=[];joins=[];failures=[]
for row in rows:
 pid=row['problemId'];j=late.get(pid);oldId=j['oldPreviewProblemId']if j else pid;old=oldRows[oldId];m=copy.deepcopy(priorMap[oldId]);e=entries.get(row['provenance'].get('authoring',{}).get('reviewId'));p=served[pid]
 assert row['familyId']==old['familyId'] and row['semanticHash']==old['semanticHash'],pid
 if not j:assert digest(row)==digest(old),(pid,'unamended source changed')
 m.update({'problemId':pid,'revision':row['problemRevision'],'contentHash':row['contentHash'],'semanticHash':row['semanticHash'],'currentDifficulty':row['difficulty'],'recommendedDifficulty':row['difficulty'],'sourceV4ProblemId':oldId,'sourceCanonicalRawHash':digest(row),'servedRawHash':digest(p),'servedChoiceMenuHash':digest(p['choices']),'newIdeaFromOptionRepair':False,'newIndependentIdeas':0,'unresolved':[]})
 if j:
  assert e and e['rawSha256']==j['rawSha256'];peer=peers[e['rawSha256']];r=peer['record'];assert e['review']['report']==peer['path'] and e['review']['reportSha256']==peer['fileSha256'];assert e['review']['difficulty']==row['difficulty']
  assert j['normalizedTaskKey']==m['normalizedTaskKey']==e['review']['normalizedLineageKey'];assert m['relatedIdeaGroupId']==e['review']['relatedIdeaGroupId']==j['relatedIdeaGroupId']
  assert e['index']==r['index'] and e['familyId']==r['familyId'];assert j['sameMathematicalTask']
  m['qualifiedOlympiad']=bool(e['review']['qualifiedOlympiad']);m['centralDecision']=e['review']['easiestOptionsVisibleRoute'];m['finalReviewId']=e['reviewId'];m['rawSha256']=e['rawSha256'];m['sourceIdentityPath']=([pid]if pid!=oldId else[])+m['sourceIdentityPath']
  m['sourceRevisionPath']=[{'problemId':oldId,'revision':old['problemRevision'],'contentHash':old['contentHash']},{'problemId':pid,'revision':row['problemRevision'],'contentHash':row['contentHash']}]
  m['finalIndependentReview']={k:v for k,v in peer.items()if k!='record'};m['sourceBindings'].append({**m['finalIndependentReview'],'rawSha256':e['rawSha256'],'sourceProblemId':oldId,'sourceContentHash':old['contentHash']})
  if r.get('recommendedDifficulty'):assert row['difficulty']==r['recommendedDifficulty'] and m['qualifiedOlympiad']==r['qualifiedOlympiad']
  if e.get('previous'):
   previous=e['previous'];assert previous['problemId']==oldId and previous['sourceContentHash']==old['contentHash'] and not previous['meaningChanged'];assert pid==oldId and row['problemRevision']==old['problemRevision']+1
  else:assert row['problemRevision']==1
  joins.append({'oldProblemId':oldId,'oldRevision':old['problemRevision'],'oldContentHash':old['contentHash'],'oldCanonicalRawHash':digest(old),'problemId':pid,'revision':row['problemRevision'],'contentHash':row['contentHash'],'canonicalRawHash':digest(row),'servedRawHash':digest(p),'servedChoiceMenuHash':digest(p['choices']),'semanticHash':row['semanticHash'],'familyId':row['familyId'],'index':e['index'],'route':e['module'],'reviewId':e['reviewId'],'rawSha256':e['rawSha256'],'independentReview':m['finalIndependentReview'],'canonicalConstruction':m['canonicalConstruction'],'relatedIdeaGroupId':m['relatedIdeaGroupId'],'structuralSignature':m['structuralSignature'],'primaryTechnique':m['primaryTechnique'],'centralDecision':m['centralDecision'],'normalizedTaskKey':m['normalizedTaskKey'],'recommendedDifficulty':row['difficulty'],'qualifiedOlympiad':m['qualifiedOlympiad'],'newIndependentIdeas':0,'joinStage':j['joinStage'],'sourceKind':'immutable-retained-revision'if e.get('previous')else'private-replacement','passed':True})
 elif e:
  assert e['review']['relatedIdeaGroupId']==m['relatedIdeaGroupId'];assert bool(e['review']['qualifiedOlympiad'])==m['qualifiedOlympiad'];assert e['review']['difficulty']==row['difficulty']
 # Record all actual and historical aliases without making them new tasks.
 aliases=set(m['sourceIdentityPath']);aliases.add(oldId)
 for b in m['sourceBindings']:
  for field in['problemId','sourceProblemId']:
   if b.get(field):aliases.add(b[field])
 if e and e.get('previous'):aliases.add(e['previous']['problemId'])
 m['historicalIdentityAliases']=sorted(aliases)
 if row['familyId'].endswith('nonnormal-transient-maximum')and e['index']in[2,5,8]:assert row['difficulty']=='hard' and not m['qualifiedOlympiad']
 if row['familyId'].endswith('oscillator-minimum-control-energy')and row['parameters']['instance']in[4,6,9]:assert row['difficulty']=='hard' and not m['qualifiedOlympiad']
 if row['familyId'].endswith('density-centroid'):assert row['difficulty']=='easy' and not m['qualifiedOlympiad']
 assert m['qualifiedOlympiad']==(row['difficulty']=='olympiad'),pid
 out.append(m)
assert len(out)==1531 and len(joins)==26
summaries={}
for topic in sorted({r['topic']for r in out}):
 summaries[topic]={}
 for level in['easy','medium','hard','olympiad']:
  rs=[r for r in out if r['topic']==topic and r['recommendedDifficulty']==level];unique={r['normalizedTaskKey']:r for r in rs};families=Counter(r['canonicalConstruction']for r in unique.values());H=10 if level=='olympiad' else 5
  summaries[topic][level]={'records':len(rs),'normalizedItems':len(unique),'constructionFamilies':len(families),'relatedIdeas':len({r['relatedIdeaGroupId']for r in rs}),'qualifiedIdeas':len({r['relatedIdeaGroupId']for r in rs if r['qualifiedOlympiad']}),'capEffective':sum(min(n,2*H)for n in families.values()),'byFamily':dict(families)}
sourceFiles=[STAGE/x for x in['canonical-previews.jsonl','retained-originals.jsonl','admission-previews.json']]+[BASE/'group-map-v4.json',P/'served-records.jsonl']+[ROOT/'.bank-data/quality'/s/'replacement-joins.json'for s in joinStages]+[ROOT/'docs/bank/problem-quality'/x for x in peerNames]
report={'status':'complete-actual-id-source-bound-final-v7-map','counts':{'records':1531,'candidates':1150,'retainedOriginals':381,'lateAmendments':26,'privateReplacements':12,'immutableRetainedRevisions':14},'sourceArtifacts':{str(p):sha(p)for p in sourceFiles},'capacity':summaries,'records':out,'unresolved':[],'scope':'Exact final identity and immutable source/served rebinding of previously reviewed1531 ODE/MV records plus26 late independently reviewed amendments. No new independent solve of1531 records is claimed. No repair receives new idea credit.'}
(P/'group-map.json').write_text(json.dumps(report,indent=2)+'\n');(P/'destination-joins.json').write_text(json.dumps({'status':'complete26-exact-destination-source-and-independent-peer-joins','records':joins,'unresolved':[]},indent=2)+'\n');print(json.dumps({'records':1531,'lateJoins':26,'capacity':{t:{l:{k:v for k,v in q.items()if k!='byFamily'}for l,q in levels.items()}for t,levels in summaries.items()}}))
