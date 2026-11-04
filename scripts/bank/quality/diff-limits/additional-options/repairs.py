"""Source-guarded finite menu overlay; preserve all mathematical tasks and levels.
Existing full authored pools are reused; simplex entropy adds explicit category-weight errors. Scalar choice verification does
not replace the original mathematical/analytic review.
"""
from pathlib import Path
from functools import lru_cache
import json,hashlib,copy
import sympy as s
from literal_numeric_extended import parse
from menu_core import choose_options,canon,digest,L
BASE=Path(__file__).resolve().parent
VERSION='quality-ode-mv-additional-opposite-pair-v2'
@lru_cache(None)
def data():
 for name,expected in json.loads((BASE/'input-manifest.json').read_text())['files'].items():
  assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==expected,('Bound input changed',name)
 rows=json.loads((BASE/'inputs.json').read_text());pools={p['problemId']:p for name in ['q4','old'] for p in json.loads((BASE/('authored-pools-'+name+'.json')).read_text())}
 pres=json.loads((BASE/'presentations.json').read_text());old=json.loads((BASE/'baseline-inputs.json').read_text())
 assert len(rows)==len(pools)==97
 return rows,pools,pres,old

def catalog():
 rows=data()[0];out=[]
 for f in sorted({r['familyId'] for r in rows}):
  rs=sorted([r for r in rows if r['familyId']==f],key=lambda r:(data()[1][r['problemId']]['parameters'].get('m',''),r['problemId']))
  out.append({'familyId':f,'instanceCount':len(rs),'finiteDomain':[{'index':i,'sourceProblemId':r['problemId'],'sourceContentHash':r['contentHash'],'sourceCanonicalInstance':r['parameters']['instance'],'parameters':data()[1][r['problemId']]['parameters']} for i,r in enumerate(rs)],'newIndependentIdeas':0})
 return out

