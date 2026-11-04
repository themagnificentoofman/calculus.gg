"""Package reviewed finite integration assets; never admits or publishes content.

Run with --source-repo and --research-root. Input assets are copied byte exactly.
The manifest records their actual inspected locations; runtime paths are relative.
"""
from pathlib import Path
import argparse,collections,copy,hashlib,json,shutil

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return [(i+1,t,json.loads(t)) for i,t in enumerate(p.read_text().splitlines()) if t]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-repo',type=Path,required=True);ap.add_argument('--research-root',type=Path,required=True);ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent);args=ap.parse_args()
 root=args.source_repo.resolve();research=args.research_root.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 sourcecopies={}
 def cp(src,dst):
  src=src.resolve();target=out/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
  sourcecopies[dst]={'originalPath':str(src),'sha256':sha(src),'bytes':src.stat().st_size};assert sha(src)==sha(target)
  return dst
 def tree(src,dst):
  for p in sorted(src.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.md']:
    cp(p,dst+'/'+str(p.relative_to(src)))
 def put(name,value):
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 ip=root/'scripts/bank/quality/integration';pre=root/'.bank-data/quality/integration-previews-v1';sign=research/'ode-multivariable/integration-sign-frozen-v3';docs=root/'docs/bank/problem-quality'
 # Keep the exact old repository-relative import geometry for historical recipes.
 fr='frozen-repo'
 cp(root/'scripts/bank/content_pipeline.py',fr+'/scripts/bank/content_pipeline.py')
 tree(root/'scripts/bank/content',fr+'/scripts/bank/content')
 for p in sorted(ip.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl']:
   cp(p,fr+'/scripts/bank/quality/integration/'+p.name)
 tree(ip/'advanced','sources/advanced');tree(ip/'headroom','sources/headroom');tree(sign,'sources/sign')
 # All current lower guarded rows are superseded; preserve their source input,
 # but do not expose an executable route for excluded rows.
 cp(root/'scripts/bank/quality/ode-mv/frozen/integration-lower-revisions.jsonl','inputs/integration-lower-revisions.jsonl')
 for name in ['source-bindings.json','admission-previews.json','canonical-previews.jsonl','report.json']:
  cp(pre/name,'inputs/preview350/'+name)
 evidence={}
 for name in ['integration-peer-review.json','integration-normalized-capacity.json','integration-lower-delivery-review.json','integration-option-peer-v2.json','integration-sign-option-peer-v3.json']:
  evidence[name]=cp(docs/'integration'/name,'evidence/'+name)
 cp(docs/'integration/integration-peer-review.json',fr+'/docs/bank/problem-quality/integration/integration-peer-review.json')
 evidence['new-integration-peer-v2.json']=cp(docs/'new-integration-peer-v2.json','evidence/new-integration-peer-v2.json')
 evidence['bessel-option-peer-review.json']=cp(research/'ode-multivariable/bessel-option-peer-review.json','evidence/bessel-option-peer-review.json')
 evidence['endpoint-bound-review.json']=cp(research/'integration-new/endpoint-options-review/all-ten-bound-review.json','evidence/endpoint-bound-review.json')
 tree(research/'integration-new/headroom-peer','evidence/headroom-peer')
 tree(research/'integration-new/endpoint-options-review','evidence/endpoint-peer')
 evidence['headroom-review.json']='evidence/headroom-peer/all-finite-review.json'
 files={
  'integration-extensions':fr+'/scripts/bank/quality/integration/integration-extensions.jsonl',
  'integration-repairs':fr+'/scripts/bank/quality/integration/integration-repairs.jsonl',
  'integration-options':fr+'/scripts/bank/quality/integration/integration-option-repairs-v2.jsonl',
  'integration-historical':fr+'/scripts/bank/quality/integration/historical-candidates.jsonl',
  'integration-new':'sources/advanced/candidates.jsonl',
  'integration-lower-guarded':'inputs/integration-lower-revisions.jsonl',
  'integration-sign':'sources/sign/integration-sign-option-candidates-v3.jsonl',
  'integration-bessel':fr+'/scripts/bank/quality/integration/bessel-option-candidates-v1.jsonl',
  'integration-moments':'sources/headroom/moment-candidates.jsonl',
  'integration-hilbert':'sources/headroom/hilbert-candidates.jsonl'}
 modules={'integration-extensions':'quality.integration.extensions','integration-repairs':'quality.integration.repairs','integration-options':'quality.integration.option_repairs','integration-historical':'quality.integration.historical','integration-new':'integrals','integration-sign':'integration_sign_options','integration-bessel':'quality.integration.bessel_options','integration-moments':'moments','integration-hilbert':'hilbert'}
 hashes={route:{H(r):(line,t,r)for line,t,r in rows(out/file)} for route,file in files.items()}
 oldplan=read(pre/'admission-previews.json');oldbindings={q['reviewId']:q for q in read(pre/'source-bindings.json')};oldbyid={q['problemId']:oldplan[q['reviewId']] for q in oldbindings.values()}
 signrows=[r for _,_,r in rows(out/files['integration-sign'])];signbyid={r['sourcePreview']['problemId']:r for r in signrows}
 oldpeer={r['problemId']:r for r in read(out/evidence['integration-peer-review.json'])['records']}
 normpeer={r['problemId']:r for r in read(out/evidence['integration-normalized-capacity.json'])['records']}
 capacity={r['problemIdOrPendingKey']:r for r in read(out/evidence['integration-lower-delivery-review.json'])['perItemCapacityPlan']}
 signpeer={(r['familyId'],r['index']):r for r in read(out/evidence['integration-sign-option-peer-v3.json'])['records']}
 besselpeer={(r['familyId'],r['index']):r for r in read(out/evidence['bessel-option-peer-review.json'])['records']}
 endpoint={(r['familyId'],r['instanceIndex']):r for r in read(out/evidence['endpoint-bound-review.json'])['records']}
 headroom={(r['familyId'],r['instanceIndex']):r for r in read(out/evidence['headroom-review.json'])['records']}
 superseded=[];joins=[];selectedlines=[]
 def ref(file,record):return {'file':file,'sha256':sha(out/file),'record':record,'humanReviewed':False,'formalProof':False}
 def add(route,rawhash,index,review,preview=None,extra=()):
  line,t,r=hashes[route][rawhash];f=r['familyId'];assert review['normalizedLineageKey'] and review['difficulty']in ['easy','medium','hard','olympiad']
  entry={'route':route,'familyId':f,'index':index,'builderModule':modules[route],'builderKind':'build','sourceFile':files[route],'sourceLine':line,'sourceLineSha256':hashlib.sha256(t.encode()).hexdigest(),'rawSha256':rawhash,'rawContentHash':r.get('contentHash'),'rawSemanticHash':r.get('semanticHash'),'rawProblemId':r.get('problemId'),'constructorVersion':r.get('constructorVersion'),'parameters':r.get('parameters'),'previous':r.get('previous'),'replacesPrivateProblemId':r.get('replacesPrivateProblemId'),'sourcePreview':r.get('sourcePreview',preview),'reviewPlan':review,'additionalIndependentEvidence':list(extra)}
  joins.append(entry);selectedlines.append(t)
 for key,p in oldplan.items():
  bind=oldbindings[key];route=p['module'];rawhash=p['rawSha256'];assert rawhash in hashes[route]
  if bind['problemId']in signbyid:
   z=signbyid[bind['problemId']];superseded.append({'reviewId':key,'route':route,'familyId':p['familyId'],'index':p['index'],'rawSha256':rawhash,'privatePreviewProblemId':bind['problemId'],'replacementRawSha256':H(z),'replacementFamilyId':z['familyId'],'replacementIndex':z['instanceIndex']});continue
  review=copy.deepcopy(p['review']);report='evidence/'+Path(review['report']).name;assert sha(out/report)==review['reportSha256'];review['report']=report
  review.pop('optionAuditReport',None);review.pop('optionAuditSha256',None);review['finalActualIdOptionAudit']='pending-root-admission';extra=[]
  if (p['familyId'],p['index'])in endpoint:
   e=endpoint[(p['familyId'],p['index'])];assert e['sourceRawSHA256']==rawhash
   review.update(difficulty='hard',qualifiedOlympiad=False,easiestOptionsVisibleRoute='The independently proved Cauchy–Schwarz lower bound and affine-trial upper bound isolate the correct literal choice.',difficultyRationale='Only elementary integral bounds and a concrete affine trial are required by these actual options; the sharp spectral derivation is longer.')
   extra.append(ref(evidence['endpoint-bound-review.json'],{'familyId':p['familyId'],'instanceIndex':p['index'],'sourceRawSHA256':rawhash}))
  add(route,rawhash,p['index'],review,{'problemId':bind['problemId'],'contentHash':bind['contentHash'],'unpublished':True},extra)
 for r in signrows:
  f,i=r['familyId'],r['instanceIndex'];sid=r['sourcePreview']['problemId'];peer=signpeer[f,i];assert peer['rawSha256']==H(r) and peer['passed']
  prior=oldbyid.get(sid);norm=normpeer.get(sid);cap=capacity.get(sid)
  review=copy.deepcopy(prior['review']) if prior else {}
  review.pop('optionAuditReport',None);review.pop('optionAuditSha256',None)
  level=review.get('difficulty',oldpeer.get(sid,{}).get('difficultyRecommended',r['difficulty']))
  key=review.get('normalizedLineageKey') or (norm or {}).get('equivalenceKey') or (cap or {}).get('normalizedLineageKey') or 'existing-instance:new:'+f+':m:'+str(r['parameters']['m'])
  review.update(status='independently-reviewed',author='integration_research-option-author',reviewer='root-independent-peer',report=evidence['integration-sign-option-peer-v3.json'],reportSha256=sha(out/evidence['integration-sign-option-peer-v3.json']),difficulty=level,qualifiedOlympiad=level=='olympiad',normalizedLineageKey=key,relatedIdeaGroupId=r['pedagogy']['relatedIdeaGroupId'],centralDecision=peer['route'],easiestOptionsVisibleRoute=peer['route'],nearestNeighbor=review.get('nearestNeighbor','Same underlying source task and lineage; the option repair creates no new construction.'),difficultyRationale=review.get('difficultyRationale',r['pedagogy']['difficultyRationale']),finalActualIdOptionAudit='pending-root-admission')
  extra=[]
  if prior:
   pr=prior['review'];ef='evidence/'+Path(pr['report']).name;extra.append(ref(ef,{'priorRawSha256':prior['rawSha256'],'priorReviewId':prior['reviewId']}))
  elif sid in oldpeer:extra.append(ref(evidence['integration-peer-review.json'],{'problemId':sid,'sourceContentHash':r['previous']['sourceContentHash']}))
  else:extra.append(ref(evidence['integration-lower-delivery-review.json'],{'problemIdOrPendingKey':sid,'sourcePreview':r['sourcePreview']}))
  if norm:extra.append(ref(evidence['integration-normalized-capacity.json'],{'problemId':sid,'equivalenceKey':norm['equivalenceKey']}))
  add('integration-sign',H(r),i,review,extra=extra)
 for _,_,r in rows(out/files['integration-bessel']):
  f,i=r['familyId'],r['instanceIndex'];p=besselpeer[f,i];assert p['rawHash']==H(r);sid=r['previous']['problemId'];key=normpeer.get(sid,{}).get('equivalenceKey','existing-instance:'+sid)
  review={'status':'independently-reviewed','author':'root','reviewer':'integration_research-independent-peer','report':evidence['bessel-option-peer-review.json'],'reportSha256':sha(out/evidence['bessel-option-peer-review.json']),'difficulty':'hard','qualifiedOlympiad':False,'normalizedLineageKey':key,'relatedIdeaGroupId':r['pedagogy']['relatedIdeaGroupId'],'centralDecision':p['easiestOptionsVisibleRoute'],'easiestOptionsVisibleRoute':p['easiestOptionsVisibleRoute'],'difficultyRationale':p['difficultyRationale'],'nearestNeighbor':p['nearestNeighbor'],'finalActualIdOptionAudit':'pending-root-admission'}
  add('integration-bessel',H(r),i,review)
 for route in ['integration-moments','integration-hilbert']:
  for _,_,r in rows(out/files[route]):
   f,i=r['familyId'],r['instanceIndex'];p=headroom[f,i];assert p['rawSHA256']==H(r)
   review={'status':'independently-reviewed','author':'root','reviewer':'source_research-independent-peer','report':evidence['headroom-review.json'],'reportSha256':sha(out/evidence['headroom-review.json']),'difficulty':p['advancedFit'],'qualifiedOlympiad':True,'normalizedLineageKey':p['normalizedTaskKey'],'relatedIdeaGroupId':r['pedagogy']['relatedIdeaGroupId'],'centralDecision':p['analyticProofReview'],'easiestOptionsVisibleRoute':p['analyticProofReview'],'difficultyRationale':'The actual four literal pairs survive the recorded simpler bounds; the full constraint or sharpness argument is necessary.','nearestNeighbor':p.get('globalRelatedLineage','The frozen two-moment bounded-density extrema construction; these are additional distinct dimensionless constraint geometries, zero new ideas.'),'globalRelatedLineage':p.get('globalRelatedLineage'),'finalActualIdOptionAudit':'pending-root-admission'}
   add(route,H(r),i,review)
 assert len(superseded)==64 and len(joins)==468
 assert len({(x['route'],x['familyId'],x['index'])for x in joins})==len(joins)
 assert len({x['rawSha256']for x in joins})==len(joins)
 previous=[x['previous']['problemId']for x in joins if x['previous']];assert len(previous)==len(set(previous)), 'Two replacements for one baseline identity'
 replaced=[x['replacesPrivateProblemId']for x in joins if x['replacesPrivateProblemId']];assert len(replaced)==len(set(replaced))
 plans={}
 for j in joins:
  k=(j['route'],j['familyId']);plans.setdefault(k,[]).append(j['index'])
 catalog=[{'route':route,'familyId':family,'indices':sorted(indices),'builderModule':modules[route],'admitted':False} for (route,family),indices in sorted(plans.items())]
 (out/'final-candidates.jsonl').write_text('\n'.join(selectedlines)+'\n')
 put('catalog.json',catalog)
 put('source-joins.json',{'status':'reviewed-source-package-not-admitted','records':joins,'humanReviewed':False,'formalProof':False})
 put('supersession-ledger.json',{'sourcePreviews':350,'supersededCount':64,'retainedPreviewRecords':286,'signRepairRecords':152,'besselRecords':8,'headroomRecords':22,'finalRecords':468,'identityPolicy':'Exact sourcePreview problem ID join to private preview; immutable baseline previous links are separately preserved. No same-family records remain unsuperseded.','records':superseded})
 put('admission-plan.json',{'status':'not-admitted','finalActualIdOptionAudit':'pending','records':[{'route':j['route'],'familyId':j['familyId'],'index':j['index'],'rawSha256':j['rawSha256'],'recommendedDifficulty':j['reviewPlan']['difficulty'],'normalizedLineageKey':j['reviewPlan']['normalizedLineageKey'],'qualifiedOlympiad':j['reviewPlan']['qualifiedOlympiad'],'previous':j['previous'],'replacesPrivateProblemId':j['replacesPrivateProblemId'],'review':j['reviewPlan']}for j in joins]})
 created=['catalog.json','source-joins.json','supersession-ledger.json','admission-plan.json','final-candidates.jsonl','assemble_bundle.py','runtime.py','worker.py','verify_bundle.py','README.md']
 manifest={'status':'portable-offline-source-bundle-not-admitted','records':len(joins),'routes':dict(collections.Counter(j['route']for j in joins)),'recommendedDifficulty':dict(collections.Counter(j['reviewPlan']['difficulty']for j in joins)),'rawDifficultyPreserved':True,'sourceCopies':sourcecopies,'createdAssets':{n:sha(out/n)for n in created if(out/n).exists()},'runtimeAPI':['catalog()','build(route, family, index)','verify(route, record, index) -> bool','reconstruction_evidence(route, family, index)','close()'],'sourceClosureNote':'Legacy repository geometry and content modules are copied byte exactly. The worker supplies local BANK_AUDIT_CONTENT_DIR and BANK_AUDIT_ARTIFACT before importing support.py; its preserved legacy fallback strings are never used. Each route has its own process and independent module namespace.','limits':['Reconstruction is not independent mathematical verification; copied peer evidence supplies that separate scope.','Analytic proof review is AI-assisted, not human review or formal proof.','Final actual destination IDs, option screens, registry, admission and production import are outside this bundle.','Per-record recommended difficulty is metadata; original raw candidate bytes stay frozen.','Only reviewed batch rows are packaged, not the unchanged retained baseline pool; batch counts are not total serving capacity.']}
 put('copy-manifest.json',manifest)
 print(json.dumps({'records':len(joins),'superseded':len(superseded),'routes':manifest['routes'],'sourceCopies':len(sourcecopies),'manifestSha256':sha(out/'copy-manifest.json')}))
if __name__=='__main__':main()
