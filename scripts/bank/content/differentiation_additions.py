#!/usr/bin/env python3
"""Independent original differentiation constructions; finite parameter domain, no network or model calls.
Each executed check evaluates a residual, initial datum, invariant or independent
finite derivation. Analytic obligations are recorded separately from machine checks.
"""
from __future__ import annotations
import argparse, hashlib, json, re, textwrap
from pathlib import Path
import sympy as s
from authored_options import select_authored_triple, supplement_differentiation_pool
R=s.Rational
x=s.symbols('x', real=True)
X,Y,D,D2=s.symbols('X Y D D2',real=True)
pi=s.pi
FAMILIES={}
def L(a):return s.latex(s.sympify(a),fold_short_frac=False)
def T(a):return r'\textnormal{'+a+'}'
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def exact(a,b):
 if isinstance(a,s.Tuple) or isinstance(b,s.Tuple):return isinstance(a,s.Tuple) and isinstance(b,s.Tuple) and len(a)==len(b) and all(exact(c,d) for c,d in zip(a,b))
 return s.simplify(s.trigsimp(s.expand_func(a-b)))==0
def ck(name,a,b=0):
 assert exact(a,b),name+': '+str(s.simplify(a-b))
 return {'name':name,'passed':True}
def reg(level,slug,group,method,reason,why,prereq=(),alternatives=(),refs=()):
 def dec(fn):
  fid='m3-differentiation-'+level+'-'+slug.lower()
  FAMILIES[fid]=dict(familyId=fid,topic='differentiation',difficulty=level,relatedIdeaGroupId=group,primaryTechnique=method,reasoningDemand=reason,difficultyRationale=why,prerequisites=list(prereq),alternativeTechniques=list(alternatives),sourceRecordIds=list(refs),editorialStatus='admitted',build=fn)
  return fn
 return dec

def pack(m,statement,answer,pool,steps,checks,conditions,analytic,structure,answer_form='exact-real'):
 answer=s.sympify(answer)
 assert checks and all(c['passed'] is True for c in checks)
 assert not answer.has(s.nan,s.zoo,s.oo,-s.oo,s.Integral,s.Sum,s.Limit)
 pool=supplement_differentiation_pool(structure,m,pool)
 clean=[]
 for value,label in pool:
  value=s.sympify(value)
  if value.has(s.nan,s.zoo,s.oo,-s.oo):continue
  if exact(value,answer) or any(exact(value,v) for v,_ in clean):continue
  clean.append((value,label))
 assert len(clean)>=3,('distractor pool collapsed',statement,clean)
 # All feasible numerical ranks are eligible; exact inequivalence remains checked below.
 chosen=select_authored_triple(answer,clean,m,structure)
 selected=[answer]+[v for v,_ in chosen]
 for a in selected:assert a.is_real is not False
 for j,a in enumerate(selected):
  for b in selected[:j]:
   if isinstance(a,s.Tuple):
    assert any(s.simplify(c-d).is_zero is False or s.simplify(c-d).equals(0) is False for c,d in zip(a,b)), 'unresolved tuple inequivalence'
   else:
    delta=s.simplify(a-b)
    assert delta.is_zero is False or delta.equals(0) is False, 'unresolved option inequivalence'
 return dict(statement=statement,answer=answer,wrongs=chosen,solutionSteps=steps+[r'\boxed{'+L(answer)+'}'],automatedChecks=checks,domain=conditions,analyticCertificate=analytic,structuralSignature=structure,answerForm=answer_form)

def values(a,items):return [(s.sympify(v),why) for v,why in items]

