"""Replace five irrelevant-parameter lower-level pools; retain their idea lineage."""
from pathlib import Path
import sys,json,copy
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE.parent))
from lower_core import *
BASE=Path(__file__).resolve().parent
OLD={r['familyId']:r for r in json.loads((BASE/'original-records.json').read_text()) if r['difficulty']!='olympiad'}
CASES={
'm3-differentiation-easy-accumulation-derivative':[(m,a) for m,a in [(1,2),(2,2),(3,2),(1,3),(2,3),(3,3),(1,4),(2,4),(3,4),(1,5)]],
'm3-limits-easy-rational-sequence-shift':[(a,c,p) for a,c,p in [(2,3,2),(3,2,2),(2,5,2),(5,2,2),(3,4,3),(4,3,3),(2,3,3),(3,2,3),(4,5,2),(5,4,2)]],
'm3-limits-medium-factorial-ratio-fixed-shift':[(m,c) for m,c in [(2,2),(3,2),(4,2),(5,2),(2,3),(3,3),(4,3),(2,4),(3,4),(2,5)]],
'm3-limits-medium-root-test-scale':[(a,m) for a,m in [(2,2),(3,2),(4,3),(5,3),(6,4),(7,4),(8,-2),(9,-3),(10,-2),(11,-3)]],
'm3-limits-medium-two-sided-square-root':[(a,c,side) for a,c,side in [(2,3,1),(3,2,-1),(2,5,-1),(5,2,1),(3,4,1),(4,3,-1),(2,3,-1),(3,2,1),(4,5,-1),(5,4,1)]]}
def construct(fid,case):
 slug=fid.split('-',3)[3]
 if slug=='accumulation-derivative':
  m,a=case;A=s.Integer(2*a*(a**m+1));F=s.integrate(t**m+1,(t,0,a*x*x));prime=2*a*x*((a*x*x)**m+1)
  ck('The independent integrated polynomial differentiates to the FTC chain expression',s.diff(F,x),prime)
  ck('Evaluation at the actual requested point',prime.subs(x,1),A)
  return candidate(r'F(x)=\int_0^{'+str(a)+r'x^2}(t^{'+str(m)+r'}+1)\,\mathrm dt.\qquad F\prime(1)=?',A,[(s.Integer(a**m+1),'Omit the moving-boundary derivative'),(s.Integer(2*(a**m+1)),'Omit the upper-bound scale in the chain derivative'),(s.Integer(2*a**(m+1)),'Omit the constant integrand contribution'),(s.Integer(2*a*(m*a**(m-1)+1)),'Differentiate the integrand instead of applying the FTC'),(2*A,'Count the chain factor twice'),(A/2,'Omit the derivative of the squared input')],[T('Apply the fundamental theorem of calculus at the moving upper endpoint, then multiply by its derivative.'),r'F\prime(x)='+L(prime),r'F\prime(1)='+L(A)],'FTC-moving-upper-endpoint-value')
 if slug=='rational-sequence-shift':
  a,c,p=case;A=R(a,c)**p;f=((a*n+1)/(c*n+2))**p
  ck('Division by the highest power gives the limit',s.limit(f,n,s.oo),A)
  return candidate(r'\lim_{n\to\infty}\left(\frac{'+str(a)+r'n+1}{'+str(c)+r'n+2}\right)^{'+str(p)+r'}',A,[(R(a,c),'Omit the fixed outer power'),(R(c,a)**p,'Invert the leading coefficient ratio'),(s.Integer(1),'Assume every equal-degree ratio tends to one'),(s.Integer(a)**p,'Omit the leading denominator coefficient'),(R(a,c*p),'Apply the exponent only as a denominator coefficient'),(R(a*p,c),'Replace raising to a power by multiplication')],[r'\frac{'+str(a)+r'n+1}{'+str(c)+r'n+2}=\frac{'+str(a)+r'+1/n}{'+str(c)+r'+2/n}\longrightarrow'+L(R(a,c)),T('The fixed power is a continuous function of this finite ratio.'),L(A)],'fixed-power-leading-coefficient-ratio')
 if slug=='factorial-ratio-fixed-shift':
  m,c=case;A=R(1,c)**m;f=s.prod((1+j/x)/c for j in range(1,m+1))
  ck('Finite factorial cancellation leaves the displayed product',s.prod(x+j for j in range(1,m+1))/(c*x)**m,f)
  ck('Each finite product factor has its leading limit',s.limit(f,x,s.oo),A)
  return candidate(r'\lim_{n\to\infty}\frac{(n+'+str(m)+r')!}{n!\,('+str(c)+r'n)^{'+str(m)+r'}}',A,[(s.Integer(1),'Omit the denominator scale'),(R(1,c),'Use only one surviving factor'),(s.Integer(c)**m,'Invert the factor limits'),(s.factorial(m)*A,'Keep the finite shift factorial after normalization'),(A/c,'Include one extra surviving factor'),(A*c,'Omit one surviving factor')],[r'\frac{(n+'+str(m)+r')!}{n!\,('+str(c)+r'n)^{'+str(m)+r'}}=\prod_{j=1}^{'+str(m)+r'}\frac{1+j/n}{'+str(c)+r'}',T('There are a fixed finite number of factors, and each has the displayed limiting denominator scale.'),L(A)],'fixed-factorial-shift-scaled-product')
 if slug=='root-test-scale':
  a,m=case;A=s.Integer(a);X=s.symbols('X',positive=True)
  ck('Logarithmic root removes the exponential growth and kills polynomial growth',s.limit(s.log(a)+m*s.log(X)/X,X,s.oo),s.log(a))
  pool=[(s.Integer(1),'Discard exponential growth together with polynomial growth'),(s.Integer(a)**m,'Treat the polynomial exponent as an outer exponent'),(R(1,a),'Reverse the logarithmic sign'),(s.Integer(a*a),'Apply the exponential base twice'),(s.sqrt(a),'Take a square root instead of the indicated root'),(s.Integer(a)*abs(m),'Keep a polynomial exponent as a multiplicative factor')]
  return candidate(r'\lim_{n\to\infty}\left('+str(a)+r'^n n^{'+str(m)+r'}\right)^{1/n}',A,pool,[T('The expression is positive, so take its natural logarithm.'),r'\ln\left(('+str(a)+r'^n n^{'+str(m)+r'})^{1/n}\right)=\ln '+str(a)+('+' if m>=0 else '')+str(m)+r'\frac{\ln n}{n}',r'\frac{\ln n}{n}\longrightarrow0',T('Exponentiate the finite logarithmic limit.'),L(A)],'exponential-times-polynomial-root-limit')
 if slug=='two-sided-square-root':
  a,c,side=case;A=R(side*a,c);X=s.symbols('X',positive=True)
  ck('One-sided substitution retains the absolute-value factor',s.sqrt(a*a*(side*X)**2+3*(side*X)**4)/(c*side*X),side*s.sqrt(a*a+3*X*X)/c)
  ck('Evaluation of the continuous branch after sign separation',s.limit(side*s.sqrt(a*a+3*X*X)/c,X,0,dir='+'),A)
  return candidate(r'\lim_{x\to0^{'+('+' if side==1 else '-')+r'}}\frac{\sqrt{'+str(a*a)+r'x^2+3x^4}}{'+str(c)+r'x}',A,[(-A,'Use the opposite one-sided sign'),(R(a,c*c)*side,'Divide by the denominator coefficient twice'),(s.Integer(side*a),'Omit the denominator coefficient'),(R(side*a*a,c),'Forget the principal square root of the leading square'),(R(side*c,a),'Invert the leading ratio'),(A/2,'Insert an unnecessary rationalization factor')],[r'\sqrt{'+str(a*a)+r'x^2+3x^4}=|x|\sqrt{'+str(a*a)+r'+3x^2}',r'\frac{|x|}{x}='+str(side)+r'\quad(x'+('>' if side==1 else '<')+r'0)',r'\frac{\sqrt{'+str(a*a)+r'x^2+3x^4}}{'+str(c)+r'x}=\frac{'+str(side)+r'}{'+str(c)+r'}\sqrt{'+str(a*a)+r'+3x^2}\longrightarrow'+L(A)],'one-sided-principal-root-sign-and-leading-scale')
 raise KeyError(fid)
