"""Immutable old-record revisions: difficulty plus specific proven option repairs."""
from pathlib import Path
import json,sys,copy,importlib.util
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE));import generate as g
s=g.s;core=g.core
ORIGINAL=g.ORIGINAL;BYID={p['problemId']:p for p in ORIGINAL}
PRESENT=json.loads((BASE/'original-reviewed-presentation.json').read_text())
PEER={v['problemId']:v for v in json.loads((BASE/'parent-existing-review.json').read_text())['results']}
oracle=g.load('quality_frozen_parent_existing_oracle',BASE/'frozen_review/parent_existing_oracle.py')
EARLY={
'm3-differentiation-olympiad-envelope-derivative':'The supplied point gives a directly solvable stationary optimizer; strict convexity and one envelope derivative give a Hard chain-rule problem.',
'm3-differentiation-olympiad-Gaussian-moment-derivative':'The right parameter derivative and standard factorial moment are direct Hard analysis; derivative order does not create an advanced decision.',
'm3-differentiation-olympiad-root-of-unity-filter':'Three conjugate exponential derivatives reduce to a residue-class zero-or-three filter; retain as Hard.',
'm3-differentiation-olympiad-global-inverse-curvature':'Two implicit derivatives and one rational optimization are Hard; the global range check does not itself make the construction Olympiad.',
'm3-limits-olympiad-product-Euler-correction':'A uniform second-order logarithmic expansion and fixed sums of powers are Hard asymptotic bookkeeping.',
'm3-limits-olympiad-central-binomial-shift':'Stirling normalization and a fixed finite product correction give Hard asymptotic bookkeeping.'}
OPTION_FAMILIES={'m3-differentiation-easy-linearization','m3-differentiation-medium-inverse-second','m3-differentiation-hard-implicit-inverse-exponential','m3-limits-hard-Riemann-sum','m3-differentiation-hard-implicit-second','m3-limits-hard-supremum-pointwise-mismatch','m3-limits-hard-Lp-maximum-limit','m3-limits-olympiad-nonlinear-recursion-rate'}
import option_repairs
OPTION_FAMILIES.update(p['familyId'] for p in ORIGINAL if p['familyId'].split('-',3)[3] in option_repairs.SLUGS)
def disposition(p):
 peer=PEER.get(p['problemId']);reason=EARLY.get(p['familyId'])
 if reason:return 'hard',reason
 if peer:return peer['difficultyRecommended'],peer['easiestOptionsVisibleRoute']
 return p['difficulty'],'Repair a validated visible-option form cue; preserve the mathematical task and difficulty.'
def needs(p):
 if p['familyId'] in g.REPLACE:return False
 level,_=disposition(p)
 return level!=p['difficulty'] or p['familyId'].endswith('-curvature-parametric') or p['familyId'] in OPTION_FAMILIES or option_repairs.single_literal_pair(p)
def catalog():
 groups={}
 for p in ORIGINAL:
  if needs(p):groups.setdefault(p['familyId'],[]).append(p)
 return [{'familyId':fid,'kind':'immutable-revision','topic':rows[0]['topic'],'instanceCount':len(rows),'finiteDomain':[{'instance':j,'sourceInstance':p['parameters']['instance'],'problemId':p['problemId'],'sourceContentHash':p['contentHash'],'difficulty':disposition(p)[0]} for j,p in enumerate(rows)]} for fid,rows in sorted(groups.items())]
def build(fid,index):
 entry=next(f for f in catalog() if f['familyId']==fid);case=entry['finiteDomain'][index];p=BYID[case['problemId']]
 level,reason=disposition(p);repair_options=fid in OPTION_FAMILIES or option_repairs.single_literal_pair(p);m=s.Integer(p['provenance']['authoring']['builderParameters']['m'])
 raw,steps,checks,pool=g.proof_source(fid,int(m));A=g.answer_value(fid,raw['answer'])
 if p['problemId'] in PEER:
  expected,independent=oracle.solve(p);assert oracle.equal(expected,A)
  checks=checks+independent
 rev=copy.deepcopy(p);review=PRESENT[p['problemId']]
 assert review['sourceContentHash']==p['contentHash']
 rev['statement']=g.statement_value(fid,review.get('statement',p['statement']));rev['solutionSteps']=review['steps']
 rev['problemRevision']=p['problemRevision']+1;rev['difficulty']=level
 rev['estimates']['difficulty']=level;rev['estimates']['solveSeconds']=180 if level=='hard' else 90
 rev['pedagogy']['difficultyRationale']=reason;pairchecks=[]
 if repair_options:
  if fid.endswith('-nonlinear-recursion-rate'):
   pool=[(m**(1/m),'Reverse the reciprocal scaling'),(m**(-2/m),'Apply the reciprocal exponent twice'),(s.Integer(1),'Drop the limiting transformed drift'),((2*m)**(-1/m),'Count the drift twice'),((m/2)**(-1/m),'Halve the drift'),((m*m)**(-1/m),'Square the transformed drift')]
  else:pool=g.repair_pool(fid,m,A,pool)
  opts,correct,pairchecks=core.choose_options(A,pool,p['parameters']['instance'],fid+'-option-repair-v2');opts=g.format_options(fid,m,opts,A)
  if fid.endswith('-nonlinear-recursion-rate'):
   for q in opts:
    value=s.sympify(q['expression']);base=s.simplify(value**m)
    q['math']=r'\left('+core.L(base)+r'\right)^{1/'+str(m)+r'}'
  oldcorrect=p['answerChoiceId']
  for q in opts:
   if q['choiceId']==correct:q['choiceId']=oldcorrect
  rev['choices']=[{'choiceId':q['choiceId'],'math':q['math']} for q in opts];rev['answerChoiceId']=oldcorrect
  rev['solutionSteps'].append(next(q['math'] for q in rev['choices'] if q['choiceId']==oldcorrect))
 rev['templateVersion']='quality-reviewed-revision-v2'
 rev['provenance']['qualityRevision']={'sourceProblemId':p['problemId'],'sourceRevision':p['problemRevision'],'sourceContentHash':p['contentHash'],'semanticHashPreserved':True,'reason':reason,'newIdeaCredit':0}
 rev['validation']={'status':'mathematically-checked-pending-independent-review','evidence':{'independentIntermediateChecks':checks,'pairwiseOptionChecks':pairchecks,'choiceMisconceptions':{q['math']:q['misconception'] for q in opts} if repair_options else {},'sourceContentHash':p['contentHash'],'peerReview':PEER.get(p['problemId'])}}
 rev.pop('contentHash',None);rev['contentHash']=core.digest(rev)
 assert rev['problemId']==p['problemId'] and rev['semanticHash']==p['semanticHash']
 return rev
def verify(raw):
 f=next(f for f in catalog() if f['familyId']==raw['familyId']);idx=next(i for i,c in enumerate(f['finiteDomain']) if c['problemId']==raw['problemId'])
 assert core.canon(raw)==core.canon(build(raw['familyId'],idx));return True
if __name__=='__main__':
 rows=[];errors=[]
 for f in catalog():
  for i in range(f['instanceCount']):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:errors.append({'familyId':f['familyId'],'index':i,'error':repr(e)})
 (BASE/'old-revisions-candidates.json').write_text(json.dumps(rows,indent=2));(BASE/'old-revisions-errors.json').write_text(json.dumps(errors,indent=2))
 print(json.dumps({'rows':len(rows),'errors':errors}))