@reg('olympiad','sharp-endpoint-derivative','chebyshev-extremality','alternating-interpolation-weights','proof','Derives a sharp derivative bound from only a uniform interval constraint by the signs of interpolation weights, and constructs an extremizer.',prereq=('Lagrange interpolation','Chebyshev recurrence'),alternatives=('endpoint Markov inequality with proof',))
def sharp_endpoint(m):
 n=int(m);C=s.chebyshevt(n,x);ans=m*m
 # A separate finite recurrence differentiates the defining polynomial recurrence at 1.
 previous,current=s.Integer(0),s.Integer(1)
 for k in range(1,n):previous,current=current,2+2*current-previous
 return pack(m,T('Among real polynomials P of degree at most ')+L(m)+T(' satisfying |P(x)|<=1 for every x in [-1,1], find the greatest possible value of ')+r'P\prime(1).',ans,[(m,'assume the endpoint bound is the interior frequency'),(m*m/2,'lose an endpoint derivative factor'),(2*m*m,'double the sharp endpoint weight sum'),(m*(m+1),'use the adjacent polynomial degree in the extremal recurrence'),(m*(m-1),'drop the linear part of the squared degree')],[r'x_k=\cos(k\pi/'+L(m)+r'),\quad k=0,\ldots,'+L(m),T('Interpolate P at these descending nodes. The kth cardinal polynomial has derivative at 1 positive for even k and negative for odd k.'),r'P\prime(1)=\sum_k P(x_k)\ell_k\prime(1)\le\sum_k|\ell_k\prime(1)|',r'T_n(\cos\theta)=\cos(n\theta)\ \Longrightarrow\ T_n(x_k)=(-1)^k',r'\sum_k|\ell_k\prime(1)|=T_n\prime(1)=n^2\quad(n='+L(m)+r')',T('The Chebyshev polynomial attains the bound and has absolute value at most one on the entire interval.')],[ck('explicit extremizer degree',s.degree(C,x),m),ck('extremizer value at endpoint',C.subs(x,1),1),ck('extremizer differentiated endpoint',s.diff(C,x).subs(x,1),ans),ck('independent differentiated recurrence',current,ans),ck('Chebyshev recurrence polynomial identity',C,2*x*s.chebyshevt(n-1,x)-s.chebyshevt(n-2,x))],['Real polynomial P; the bound holds on the full closed interval, not just at sample nodes.'],['Let ell_k(x)=product_{j!=k}(x-x_j)/(x_k-x_j). For k>0, differentiating at x_0=1 leaves a strictly positive numerator and a denominator with exactly k negative factors, hence sign (-1)^k. For k=0, ell_0 prime(1)=sum_{j>0}1/(1-x_j)>0. Exact interpolation therefore bounds P prime(1) by the sum of absolute weights. The recurrence T_0=1,T_1=x,T_{n+1}=2xT_n-T_{n-1}, together with the cosine addition formula, proves T_n(cos theta)=cos(n theta). Its alternating node values make that weight sum exactly T_n prime(1). Differentiating the recurrence at 1 gives a_0=0,a_1=1,a_{n+1}=2+2a_n-a_{n-1}, hence a_n=n squared. This also supplies an attainable extremizer, completing sharpness.'],'sharp-uniform-polynomial-endpoint-derivative')

