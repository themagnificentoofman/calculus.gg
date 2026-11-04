"""Finite common-form nonnormal-transient choice repair; no runtime authoring."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,json,re,itertools
import sympy as s
from differentiation_literal_choices import parse
from limits_intervals import enclose
P=Path(__file__).resolve().parent
FAMILY='q4-differential-equations-nonnormal-transient-maximum'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
@lru_cache(None)
def sources():return {r['parameters']['instance']:r for r in map(json.loads,(P/'source-records.jsonl').read_text().splitlines())}
# numerator branch, damping exponent sign, reverse the dimensionless time.
ROUTES={
 'correct':(1,1,False,'correct'),
 'small':(-1,1,False,'Select the smaller singular-value branch at the maximizing time.'),
 'reciprocal-time':(1,1,True,'Invert the dimensionless maximizing time in the damping factor while retaining the singular-value factor.'),
 'small-reciprocal-time':(-1,1,True,'Select the smaller singular-value branch and invert the damping time.'),
 'growth':(1,-1,False,'Replace exponential damping by exponential growth at the maximizing time.'),
 'small-growth':(-1,-1,False,'Select the smaller singular-value branch and reverse the damping sign.'),
 'reciprocal-growth':(1,-1,True,'Invert the damping time and reverse its sign while retaining the larger singular-value factor.'),
 'small-reciprocal-growth':(-1,-1,True,'Select the smaller singular-value branch, invert the damping time, and reverse its sign.'),
}
MENUS={
 0:['decay-time-one','reciprocal-norm','growth'],
 1:['decay-time-one','reciprocal-growth-norm','growth'],
 2:['growth','reciprocal-growth','small-reciprocal-growth'],
 3:['decay-time-one','reciprocal-norm','small'],
 4:['decay-time-one','reciprocal-growth-norm','reciprocal-time'],
 5:['growth','reciprocal-growth','small-reciprocal-growth'],
 6:['decay-time-one','reciprocal-growth-norm','growth'],
 7:['decay-time-one','reciprocal-norm','small'],
 8:['growth','reciprocal-growth','small-reciprocal-growth'],
 9:['decay-time-one','reciprocal-growth-norm','reciprocal-time'],
}
def data(old):
 m=re.search(r'\\begin\{pmatrix\}-1&(.*?)\\\\0&-1\\end',old['statement']);assert m
 K=parse(m[1]);assert K.is_Rational and K>2
 q=int(s.denom(K));k=int(K*q);D=s.sqrt(k*k-4*q*q);d=D/q
 return K,q,k,D,d

def pool(old):
 K,q,k,D,d=data(old);a=s.latex(D);b=str(k);items={}
 for name,(branch,sign,reciprocal,label)in ROUTES.items():
  numerator=str(k)+(' + 'if branch==1 else' - ')+s.latex(D)
  exp_n,exp_d=(b,a)if reciprocal else(a,b)
  math=r'\frac{'+numerator+'}{'+str(2*q)+r' e^{'+('+'if sign==1 else'-')+r'\frac{'+exp_n+'}{'+exp_d+'}}}'
  value=(K+branch*d)*s.exp(-sign*(K/d if reciprocal else d/K))/2
  items[name]={'choiceId':'ch_'+digest([FAMILY,old['parameters']['instance'],name,math])[:16],
               'math':math,'misconception':label,'expression':s.srepr(value),'namedRoute':name}

 # Actual operator norm at a mistaken time, with the singular vector still optimized.
 one=(s.sqrt(k*k+4*q*q)+k)/(2*q*s.E)
 extra={
 'decay-time-one':(r'\frac{'+str(k)+' + '+s.latex(s.sqrt(k*k+4*q*q))+'}{'+str(2*q)+r' e}',one,'Assume the amplification peaks at the exponential decay time t=1, but correctly optimize the initial direction.'),
 }
 for name,sign in [('reciprocal-norm',1),('reciprocal-growth-norm',-1)]:
  E=s.sqrt(k**4+4*q*q*(k*k-4*q*q))
  math=r'\frac{'+str(k*k)+' + '+s.latex(E)+'}{'+s.latex(2*q*D)+r' e^{'+('+'if sign==1 else'-')+r'\frac{'+str(k)+'}{'+s.latex(D)+'}}}'
  value=(k*k+E)/(2*q*D)*s.exp(-sign*k/D)
  extra[name]=(math,value,'Invert the dimensionless maximizing time and evaluate the full operator norm there.'if sign==1 else'Invert the dimensionless maximizing time and reverse damping when evaluating the full singular-value factor.')
 for name,(math,value,label)in extra.items():
  items[name]={'choiceId':'ch_'+digest([FAMILY,old['parameters']['instance'],name,math])[:16],
   'math':math,'misconception':label,'expression':s.srepr(value),'namedRoute':name}
 return items

def build(family,index):
 if family!=FAMILY or type(index)is not int or index not in MENUS:raise ValueError('Outside frozen finite domain')
 old=copy.deepcopy(sources()[index]);K,q,k,D,d=data(old);items=pool(old);choices=[items[n]for n in ['correct']+MENUS[index]]
 # This deterministic author ordering is not the shared gameplay shuffle.
 choices.sort(key=lambda c:digest([old['problemId'],c['choiceId'],'common-form-v1']))
 selected=items['correct'];level='hard'if index in[2,5,8]else old['difficulty']
 raw={k:copy.deepcopy(old[k])for k in ['familyId','topic','statement','assumptions','pedagogy']}
 raw.update({'constructorVersion':'nonnormal-visible-bounds-options-v2','instanceIndex':index,'finiteInstanceIndices':list(range(10)),
  'parameters':{'instance':index,'literalShear':str(K)},'difficulty':level,'choices':choices,'answerChoiceId':selected['choiceId'],
  'solutionSteps':old['solutionSteps']+[selected['math']],
  'sourcePreview':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],
   'semanticHash':old['semanticHash'],'canonicalRawHash':digest(old)},'replacesPrivateProblemId':old['problemId'],
  'provenance':{'kind':'original','theoremReferenceURLs':old.get('provenance',{}).get('authoring',{}).get('theoremReferenceURLs',[])},
  'review':{'meaningChanged':False,'newIndependentIdeas':0,'qualifiedOlympiad':level=='olympiad','recommendedDifficulty':level,
   'easiestOptionsVisibleRoute':'Compute the Euclidean operator norm of the triangular flow, then maximize its logarithm over nonnegative time. The norm is e^(-t)(sqrt(K^2*t^2+4)+K*t)/2 and the unique positive critical time is sqrt(K^2-4)/K.',
   'difficultyRationale':'The seven potential Olympiad menus include the actual norm at t=1, which survives elementary lower and upper bounds; deciding against it requires the time-optimization step. All displayed alternatives are complete radical/exponential norm expressions. The previous Hard dispositions for indices2,5,8 remain conservative editorial ceilings; no advanced capacity is reclaimed solely because their former shortcut was removed.',
   'priorHardShortcutStillDecidesNewMenu':False if index in[2,5,8]else None,
   'preserveNormalizedLineage':True,'status':'pending-independent-peer-and-final-catalog-screen'},
  'presentationRule':'Capture the current exact-source statement/steps, then append the exact equivalent selected result; use complete radical/exponential norm values for every alternative.'})
 raw['contentHash']=digest(raw);return raw

def sign_certificate(expr):
 z=s.simplify(expr).rewrite(s.exp);lo,hi=enclose(z);assert lo>0 or hi<0,(expr,lo,hi)
 return {'lower':str(lo),'upper':str(hi),'sign':1 if lo>0 else -1}

def verify(raw):
 index=raw['instanceIndex'];old=sources()[index]
 assert canonical(raw)==canonical(build(raw['familyId'],index))
 K,q,k,D,d=data(old);t=s.symbols('t',nonnegative=True)
 # Singular values are the positive roots obtained from F(t)^T F(t).
 S=s.Matrix([[1,K*t],[0,1]]);lam=(s.sqrt(K*K*t*t+4)+K*t)**2/4
 assert s.simplify((S.T*S-lam*s.eye(2)).det())==0
 log_derivative=K/s.sqrt(K*K*t*t+4)-1
 assert s.simplify(log_derivative.subs(t,d/K))==0
 assert s.simplify(s.diff(s.log((s.sqrt(K*K*t*t+4)+K*t)/2)-t,t)-log_derivative)==0
 expected=(K+d)*s.exp(-d/K)/2
 oldanswer=parse(next(c['math']for c in old['choices']if c['choiceId']==old['answerChoiceId']))
 assert s.simplify(expected-oldanswer)==0
 assert s.simplify(parse(old['solutionSteps'][-1])-expected)==0
 choices=pool(old);values={v['choiceId']:s.sympify(v['expression'])for v in choices.values()}
 assert s.simplify(values[raw['answerChoiceId']]-expected)==0
 pairs=[]
 for a,b in itertools.combinations(raw['choices'],2):
  pairs.append({'choiceIds':[a['choiceId'],b['choiceId']],'difference':sign_certificate(values[a['choiceId']]-values[b['choiceId']]),
                'sum':sign_certificate(values[a['choiceId']]+values[b['choiceId']])})
 rank=sum(sign_certificate(values[raw['answerChoiceId']]-values[c['choiceId']])['sign']>0 for c in raw['choices']if c['choiceId']!=raw['answerChoiceId'])
 return {'rawSha256':digest(raw),'sourceCanonicalRawHash':digest(old),'answerSameExact':True,'oldConclusionSameExact':True,
  'finiteDomain':['K>2','t>=0','nonzero real initial vector','Euclidean norm'],
  'globalMaximumProof':'The logarithmic derivative K/sqrt(K²t²+4)−1 decreases strictly from K/2−1>0 to−1, so its unique zero gives the global maximum. The positive flow singular value follows from the exact characteristic polynomial; the initial norm ratio at zero is1.',
  'literalChoicePairCertificates':pairs,'correctNumericRankZeroBased':rank,'correctForm':'Larger singular-value branch and positive damping exponent at the correct dimensionless time.','passed':True}
if __name__=='__main__':
 rows=[];reviews=[]
 for i in range(10):r=build(FAMILY,i);rows.append(r);reviews.append({'familyId':FAMILY,'index':i,**verify(r)})
 (P/'candidates.jsonl').write_text(''.join(canonical(r)+'\n'for r in rows));(P/'finite-review.json').write_text(json.dumps({'records':reviews,'counts':{'records':10,'pairInequalities':60,'sumInequalities':60},'scope':'Author finite analytic/checkable review, independent peer still required.'},indent=2)+'\n')
 print(json.dumps({'records':len(rows),'ranks':[r['correctNumericRankZeroBased']for r in reviews]}))
