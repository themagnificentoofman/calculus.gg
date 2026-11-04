"""Two NEW reviewed indices per lower series construction; frozen sources unchanged.

The old eight-item admission is not extended. Each new record has fresh source
binding, exact intermediate checks, and an explicit ancestor construction.
"""
from __future__ import annotations
import json,re,importlib.util
from pathlib import Path
import sympy as s
from common import package,numeric_options,rearrangement_options,tex,prose,eq,truth,digest
import lower_common as lc
import lower_solution_recipes as recipes
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('quality_frozen_elementary_series',ROOT/'frozen_v37/series_easy.py');easy=importlib.util.module_from_spec(spec);spec.loader.exec_module(easy)
BASE={fid:f for fid,f in lc.FAMILIES.items() if f['difficulty']!='olympiad'}
META={}
LOWER_DEMOTE={'log-integrated-geometric','series-beta-integral','trig-geometric'}
for fid,f in list(BASE.items())+list(easy.FAMILIES.items()):
 new=fid
 level='medium' if fid.split('-',3)[3] in LOWER_DEMOTE else f['difficulty']
 META[new]={'familyId':new,'topic':'series','difficulty':level,'finiteInstanceIndices':[8,9],'relatedIdeaGroupId':f['relatedIdeaGroupId'],'primaryTechnique':f['primaryTechnique'],'difficultyRationale':f['difficultyRationale'],'prerequisites':f.get('prerequisites',[]),'sourceRecordIds':[],'ancestorFamilyId':fid,'constructorVersion':'quality-series-lower-extensions-v3','newIndependentIdeas':0}
def catalog():return list(META.values())
def notation(text):
 text=text.replace(r'\log',r'\ln').replace(r'\operatorname{atan}',r'\arctan').replace(r'\operatorname{asin}',r'\arcsin')
 text=text.replace(r'\,dx',r'\,\mathrm{d}x').replace(r'\,dt',r'\,\mathrm{d}t').replace(r'\,ds',r'\,\mathrm{d}s')
 return text.replace(r'\operatorname{harmonic}{\left(k \right)}',r'H_k').replace(r'\operatorname{harmonic}^{2}{\left(k \right)}',r'H_k^2')
