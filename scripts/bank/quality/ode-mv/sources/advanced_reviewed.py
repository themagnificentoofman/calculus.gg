"""Versioned, review-driven overlay over the immutable 417-row research snapshot.
Old files remain unchanged; final build API is this module, not the draft modules.
"""
import copy,json,re
from pathlib import Path
import sympy as s
from common import H,L,R
from normalization import normalized_lineage
from presentation import corrected_math,factorized_rational_tex
import ode as draft_ode
import multivariable as draft_mv
import advanced_additions as extra_ode
import mv_additions as extra_mv
ROOT=Path(__file__).resolve().parent
DEMOTED={'q4-differential-equations-polynomial-root-moment':'Two polynomial coefficients and Newton sums give a standard Hard route.','q4-differential-equations-boundary-layer-energy':'An explicit linear equation and a single exponential layer integral give a standard Hard route.','q4-differential-equations-logarithmic-relaxation-constant':'Reciprocal separation and one logarithmic asymptotic give a standard Hard route.','q4-multivariable-optimizer-fourth-envelope-derivative':'Coupled implicit jets and the envelope derivative give a standard Hard route.','q4-multivariable-Hessian-boundary-determinant':'The explicit polynomial permits direct Hessian expansion and disk moments. The arbitrary-boundary-data replacement removes this shortcut.'}
GROUPS={'q4-differential-equations-small-loop-geometric-phase':'noncommuting-small-loop-limit','q4-multivariable-Vandermonde-Gram-integral':'moment-determinant-antisymmetrization','q4-multivariable-elliptic-torsion-sharp-functional':'Hilbert-representer-sharp-functional','q4-multivariable-harmonic-gradient-extremum':'Hilbert-representer-sharp-functional'}
ADDITIONAL_DOMAINS={'q4-differential-equations-weighted-string-first-eigenvalue':[{'k':1,'n':n} for n in range(9,19)],'q4-differential-equations-critical-radial-bubble':[{'a':1,'n':n} for n in range(9,19)],'q4-differential-equations-global-Riccati-threshold':[{'k':1,'n':n} for n in range(6,16)],'q4-differential-equations-spectral-potential-derivative':[{'ell':'1','n':n} for n in range(6,11)]}
ADDITIONAL_DOMAINS.update({'q4-multivariable-support-function-area':[{'n':n,'m':m} for n in range(6,11) for m in (2,3)],'q4-multivariable-cubic-coefficient-body':[{'m':str(m)} for m in range(8,13)],'q4-multivariable-three-cylinder-moments':[{'m':m} for m in range(7,12)],'q4-multivariable-folded-map-counted-area':[{'a':'1','n':n} for n in range(7,12)]})
GROUPS.update({'q4-multivariable-Gaussian-entropy-variational':'Gibbs-relative-entropy-extremality','q4-differential-equations-oscillator-minimum-control-energy':'Gram-moment-projection'})
REGISTRIES=[draft_ode.reg,draft_mv.reg,extra_ode.reg,extra_mv.reg]
for reg in REGISTRIES:
 for fid,meta in reg.families.items():
  if fid in DEMOTED:meta['difficulty']='hard';meta['distinctDecision']=DEMOTED[fid]
  if fid in GROUPS:meta['relatedIdeaGroupId']=GROUPS[fid]
  if fid in ADDITIONAL_DOMAINS:meta['finiteParameters']=meta['finiteParameters']+ADDITIONAL_DOMAINS[fid]
old_control=draft_ode.reg.families['q4-differential-equations-oscillator-minimum-control-energy']['build']
def repaired_control(**kw):
 p=old_control(**kw);w=kw['w'];end=s.pi/(kw['q']*w);t=s.symbols('t',real=True);h=s.Matrix([s.sin(w*(end-t))/w,s.cos(w*(end-t))]);G=s.Matrix(2,2,lambda i,j:s.integrate(h[i]*h[j],(t,0,end)));A,B,C=G[0,0],G[1,1],G[0,1];D=A*B-C*C
 p['pool']=[(A/D,'return the velocity diagonal of the inverse Gram matrix'),((A+B-2*C)/D,'impose terminal velocity one instead of zero'),((A+B+2*C)/D,'impose terminal velocity minus one instead of zero'),((4*A+B-4*C)/D,'impose terminal velocity two instead of zero'),(B/(A*B-C*C/4),'halve the off-diagonal kernel moment'),(B/(2*D),'double the entire Gram matrix by counting the interval twice')]
 p['pool']=[(s.simplify(v),why) for v,why in p['pool']]
 return p
