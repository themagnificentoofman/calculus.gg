"""Six guarded option-only revisions; no registry or immutable-record writes.

API supports(record), build_patch(record), verify_patch(patch, record).
The parent supplies canonical destination identities after independent review.
"""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,itertools,json,re
import sympy as s
from literal_math import parse
from enclosures import enclose,dump
from audit_pairs import audit
BASE=Path(__file__).resolve().parent
VERSION='series-mathematical-sign-domain-options-v1'
IDS={'cn_07f9f8471f9274bac8b9','cn_7b14effdf2336331644a','cn_5a178a9f09c990290769','cn_beb20410c10a5a949bde','cn_7aff2c8e88ced577e84c','cn_5dfc0a749b042bab1d75'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def tex(v):return s.latex(v).replace(r'\log',r'\ln')
@lru_cache(None)
def originals():return {r['problemId']:r for r in map(json.loads,(BASE/'full-source-records.jsonl').read_text().splitlines())if r['problemId']in IDS}
def supports(record):
 old=originals().get(record.get('problemId'));return old is not None and H(old)==H(record)
def build_patch(record):
 if not supports(record):raise ValueError('Outside exact original content/hash guard')
 r=record;f=r['familyId'];i=r['parameters']['instance'];choices=copy.deepcopy(r['choices']);correct=next(c for c in choices if c['choiceId']==r['answerChoiceId']);A=parse(correct['math']);checks=[]
 if f.endswith('taylor-coefficient-derivative'):
  match=re.search(r'a_\{(\d+)\}=([^.]*)\.',r['statement']);assert match
  n=int(match[1]);a=parse(match[2]);assert n==i+4
  independent=s.factorial(n)*a;x=s.symbols('x');assert s.diff(a*(x-2)**n,x,n).subs(x,2)==independent==A
  j=next(j for j,c in enumerate(choices)if parse(c['math'])==-A)
  if i==0:wrong=n*A;why='Multiply by the derivative order after already applying its factorial'
  else:wrong=(n+1)*A;why='Use the next factorial instead of the requested derivative-order factorial'
  checks=[{'description':'Read the literal coefficient and derivative order','order':n,'coefficient':str(a)},{'description':'Derivative of the coefficient monomial at the center equals the preserved answer','value':str(independent),'result':True}]
  reason='Remove the lone correct-answer/sign-flip pair. The replacement is an unused factorial-conversion error with the same sign as the supplied coefficient; sign alone cannot identify the answer.'
 else:
  assert f=='quality-series-olympiad-singular-cauchy-coefficient'
  alpha=parse(re.search(r'k\^\{(\\frac\{\d+\}\{\d+\})\}',r['statement'])[1]);assert 0<alpha<1
  independent=s.gamma(1-alpha)**2/s.gamma(2-2*alpha);assert s.simplify(s.expand_func(independent-A))==0
  if i in [4,7]:
   j=next(j for j,c in enumerate(choices)if any(g.args[0]<0 for g in parse(c['math']).atoms(s.gamma)))
   wrong=s.gamma(1-alpha)**2/s.gamma(3-2*alpha);why='Increase the denominator Gamma argument by one without the compensating recurrence factor'
   reason='The former wrong option used Gamma at a negative argument although the statement defines it only for positive arguments. The replacement keeps every Gamma input within that displayed definition.'
  else:
   assert i==6;j=next(j for j,c in enumerate(choices)if s.simplify(parse(c['math'])+A/2)==0)
   wrong=A/4;why='Apply the symmetry half-factor twice instead of retaining the complete beta integral'
   reason='Remove the single pair of wrong opposite values. Both alternatives remain plausible positive beta-normalization errors; the correct choice and question are unchanged.'
  checks=[{'description':'Read singular exponent and check endpoint integrability','alpha':str(alpha),'zeroLessAlphaLessOne':True},{'description':'Preserved answer equals the convergent beta integral','expression':s.srepr(independent),'result':True}]
 wrong=s.simplify(wrong);old=choices[j];choices[j]={'choiceId':'ch_'+H([VERSION,s.srepr(wrong)])[:16],'math':tex(wrong),'misconception':why}
 vals=[parse(c['math'])for c in choices];pairs=[]
 for p,q in itertools.combinations(range(4),2):
  diff=s.factor_terms(s.expand_func(vals[p]-vals[q]));iv=enclose(diff);assert iv[0]>0 or iv[1]<0
  pairs.append({'choiceIds':[choices[p]['choiceId'],choices[q]['choiceId']],'difference':s.srepr(diff),'outwardRationalEnclosure':dump(iv)})
 assert next(c for c in choices if c['choiceId']==r['answerChoiceId'])==correct
 assert all(g.args[0]>0 for v in vals for g in v.atoms(s.gamma))
 projection={k:r[k]for k in ['problemId','familyId','answerChoiceId','pedagogy']};projection['choices']=choices;pairreview=audit(projection);assert pairreview['mathematicalPairCount']==0
 return {'patchVersion':VERSION,'problemId':r['problemId'],'familyId':f,'instanceIndex':i,'sourceRevision':r['problemRevision'],'sourceContentHash':r['contentHash'],'sourceSemanticHash':r['semanticHash'],'sourceRawSHA256':H(r),'sourceChoicesSHA256':H(r['choices']),'choices':choices,'answerChoiceId':r['answerChoiceId'],'preservedCorrectChoice':correct,'replacedChoice':old,'replacementChoice':choices[j],'reason':reason,'meaningChanged':False,'preserveStatementSolutionAndLineage':True,'mathematicalChecks':checks,'sixChoiceInequalityCertificates':pairs,'mathematicalOppositePairs':pairreview['oppositePairs'],'newIndependentIdeas':0,'reviewStatus':'candidate-awaiting-independent-parent-review','humanReviewed':False,'formalProof':False}
def verify_patch(patch,record):
 try:return canonical(patch)==canonical(build_patch(record))
 except(ValueError,KeyError,AssertionError,StopIteration):return False
if __name__=='__main__':
 rows=[build_patch(r)for _,r in sorted(originals().items())];assert len(rows)==6
 (BASE/'option-patches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'patches':len(rows),'exactInequalityCertificates':sum(len(p['sixChoiceInequalityCertificates'])for p in rows)}))
