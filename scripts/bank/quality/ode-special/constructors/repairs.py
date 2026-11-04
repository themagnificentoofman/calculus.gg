"""Separate17-row source-bound Green/Bessel menu layer; no frozen source mutation."""
from pathlib import Path
from functools import lru_cache
import json,hashlib,itertools,re
import sympy as s
from menu_core import choose_options,canon,digest,L
from literal_special import parse,alpha,B
from special_intervals import certificate
P=Path(__file__).resolve().parent
VERSION='quality-green-bessel-option-overlay-v1'
@lru_cache(None)
def inputs():
 manifest=json.loads((P/'input-manifest.json').read_text())
 for name,h in manifest['files'].items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==h
 return json.loads((P/'inputs.json').read_text())
def catalog():
 rows=inputs();return [{'familyId':f,'indices':sorted(q['activeMenu']['parameters']['instance'] for q in rows if q['activeMenu']['familyId']==f),'newIdeas':0} for f in sorted({q['activeMenu']['familyId'] for q in rows})]
def positive_poly(v):
 u=s.Symbol('u',positive=True);v=s.cancel((v/B).subs(alpha**2,u+4));num,den=s.fraction(v);co=s.Poly(num,u).all_coeffs();assert den.is_positive
 if all(c>=0 for c in co) and any(c>0 for c in co):sign='positive'
 elif all(c<=0 for c in co) and any(c<0 for c in co):sign='negative'
 elif all(c==0 for c in co):sign='zero'
 else:raise AssertionError(v)
 return {'sign':sign,'polynomial':s.srepr(num),'denominator':s.srepr(den),'domain':'B>0, u=alpha²−4>0'}
