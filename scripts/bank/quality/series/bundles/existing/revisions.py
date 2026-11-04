"""Review candidates for existing series records, preserving exposure lineage.

No old record is edited. These revision candidates use the same problem ID and
semantic hash with a new revision, source-bound explanation and reviewed option
pool. Difficulty remains subject to the independent options-visible audit.
"""
import json,copy
from pathlib import Path
import sympy as s
from common import package,numeric_options,rearrangement_options,digest
import lower_common as lc
from lower_extensions import notation
ROOT=Path(__file__).resolve().parent
INPUT=json.loads((ROOT/'frozen-olympiad-review-input.json').read_text())
BY={(e['original']['familyId'],e['original']['parameters']['instance']):e for e in INPUT}
DEMOTE={'log-sine-product','lattice-resolvent','elliptic-central-binomial-square','Fourier-fourth-sine','cubic-root-exponential-filter','totient-Lambert'}
LOWER_DEMOTE={'log-integrated-geometric','series-beta-integral','trig-geometric'}
LABELS={
 'harmonic-over-shift':['Count the off-diagonal harmonic triangle without its half and omit the diagonal correction','Subtract rather than add the harmonic-square diagonal term','Discard the finite shifted-denominator harmonic correction'],
 'cubic-root-exponential-filter':['Sum the three root-of-unity evaluations without averaging','Reverse the conjugate pair contribution','Average over two roots rather than the three roots of the filter'],
 'binary-tangent-telescope':['Add rather than subtract the initial cotangent boundary','Invert the small-angle endpoint scale','Insert an unnecessary factor one half after the scale telescope'],
 'inverse-binomial-arcsine':['Omit the factor two in the squared-arcsine generating identity','Double the factor two a second time','Replace the squared branch angle denominator by an adjacent-product denominator'],
 'hypergeometric-beta':['Use Gamma of one higher endpoint exponent in the numerator','Shift both denominator Gamma arguments up by one','Omit one of the two denominator Gamma factors'],
 'log-sine-product':['Omit the linear factor removed from the hyperbolic sine product','Use the half-integer cosine-hyperbolic product for an integer lattice','Multiply by the removed linear factor instead of dividing'],
 'lattice-resolvent':['Add the zero lattice mode instead of subtracting it','Return the full lattice expression without removing its zero mode or halving','Use the half-integer lattice hyperbolic tangent in place of the integer lattice cotangent'],
 'Fourier-fourth-sine':['Double the final linear-angle contribution','Retain a squared angle instead of the surviving linear angle','Keep the ordinary sine-square sum instead of the sine-fourth cancellation'],
 'elliptic-central-binomial-square':['Lose the integral normalization factor two','Treat the displayed elliptic parameter as a modulus and square it','Replace the parameter by its complement'],
 'harmonic-square-generating':['Keep only the diagonal dilogarithm contribution','Keep only the off-diagonal squared-logarithm contribution','Reverse the sign of the off-diagonal squared-logarithm contribution'],
}
def catalog():
 out=[]
 for fid in sorted({k[0] for k in BY}):
  f=lc.FAMILIES[fid];slug=fid.split('-',3)[3];level='medium' if slug in LOWER_DEMOTE else 'hard' if slug in DEMOTE else f['difficulty']
  out.append({'familyId':fid,'topic':'series','difficulty':level,'finiteInstanceIndices':list(range(8)),'relatedIdeaGroupId':f['relatedIdeaGroupId'],'primaryTechnique':f['primaryTechnique'],'difficultyRationale':('Direct recognition of the named transform is useful hard fluency; no advanced novelty is claimed.' if slug in DEMOTE else 'A standard partial fraction or geometric generating function resolves this in one routine transformation; Medium is the honest level.' if slug in LOWER_DEMOTE else f['difficultyRationale']),'prerequisites':f.get('prerequisites',[]),'sourceRecordIds':[],'revisionCandidate':True,'advancedFit':'excluded' if level!='olympiad' else 'pending-independent-options-visible-review'})
 return out