@reg('olympiad','cyclic-determinant-second-derivative','determinant-principal-minor-combinatorics','multilinearity-and-cycle-deletion','synthesis','Extracts a second determinant derivative through all principal minors, recognizes two paths after deleting a vertex pair, and counts cyclic distances.',prereq=('determinant multilinearity','tridiagonal determinant recurrence','finite sums'))
def cyclic_determinant(m):
 n=int(m);A=2*s.eye(n)
 for j in range(n):A[j,(j+1)%n]=-1;A[(j+1)%n,j]=-1
 # charpoly evaluates det(lambda I-A); substitute lambda=-x and correct sign.
 z=s.symbols('lambda');Dpoly=s.Poly(A.charpoly(z).as_expr().subs(z,-x)*(-1)**n,x).as_expr();ans=m*m*(m*m-1)/6
 minors=sum(A.extract([k for k in range(n) if k not in (i,j)],[k for k in range(n) if k not in (i,j)]).det() for i in range(n) for j in range(i+1,n))
 distance_sum=sum(s.Integer(r)*(n-r) for r in range(1,n))
 displayed=r'A_{ij}(x)=\begin{cases}2+x,&i=j,\\-1,&i-j\equiv\pm1\pmod{'+L(m)+r'},\\0,&\mathrm{otherwise}.\end{cases}'
 return pack(m,T('Let A(x) be the following ')+L(m)+T(' by ')+L(m)+T(' matrix whose entries are ')+displayed+r'.\quad\left.\frac{d^2}{dx^2}\det A(x)\right|_{x=0}=?',ans,[(ans/2,'return the quadratic coefficient without multiplying by two'),(2*ans,'count both orientations twice after differentiating'),(m*m,'return the first determinant derivative'),(m*(m*m-1)/6,'omit the choice of starting vertex'),(m*m*(m*m+1)/6,'use the wrong finite-sum subtraction')],[T('By determinant multilinearity, the coefficient of x squared is the sum of principal minors obtained by deleting two vertices.'),T('A path block of length k with diagonal 2 and adjacent -1 has determinant k+1, from ')+r'D_k=2D_{k-1}-D_{k-2},\quad D_0=1,\ D_1=2.',T('Deleting vertices at cyclic distance r leaves path lengths r-1 and n-r-1; the minor equals r(n-r).'),r'[x^2]\det A(x)=\frac n2\sum_{r=1}^{n-1}r(n-r)=\frac{n^2(n^2-1)}{12}',r'(\det A)\prime\prime(0)=2!\,[x^2]\det A(x),\quad n='+L(m)],[ck('characteristic polynomial second derivative',s.diff(Dpoly,x,2).subs(x,0),ans),ck('independent principal-minor coefficient',2*minors,ans),ck('cyclic distance count',m*distance_sum/2,minors),ck('zero eigenvalue at origin',Dpoly.subs(x,0))],['Matrix size n>=4, avoiding coincident neighbor edges. The derivative is with respect to the common diagonal increment x.'],['Multilinearity in columns selects either the old column or x times its coordinate vector. Selecting two coordinate columns leaves the corresponding principal minor with positive sign; thus the x squared coefficient is their sum. Every unordered vertex pair is counted twice by the n starting vertices and distances 1,...,n-1, including antipodal pairs. Removing the pair splits the cycle into two path blocks, with an empty block assigned determinant one. Their exact recurrence gives product r(n-r), and summing r and r squared yields the displayed formula.'],'cycle-Laplacian-second-diagonal-determinant-derivative')

@reg('olympiad','oscillatory-regularity-pair','oscillatory-regularity-threshold','leading-oscillatory-derivative-induction','proof','Separates existence of a derivative at a point from continuity of that derivative, using a full leading-term induction and oscillating failure sequences.',prereq=('higher derivatives at a point','asymptotic bounds','oscillatory sequences'))
def oscillatory_regularity(m):
 n=int(m);A=x**(2*n+2);B=s.Integer(0);checks=[]
 for k in range(1,n+2):
  nextA=s.diff(A,x)+B/x**2;nextB=s.diff(B,x)-A/x**2
  checks.append(ck('product-chain derivative recurrence '+str(k),s.diff(A*s.sin(1/x)+B*s.cos(1/x),x),nextA*s.sin(1/x)+nextB*s.cos(1/x)))
  A=s.expand(nextA);B=s.expand(nextB)
  low=2*n+2-2*k
  assert s.degree(A,x) is not s.S.NegativeInfinity or s.degree(B,x) is not s.S.NegativeInfinity
  assert all(int(power[0])>=low for expr in (A,B) for power,coef in s.Poly(expr,x).terms() if coef!=0)
  checks.append({'name':'all powers meet inductive lower bound at derivative '+str(k),'passed':True})
 assert (A.subs(x,0),B.subs(x,0)) in [(1,0),(-1,0),(0,1),(0,-1)]
 checks.append({'name':'highest existing derivative has a unit nonzero oscillating leading coefficient','passed':True})
 ans=s.Tuple(m+1,m)
 return pack(m,r'f(x)=\begin{cases}x^{'+L(2*m+2)+r'}\sin(1/x),&x\ne0,\\0,&x=0.\end{cases}\quad'+T('Find (r,s), where r is the greatest integer for which f has an rth derivative at 0, and s is the greatest integer for which all derivatives through order s are continuous on a neighborhood of 0.'),ans,[(s.Tuple(m,m),'require continuity to count a derivative at the point'),(s.Tuple(m+1,m+1),'assume an existing derivative must be continuous'),(s.Tuple(2*m+1,2*m),'ignore two powers lost through the oscillatory phase'),(s.Tuple(m+2,m+1),'allow one additional order after the leading oscillation becomes constant size'),(s.Tuple(m,m-1),'lose an extra order in the difference quotient')],[r'f^{(k)}(x)=x^{'+L(2*m+2)+r'-2k}\left(\varepsilon_k\phi_k(1/x)+O(x)\right)\quad(x\ne0)',T('The trigonometric factor alternates between sine and cosine, with coefficient 1 or -1. Induction follows by differentiating the phase.'),r'k\le '+L(m+1)+r'\ \Longrightarrow\ \frac{f^{(k-1)}(x)}x=O\!\left(x^{'+L(2*m+3)+r'-2k}\right)\to0',T('Thus all these derivatives at zero exist and equal zero. Through order m the punctured derivatives also tend to zero.'),T('At order m+1, a nonzero sine or cosine term has constant amplitude. Suitable sequences make it approach 1 and -1, so this derivative is not continuous; dividing it by x also prevents the next derivative from existing.')],checks,['Real x near zero; derivatives at zero are defined recursively by two-sided difference quotients.'],['Write each punctured derivative as A_k(x)sin(1/x)+B_k(x)cos(1/x). The recurrence A_(k+1)=A_k prime+B_k/x squared, B_(k+1)=B_k prime-A_k/x squared shows its smallest power is 2m+2-2k, with coefficient vector cycling (1,0),(0,-1),(-1,0),(0,1). All other terms have at least one higher power. For k<=m+1, the preceding derivative divided by x is O(|x|^(2m+3-2k)), which tends to zero, proving the derivative at zero inductively. For k<=m, the punctured derivative tends to zero, proving continuity. At k=m+1, choose positive sequences whose reciprocal phase makes the leading sine/cosine equal 1 and -1; the O(x) remainder vanishes. Hence this derivative is discontinuous. Along a sequence with leading value 1, its difference quotient at zero is unbounded, so derivative m+2 does not exist.'],'oscillatory-higher-derivative-existence-versus-continuity','ordered-integer-pair')

