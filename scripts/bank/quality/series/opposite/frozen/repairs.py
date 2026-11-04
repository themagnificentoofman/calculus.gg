"""Guarded immutable option patches; no app, registry or admitted bank mutations.
API: supports(original), build_patch(original), verify_patch(patch, original).
The parent assigns canonical destination revisions/hashes after independent review.
"""
from pathlib import Path
from functools import lru_cache
import json,hashlib,itertools,copy,re
import sympy as s
from intervals import enclose,disjoint,dump
HERE=Path(__file__).resolve().parent
VERSION='series-opposite-pair-options-v1'
SLUGS=['binomial-alternating-difference','binomial-beta-cancellation','Abel-logarithmic-sum','cubic-root-exponential-filter','harmonic-square-generating']
def raw_hash(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def tex(v):return s.latex(s.expand_mul(v)).replace(r'\log',r'\ln')
def norm(t):return re.sub(r'\s+','',t).replace(r'\log',r'\ln')
@lru_cache(None)
def originals():return {r['problemId']:r for r in map(json.loads,(HERE/'source-records.jsonl').read_text().splitlines())}
def supports(record):
 old=originals().get(record.get('problemId'));return old is not None and raw_hash(record)==raw_hash(old)
def make_pool(r):
 slug=next(t for t in SLUGS if r['familyId'].endswith(t));i=r['parameters']['instance'];m=i+4;facts=[]
 if slug=='binomial-alternating-difference':
  A=s.factorial(m);pool=[(s.factorial(m-1),'Omit the last factor from the degree-order finite difference'),(s.factorial(m-2),'Apply two fewer difference normalizations'),(A/2,'Halve the alternating difference as if symmetric endpoints were duplicated'),(s.factorial(m+1),'Use the next difference order'),(m*A,'Include the final derivative degree factor twice'),(2*A,'Count both orientations of the same alternating difference')]
  assert sum((-1)**(m-k)*s.binomial(m,k)*k**m for k in range(m+1))==A
  facts=['The original finite sum independently equals the factorial. Every alternative is a positive integer derived from an omitted or repeated difference normalization. At least one wrong neighboring factorial is retained, so factorial recognizability alone does not isolate the answer.']
 elif slug=='binomial-beta-cancellation':
  A=s.factorial(m-1)*s.factorial(m)/s.factorial(2*m);pool=[(A/m,'Use the lower numerator factorial in both beta parameters'),(A/(2*m+1),'Shift the denominator factorial one place too far'),(A/2,'Apply the beta symmetry half factor twice'),(m*A,'Raise the first numerator factorial without changing the denominator'),(2*m*A,'Stop the denominator factorial one factor early'),(2*A,'Drop the half factor from the symmetric beta integral')]
  assert sum((-1)**k*s.binomial(m,k)/s.Integer(k+m) for k in range(m+1))==A
  facts=['The original finite binomial sum is checked exactly. All four retained alternatives are positive reduced unit fractions; positivity and fraction shape do not select one.']
 elif slug=='Abel-logarithmic-sum':
  a=[s.Rational(1,2),s.Integer(1),s.Rational(3,2),s.Integer(2),s.Integer(3),s.Integer(4),s.Integer(5),s.Integer(6)][i];C=s.log(s.gamma((a+1)/2)/s.gamma(a/2));h=s.log(2);A=C+h/2
  pool=[(2*A,'Sum the neighboring partial-sum limits without their average'),(A/2,'Average the neighboring endpoint correction twice'),(C+h,'Retain the full odd endpoint logarithm instead of its Cesaro half'),(C+h/4,'Halve the endpoint logarithm correction twice'),(2*C+h/2,'Square the paired Gamma ratio before taking its logarithm'),(C/2+h/2,'Take a square root of the paired Gamma ratio')]
  facts=['The finite paired-Gamma and Cesaro-to-Abel proof is unchanged. Wrong coefficients reflect explicit mistakes in the two endpoint contributions. Only alternatives with the same certified sign as the answer are eligible; opposite-pair selection is impossible.']
 elif slug=='cubic-root-exponential-filter':
  E=s.exp(m)/3;T=2*s.exp(-s.Rational(m,2))*s.cos(s.sqrt(3)*m/2)/3;A=E+T
  pool=[(E+T/2,'Retain only one of the two conjugate roots'),(E+T/3,'Apply the three-root averaging factor to the conjugate part twice'),(E+T/6,'Retain one conjugate root and apply the three-root averaging factor twice'),(E+s.Rational(3,2)*T,'Average the conjugate part over two roots instead of three'),(E+2*T,'Count the conjugate root pair twice'),(E+3*T,'Omit the three-root averaging factor from the conjugate part')]
  assert disjoint(enclose(T),enclose(0))
  facts=['The unchanged roots-of-unity identity gives E+T. Every alternative keeps the same real-root contribution and makes a distinct error in the conjugate-root contribution. Explicit cosine Taylor enclosures certify T is nonzero for every actual integer argument, and every displayed value is positive.']
 else:
  x=s.Rational(1,m);D=s.polylog(2,x);L=s.log(1-x)**2;den=1-x;A=(D+L)/den
  pool=[((2*D+L)/den,'Count the harmonic-square diagonal twice'),((D+2*L)/den,'Count the off-diagonal squared-logarithm contribution twice'),((D/2+L)/den,'Halve the diagonal term during the symmetry split'),((D+L/2)/den,'Halve the off-diagonal term twice'),(2*A,'Count both ordered index triangles after including the diagonal'),(A/2,'Divide the complete harmonic-square generating function by two')]
  facts=['The unchanged discrete-difference generating-function proof gives (D+L)/(1-r). Every option retains both positive components. Their coefficients represent diagonal/triangle overcounts or omitted halves. At least one wrong alternative survives the elementary first-term and H_k≤k bounds.']
 A=s.expand_mul(A);pool=[(s.expand_mul(v),why) for v,why in pool];return slug,A,pool,facts

def select(r,A,pool):
 i=r['parameters']['instance'];a=enclose(A);sgn=1 if a[0]>0 else -1;assert sgn==1 or a[1]<0
 clean=[]
 for v,why in pool:
  b=enclose(v)
  if (sgn==1 and b[0]>0 or sgn==-1 and b[1]<0) and disjoint(a,b) and all(disjoint(b,enclose(q[0])) for q in clean):clean.append((v,why))
 assert len(clean)>=3
 lower=[q for q in clean if enclose(q[0])[1]<a[0]];upper=[q for q in clean if enclose(q[0])[0]>a[1]];assert len(lower)+len(upper)==len(clean)
 feasible=[]
 for rank in range(4):
  for lo in itertools.combinations(lower,rank):
   for hi in itertools.combinations(upper,3-rank):
    combo=list(lo+hi)
    if r['familyId'].endswith('binomial-alternating-difference') and not any(v in [s.factorial(i+2),s.factorial(i+3),s.factorial(i+5)] for v,why in combo):continue
    if r['familyId'].endswith('harmonic-square-generating'):
     x=s.Rational(1,i+4);upperbound=x*(1+x)/(1-x)**3
     if not any(enclose(v)[1]>=enclose(x)[0] and enclose(v)[0]<=enclose(upperbound)[1] for v,why in combo):continue
    feasible.append((rank,combo))
 ranks=sorted({rank for rank,combo in feasible});assert ranks
 rank=ranks[[0,3,1,2][i%4]%len(ranks)];choices=[co for ra,co in feasible if ra==rank]
 choice=choices[int(hashlib.sha256((r['problemId']+VERSION).encode()).hexdigest(),16)%len(choices)]
 return choice,{'correctNumericRankZeroBased':rank,'allFeasibleRanks':ranks,'commonSign':sgn,'sameSignPoolSize':len(clean)}
def build_patch(record):
 assert supports(record),'Exact canonical source guard failed'
 slug,A,pool,route=make_pool(record);correct=copy.deepcopy(next(c for c in record['choices'] if c['choiceId']==record['answerChoiceId']));assert norm(correct['math'])==norm(tex(A)),(slug,correct['math'],tex(A))
 chosen,selection=select(record,A,pool);wrongs=[{'choiceId':'qsp_'+hashlib.sha256((record['problemId']+s.srepr(v)).encode()).hexdigest()[:16],'math':tex(v),'misconception':why} for v,why in chosen];wit=iter(wrongs);choices=[correct if c['choiceId']==correct['choiceId'] else next(wit) for c in record['choices']];expressions={correct['choiceId']:A};expressions.update({c['choiceId']:v for c,(v,why) in zip(wrongs,chosen)})
 certificates=[]
 for left,right in itertools.combinations(choices,2):
  le,re=enclose(expressions[left['choiceId']]),enclose(expressions[right['choiceId']]);assert disjoint(le,re);certificates.append({'choiceIds':[left['choiceId'],right['choiceId']],'method':'Disjoint explicit outward-rational enclosures','enclosures':[dump(le),dump(re)]})
 return {'problemId':record['problemId'],'familyId':record['familyId'],'sourceContentHash':record['contentHash'],'sourceSemanticHash':record['semanticHash'],'sourceRawHash':raw_hash(record),'recipeVersion':VERSION,'revisionKind':'option-only','meaningChanged':False,'choices':choices,'answerChoiceId':record['answerChoiceId'],'choiceExpressions':{k:s.srepr(v) for k,v in expressions.items()},'independentExactAnswer':s.srepr(A),'selectionEvidence':selection,'pairwiseChoiceCertificates':certificates,'routeAndMisconceptions':route,'explanationAndQuestionUnchanged':True,'newIndependentIdeas':0}
def verify_patch(patch,original):
 try:return supports(original) and patch==build_patch(original)
 except Exception:return False
if __name__=='__main__':
 out=[]
 for r in originals().values():
  try:out.append(build_patch(r))
  except Exception as e:print(r['familyId'],r['parameters'],repr(e));raise
 (HERE/'option-patches.json').write_text(json.dumps(out,indent=2)+'\n');print('built',len(out))