def build(fid,index):
 assert type(index)is int and index in next(f['indices'] for f in catalog() if f['familyId']==fid)
 q=next(q for q in inputs() if q['activeMenu']['familyId']==fid and q['activeMenu']['parameters']['instance']==index);old=q['sourceCanonical'];r=q['activeMenu'];original=parse(next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']));checks=[]
 if fid.endswith('Bessel-zero-normalization'):
  nu=int(re.search(r'J_\{(\d+)\}',r['statement'])[1]);A=B/2
  low=[(B/4,'Apply the boundary identity factor one half twice'),(B/(2*alpha**2),'Divide by the root scaling Jacobian twice'),(s.Integer(0),'Use the vanishing root value rather than the nonzero derivative in the boundary term')]
  high=[(B,'Omit the boundary identity factor one half'),(alpha**2*B/2,'Omit the root scaling Jacobian'),(alpha**2*B,'Omit both the root scaling Jacobian and the boundary factor one half')]
  count=index%4;eligible=[]
  for lo in itertools.combinations(low,count):
   for hi in itertools.combinations(high,3-count):
    items=list(lo)+list(hi)
    # A comparable root-independent boundary-factor mistake prevents a unique alpha-presence cue.
    if not any(v in [B/4,B] for v,_ in items):continue
    eligible.append(items)
  assert eligible;wrong=min(eligible,key=lambda p:digest([fid,index,[(s.srepr(v),why) for v,why in p]]))
  choices=[]
  for v,why in [(A,'correct')]+wrong:
   tex=L(v).replace('B',r'J^{2}_{'+str(nu+1)+r'}\left(\alpha\right)')
   choices.append({'choiceId':r['answerChoiceId'] if why=='correct' else 'ch_'+digest(s.srepr(v))[:16],'math':tex,'expression':s.srepr(v),'misconception':why})
  choices.sort(key=lambda c:digest([fid,index,c['choiceId']]))
  evidence=positive_poly;parameters={'nu':nu,'rootOrdinal':index%2+1};reason='The displayed series gives the Bessel equation; a boundary differential identity and derivative recurrence are needed to connect the integral to the adjacent-order root value. Positivity and alpha>2 alone leave at least two candidates. The repair preserves this mathematical decision, not a coverage-count label.'
 elif fid.endswith('Green-kernel-square-trace'):
  a=s.sqrt(int(re.search(r'-G_\{tt\}\+(\d+)G',r['statement'])[1]));A=s.coth(a)/(4*a**3)+1/(4*a*a*s.sinh(a)**2)-1/(2*a**4);d=1/(4*a*a*s.sinh(a)**2)
  pool=[(2*A,'Omit the derivative chain factor two'),(-A,'Reverse the inverse-operator derivative sign'),(A-d,'Omit the derivative of hyperbolic cotangent'),(A+1/(2*a**4),'Omit the endpoint normalization derivative'),(A-2*d,'Reverse the derivative sign of hyperbolic cotangent'),(A/2,'Apply the parameter-chain factor one half twice'),(4*A,'Count the two symmetric integration triangles twice after omitting the derivative chain factor two')]
  ordinal=next(f['indices'] for f in catalog() if f['familyId']==fid).index(index);choices,correct,_=choose_options(A,pool,ordinal,fid+'-supported-hyperbolic-pool')
  for c in choices:
   if c['choiceId']==correct:c['choiceId']=r['answerChoiceId']
  evidence=lambda v:{'sign':'zero','route':'exact identity'} if s.simplify(v)==0 else certificate(v)
  parameters={'a':str(a)};reason='Construct the matched Green kernel, integrate its diagonal, then differentiate the resolvent parameter; an ordinary positive-integral sign check no longer selects the sole paired magnitude.'
 else:raise KeyError(fid)
 assert s.simplify(original-A)==0
 vals=[parse(c['math']) for c in choices];opposites=[]
 for i,j in itertools.combinations(range(4),2):
  diff=evidence(vals[i]-vals[j]);total=evidence(vals[i]+vals[j]);assert diff['sign']in['positive','negative'] and total['sign']!='unresolved'
  checks.append({'choiceIds':[choices[i]['choiceId'],choices[j]['choiceId']],'difference':diff,'sum':total})
  if total['sign']=='zero':opposites.append([choices[i]['choiceId'],choices[j]['choiceId']])
 assert len(opposites) in[0,2]
 final=next(c['math'] for c in choices if c['choiceId']==r['answerChoiceId']);steps=list(r['solutionSteps']);
 if steps[-1]!=final:steps.append(final)
 out={'familyId':fid,'topic':r['topic'],'difficulty':r['difficulty'],'instanceIndex':index,'parameters':parameters,'finiteInstanceIndices':next(f['indices'] for f in catalog() if f['familyId']==fid),'statement':r['statement'],'choices':choices,'answerChoiceId':r['answerChoiceId'],'solutionSteps':steps,'assumptions':r['assumptions'],'pedagogy':r['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':r['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':q['sourceCanonicalHash'],'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')},'sourcePresentation':q['presentationBinding'],'replacesPrivateProblemId':old['problemId'],'verificationEvidence':checks,'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[]),'review':{'status':'pending-independent-root-review','meaningChanged':False,'preservePreviousLineage':True,'newIndependentIdeas':0,'difficultyRationale':reason,'sourceIndependentReview':'unsupported-peer/review-results.json','optionRepairReason':'Remove a confirmed opposite-pair or normalized-rank invariant using actual boundary, Jacobian, chain-factor and integration-count mistakes. All feasible coefficient ranks are allowed; no artificial middle-only rule.'}}
 out['contentHash']=digest(out);return out

def verify(raw):return canon(raw)==canon(build(raw['familyId'],raw['instanceIndex']))
if __name__=='__main__':
 rows=[build(f['familyId'],i) for f in catalog() for i in f['indices']];assert len(rows)==17
 (P/'candidates.jsonl').write_text(''.join(canon(r)+'\n' for r in rows));(P/'catalog.json').write_text(json.dumps(catalog(),indent=2)+'\n');print('built',len(rows))