@reg('olympiad','Newton-iteration-jet','Newton-error-valuation-composition','quadratic-error-order-doubling','reframing','Avoids an eighth-order chain-rule expansion by tracking the first nonzero Newton error and its order through three compositions.',prereq=('Newton iteration','Taylor coefficients','composition order'))
def newton_jet(m):
 n=int(m);z=s.symbols('z');N=((m-1)*x+x**(1-m))/m;c=(m-1)/2;ans=s.factorial(8)*c**7
 jet=s.expand(sum((s.binomial(1-m,k)/m+(m-1)/m if k==1 else s.binomial(1-m,k)/m)*z**k for k in range(1,9)))
 g=z;minimums=[]
 for _ in range(3):
  # Truncate after each multiplication rather than building enormous rational iterates.
  out=s.Integer(0);power=s.Integer(1)
  for k in range(1,9):
   power=s.Poly(s.expand(power*g),z).as_dict();power=sum(coef*z**degree[0] for degree,coef in power.items() if degree[0]<=8)
   out+=jet.coeff(z,k)*power
  g=s.expand(out);minimums.append(min(degree[0] for degree,coef in s.Poly(g,z).terms() if coef!=0))
 return pack(m,r'N(x)=x-\frac{x^{'+L(m)+r'}-1}{'+L(m)+r'x^{'+L(m-1)+r'}},\quad H=N\circ N\circ N.\quad H^{(8)}(1)=?',ans,[(ans/s.factorial(8),'return a Taylor coefficient instead of a derivative'),(s.factorial(8)*c**3,'multiply three coefficients but ignore error squaring'),(s.factorial(8)*c**8,'use the final order as the coefficient exponent'),(s.factorial(8)*(m-1)**7,'omit the quadratic Taylor factor one half at every stage'),(ans/2,'divide the eighth derivative by an extra factor two'),(-ans,'reverse the Newton correction sign')],[r'N(1+z)-1=cz^2+O(z^3),\quad c=\frac{'+L(m-1)+r'}2',r'N^{\circ2}(1+z)-1=c^3z^4+O(z^5)',r'H(1+z)-1=c^7z^8+O(z^9)',T('Each composition squares the error and multiplies its leading coefficient by c. Multiply the final coefficient by 8 factorial.')],[ck('Newton map fixed point',N.subs(x,1),1),ck('Newton map zero first derivative',s.diff(N,x).subs(x,1)),ck('Newton quadratic coefficient',s.diff(N,x,2).subs(x,1)/2,c),ck('jet first coefficient',jet.coeff(z,1)),ck('jet second coefficient',jet.coeff(z,2),c),ck('exact finite jet coefficient after three compositions',s.factorial(8)*g.coeff(z,8),ans),ck('orders double in exact composed jets',s.Tuple(*minimums),s.Tuple(2,4,8))],['N is analytic near its nonzero fixed point x=1; composition is taken three times.'],['The rational Newton map is analytic near 1 and has vanishing first derivative but nonzero quadratic coefficient c. If E(z)=a z^r+O(z^(r+1)), then N(1+E)-1=c a squared z^(2r)+O(z^(2r+1)). Applying this twice to the first error gives orders 2,4,8 and coefficients c,c cubed,c to the seventh power. No lower-order Taylor term survives, and the eighth derivative is 8 factorial times that coefficient. The independent exact truncated-jet composition checks this finite claim without assuming the final formula.'],'Newton-three-compositions-first-surviving-eighth-derivative')