def catalog():
 return [{'familyId':'q2-repair-'+fid,'originalFamilyId':fid,'topic':OLD[fid]['topic'],'difficulty':OLD[fid]['difficulty'],'instanceCount':len(cs),'finiteDomain':[{'instance':i,'case':list(c)} for i,c in enumerate(cs)]} for fid,cs in CASES.items()]
def build(fid,index):
 old=fid[len('q2-repair-'):];assert old in CASES and 0<=index<len(CASES[old]);original=OLD[old];case=CASES[old][index]
 tok=CHECKS.set([])
 try:p=construct(old,case);evidence=list(CHECKS.get())
 finally:CHECKS.reset(tok)
 opts,answer,pairs=choose_options(p['answer'],p['pool'],index,fid);ped=copy.deepcopy(original['pedagogy']);ped['structuralSignature']=p['structuralSignature'];ped['difficultyRationale']+=' The original irrelevant parameter pool is withdrawn; these finite cases vary the requested value through actual mathematical data. Zero new-idea credit.'
 steps=p['solutionSteps'];final=L(p['answer']);steps=steps+[final] if steps[-1]!=final else steps
 return {'familyId':fid,'topic':original['topic'],'difficulty':original['difficulty'],'parameters':{'instance':index,'case':{'values':list(case),'caseId':str(index)}},'statement':p['statement'],'answerChoiceId':answer,'answerMath':final,'answerExpression':s.srepr(p['answer']),'choices':opts,'solutionSteps':steps,'pedagogy':ped,'provenance':{'kind':'original-finite-pool-replacement','lineage':{'originalFamilyId':old,'construction':original['pedagogy']['constructionId'],'newIdeaCredit':0},'withdrawOriginalFinitePool':True},'validation':{'status':'mathematically-checked-pending-independent-review','evidence':{'independentIntermediateChecks':evidence,'pairwiseOptionChecks':pairs}},'editorialStatus':'needs-independent-review'}
def verify(raw):assert canon(raw)==canon(build(raw['familyId'],raw['parameters']['instance']));return True
if __name__=='__main__':
 rows=[build(f['familyId'],i) for f in catalog() for i in range(f['instanceCount'])]
 (BASE/'replacements-candidates.json').write_text(json.dumps(rows,indent=2));print(len(rows))
