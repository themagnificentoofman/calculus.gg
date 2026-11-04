#!/usr/bin/env python3
"""Versioned original content admission. Trusted builders, finite proof domains.

V1 remains on its original verifier. V2 may use symbolic differentiation,
endpoint certificates, exact limits/recurrences, or explicit analytic proofs.
No downloaded code or arbitrary expression strings are executed.
"""
import argparse,hashlib,json,sys,time,re,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent/'content'))
VERSION='original-constructions-m3-v1'
TAXONOMY=json.loads((Path(__file__).parent/'content/technique-taxonomy.json').read_text())
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def technique_tag(value):
 tag=re.sub('-+','-',re.sub('[^a-z0-9-]','-',value.lower())).strip('-')
 if not re.fullmatch('[a-z][a-z0-9-]{1,63}',tag):raise ValueError('Technique needs an explicit bounded slug: '+value)
 return tag
def readable_math(value):
 def clause(m):
  parts=textwrap.wrap(m.group(1),width=30)
  return m.group(0) if len(parts)<2 else r'\begin{gathered}'+r'\\'.join(r'\textnormal{'+p+'}' for p in parts)+r'\end{gathered}'
 return re.sub(r'\\textnormal\{([^{}]+)\}',clause,value)
def modules(scope='all'):
 import integration
 if scope=='integration':return [integration]
 import coverage,ode
 return [integration,coverage,ode]
def module_for(family):
 if family.startswith('io3-'):
  import integration
  return integration
 if family.startswith('m3-differential-equations-'):
  import ode
  return ode
 import coverage
 return coverage
def adapt(raw,index):
 p=raw['pedagogy'].copy()
 level=raw['difficulty'];seconds=raw.get('estimatedSolveSeconds',360)
 if raw['familyId'] in ['io3-inverse-moment','io3-binomial-exponential','io3-floor-laplace']:
  level='hard';seconds=150;p['reasoningDemand']=['recognition','method-selection']
  p['difficultyRationale']='Hard fluency: '+raw.get('priorityCoverageExclusionReason','A direct but nontrivial transformation.')+' Not admitted to Olympiad.'
 detailed=p['primaryTechnique'];p['primaryTechnique']=TAXONOMY.get(detailed,detailed)
 refs=raw.get('provenance',{}).get('theoremReferenceURLs',[])
 p['sourceRecordIds']=['nist-dlmf'] if refs else []
 demand=p['reasoningDemand'];p['reasoningDemand']=[demand] if isinstance(demand,str) else demand
 conditions=raw.get('assumptions',raw.get('domain',[]))
 v=raw.get('verification',raw.get('validation',{}));route=v.get('route',raw.get('verificationRoute'))
 why=raw.get('distractorMisconceptions',[])
 choices=[dict(c,misconception=c.get('misconception','correct' if c['choiceId']==raw['answerChoiceId'] else why[max(0,i-1)] if why else 'Authored alternative; see worked explanation.')) for i,c in enumerate(raw['choices'])]
 body={'schemaVersion':2,'problemId':'cn_'+digest([raw['familyId'],index])[:20],'problemRevision':1,
 'familyId':raw['familyId'],'templateVersion':VERSION,'parameters':{'instance':index},
 'semanticHash':digest({'statement':raw['statement'],'topic':raw['topic']}),
 'statement':readable_math(raw['statement']),'choices':choices,'answerChoiceId':raw['answerChoiceId'],'solutionSteps':list(map(readable_math,raw['solutionSteps'])),
 'assumptions':conditions or ['Real variables on the displayed domain; all stated parameter restrictions apply.'],
 'topic':raw['topic'],'difficulty':level,'subtopic':p['relatedIdeaGroupId'],
 'techniqueTags':list(dict.fromkeys(map(technique_tag,[p['primaryTechnique'],detailed]+p['alternativeTechniques']))), 'pedagogy':p,
 'provenance':{'kind':'original','sourceUrl':None,'sourceItem':None,'license':'LicenseRef-CalculusNinja-Original',
 'attribution':'Original Calculus Ninja content. AI-assisted authoring and editorial review; reproducible mathematical checks. No third-party problem wording or solution copied.',
 'authoring':{'version':VERSION,'independentOriginal':True,'sourceTextReused':False,'builderParameters':raw['parameters'],'detailedTechnique':detailed,'proposedDifficulty':raw['difficulty'],'admittedDifficulty':level,'priorityMinimumEligible':raw.get('priorityCoverageEligible'),'priorityExclusionReason':raw.get('priorityCoverageExclusionReason'),'theoremReferenceURLs':refs,'referencePurpose':'Mathematical theorem reference only; no source expression or asset copied.'}},
 'validation':{'status':'passed','methods':[route,'exact-choice-non-equivalence','trusted-source-reconstruction'],
 'evidence':{'verificationRoute':route,'parameterDomain':{'instance':list(range(8))},'builderParameterDomain':raw.get('parameterDomain'),'assumptionsChecked':True,'solutionDerivationChecked':True,'uniqueCorrectOption':True,'certificate':v,'executedChecks':raw.get('automatedChecks',v.get('exactChecks',[])),'analyticCertificate':raw.get('analyticCertificate',v.get('proofSteps',[])),'distractorAudit':raw.get('optionAudit'),'numericalAgreementUsedAsProof':False,'formalProofAssistantChecked':False,'editorialReview':'AI-assisted; not human review'},'humanReviewed':False},
 'estimates':{'difficulty':level,'solveSeconds':seconds,'basis':p['difficultyRationale']+' Editorial estimate; player calibration pending.'}}
 body['contentHash']=digest(body);return body

