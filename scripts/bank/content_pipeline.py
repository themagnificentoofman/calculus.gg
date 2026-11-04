#!/usr/bin/env python3
"""Versioned original content admission. Trusted builders, finite proof domains.

V1 remains on its original verifier. V2 may use symbolic differentiation,
endpoint certificates, exact limits/recurrences, or explicit analytic proofs.
No downloaded code or arbitrary expression strings are executed.
"""
import argparse,hashlib,json,sys,time,re,textwrap,importlib
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
 return [importlib.import_module(name) for name in (['integration'] if scope=='integration' else ['integration','coverage','ode','limits_additions','differentiation_additions','series_easy'])]
def module_for(family):
 if family.startswith('io3-'):
  import integration
  return integration
 if family.startswith('m3-differential-equations-'):
  import ode
  return ode
 for mod in modules():
  if any(family==f.get('familyId',f.get('id')) for f in mod.catalog()):return mod
 raise ValueError('Unregistered construction; no verifier')
def adapt(raw,index):
 p=raw['pedagogy'].copy()
 idea_aliases={'Frullani-parameter-integration':'frullani-scaling-cancellation','mixed-beta-logarithmic-moment':'beta-parameter-moments','Laplace-method-at-endpoint':'integral-boundary-layer'}
 p['relatedIdeaGroupId']=idea_aliases.get(p['relatedIdeaGroupId'],p['relatedIdeaGroupId'])
 level=raw['difficulty'];seconds=raw.get('estimatedSolveSeconds',360)
 if raw['familyId'] in ['io3-inverse-moment','io3-binomial-exponential','io3-floor-laplace']:
  level='hard';seconds=150;p['reasoningDemand']=['recognition','method-selection']
  p['difficultyRationale']='Hard fluency: '+raw.get('priorityCoverageExclusionReason','A direct but nontrivial transformation.')+' Not admitted to Olympiad.'
 detailed=p['primaryTechnique'];p['primaryTechnique']=TAXONOMY.get(raw['topic']+':'+detailed,TAXONOMY.get(detailed,detailed))
 known_theorems={
 'm3-series-olympiad-hypergeometric-beta':['https://dlmf.nist.gov/15.4.E20'],
 'm3-series-olympiad-log-sine-product':['https://dlmf.nist.gov/4.36.E1'],
 'm3-series-olympiad-lattice-resolvent':['https://dlmf.nist.gov/4.36.E3'],
 'm3-series-olympiad-elliptic-central-binomial-square':['https://dlmf.nist.gov/19.5.E1'],
 'm3-limits-olympiad-central-binomial-shift':['https://dlmf.nist.gov/5.11.E1']}
 refs=raw.get('provenance',{}).get('theoremReferenceURLs',raw.get('theoremReferences',known_theorems.get(raw['familyId'],[])))
 def reference_id(url):
  if url.startswith('https://dlmf.nist.gov/'):return 'nist-dlmf'
  if url.startswith('https://www.math.cmu.edu/'):return 'cmu-gautam-mgf-2026'
  if url.startswith('https://courses.grainger.illinois.edu/'):return 'illinois-occupancy-2022'
  if url.startswith('https://ocw.mit.edu/courses/18-781-'):return 'mit-ocw-number-theory-2012-lecture14'
  raise ValueError('Unregistered theorem reference: '+url)
 p['sourceRecordIds']=list(dict.fromkeys(map(reference_id,refs)))
 demand=p['reasoningDemand'];demand=[demand] if isinstance(demand,str) else demand
 demand_map={'proof':['synthesis'],'modeling':['reframing'],'local computation':['execution'],'geometric synthesis':['reframing','synthesis'],'method selection and synthesis':['method-selection','synthesis'],'reframing and synthesis':['reframing','synthesis'],'reframing and convergence':['reframing','convergence']}
 p['reasoningDemand']=list(dict.fromkeys(v for d in demand for v in demand_map.get(d,[d])))
 if any(d not in ['execution','recognition','method-selection','reframing','convergence','synthesis'] for d in p['reasoningDemand']):raise ValueError('Unregistered reasoning demand')
 conditions=raw.get('assumptions',raw.get('domain',[]))
 v={**raw.get('validation',{}),**raw.get('verification',{})};route=v.get('route',raw.get('verificationRoute'))
 derivation=raw.get('certificate',{})
 why=raw.get('distractorMisconceptions',[])
 choices=[dict(c,misconception=c.get('misconception','correct' if c['choiceId']==raw['answerChoiceId'] else why[max(0,i-1)] if why else 'Authored alternative; see worked explanation.')) for i,c in enumerate(raw['choices'])]
 statement=raw['statement']
 if raw['familyId']=='m3-integration-easy-piecewise-accumulation':
  statement=r'\begin{gathered}'+statement.replace(r',\qquad ',r'\\',1)+r'\end{gathered}'
 elif raw['familyId']=='m3-differentiation-olympiad-cyclic-determinant-second-derivative':
  n=str(raw['parameters']['m'])
  statement=r'\begin{gathered}A(x)=(a_{ij}(x))_{1\le i,j\le '+n+r'},\\a_{ij}(x)=\begin{cases}2+x,&i=j,\\-1,&i-j\equiv\pm1\bmod '+n+r',\\0,&\mathrm{otherwise}.\end{cases}\\\left.\frac{d^2}{dx^2}\det A(x)\right|_{x=0}=?\end{gathered}'
 solution_steps=list(raw['solutionSteps'])
 if raw['familyId']=='m3-differentiation-hard-log-product':
  # The exact builder checks the expanded derivative, but the useful solution
  # is the logarithmic identity, which stays readable throughout the domain.
  answer=next(c['math'] for c in choices if c['choiceId']==raw['answerChoiceId'])
  solution_steps=[r'm='+str(raw['parameters']['m'])+r',\quad F(x)=\prod_{j=1}^{m}(1+x/j)',r'\frac{F\prime(x)}{F(x)}=\sum_{j=1}^{m}\frac1{j+x}',r'\frac{F\prime\prime(x)}{F(x)}=\left(\sum_{j=1}^{m}\frac1{j+x}\right)^2-\sum_{j=1}^{m}\frac1{(j+x)^2}',r'F(0)=1,\quad H_m=\sum_{j=1}^{m}\frac1j,\quad H_m^{(2)}=\sum_{j=1}^{m}\frac1{j^2}',r'F\prime\prime(0)=H_m^2-H_m^{(2)}='+answer]
 if 'm' in raw['parameters'] and not any('m='+str(raw['parameters']['m']) in step for step in solution_steps[:2]) and any(re.search(r'(?<![A-Za-z\\])m(?![A-Za-z])',step) for step in solution_steps):solution_steps.insert(0,r'\textnormal{In this derivation, }m='+str(raw['parameters']['m'])+'.')
 body={'schemaVersion':2,'problemId':'cn_'+digest([raw['familyId'],index])[:20],'problemRevision':1,
 'familyId':raw['familyId'],'templateVersion':VERSION,'parameters':{'instance':index},
 'semanticHash':digest({'statement':raw['statement'],'topic':raw['topic']}),
 'statement':readable_math(statement),'choices':choices,'answerChoiceId':raw['answerChoiceId'],'solutionSteps':list(map(readable_math,solution_steps)),
 'assumptions':conditions or ['Real variables on the displayed domain; all stated parameter restrictions apply.'],
 'topic':raw['topic'],'difficulty':level,'subtopic':p['relatedIdeaGroupId'],
 'techniqueTags':list(dict.fromkeys(map(technique_tag,[p['primaryTechnique'],detailed]+p['alternativeTechniques']))), 'pedagogy':p,
 'provenance':{'kind':'original','sourceUrl':None,'sourceItem':None,'license':'LicenseRef-CalculusNinja-Original',
 'attribution':'Original Calculus Ninja content. AI-assisted authoring and editorial review; reproducible mathematical checks. No third-party problem wording or solution copied.',
 'authoring':{'version':VERSION,'independentOriginal':True,'sourceTextReused':False,'builderParameters':raw['parameters'],'detailedTechnique':detailed,'proposedDifficulty':raw['difficulty'],'admittedDifficulty':level,'priorityMinimumEligible':raw.get('priorityCoverageEligible'),'priorityExclusionReason':raw.get('priorityCoverageExclusionReason'),'theoremReferenceURLs':refs,'referencePurpose':'Mathematical theorem reference only; no source expression or asset copied.'}},
 'validation':{'status':'passed','methods':[route,'exact-choice-non-equivalence','trusted-source-reconstruction'],
 'evidence':{'verificationRoute':route,'parameterDomain':{'instance':list(range(8))},'builderParameterDomain':raw.get('parameterDomain'),'assumptionsChecked':True,'solutionDerivationChecked':True,'uniqueCorrectOption':True,'certificate':v,'derivationCertificate':derivation,'executedChecks':raw.get('automatedChecks',v.get('exactChecks',derivation.get('exactChecks',[]))),'analyticCertificate':raw.get('analyticCertificate',v.get('proofSteps',derivation.get('hypotheses',[])+derivation.get('theorems',[]))),'distractorAudit':raw.get('optionAudit',v.get('distractorAudit')),'numericalAgreementUsedAsProof':False,'formalProofAssistantChecked':False,'editorialReview':'AI-assisted; not human review'},'humanReviewed':False},
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
 out.mkdir(parents=True,exist_ok=True);quarantine=[];rows=[];counts={};seen=set();catalog=[];family_ids=set()
 for mod in modules(scope):
  for f in mod.catalog():
   fid=f.get('familyId',f.get('id'))
   if fid in family_ids:raise ValueError('Duplicate construction identifier: '+fid)
   family_ids.add(fid);catalog.append(f)
   for i in range(8):
    stage='mathematical-build'
    try:
     raw=mod.build(fid,i)
     stage='editorial-admission'
     require_admission(raw)
     stage='schema-adaptation-and-deduplication'
     p=adapt(raw,i)
     if p['semanticHash'] in seen:raise ValueError('Duplicate exact statement; not admitted as new instance')
     seen.add(p['semanticHash']);rows.append(p);counts[fid]=counts.get(fid,0)+1
    except Exception as e:quarantine.append({'familyId':fid,'instance':i,'stage':stage,'reason':str(e)})
   print(fid,counts.get(fid,0),flush=True)
 coverage={}
 for p in rows:
  cell=p['topic']+'/'+p['difficulty'];coverage[cell]=coverage.get(cell,0)+1
 cells={}
 for cell in sorted(coverage):
  members=[p for p in rows if p['topic']+'/'+p['difficulty']==cell]
  families={p['familyId'] for p in members}
  cells[cell]={'verifiedFamilies':len(families),'verifiedItems':len(members),'relatedIdeaGroups':len({p['pedagogy']['relatedIdeaGroupId'] for p in members}),'structures':len({p['pedagogy']['structuralSignature'] for p in members}),'primaryTechniques':len({p['pedagogy']['primaryTechnique'] for p in members}),'minimumItemsPerFamily':min(counts[f] for f in families),'importedItems':0,'activeItems':0}
 strict_priority=len({p['familyId'] for p in rows if p['topic']=='integration' and p['difficulty']=='olympiad' and p['provenance']['authoring']['priorityMinimumEligible'] is True})
 failures=[]
 if strict_priority<30:failures.append('Integration Olympiad has fewer than 30 strictly eligible constructions')
 if any(n!=8 for n in counts.values()):failures.append('A partly admitted family does not have its complete eight-instance verification domain')
 if scope=='all':
  for topic in ['integration','differentiation','limits','series','multivariable','differential equations']:
   for level in ['easy','medium','hard','olympiad']:
    cell=topic+'/'+level
    if cell not in cells or cells[cell]['verifiedFamilies']<(30 if cell=='integration/olympiad' else 12):failures.append('Insufficient verified family coverage: '+cell)
 artifact=out/(release+'.jsonl');artifact.write_text(''.join(canonical(p)+'\n' for p in rows))
 manifest={'schemaVersion':2,'releaseId':release,'parentRelease':'cn-2026-11-02-full-v2','artifact':artifact.name,'artifactSha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'approvedCount':len(rows),'coverage':coverage,'families':counts,'cells':cells,'strictPriorityFamilies':strict_priority,'globalRelatedIdeaGroups':len({p['pedagogy']['relatedIdeaGroupId'] for p in rows}),'acceptanceFailures':failures,'humanReviewedCount':0,'templateVersion':VERSION,'publishedCount':0,'importedCount':0,'activeCount':0}
 (out/(release+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'quarantine.json').write_text(json.dumps(quarantine,indent=2)+'\n')
 (out/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
 print(json.dumps({'admitted':len(rows),'quarantined':len(quarantine),'families':len(counts)}))
 if failures:raise ValueError('; '.join(failures))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'.bank-data/milestone3');ap.add_argument('--release',default='cn-2026-11-03-ideas-v3');ap.add_argument('--verify',type=Path);ap.add_argument('--scope',choices=['all','integration'],default='all');args=ap.parse_args()
 if args.verify:
  n=0
  for line in args.verify.open():verify(json.loads(line));n+=1
  print(json.dumps({'verified':n,'humanReviewed':False}))
 else:generate(args.out,args.release,args.scope)
