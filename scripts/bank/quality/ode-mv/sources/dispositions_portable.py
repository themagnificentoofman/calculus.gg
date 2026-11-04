"""Portable exact-output extraction of the frozen difficulty recipe. No application import path required."""
import copy
from common import H,L,check,s
import baseline_support as base
from presentation import corrected_math
WEAK={'m3-differential-equations-olympiad-quartic-period': 'Energy separation followed by a beta substitution is a standard nonlinear oscillator calculation.', 'm3-differential-equations-olympiad-sharp-lifetime-comparison': 'The bounded arctangent substitution immediately gives the bound and tangent witness.', 'm3-differential-equations-olympiad-nonlinear-radial-asymptotic': 'Differentiating the squared radius gives a separable scalar equation.', 'm3-multivariable-olympiad-simplex-log-partition': 'First-order equations invert normalized exponential weights; convexity then proves the ordinary stationary minimum.', 'm3-multivariable-olympiad-high-dimensional-lp-ball': 'A direct coordinate-power substitution and the Dirichlet formula suffice; dimension notation adds no decision.', 'm3-multivariable-olympiad-log-simplex-moment': 'Differentiate a standard Dirichlet moment twice and insert integer polygamma values.'}

def supports(r):return r.get('familyId') in WEAK

def build_revision(original):
 assert supports(original)
 r=copy.deepcopy(original);fid=r['familyId'];m=s.Integer(r['provenance']['authoring']['builderParameters']['m']);slug=fid.split('-olympiad-',1)[1]
 fn=base.solutions.ode if r['topic']=='differential equations' else base.solutions.multivariable
 steps,answer=fn(original,m,slug)
 checks=(base.checks.ode if r['topic']=='differential equations' else base.checks.multivariable)(m,slug,original)
 old=base.FAMILIES[fid]['build'](m);checks.append(check('unchanged mathematical result',answer,old['answer']))
 r['statement']=corrected_math(r['statement'])
 if fid=='m3-multivariable-olympiad-high-dimensional-lp-ball':
  r['statement']=r['statement'].replace('x_10','x_{10}').replace('x_11','x_{11}')
 r['solutionSteps']=[corrected_math(q) for q in steps]+[L(answer)];r['difficulty']='hard';r['estimates']={'difficulty':'hard','solveSeconds':240,'basis':WEAK[fid]+' AI-assisted editorial estimate; player calibration pending.'}
 r['pedagogy']['difficultyRationale']=WEAK[fid];r['provenance']['authoring']['admittedDifficulty']='hard'
 r['review']={'status':'candidate-awaiting-independent-review','humanReviewed':False,'formalProof':False,'semanticChangeReason':'Difficulty-only revision: the mathematical question, choices, correct answer and semantic identity are unchanged. '+WEAK[fid]}
 r['admission']={'previous':{k:original[k] for k in ['problemId','problemRevision','contentHash','semanticHash']}|{'meaningChanged':False}}
 r['verificationEvidence']=checks;r['revisionKind']='difficulty-only';r['constructorVersion']='quality-ode-mv-difficulty-v1';r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r

def verify_revision(candidate,original):
 try:return supports(original) and candidate==build_revision(original)
 except Exception:return False