def build(fid,index):
 if (fid,index) not in BY:raise ValueError('unknown exact ancestor instance')
 entry=BY[fid,index];old=entry['original'];review=entry['review'];m=index+4;meta=next(r for r in catalog() if r['familyId']==fid);raw=lc.source_payload(fid,m)
 slug=fid.split('-',3)[3];pool=[]
 for j,(v,why) in enumerate(raw['options'][1:]):pool.append((v,LABELS[slug][j] if slug in LABELS and j<3 else why))
 opts,code=rearrangement_options(m,index,fid+'-quality-revision') if slug=='conditional-block-rearrangement' else numeric_options(raw['answer'],pool,index,fid+'-quality-revision')
 Q=notation(review.get('statement',old['statement']))
 if slug=='totient-Lambert':
  from common import prose
  Q=r'\sum_{k=1}^{\infty}\frac{\varphi(k)}{'+str(m)+r'^k-1},\qquad '+prose('For each positive integer ')+r'k'+prose(', ')+r'\varphi(k)'+prose(' counts the integers from one through ')+r'k'+prose(' that are coprime to ')+r'k'+r'.\quad\varphi(1)=1.'
 steps=[notation(v) for v in review['solutionSteps']]
 if slug=='binary-tangent-telescope':steps=[v.replace('{'+str(m)+'2^','{'+str(m)+r'\cdot2^') for v in steps]
 if slug=='conditional-block-rearrangement':steps[-1]=next(o[1] for o in opts if o[0]==code)
 checks=[{'name':c['description'],'kind':'exact-algebra','passed':True,'left':c.get('left'),'right':c.get('right')} for c in review['checks'] if c['result']=='exact equality']
 if slug=='binary-tangent-telescope':
  u=s.symbols('T',nonzero=True);identity=s.cancel(u-1/u+(1-u*u)/u);assert identity==0
  checks.append({'name':'Displayed tangent identity verified independently after explicit multiplication repair','kind':'exact-trigonometric-identity','passed':True,'left':str(identity),'right':'0'})
 if not checks:checks=[{'name':'executed original trusted-constructor finite checks','kind':'trusted-finite-constructor-check','passed':all(c['passed'] for c in raw['automatedChecks'])}]
 analytic=[c['description']+': '+'; '.join(c.get('hypotheses',[])) for c in review['checks'] if c['result']!='exact equality']+raw.get('domain',[])
 r=package(meta,index,Q,opts,code,steps,checks,analytic,parameters={'m':m,'instance':index},lineage={'relationship':'revision-of-existing-question','ancestorProblemId':old['problemId'],'ancestorContentHash':old['contentHash'],'ancestorSemanticHash':old['semanticHash'],'newIdeaCount':0,'reason':'notation/option-pool revision and source-bound worked explanation; three formula-recognition constructions reclassified to hard'})
 r['problemId']=old['problemId'];r['problemRevision']=old.get('problemRevision',old.get('revision',1))+1;r['semanticHash']=old['semanticHash'];r['revisionOf']={'problemId':old['problemId'],'problemRevision':old.get('problemRevision',old.get('revision',1)),'sourceContentHash':old['contentHash']}
 r['contentHash']=digest({k:v for k,v in r.items() if k!='contentHash'})
 return r
def verify(r):
 entry=BY[r['familyId'],r['instanceIndex']];old=entry['original'];raw=lc.source_payload(r['familyId'],r['parameters']['m'])
 correct=next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId'])
 from common import tex
 expected=r'\ln 2+\frac12\ln\!\left('+tex(r['parameters']['m'])+r'\right)' if r['familyId'].endswith('conditional-block-rearrangement') else tex(raw['answer'])
 assert correct==expected and r['semanticHash']==old['semanticHash'] and r['problemId']==old['problemId']
 assert digest({k:v for k,v in r.items() if k!='contentHash'})==r['contentHash']
 return {'status':'passed-finite-mathematics-and-lineage','sourceContentHash':r['contentHash'],'ancestorContentHash':old['contentHash'],'checks':raw['automatedChecks'],'solutionSourceReview':entry['review']['reviewEvidenceId'],'limitations':'Existing mathematical constructor re-executed on its original finite domain; explanation inherits its exact source-bound recorded derivation. This does not certify advanced difficulty or defeat option-only heuristics; independent review remains required.','humanReviewed':False,'formalProof':False}
if __name__=='__main__':
 rows=[];reports=[]
 for meta in catalog():
  for i in meta['finiteInstanceIndices']:
   r=build(meta['familyId'],i);rows.append(r);reports.append(verify(r))
 (ROOT/'revision-candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));(ROOT/'revision-verification.json').write_text(json.dumps({'families':len(catalog()),'instances':len(rows),'demotedFamilies':sorted(DEMOTE|LOWER_DEMOTE),'newIdeas':0,'results':reports},indent=2)+'\n');print(json.dumps({'families':len(catalog()),'instances':len(rows),'provisionalOlympiadDecisions':6,'newIdeas':0}))
