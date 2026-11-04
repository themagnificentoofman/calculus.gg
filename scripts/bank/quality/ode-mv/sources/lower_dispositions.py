"""Immutable source-bound difficulty revisions from the root's literal review."""
from pathlib import Path
import json,hashlib,copy
import extensions_v2 as presentation_v2
from common import H,L,s
P=Path(__file__).resolve().parent
DECISIONS={
'm3-multivariable-hard-moving-domain-derivative':('medium','Differentiate the displayed elementary domain integral or its explicit boundary term; no advanced moving-domain theorem is needed.'),
'm3-multivariable-hard-nonconservative-hole':('medium','Parametrize the specified circle; its radial factors cancel directly in the circulation.'),
'm3-multivariable-hard-Stokes-tilted-surface':('medium','The exact z dz contribution integrates to zero and the remaining constant curl gives the circulation by an elementary area computation.'),
'm3-multivariable-hard-boundary-versus-interior':('medium','One displayed inequality identifies an attainable corner extremum; a multi-case constrained optimization analysis is unnecessary.'),
'm3-multivariable-hard-mixed-Hessian-coordinate':('medium','Substitute the two linear coordinates and extract one quadratic coefficient; the Hessian label does not add difficulty.'),
'm3-differential-equations-hard-step-forcing':('medium','Shift the onset time and solve the familiar constant-forced harmonic oscillator with zero initial data.'),
'm3-differential-equations-hard-wronskian-transport':('medium','Differentiate the two-by-two Wronskian, cancel the shared zeroth-order term, and separate the resulting first-order scalar equation.'),
'm3-multivariable-hard-path-dependent-directional':('easy','The path is explicitly supplied. Substitute its concrete power and cancel to obtain one half; discovering an approach path is not required.')}
def supports(r):return r.get('familyId') in DECISIONS
def build_revision(original):
 assert supports(original);fid=original['familyId'];level,reason=DECISIONS[fid];r=copy.deepcopy(original)
 m=s.Integer(original['provenance']['authoring']['builderParameters']['m'])
 payload=presentation_v2.source_case(fid,m)
 r['statement']=payload['statement'];r['solutionSteps']=payload['solutionSteps']+[L(payload['answer'])]
 r['verificationEvidence']=payload['checks'];r['pedagogy']['difficultyRationale']=reason
 r['review']={'status':'candidate-awaiting-final-source-bound-admission','humanReviewed':False,'formalProof':False}
 r['admission']={'previous':{k:original[k] for k in ['problemId','problemRevision','contentHash','semanticHash']}|{'meaningChanged':False}}
 r['difficulty']=level;r['estimates'].update(difficulty=level,solveSeconds=45 if level=='easy' else 150,basis=reason+' Independent AI-assisted options-visible review; player calibration pending.')
 r['provenance']['authoring']['admittedDifficulty']=level
 r['constructorVersion']='quality-ode-mv-lower-difficulty-v1'
 r['review'].update(recommendedDifficulty=level,qualifiedOlympiad=False,relatedIdeaGroupId=r['pedagogy']['relatedIdeaGroupId'],easiestOptionsVisibleRoute=reason,semanticChangeReason='Difficulty and reviewed presentation only. The concrete calculation, correct answer, all choices, stable problemId and semantic/exposure identity are preserved. '+reason)
 r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r
def verify_revision(candidate,original):
 try:return supports(original) and candidate==build_revision(original)
 except Exception:return False
if __name__=='__main__':
 source=P.parents[1]/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl';rows=[build_revision(r) for r in map(json.loads,source.read_text().splitlines()) if supports(r)];assert len(rows)==64
 tmp=P/'lower-difficulty-revisions.jsonl.tmp';tmp.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows));tmp.replace(P/'lower-difficulty-revisions.jsonl')
 (P/'lower-difficulty-verification.json').write_text(json.dumps({'records':64,'families':8,'executedChecks':sum(len(r['verificationEvidence']) for r in rows),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'artifactSha256':hashlib.sha256((P/'lower-difficulty-revisions.jsonl').read_bytes()).hexdigest(),'scope':'Original eight finite cases in each reviewed lower family; all identities/grades/exposure preserved. New extension level overrides are separately applied by the parent canonical review.','status':'candidate-not-admission'},indent=2)+'\n');print('64 lower difficulty revisions')
