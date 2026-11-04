"""Independent finite review of a parent-discovered options-visible shortcut.
Imports no author constructor. The existing frozen integration source is read-only.
"""
from pathlib import Path
import argparse,json,hashlib,re,itertools
from fractions import Fraction as F
import sympy as s
from rigorous_intervals import box,add,mul,neg,pi_box,enclose as base_enclose,dump

def atan(q):
 q=F(q)
 if q<0:return neg(atan(-q))
 if q==1:return mul(box(F(1,4)),pi_box())
 if q>1:return add(mul(box(F(1,2)),pi_box()),neg(atan(1/q)))
 N=300;value=sum((-1)**k*q**(2*k+1)/F(2*k+1) for k in range(N));tail=q**(2*N+1)/F(2*N+1)
 return box(value-tail,value+tail)
def interval(e):
 if e.func==s.atan:
  q=e.args[0];assert q.is_Rational;return atan(F(int(q.p),int(q.q)))
 if e.is_Add:
  out=box(0)
  for a in e.args:out=add(out,interval(a))
  return out
 if e.is_Mul:
  out=box(1)
  for a in e.args:out=mul(out,interval(a))
  return out
 if e.is_Pow and e.exp==2:
  a=interval(e.base);return box(min(a[0]**2,a[1]**2),max(a[0]**2,a[1]**2))
 return base_enclose(e)
def tex(e):return re.sub(r'\s+','',s.latex(e).replace(r'\operatorname{atan}',r'\arctan'))
def raw(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=[r for r in map(json.loads,a.source.read_text().splitlines()) if r['familyId'].endswith('coupled-endpoint-sharp-energy')];out=[];x,k=s.symbols('x k',real=True);c=1/(k-1)
 lowerden=s.integrate(x*(c+1)**2+(1-x)*c*c,(x,0,1));assert s.simplify(lowerden-(k*k+1)/(2*(k-1)**2))==0
 trialden=s.integrate((1+(k-1)*x)**2,(x,0,1));assert s.simplify(trialden-(k*k+k+1)/3)==0
 for r in rows:
  q=s.Rational(r['parameters']['endpointRatio']);assert q>1;L=2*(q-1)**2/(q*q+1);U=3*(q-1)**2/(q*q+q+1);A=4*s.atan((q-1)/(q+1))**2;values=[A,A/4,4*A,s.atan(q)**2,4*s.atan(1/q)**2,s.pi**2/4,s.pi**2];mapping={tex(v):v for v in values};choices=[]
  for choice in r['choices']:
   literal=re.sub(r'\s+','',choice['math']);assert literal in mapping,(literal,list(mapping));v=mapping[literal];I=interval(v);survive=not(I[1]<L or I[0]>U);choices.append({'choiceId':choice['choiceId'],'literalMath':choice['math'],'independentlyDecodedExpression':s.srepr(v),'certifiedEnclosure':dump(I),'survivesNecessaryInterval':survive})
  survivors=[v['choiceId'] for v in choices if v['survivesNecessaryInterval']];assert survivors==[r['answerChoiceId']]
  out.append({'problemId':r['problemId'],'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'endpointRatio':str(q),'sourceContentHash':r['contentHash'],'sourceSemanticHash':r['semanticHash'],'sourceRawSHA256':raw(r),'lowerBound':str(L),'upperBound':str(U),'choices':choices,'onlySurvivingChoice':survivors[0],'actualOptionsDifficulty':'hard','advancedCapacityCredit':0,'formulaCorrectness':'Unchanged sharp constant agrees with the prior exact ground-state proof; this review concerns an easier actual-option route.'})
 report={'sourceArtifact':str(a.source.resolve()),'sourceArtifactSHA256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'reviewerCodeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'counts':{'actualCases':len(out),'oneChoiceSurvives':sum(bool(r['onlySurvivingChoice']) for r in out),'hardRecommendations':len(out),'advancedGroupsFromTheseActualOptions':0,'advancedCapacityFromTheseActualOptions':0},'independentDerivation':['For an admissible C1 function, the endpoint relation gives f(0)=integral(fprime)/(k−1). Hence f(x)=integral[1/(k−1)+indicator(t≤x)]fprime(t)dt.','Pointwise Cauchy-Schwarz followed by integration in x bounds integral f² by [(k²+1)/(2(k−1)²)] integral fprime². Therefore the best constant is at least2(k−1)²/(k²+1).','The admissible affine trial f(x)=1+(k−1)x has derivative energy(k−1)² and squared norm(k²+k+1)/3. Therefore the best constant is at most3(k−1)²/(k²+k+1).','The two polynomial integrals are independently checked symbolically. Every literal displayed choice is decoded from explicit expression templates and enclosed using alternating arctangent series with rational remainder, plus a Machin pi enclosure. No float decides exclusion.'],'records':out,'disposition':'All ten current finite option sets are answered by the necessary Cauchy-Schwarz/trial interval. Recommend Hard for every index, preserve the correct long proof and original frozen artifact, and assign no Olympiad group/capacity credit to these actual questions. This finding is not a mathematical error in the sharp constant.','humanReviewed':False,'formalProof':False,'authorConstructorImported':False,'productionMutation':False};a.out.write_text(json.dumps(report,indent=2)+'\n');print(report['counts']);print('reportSHA256',hashlib.sha256(a.out.read_bytes()).hexdigest())
if __name__=='__main__':main()