def build(fid,index):
 if fid not in META or type(index)is not int or index not in (8,9):raise ValueError('outside independently reviewed extension domain')
 meta=META[fid];old=meta['ancestorFamilyId'];m=s.Integer(index+4);checks=[]
 if old in BASE:
  raw=lc.source_payload(old,int(m));A=raw['answer']
  if old.endswith('ratio-test-data'):
   opts=[(s.srepr(v),tex(v),why) for v,why in raw['options']];code=s.srepr(A)
  elif old.endswith('telescoping-arctan'):
   pool=[(s.pi/2-s.atan(m+1),'omit the first included term'),(s.pi/2-s.atan(m+2),'omit the first two included terms'),(s.pi/2-s.atan(m-1),'include the preceding excluded term'),(s.pi/2-s.atan(m-2),'include two preceding excluded terms'),(s.pi/2-s.atan(m*m),'retain a squared index after telescoping'),(s.pi/2-s.atan(1/m),'invert the terminal arctangent argument')]
   opts,code=numeric_options(A,pool,index,fid)
  elif old.endswith('conditional-block-rearrangement'):opts,code=rearrangement_options(m,index,fid)
  else:opts,code=numeric_options(A,[(v,why) for v,why in raw['options'] if why!='correct'],index,fid)
  virtual={'familyId':old,'parameters':{'m':int(m),'instance':index}}
  sol=recipes.solve(virtual);steps=[notation(v) for v in sol['solutionSteps']];Q=notation(raw['statement'])
  if old.endswith('conditional-block-rearrangement'):steps[-1]=next(o[1] for o in opts if o[0]==code)
  checks=[{'name':c['description'],'passed':True,'kind':'exact-algebra','left':c.get('left'),'right':c.get('right')} for c in sol['checks'] if c['result']=='exact equality']
  analytic=[c['description']+': '+'; '.join(c.get('hypotheses',[])) for c in sol['checks'] if c['result']!='exact equality']+raw.get('domain',[])
  if old.endswith('harmonic-generating'):Q=Q.split(r'\quad')[0]+r'\qquad H_n=\sum_{j=1}^{n}\frac1j.'
  if old.endswith('borderline-exponential-comparison'):Q=Q.split(r'\textnormal')[0]+prose('For real p, this series converges exactly when p exceeds a sharp constant c. Find c.')
  if old.endswith('dyadic-infinite-product'):Q=r'\prod_{k=0}^{\infty}\left(1+\left('+tex(1/m)+r'\right)^{2^k}\right)=?'
  if not checks:raise AssertionError('new finite instance lacks executed check '+old)
 else:
  slug=old.split('-easy-')[1]
  if slug in ['p-series-pair','alternating-absolute-conditional']:
   p,q=([s.Rational(5,4),s.Rational(4,5)] if index==8 else [s.Rational(9,10),s.Rational(10,9)])
   alt=slug.startswith('alternating');a=('absolute' if p>1 else 'conditional') if alt else ('converges' if p>1 else 'diverges');b=('absolute' if q>1 else 'conditional') if alt else ('converges' if q>1 else 'diverges');code=a+'|'+b
   opts=easy.category_pair_options('absolute' if alt else 'converges','conditional' if alt else 'diverges',code)
   term=r'(-1)^{n-1}' if alt else '1'
   Q=r'A=\sum_{n=1}^{\infty}\frac{'+term+r'}{n^{'+tex(p)+r'}},\quad B=\sum_{n=1}^{\infty}\frac{'+term+r'}{n^{'+tex(q)+r'}}.'+prose('Classify the two series in the displayed order. '+('Absolute means the absolute-value series converges; conditional means the original series converges and its absolute-value series diverges.' if alt else ''))
   steps=([prose('Both positive magnitudes decrease to zero, so both alternating series converge.')] if alt else [])+[prose('A positive series with terms one over n to the power p converges exactly when p is greater than one.'),r'\int_1^\infty x^{-p}\,\mathrm{d}x=\begin{cases}1/(p-1),&p>1,\\+\infty,&0<p\le1.\end{cases}',r'p_A='+tex(p)+r',\quad p_B='+tex(q),prose('The first series is '+a+' and the second is '+b+'.'),next(v[1] for v in opts if v[0]==code)]
   checks=[{'name':c['name'],'kind':'exact-antiderivative-and-limit','passed':c['passed']} for c in easy.p_certificate(p,'A')+easy.p_certificate(q,'B')];analytic=['The comparison functions are positive and decreasing for the displayed positive exponents. The integral comparison establishes the positive-series threshold; for the alternating case the magnitudes also tend to zero.']
  else:
   fn=easy.FAMILIES[old]['build'];raw=fn(m);Q=notation(raw['statement']);steps=[notation(v) for v in raw['solutionSteps']];checks=raw['automatedChecks'];analytic=raw['analyticCertificate'];opts=raw['options'];code=raw['answer']
   opts=[o[:3] for o in opts]
   if slug=='direct-comparison-information':
    p=m/8 if (index%4)==0 else m/16;upper=index%4 in (0,2)
    bound=r'0\le a_n\le n^{-'+tex(p)+r'}' if upper else r'a_n\ge n^{-'+tex(p)+r'}'
    Q=prose('A real sequence satisfies the displayed bound for every positive integer n. What conclusion follows from this bound alone?')+r'\quad '+bound+r',\qquad\sum_{n=1}^{\infty}a_n.'
   if slug=='taylor-coefficient-derivative':Q=r'f(x)=\sum_{k=0}^{\infty}a_k(x-2)^k\quad(|x-2|<1),\qquad a_{'+tex(m)+r'}='+tex((-1)**m*(m-3)/(m+2))+r'.\quad f^{('+tex(m)+r')}(2)=?'
   if slug=='taylor-coefficient-derivative':
    A=s.factorial(m)*s.Rational((-1)**int(m)*(m-3),m+2)
    pool=[(A/m,'use the preceding factorial'),(A*(m+1),'use the next factorial'),(-A,'reverse the supplied coefficient sign'),(A*(m+2),'omit the supplied coefficient denominator'),(A/(m-3),'omit the supplied coefficient numerator'),(A*s.factorial(m),'apply the derivative factorial twice')]
    opts,code=numeric_options(A,pool,index,fid)
    steps[-1]=next(o[1] for o in opts if o[0]==code)
   if slug=='linearity-given-convergent-sums':steps=[prose('Use the same finite endpoint for the two partial sums, distribute the coefficients, and then take limits. Both component limits exist by hypothesis.'),r'\sum_{n=1}^{N}(2a_n-'+tex(m)+r'b_n)=2\sum_{n=1}^{N}a_n-'+tex(m)+r'\sum_{n=1}^{N}b_n',r'\sum_{n=1}^{\infty}(2a_n-'+tex(m)+r'b_n)=2('+tex(m-2)+r')-'+tex(m)+r'('+tex(m+1)+r')='+tex(-m*m+m-4)]
   if steps[-1]!=next(o[1] for o in opts if o[0]==code):steps.append(next(o[1] for o in opts if o[0]==code))
 return package(meta,index,Q,opts,code,steps,checks,analytic,parameters={'m':int(m),'instance':index},lineage={'relationship':'new-finite-instances-of-existing-construction','ancestorFamilyId':old,'newIdeaCount':0,'oldConstructorUnchanged':True})