def build(family,index):
 if type(index)is not int or not 0<=index<8:raise ValueError('Outside finite verification domain')
 raw=module_for(family).build(family,index)
 require_admission(raw)
 return adapt(raw,index)
def require_admission(raw):
 if raw['familyId'].startswith('io3-'):
  if raw.get('verification',{}).get('status')!='certificate-checked':raise ValueError('Integration proof audit incomplete')
 elif raw.get('editorialStatus')!='admitted' or raw.get('validation',{}).get('status')!='verified':
  raise ValueError('Mathematical/editorial admission unresolved: '+str(raw.get('editorialStatus')))
def verify(p):
 if p.get('templateVersion')=='standalone-polynomial-v1':
  import standalone
  return standalone.verify(p)
 if p.get('templateVersion')!=VERSION:raise ValueError('Unsupported version; require explicit verifier')
 if set(p.get('parameters',{}))!={'instance'}:raise ValueError('Unexpected parameters')
 expected=build(p.get('familyId',''),p['parameters']['instance'])
 if canonical(p)!=canonical(expected):raise ValueError('Reconstruction mismatch: '+p.get('problemId','unknown'))
 return True

def generate(out,release,scope):
 out.mkdir(parents=True,exist_ok=True);quarantine=[];rows=[];counts={};seen=set();catalog=[]
 for mod in modules(scope):
  for f in mod.catalog():
   fid=f.get('familyId',f.get('id'));catalog.append(f)
   for i in range(8):
    try:
     raw=mod.build(fid,i)
     require_admission(raw)
     p=adapt(raw,i)
     if p['semanticHash'] in seen:raise ValueError('Duplicate exact statement; not admitted as new instance')
     seen.add(p['semanticHash']);rows.append(p);counts[fid]=counts.get(fid,0)+1
    except Exception as e:quarantine.append({'familyId':fid,'instance':i,'reason':str(e)})
   print(fid,counts.get(fid,0),flush=True)
 coverage={}
 for p in rows:
  cell=p['topic']+'/'+p['difficulty'];coverage[cell]=coverage.get(cell,0)+1
 artifact=out/(release+'.jsonl');artifact.write_text(''.join(canonical(p)+'\n' for p in rows))
 manifest={'schemaVersion':2,'releaseId':release,'parentRelease':'cn-2026-11-02-full-v2','artifact':artifact.name,'artifactSha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'approvedCount':len(rows),'coverage':coverage,'families':counts,'humanReviewedCount':0,'templateVersion':VERSION,'publishedCount':0,'importedCount':0,'activeCount':0}
 (out/(release+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'quarantine.json').write_text(json.dumps(quarantine,indent=2)+'\n')
 (out/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
 print(json.dumps({'admitted':len(rows),'quarantined':len(quarantine),'families':len(counts)}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'.bank-data/milestone3');ap.add_argument('--release',default='cn-2026-11-03-ideas-v3');ap.add_argument('--verify',type=Path);ap.add_argument('--scope',choices=['all','integration'],default='all');args=ap.parse_args()
 if args.verify:
  n=0
  for line in args.verify.open():verify(json.loads(line));n+=1
  print(json.dumps({'verified':n,'humanReviewed':False}))
 else:generate(args.out,args.release,args.scope)