@reg('hard','moving-endpoint-parameter-second','Leibniz-moving-endpoints-parameter','Leibniz-rule-twice','synthesis','Combines moving integration limits with explicit parameter dependence, retaining a boundary contribution from an integral that collapses at the evaluation point.',prereq=('Leibniz differentiation rule','chain rule','fundamental theorem'))
def moving_endpoint(m):
 t=s.symbols('t',real=True);F=(s.exp(x**(m+1))-s.exp(x*x))/x;J=(s.exp(x**(m+1))*(x**(m+1)-1)-s.exp(x*x)*(x*x-1))/x**2
 boundary=m*x**(m-1)*s.exp(x**(m+1))-s.exp(x*x);ans=(2*m*m+m-3)*s.E
 return pack(m,r'F(x)=\int_x^{x^{'+L(m)+r'}}e^{xt}\,dt\quad(x>0).\quad F\prime\prime(1)=?',ans,[((2*m*m-2)*s.E,'drop the moving-boundary contribution of the remaining integral'),((m*m+2*m-3)*s.E,'omit one derivative of the moving upper endpoint factor'),(2*ans,'count the boundary terms twice'),(ans/2,'return the quadratic Taylor coefficient'),(-(2*m*m+m-3)*s.E,'reverse the orientation of both limits')],[r'F\prime(x)='+L(boundary)+r'+\int_x^{x^{'+L(m)+r'}}t e^{xt}\,dt',T('Differentiate again. The first two terms contribute (2m squared-2)e at x=1.'),T('The remaining integral has zero length at x=1, but its derivative contributes (m-1)e from its moving boundaries; the interior integral still vanishes.'),r'F\prime\prime(1)=(2\cdot'+L(m*m)+r'-2+'+L(m)+r'-1)e'],[ck('closed integral differentiates by Leibniz',s.diff(F,x),boundary+J),ck('closed integral primitive in t',s.diff(s.exp(x*t)/x,t),s.exp(x*t)),ck('second derivative independent closed form',s.diff(F,x,2).subs(x,1),ans),ck('remaining-integral boundary contribution',s.diff(J,x).subs(x,1),(m-1)*s.E)],['x lies in a positive neighborhood of 1; both endpoints and the integrand are smooth.'],['Leibniz differentiation applies on a compact rectangle around x=1 containing both moving endpoints. Although the integral itself vanishes at coincident endpoints, its derivative is the integrand at the endpoint times the difference of endpoint velocities. The second differentiation must retain this term. The explicit primitive supplies a separate exact check.'],'second-Leibniz-derivative-collapsing-moving-interval')

def display_statement(statement):
 pieces=re.split(r'(\\textnormal\{[^{}]*\}|\\quad\s*)',statement)
 lines=[]
 for piece in pieces:
  piece=piece.strip()
  if not piece or piece.startswith(r'\quad'):continue
  if piece.startswith(r'\textnormal{') and piece.endswith('}'):
   lines.extend(T(part) for part in textwrap.wrap(piece[len(r'\textnormal{'):-1],width=30))
  else:lines.append(piece)
 return statement if len(lines)<2 else r'\begin{gathered}'+r'\\'.join(lines)+r'\end{gathered}'