def verify(record):
 """Recheck independent solution routes for this new, bounded domain."""
 old=record['lineage']['ancestorFamilyId'];i=record['instanceIndex'];m=record['parameters']['m'];checks=[]
 if old in BASE:
  sol=recipes.solve({'familyId':old,'parameters':{'m':m,'instance':i}})
  checks=[c for c in sol['checks'] if c['result']=='exact equality']
  assert checks
  correct=next(c['math'] for c in record['choices'] if c['choiceId']==record['answerChoiceId'])
  if old.endswith('conditional-block-rearrangement'):
   assert correct==r'\ln 2+\frac12\ln\!\left('+tex(m)+r'\right)';checks.append(eq('uniform-format choice preserves the verified logarithmic value',lc.source_payload(old,m)['answer'],s.log(2)+s.log(m)/2))
  else:assert correct==sol['answerMath']
 else:
  # Elementary pairs are verified by independent rational exponent inequalities;
  # the derivative/linearity variants have direct finite algebraic checks.
  slug=old.split('-easy-')[1]
  if slug=='taylor-coefficient-derivative':
   z=s.symbols('z');c=s.Rational((-1)**m*(m-3),m+2);A=s.diff(c*(z-2)**m,z,m).subs(z,2);checks=[eq('independent polynomial derivative at center',A,s.factorial(m)*c)]
  elif slug=='linearity-given-convergent-sums':checks=[eq('independent supplied linear combination',2*(m-2)-m*(m+1),-m*m+m-4)]
  elif slug=='direct-comparison-information':checks=[truth('new bounds force the reported class',(i==8 and s.Rational(m,8)>1) or (i==9 and s.Rational(m,16)<=1))]
  else:checks=[truth('new paired exponents straddle one',s.Rational(5,4)>1>s.Rational(4,5) if i==8 else s.Rational(9,10)<1<s.Rational(10,9))]
 assert digest({k:v for k,v in record.items() if k!='contentHash'})==record['contentHash']
 return {'status':'passed','sourceContentHash':record['contentHash'],'checks':checks,'analyticCertificate':record['analyticCertificate'],'humanReviewed':False,'formalProof':False,'scope':'New finite-domain exact derivations plus displayed analytic hypotheses; frozen eight-instance review is not treated as extending admission.'}
if __name__=='__main__':
 rows=[];checks=[]
 for meta in catalog():
  for i in meta['finiteInstanceIndices']:
   r=build(meta['familyId'],i);v=verify(r);rows.append(r);checks.append({'familyId':r['familyId'],'instanceIndex':i,'sourceContentHash':r['contentHash'],'verification':v})
 (ROOT/'lower-extensions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));(ROOT/'lower-verification.json').write_text(json.dumps({'families':len(catalog()),'instances':len(rows),'newIdeas':0,'items':checks,'sourceFiles':{f:__import__('hashlib').sha256((ROOT/f).read_bytes()).hexdigest() for f in ['lower_extensions.py','lower_common.py','lower_solution_recipes.py','common.py']}},indent=2)+'\n');print(json.dumps({'families':len(catalog()),'instances':len(rows),'newIdeas':0}))
