"""Immutable Gamma/PV distractor repairs, pending independent review.

The published source and mathematical task are unchanged. Common expression
forms remove simplification/length tells; each alternative has a named route.
"""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/bank'))
import content_pipeline
from .support import tex
FAMILIES=['io3-gamma-unit-average','io3-principal-value']
VERSION='quality-integration-option-repairs-v2'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def catalog():return [{'familyId':f,'indices':list(range(8)),'newIndependentIdeas':0} for f in FAMILIES]

def build(fid,index):
 if fid not in FAMILIES or type(index)is not int or index not in range(8):raise ValueError('Unreviewed domain')
 old=content_pipeline.build(fid,index);pars=old['provenance']['authoring']['builderParameters']
 overlay=json.loads(Path(__file__).with_name('option-presentations-v2.json').read_text())[old['problemId']]
 assert overlay['sourceContentHash']==old['contentHash'] and overlay['revision']==old['problemRevision']
 choices=[];checks=[]
 def add(value,math,why):
  choices.append({'choiceId':'ch_'+hashlib.sha256(canonical(s.srepr(value)).encode()).hexdigest()[:16],'math':math,'misconception':why,'expression':s.srepr(value)})
 if fid=='io3-principal-value':
  p,q=pars['p'],pars['q'];r=s.Rational(p,q);assert 0<r<s.Rational(1,2) and r!=s.Rational(1,4)
  angle=r'\left('+tex(r)+r'\pi\right)';theta=s.pi*r;A=s.pi/q*s.cot(theta)
  ratio=r'\frac{\cos'+angle+r'}{\sin'+angle+'}'
  inverse=r'\frac{\sin'+angle+r'}{\cos'+angle+'}'
  product=r'\sin'+angle+r'\cos'+angle
  coeff=lambda c:tex(s.simplify(c*s.pi))
  pool=[(A/2,coeff(s.Rational(1,2*q))+ratio,'Retain an extra half from the symmetric split'),(A/q,coeff(s.Rational(1,q*q))+ratio,'Apply the power-substitution Jacobian twice'),(s.pi/q*s.sin(theta)*s.cos(theta),coeff(s.Rational(1,q))+product,'Multiply sine and cosine instead of dividing the reflection ratio'),(2*A,coeff(s.Rational(2,q))+ratio,'Count the symmetric contribution twice'),(q*A,coeff(1)+ratio,'Omit the power-substitution Jacobian'),(s.pi/q*s.tan(theta),coeff(s.Rational(1,q))+inverse,'Invert the sine-cosine reflection ratio')]
  unique=[]
  for candidate in pool:
   if not any(s.simplify(candidate[0]-v[0]).equals(0) for v in unique):unique.append(candidate)
  combinations=[]
  for subset in itertools.combinations(unique,3):
   below=sum(bool(s.N(v[0]-A,60)<0) for v in subset)
   # The peer comparison bound must leave at least one wrong alternative.
   inside=any(0<float(s.N(v[0],60))<float(s.N(s.pi/q,60)) for v in subset)
   if inside or index==0:combinations.append((below,subset))
  feasible=sorted({k for k,_ in combinations});target=feasible[index%len(feasible)]
  eligible=[v for k,v in combinations if k==target]
  selected=eligible[index%len(eligible)]
  for value,display,why in [(A,coeff(s.Rational(1,q))+ratio,'correct'),*selected]:
   add(s.Tuple(s.Symbol('divergent'),value),r'\left(\textnormal{divergent},\ '+display+r'\right)',why)
  x=s.symbols('x',positive=True)
  residue=s.limit((x-1)*x**(p-1)/(1-x**q),x,1)
  assert residue==-s.Rational(1,q)
  checks=[{'description':'Nonzero simple-pole residue','result':str(residue)},{'description':'All four acute trigonometric values are exactly inequivalent','result':True},{'description':'Numerical editorial audit of authored misconception ranks and the elementary peer bound; not an equivalence proof','correctAscendingRank':target+1,'feasibleRanks':[v+1 for v in feasible]}]
 else:
  a=s.Rational(*pars['a']);base=a*s.log(a)-a
  # Errors in the reflected constant are kept inside one logarithmic form.
  pool=[(s.pi,'Omit the factor two from the log-sine normalization'),(4*s.pi,'Count the double-angle normalization twice'),(s.pi**2,'Miss the reflected averaging factor and the log-sine factor two'),(2/s.pi,'Reverse the Gamma-reflection logarithm of pi'),(2*s.pi**2,'Count the reflection logarithm of pi twice')]
  # Deterministic finite misconception subsets; no data-dependent tuning.
  subsets=[(0,1,2),(0,1,4),(1,2,3),(0,3,4),(0,1,2),(0,1,4),(0,1,3),(0,3,4)]
  selected=[(2*s.pi,'correct')]+[pool[j] for j in subsets[index]]
  for C,why in selected:
   value=base+s.log(C)/2
   common=r'\frac12\ln\!\left(\left('+tex(C)+r'\right)\left('+tex(a)+r'\right)^{'+tex(2*a)+r'}\right)-'+tex(a)
   add(value,common,why)
  A=s.symbols('A',positive=True);F=A*s.log(A)-A+s.log(2*s.pi)/2
  assert s.diff(F,A)==s.log(A)
  checks=[{'description':'Sliding-average derivative after Gamma recurrence','result':'ln(A)'},{'description':'Positive logarithm arguments; reflected constant equals one half ln(2 pi)','result':True}]
 for left,right in itertools.combinations(choices,2):
  a,b=s.sympify(left['expression']),s.sympify(right['expression'])
  if isinstance(a,s.Tuple):assert a[0]!=b[0] or s.simplify(a[1]-b[1]).equals(0) is False
  else:assert s.simplify(s.expand_log(a-b,force=True)).equals(0) is False
 steps=overlay['steps']+[r'\textnormal{In the common form used by the choices, the result is}',choices[0]['math']]
 return {'familyId':fid,'topic':'integration','difficulty':'hard' if index==0 or (fid=='io3-gamma-unit-average' and index==2) else 'olympiad','instanceIndex':index,'parameters':{'instance':index},'statement':overlay.get('statement',old['statement']),'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':steps,'assumptions':old['assumptions'],'pedagogy':old['pedagogy'],'provenance':{'kind':'original','theoremReferenceURLs':old['provenance']['authoring']['theoremReferenceURLs']},'verificationEvidence':checks,'analyticCertificate':old['validation']['evidence']['analyticCertificate'],'previous':{'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':False},'constructorVersion':VERSION,'reviewStatus':'candidate-awaiting-independent-review'}
def verify(row):return canonical(row)==canonical(build(row['familyId'],row['instanceIndex']))
if __name__=='__main__':
 rows=[build(f,i) for f in FAMILIES for i in range(8)];Path(sys.argv[1]).write_text(''.join(canonical(r)+'\n' for r in rows));print(canonical({'items':len(rows),'immutableRevisions':len(rows),'status':'pending-independent-review'}))