def catalog():
 return [{k:v for k,v in meta.items() if k!='build'} for meta in FAMILIES.values()]

def build(family_id,instance_index):
 if family_id not in FAMILIES:raise ValueError('unknown family')
 if type(instance_index) is not int or not 0<=instance_index<8:raise ValueError('instance index must be an integer in 0..7')
 meta=FAMILIES[family_id];m=instance_index+4;p=meta['build'](s.Integer(m));answer=p.pop('answer');wrongs=p.pop('wrongs')
 p['statement']=display_statement(p['statement']);p['solutionSteps']=[display_statement(v) for v in p['solutionSteps']]
 expression_choices=[(answer,'correct')]+wrongs
 choices=[dict(choiceId='ch_'+H(s.srepr(v))[:16],math=L(v),misconception=why) for v,why in expression_choices]
 correct=choices[0]['choiceId']
 # Deterministic content order varies too; runtime still must permute by stable IDs.
 turn=int(H({'family':family_id,'index':instance_index})[:8],16)%4
 choices=choices[turn:]+choices[:turn]
 semantic=H({'familyId':family_id,'parameter':m,'statement':p['statement']})
 record={k:v for k,v in meta.items() if k!='build'}
 record.update(p,schemaVersion=2,problemId='cn_m3_'+semantic[:20],problemRevision=1,parameters={'m':m},parameterDomain={'m':list(range(4,12))},semanticHash=semantic,choices=choices,answerChoiceId=correct,normalizedStructure=p['structuralSignature'],estimatedSolveSeconds={'easy':60,'medium':130,'hard':260,'olympiad':480}[meta['difficulty']],source={'kind':'independently-authored','thirdPartyProblemAdapted':False,'attribution':'Original Calculus Ninja content, AI-assisted; machine checks and analytic arguments distinguished.','license':'LicenseRef-CalculusNinja-Original'},validation={'status':'verified','route':'derivation-specific-residual-invariant-or-exact-finite-derivation','engine':'SymPy '+s.__version__,'humanReviewed':False,'formalProof':False,'analyticCertificateMachineProved':False,'editorialReview':'AI-assisted; not human review','numericalAgreementUsedAsProof':False,'parameterCheck':True,'uniqueCorrectOption':True})
 record['pedagogy']={k:record[k] for k in ['relatedIdeaGroupId','structuralSignature','primaryTechnique','alternativeTechniques','prerequisites','answerForm','difficultyRationale','sourceRecordIds']}
 record['pedagogy'].update(constructionId=family_id,reasoningDemand=[record['reasoningDemand']],responseFormat='multiple-choice')
 record['contentHash']=H(record)
 return record

def verify(record):
 try:
  m=record['parameters']['m']
  if type(m) is not int:return False
  return record==build(record['familyId'],m-4)
 except (KeyError,ValueError,AssertionError,TypeError):return False

def generate(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];quarantine=[]
 for f in catalog():
  for i in range(8):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:quarantine.append({'familyId':f['familyId'],'instanceIndex':i,'error':type(e).__name__+': '+str(e)})
  print(f['familyId'],len(rows),'rows',len(quarantine),'quarantined',flush=True)
 counts={level:{'families':sum(f['difficulty']==level for f in catalog()),'instances':sum(r['difficulty']==level for r in rows)} for level in ['easy','medium','hard','olympiad']}
 assert len({r['problemId'] for r in rows})==len(rows)
 assert len({r['semanticHash'] for r in rows})==len(rows)
 (out/'catalog.json').write_text(json.dumps(catalog(),indent=2)+'\n')
 (out/'candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 report={'counts':counts,'candidateCount':len(rows),'activeImportedCount':0,'quarantine':quarantine,'uniqueIds':True,'uniqueSemanticHashes':True,'executedCheckCount':sum(len(r['automatedChecks']) for r in rows),'humanReviewed':False,'analyticArguments':'Human-readable analytic certificates are AI-authored, distinct from executed symbolic checks.','difficultyReview':'AI-assisted editorial admission; an independent AI peer reviewed all five proofs and level fit. No human or formal proof review is claimed.','relatedIdeaGroupCount':len({f['relatedIdeaGroupId'] for f in catalog()}),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 return report

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(Path(__file__).parent));args=ap.parse_args();generate(args.out)
