"""Create a NEW portable asset directory; does not edit admission registries."""
from pathlib import Path
import argparse,collections,copy,hashlib,json,shutil
from capacity_after_options import recalculate
BASE=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
ROUTES={'domain-six':('six-row-frozen-v1','option-patches.json','domain-option-peer-v1.json'),'bracket-eighty':('eighty-row-frozen-v1','bracket-option-patches.json','bracket-option-peer-v1.json'),'support-seventy-six':('last76-frozen-v1','support-option-patches.json','last76-independent-peer.json')}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;assert not out.exists(),'A bundle must be written to a new directory';out.mkdir(parents=True)
 copies=[]
 def cp(src,relative):
  dst=out/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst);copies.append({'path':str(relative),'sha256':sha(dst),'origin':str(src.resolve())})
 sources=list(map(json.loads,(BASE/'full-source-records.jsonl').read_text().splitlines()));full={r['problemId']:r for r in sources};baseline={r['problemId']:r for r in map(json.loads,a.baseline.read_text().splitlines())};projection=list(map(json.loads,(BASE/'effective705-final-v3.jsonl').read_text().splitlines()));project={r['problemId']:r for r in projection};ledgerpath=a.repo/'docs/bank/problem-quality/series/author-capacity-ledger.json';ledger=json.loads(ledgerpath.read_text());oldkeys={(r['familyId'],r['instanceIndex']):r for r in ledger['recordNormalizedKeys']}
 patchrows=[];joins=[];catalog=collections.defaultdict(list);changes=[];peerrows={};peerfiles={}
 for route,(folder,artifact,reportname)in ROUTES.items():
  for path in sorted((BASE/folder).iterdir()):
   if path.is_file():cp(path,Path('frozen')/folder/path.name)
  p=a.repo/'docs/bank/problem-quality/series'/reportname;peer=json.loads(p.read_text());peerfiles[route]={'path':'evidence/'+reportname,'sha256':sha(p)};cp(p,Path('evidence')/reportname)
  assert peer.get('inputSHA256',peer.get('inputSha256'))==sha(BASE/folder/artifact)
  for name,digest in peer.get('reviewCodeSHA256',peer.get('reviewSources')).items():
   source=a.repo/'scripts/bank/quality/peer'/name;assert sha(source)==digest;dst=Path('evidence/independent-code')/name
   if not(out/dst).exists():cp(source,dst)
  peerrows[route]={r['problemId']:r for r in peer['records']};patches=json.loads((BASE/folder/artifact).read_text());assert len(peerrows[route])==len(patches)
  for p in patches:
   r=full[p['problemId']];pr=peerrows[route][r['problemId']];assert H(r)==p['sourceRawSHA256']==pr['sourceRawSHA256'];assert H(p)==pr.get('patchSHA256',pr.get('patchSha256'));assert pr['passed']is True
   key=(p['familyId'],p['instanceIndex']);prior=oldkeys[key];level=pr.get('recommendedDifficulty',prior['difficulty']);change=None
   if level!=prior['difficulty']:
    change={'problemId':r['problemId'],'familyId':r['familyId'],'index':p['instanceIndex'],'previousReviewedDifficulty':prior['difficulty'],'recommendedDifficulty':level,'reason':pr['easiestOptionsVisibleRoute'],'shortcutCertificates':pr['shortcutCertificates'],'peerReport':peerfiles[route]};changes.append(change)
   old=baseline.get(r['problemId']);ident=lambda q:{k:q[k]for k in ['problemId','problemRevision','contentHash','semanticHash']}
   j={'route':route,'familyId':p['familyId'],'instanceIndex':p['instanceIndex'],'sourcePreview':ident(r)|{'canonicalRawSHA256':H(r)},'patchCanonicalSHA256':H(p),'patchArtifact':'frozen/'+folder+'/'+artifact,'patchArtifactSHA256':sha(BASE/folder/artifact),'independentReview':peerfiles[route]|{'recordProblemId':r['problemId'],'recordSHA256':H(pr)},'reviewedDifficulty':level,'previousReviewedDifficulty':prior['difficulty'],'qualifiedOlympiad':level=='olympiad','normalizedLineageKey':prior['normalizedKey'],'normalizationReason':prior['normalizationReason'],'baselinePrevious':None if old is None else ident(old)|{'canonicalRawSHA256':H(old)},'replacesPrivateProblemId':r['problemId']if old is None else None,'statementMeaningChanged':False,'answerChanged':False,'optionsChanged':True,'difficultyChanged':level!=prior['difficulty'],'meaningChanged':False,'preserveSemanticLineage':True,'requiresNewImmutableRevision':True,'presentationInheritance':{'artifact':'source-presentations.json','sourceContentHash':r['contentHash'],'rule':'Use the captured current reviewed statement and solution steps when forming the new immutable revision. Do not transplant historical generic prose into a new hash.'},'newIndependentIdeas':0,'admitted':False};joins.append(j);patchrows.append(p);catalog[(route,p['familyId'])].append(p['instanceIndex'])
 assert len(joins)==len({r['sourcePreview']['problemId']for r in joins})==162
 for name in ['last76-statement-first-review.json','last76-independent-peer-initial.json']:
  cp(a.repo/'docs/bank/problem-quality/series'/name,Path('evidence')/name)
 cp(ledgerpath,Path('evidence/previous-capacity-ledger.json'))
 for name in ['full-source-records.jsonl','source-manifest.json','source-presentations.json']:cp(BASE/name,Path(name))
 write(out/'baseline-previous-records.json',[baseline[j['sourcePreview']['problemId']]for j in joins if j['baselinePrevious']])
 write(out/'option-patches.json',patchrows);write(out/'source-joins.json',joins);write(out/'difficulty-changes.json',changes);write(out/'catalog.json',[{'route':route,'familyId':family,'indices':sorted(indices)}for(route,family),indices in sorted(catalog.items())])
 for src,dst in [('bundle_runtime.py','runtime.py'),('bundle_worker.py','worker.py'),('bundle_verify.py','verify_bundle.py'),('bundle_reproduce.py','reproduce.py')]:cp(BASE/src,Path(dst))
 for name in ['literal_math.py','enclosures.py','intervals.py','intervals_base.py','atan_certificate.py','audit_pairs.py','audit_ranks.py','domain_inventory.py','capacity_after_options.py','option-audit.mjs','capture_presentations.mjs','render_final_patches.cjs','complete_review_final.py']:
  cp(BASE/name,Path('review-code')/name)
 for name in ['effective705-input.jsonl','effective705-final-v3.jsonl','mathematical-pairs-final-v3.json','mathematical-ranks-final-v3.json','root-option-screen-final-v3.json','root-mathematical-opposite-input.json','root-option-screen-input.json','complete705-final-review.json','complete705-supplemental-review.json','domain-inventory-final.json','patch-render-report-final.json']:
  cp(BASE/name,Path('review')/name)
 cp(BASE/'evidence/compact-bank-selection.ts',Path('evidence/compact-bank-selection.ts'))
 cp(Path(__file__),Path('evidence/assembly-code.py'))
 report=json.loads((BASE/'complete705-final-review.json').read_text());report['status']='complete-bounded705-supplemental-review-with-independent162-checks';report['counts']['independentlyParentReviewedPatches']=162;report['counts']['patchesAwaitingParentReview']=0;report['recommendedDifficultyChanges']=changes;report['independentPatchReports']=peerfiles;report['presentationInheritance']={'artifact':'source-presentations.json','sha256':sha(out/'source-presentations.json'),'records':705,'reason':'Immutable sources can retain stale historical prose. New option revisions inherit the current exact-source reviewed presentation, rather than relying on the old hash guard.'};report['limitations'][1]='All162 amendments passed separate independent mathematics checks. The13 exact options-visible level changes are mandatory dispositions. This is not a guarantee against every possible learned classifier, final actual-destination-ID screening, or admission.'
 domains=json.loads((BASE/'domain-inventory-final.json').read_text());domainby={r['problemId']:r for r in domains['recordsEvidence']}
 for family in report['families']:
  rs=[r for r in projection if r['familyId']==family['familyId']];wrong=[c for r in rs for c in r['choices']if c['choiceId']!=r['answerChoiceId']];names=sorted({c.get('misconception','')for c in wrong});assert ''not in names
  family['wrongChoiceMisconceptionInventory']={'wrongChoices':len(wrong),'namedRoutes':names,'scope':'All final wrong choices retain an authored route. Separate independent162 reports reconstruct changed menus; unchanged705 source mathematics retains its earlier source-bound review rather than a newly claimed full derivation.'}
  family['domainDisposition']={'artifact':'review/domain-inventory-final.json','records':len(rs),'statuses':dict(collections.Counter(domainby[r['problemId']]['status']for r in rs)),'unresolved':0,'scope':'All literal function arguments are checked before symbolic evaluation; categorical labels have explicit non-arithmetic scope.'}
  family['notationDisposition']={'changedMenusStrictKaTeX':'648 fields passed in review/patch-render-report-final.json','unchangedSourceScope':'Original canonical statement/solution bytes are preserved. Captured reviewed presentation supplies current notation and explanations for immutable revisions. Historical log/atan spelling in source choices is normalized only by the canonical parent adapter.','newUnresolved':0}
  family['mandatoryLevelChanges']=[c for c in changes if c['familyId']==family['familyId']]
 for j in report['sourceJoins']:
  if j['patchSHA256']:
   patchjoin=next(q for q in joins if q['sourcePreview']['problemId']==j['problemId']);j['independentReview']=patchjoin['independentReview'];j['reviewedDifficulty']=patchjoin['reviewedDifficulty'];j['presentationInheritance']=patchjoin['presentationInheritance']
 report['remainingAdmissionRequirements']=['Parent applies13 immutable finite-level dispositions and source-bound current presentation inheritance.','Parent assigns actual new destination IDs/hashes and reruns the per-family/per-form screen on those final IDs.','Original44 overlays,455 admitted artifacts, previous reports, canonical hashes and saved snapshots remain unchanged.'];write(out/'complete705-supplemental-review.json',report)
 cap=recalculate(ledger,sources,changes);cap['inputs']={'previousLedgerSHA256':sha(ledgerpath),'originalsSHA256':sha(BASE/'full-source-records.jsonl'),'difficultyChangesSHA256':sha(out/'difficulty-changes.json')};write(out/'capacity-after-options.json',cap)
 assert cap['afterCounts']['olympiad']['topicLocalGroups']==30 and cap['afterCounts']['olympiad']['normalizedMeaningfulItems']==240
 write(out/'copy-manifest.json',{'files':copies,'scope':'All copied source/evidence bytes equal their exact origin. Newly assembled joins/metadata are separately hashed in delivery-manifest.json.'})
 print(json.dumps({'output':str(out),'patches':len(joins),'difficultyChanges':len(changes),'counts':{k:{q:v for q,v in x.items()if q!='normalizedItemsPerFamily'}for k,x in cap['afterCounts'].items()}}))
if __name__=='__main__':main()
