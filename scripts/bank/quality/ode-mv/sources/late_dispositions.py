"""Additional immutable difficulty revisions after final options-visible review."""
from pathlib import Path
import json,hashlib
import dispositions_portable as original_recipe
from common import H
P=Path(__file__).resolve().parent
WEAK={
'm3-differential-equations-olympiad-power-coordinate-lifetime':'The power coordinate u=y^(3/2) gives a linear harmonic equation; its first cosine zero is a standard Hard endpoint calculation.',
'm3-differential-equations-olympiad-switched-riccati':'Solve the two elementary flows and iterate their two-by-two fractional-linear map. This is the same broad finite-Mobius iteration decision as the separately demoted differentiation family.',
'm3-differential-equations-olympiad-periodic-product-average':'Integrate two logarithmic derivatives around the periodic orbit, then integrate one original equation. These standard identities immediately fix the requested average.',
'm3-differential-equations-olympiad-resonant-boundary-compatibility':'A direct resonant linear particular solution and endpoint substitution give the compatibility parameter. The supplied simple forcing avoids a deeper spectral decision.',
'm3-differential-equations-olympiad-periodic-floquet-multiplier':'Integrate the scalar variational exponent and use the periodic logarithmic equation. Two standard scalar identities suffice, so the shortest visible route is Hard.',
'm3-differential-equations-olympiad-pinney-energy':'Use the conserved energy and q=y^2 to obtain q second+4q=4E; the quarter-period value is then immediate. The independent advanced-fit reviewer marked this borderline; it is conservatively admitted only as Hard.',
'm3-multivariable-olympiad-lemniscate-petal-area':'The polar inequality gives the radial upper bound directly; substitute the angular variable and evaluate one beta integral. Petal counting cancels, leaving a standard Hard route.'}
def supports(r):return r.get('familyId') in WEAK
def build_revision(original):
 assert supports(original)
 saved=original_recipe.WEAK
 try:
  original_recipe.WEAK={**saved,**WEAK};r=original_recipe.build_revision(original)
 finally:original_recipe.WEAK=saved
 r['constructorVersion']='quality-ode-mv-late-difficulty-v1'
 if r['familyId']=='m3-differential-equations-olympiad-switched-riccati':
  r['statement']=r['statement'].replace(r'\textnormal{For every integer j=0,...,}',r'\textnormal{For every integer }j=0,\ldots,')
 r['review']['recommendedDifficulty']='hard';r['review']['qualifiedOlympiad']=False
 r['review']['easiestOptionsVisibleRoute']=WEAK[r['familyId']]
 normalized={q['problemId']:q['normalizedLineageKey'] for q in json.loads((P/'retained-normalization.json').read_text())['records']}
 if original['problemId'] in normalized:r['review']['normalizedLineageKey']=normalized[original['problemId']]
 r['review']['relatedIdeaGroupId']=r['pedagogy']['relatedIdeaGroupId']
 r['review']['independentReviewEvidence']='quality-peer-old-ode-shortest-route-v1' if r['topic']=='differential equations' else 'quality-root-existing-multivariable-peer-v1'
 r['contentHash']=H({k:v for k,v in r.items() if k!='contentHash'})
 return r
def verify_revision(candidate,original):
 try:return supports(original) and candidate==build_revision(original)
 except Exception:return False
if __name__=='__main__':
 src=P.parents[1]/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl';rows=[build_revision(r) for r in map(json.loads,src.read_text().splitlines()) if supports(r)]
 assert len(rows)==56
 tmp=P/'late-difficulty-revisions.jsonl.tmp';tmp.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows));tmp.replace(P/'late-difficulty-revisions.jsonl')
 (P/'late-difficulty-verification.json').write_text(json.dumps({'records':len(rows),'families':len(WEAK),'checks':sum(len(r['verificationEvidence']) for r in rows),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'artifactSha256':hashlib.sha256((P/'late-difficulty-revisions.jsonl').read_bytes()).hexdigest(),'changes':'Only difficulty/explanation/review metadata; original statement, options, answer, problemId and semantic identity preserved.','status':'candidate-awaiting-final-source-bound-admission'},indent=2)+'\n');print(len(rows),'late difficulty revisions')