def build(fid,index):
 meta=next(f for f in catalog() if f['familyId']==fid);assert type(index)is int and 0<=index<meta['instanceCount']
 case=meta['finiteDomain'][index];old=next(r for r in data()[0] if r['problemId']==case['sourceProblemId']);p=data()[1][old['problemId']];pres=data()[2][old['problemId']]
 assert p['sourceContentHash']==pres['sourceContentHash']==old['contentHash']
 A=s.sympify(p['answerExpression']);pool=[(s.sympify(v['expression']),v['misconception']) for v in p['pool']]
 actual=parse(next(c['math'] for c in old['choices'] if c['choiceId']==old['answerChoiceId']));assert s.simplify(s.expand_func(actual-A))==0
 forms=[]
 if fid.endswith('simplex-log-partition'):
  m=s.Integer(p['parameters']['m']);args=[m,m/2,m/(m-3)];base=[s.Integer(2),s.Integer(4),2*(m-3)]
  def entropy_form(coeffs):return sum(c*s.log(a) for c,a in zip(coeffs,args))/(2*m)
  forms=[(entropy_form(base),base)]
  pool=[]
  for j in range(3):
   for factor in [s.Rational(1,2),s.Integer(2)]:
    coeff=base.copy();coeff[j]*=factor;value=entropy_form(coeff);pool.append((value,('Halve' if factor<1 else 'Double')+' the entropy weight of category '+str(j+1)+' while retaining all three category contributions'));forms.append((value,coeff))
  for j in range(3):
   coeff=[c if k==j else c/2 for k,c in enumerate(base)];value=entropy_form(coeff);pool.append((value,'Halve the two entropy weights outside category '+str(j+1)+' while retaining all category terms'));forms.append((value,coeff))
  assert s.simplify(s.expand_log(forms[0][0]-A,force=True))==0
 choices,correct,checks=choose_options(A,pool,index,fid+'-existing-authored-pool-opposite-repair')
 if forms:
  for choice in choices:
   value=s.sympify(choice['expression']);matches=[coeff for q,coeff in forms if s.simplify(s.expand_log(q-value,force=True))==0];assert matches
   coeff=matches[0];terms=[('' if c==1 else L(c))+r'\ln\left('+L(a)+r'\right)' for c,a in zip(coeff,args)]
   choice['math']=r'\frac{'+ '+'.join(terms)+r'}{'+str(2*m)+'}'
 # Retain the established correct choice identity; expression convention is common.
 for c in choices:
  if c['choiceId']==correct:c['choiceId']=old['answerChoiceId']
 correct=old['answerChoiceId'];final=next(c['math'] for c in choices if c['choiceId']==correct)
 vals=[parse(c['math']) for c in choices]
 for j,v in enumerate(vals):
  assert s.simplify(s.expand_func(v-s.sympify(choices[j]['expression'])))==0
  for w in vals[:j]:assert s.simplify(s.expand_func(v-w)).equals(0)is False
 pairs=[(i,j) for i in range(4) for j in range(i) if s.simplify(s.expand_func(vals[i]+vals[j]))==0]
 assert len(pairs) in [0,2]
 steps=list(pres['steps']);
 if steps[-1]!=final:steps.append(final)
 out={'familyId':fid,'topic':old['topic'],'difficulty':old['difficulty'],'instanceIndex':index,'parameters':p['parameters'],'finiteInstanceIndices':list(range(meta['instanceCount'])),'statement':pres['statement'],'choices':choices,'answerChoiceId':correct,'solutionSteps':steps,'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'constructorVersion':VERSION,'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring'].get('theoremReferenceURLs',[])},'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old),'rawConstructorHash':old['provenance']['authoring'].get('rawSha256')},'sourcePresentation':{'entryHash':digest(pres),'source':pres['source']},'verificationEvidence':checks+[{'kind':'literal-choice-reparse','count':4,'passed':True},{'kind':'exact-expanded-pair-inequalities','count':6,'passed':True},{'kind':'exact-expanded-opposite-pairs','count':len(pairs),'passed':True}], 'analyticCertificate':old['validation']['evidence'].get('analyticCertificate',[]),'sourceProofBinding':{'fullOriginalValidationHash':digest(old['validation']),'answerUnchanged':True,'statementUnchangedFromBoundPresentation':True,'solutionUnchangedExceptEquivalentFinalAnswerDisplay':True,'originalConstructorChecks':p['executedOriginalConstructorChecks'],'authoredPoolHash':digest(p)},'review':{'status':'candidate-awaiting-independent-peer-and-final-id-screen','meaningChanged':False,'preservePreviousLineage':True,'newIndependentIdeas':0,'optionRepairReason':'Reuse existing authored values, plus explicit complete entropy category-weight errors where term omission leaked length; exclude a singleton mathematical or literal opposite pair. This layer performs no new question or difficulty changes.'}}
 baseline=data()[3].get(old['problemId'])
 binding=json.loads((BASE/'admission-source-bindings.json').read_text())['records'][old['problemId']]
 assert binding['sourceContentHash']==old['contentHash']
 if binding['previous'] is not None:
  out['previous']=binding['previous']
  out['review']['baselineMeaningChanged']=bool(binding['previous'].get('meaningChanged'))
  if binding['semanticChangeReason']:out['review']['semanticChangeReason']=binding['semanticChangeReason']
 elif baseline:
  assert baseline['semanticHash']==old['semanticHash']
  out['previous']={'problemId':baseline['problemId'],'revision':baseline['problemRevision'],'sourceContentHash':baseline['contentHash'],'semanticHash':baseline['semanticHash'],'meaningChanged':False}
 else:out['replacesPrivateProblemId']=old['problemId']
 out['contentHash']=digest(out);return out

def verify(raw):
 return canon(raw)==canon(build(raw['familyId'],raw['instanceIndex']))

if __name__=='__main__':
 rows=[];failures=[]
 for f in catalog():
  for i in range(f['instanceCount']):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:failures.append({'familyId':f['familyId'],'index':i,'error':repr(e)})
 (BASE/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
 assert not failures,failures
 (BASE/'candidates.jsonl').write_text(''.join(canon(r)+'\n' for r in rows))
 (BASE/'catalog.json').write_text(json.dumps(catalog(),indent=2)+'\n')
 print(json.dumps({'records':len(rows),'families':len(catalog()),'baselineRevisions':sum('previous' in r for r in rows),'privateReplacements':sum('replacesPrivateProblemId' in r for r in rows)}))