draft_ode.reg.families['q4-differential-equations-oscillator-minimum-control-energy']['build']=repaired_control
FAMILIES={fid:reg for reg in REGISTRIES for fid in reg.families}
SNAPSHOT_SHA='0f155e821a117d50a8396adb632a61c333315097416a7654c85e0d3e3196f8ba'

def build(fid,index):
 r=FAMILIES[fid].build(fid,index)
 r['statement']=corrected_math(r['statement']);r['solutionSteps']=[corrected_math(q) for q in r['solutionSteps']]
 key,invariants,why=normalized_lineage(fid,r['parameters'])
 r['review'].update(normalizedLineageKey=key,normalizedLineageInvariants=invariants,normalizedLineageReason=why,normalizationScope='Conservative advanced meaningful-headroom review. Lower fluency calculations keep parameter-specific exposure identities; exact/cosmetic duplicates remain blocked at every level.')
 if fid=='q4-multivariable-minimum-enclosing-ellipse' and invariants.get('canonical')=='uncapped-rectangle-optimum':
  r['difficulty']='hard';r['pedagogy']['difficultyRationale']='The unconstrained enclosing-rectangle optimum is feasible; a standard symmetry and AM-GM calculation gives a Hard shortest route.';r['review']['difficultyDecision']='finite-subset-demoted-to-hard'
 r['review'].update(relatedIdeaGroupId=r['relatedIdeaGroupId'],recommendedDifficulty=r['difficulty'],qualifiedOlympiadCandidate=r['difficulty']=='olympiad')
 if fid=='q4-differential-equations-Hermite-ODE-discriminant':
  for choice in r['choices']:choice['math']=factorized_rational_tex(choice['math'])
  r['solutionSteps'][-1]=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId'])
 r['constructorVersion']='quality-ode-multivariable-reviewed-v2'
 r['review']['independentReviewSnapshotSha256']=SNAPSHOT_SHA
 r['review']['scope']='Original42 groups independently solved from statements and choices before proofs; all finite intermediate checks separate. Replacements and expanded finite domains require their own later peer evidence.'
 if fid in DEMOTED:r['review']['difficultyDecision']='demoted-to-hard';r['review']['difficultyReason']=DEMOTED[fid]
 r['review']['status']='candidate-awaiting-final-source-bound-admission'
 r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r

def catalog():return [r for reg in REGISTRIES for r in reg.catalog()]
def all_candidates():
 for f in catalog():
  for i in range(f['instanceCount']):yield build(f['familyId'],i)
def verify(r):
 try:return r==build(r['familyId'],r['instanceIndex'])
 except Exception:return False

if __name__=='__main__':
 import hashlib,time
 rows=[];counts=[];errors=[]
 for f in catalog():
  before=len(rows)
  for i in range(f['instanceCount']):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:errors.append({'familyId':f['familyId'],'index':i,'error':repr(e)})
  counts.append({'familyId':f['familyId'],'records':len(rows)-before,'domain':f['instanceCount'],'difficulty':f['difficulty']});print(counts[-1],flush=True)
 tmp=ROOT/'reviewed-candidates.jsonl.tmp';tmp.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows));tmp.replace(ROOT/'reviewed-candidates.jsonl')
 report={'records':len(rows),'families':len(counts),'counts':counts,'errors':errors,'executedChecks':sum(len(r['verificationEvidence']) for r in rows),'sourceSha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['common.py','ode.py','multivariable.py','advanced_additions.py','mv_additions.py','advanced_reviewed.py','normalization.py','presentation.py']},'artifactSha256':hashlib.sha256((ROOT/'reviewed-candidates.jsonl').read_bytes()).hexdigest(),'status':'candidate-not-admission'}
 (ROOT/'reviewed-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('records',len(rows),'errors',len(errors),flush=True)
