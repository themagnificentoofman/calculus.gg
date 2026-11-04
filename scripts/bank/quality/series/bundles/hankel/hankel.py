"""Original finite geometric-moment determinant constructions, independent review pending."""
from pathlib import Path
import json,hashlib
import sympy as s
from common import tex as L,prose as T,eq,truth,package,numeric_options,digest,OPTION_AUDITS
R=s.Rational
FID='quality-series-olympiad-geometric-moment-determinant'
META={'familyId':FID,'topic':'series','difficulty':'olympiad','finiteInstanceIndices':list(range(10)),'relatedIdeaGroupId':'Cauchy-geometric-moment-determinant','primaryTechnique':'alternating-polynomial-factorization','difficultyRationale':'The geometric sums expose a moment matrix, but a Cauchy determinant factorization and pairwise geometric exponent count are needed to recover its normalized determinant. Direct geometric summation alone does not answer the question.','prerequisites':['determinants','geometric series','Vandermonde factorization'],'sourceRecordIds':[],'constructorVersion':'quality-series-Hankel-v1','nearestNeighbors':[{'group':'Hilbert-sequence-two-moment-projection','relationship':'Both use a Gram-like matrix; this problem derives an arbitrary-rank determinant, not a two-constraint energy projection.'},{'group':'spectral-Hankel-differentiation','relationship':'Possible global relationship requires parent taxonomy review; no eigenvalue differentiation or perturbation is used here.'}],'newIndependentIdeas':1}
def catalog():return [META]
def parameters(i):return 5+i//2,2+i%2

def data(i):
 n,b=parameters(i);q=R(1,b);E=n*(n-1)*(2*n-1)//6;C=n*(n-1)//2;S=n*(n-1)*(n-2)//6
 denominator=s.prod(1-q**(j+k+1) for j in range(n) for k in range(n))
 differences=s.prod((1-q**d)**(2*(n-d)) for d in range(1,n))
 return n,b,q,E,C,S,denominator,differences

def build(fid,i):
 if fid!=FID or type(i)is not int or i not in range(10):raise ValueError('Outside reviewed finite domain')
 n,b,q,E,C,S,den,diff=data(i);A=q**E
 errors=[(E-C,'Omit the shift in every column-node exponent'),(E+C,'Shift every column-node exponent an additional step'),(E-S,'Omit the geometric powers from one Vandermonde factor'),(E+S,'Count one set of geometric powers twice'),(C,'Keep only the column shift and omit both row-index contributions'),(2*E,'Square the total extracted geometric factor')]
 opts,code=numeric_options(A,[(q**e,why) for e,why in errors],i,FID)
 oldkey=digest([[(c,t) for c,t,_ in opts],code]);exponent={s.srepr(q**e):e for e,_ in errors};exponent[s.srepr(A)]=E
 opts=[(c,str(b)+r'^{-'+str(exponent[c])+'}',why) for c,_,why in opts]
 OPTION_AUDITS[digest([[(c,t) for c,t,_ in opts],code])]=OPTION_AUDITS[oldkey]
 final=str(b)+r'^{-'+str(E)+'}'
 Q=r'n='+str(n)+r',\quad q=\frac1{'+str(b)+r'},\qquad M_{ij}=\sum_{k=0}^{\infty}q^{(i+j+1)k}\quad(0\le i,j<n).\quad '+T('Here M is the square matrix with these entries. Find the displayed normalized determinant.')+r'\quad\frac{\det(M)\displaystyle\prod_{i,j=0}^{n-1}(1-q^{i+j+1})}{\displaystyle\prod_{d=1}^{n-1}(1-q^d)^{2(n-d)}}.'
 steps=[T('All entrywise geometric series converge, since their ratios lie strictly between zero and one.'),r'M_{ij}=\frac1{1-q^{i+j+1}}=\frac1{1-u_iv_j},\qquad u_i=q^i,\quad v_j=q^{j+1}.',T('Multiply a determinant of this form by all its denominators. The result is a polynomial alternating in the row nodes and separately in the column nodes. It therefore contains both Vandermonde products.'),r'P(u,v)=\det\!\left[\frac1{1-u_iv_j}\right]\prod_{i,j=0}^{n-1}(1-u_iv_j).',r'P(u,v)=C\prod_{0\le i<j<n}(u_i-u_j)(v_i-v_j).',T('Each node has degree at most n minus one in the polynomial, exactly the degree of its Vandermonde factor. Thus the remaining factor C is a constant. To determine it, replace every row node by t times that node and expand about t equal to zero.'),r'\frac1{1-tu_iv_j}=\sum_{r=0}^{\infty}t^r u_i^r v_j^r.',T('Multilinearity makes any repeated exponent give a zero determinant. The first nonzero total degree uses precisely the exponents from zero through n minus one. Its coefficient is the product of the two Vandermonde determinants. The denominator product has constant term one, so C equals one.'),r'\det\!\left[\frac1{1-u_iv_j}\right]=\frac{\prod_{i<j}(u_i-u_j)(v_i-v_j)}{\prod_{i,j}(1-u_iv_j)}.',T('Now extract the powers of q from each pair. A difference of indices d occurs n minus d times.'),r'(u_i-u_j)(v_i-v_j)=q^{2i+1}(1-q^{j-i})^2\quad(i<j),',r'\prod_{i<j}(u_i-u_j)(v_i-v_j)=q^{\sum_{i=0}^{n-2}(n-1-i)(2i+1)}\prod_{d=1}^{n-1}(1-q^d)^{2(n-d)}.',r'\sum_{i=0}^{n-2}(n-1-i)(2i+1)=\frac{n(n-1)(2n-1)}6='+str(E)+'.',r'q^{'+str(E)+r'}='+final,final]
 checks=[truth('all geometric ratios are strictly inside the unit interval',0<q<1),eq('pairwise geometric exponent sum',sum((n-1-j)*(2*j+1) for j in range(n-1)),E),eq('pairwise products match grouped differences',s.prod((q**j-q**k)*(q**(j+1)-q**(k+1)) for j in range(n) for k in range(j+1,n)),A*diff)]
 analytic=['The matrix and every product are finite, and no denominator vanishes since 0<q<1. Multiplying the determinant by its full denominator clears fractions. Alternation forces each pairwise difference divisor; the individual node degree bound leaves only a constant. The local analytic expansion near t=0 is valid uniformly over finitely many nodes. Multilinearity or finite Cauchy-Binet computes its first nonzero coefficient from exponents0 through n-1, fixing the constant as1. This finite polynomial identity then holds wherever its displayed rational denominators are nonzero.']
 r=package(META,i,Q,opts,code,steps,checks,analytic,parameters={'matrixSize':n,'geometricBase':b,'normalizingExponent':E})
 return r

def verify(record):
 """Separate route: exact rational Gaussian elimination, never the product formula."""
 n=record['parameters']['matrixSize'];b=record['parameters']['geometricBase'];q=R(1,b)
 M=s.Matrix(n,n,lambda j,k:1/(1-q**(j+k+1)))
 actual=M.det(method='domain-ge')
 den=s.prod(1-q**(j+k+1) for j in range(n) for k in range(n));difference=s.prod((1-q**d)**(2*(n-d)) for d in range(1,n));target=q**sum(j*j for j in range(1,n))
 checks=[eq('Independent exact rational matrix elimination',actual*den/difference,target),truth('positive normalizing factors',den>0 and difference>0),truth('exact determinant positivity',actual>0)]
 correct=next(c['math'] for c in record['choices'] if c['choiceId']==record['answerChoiceId']);assert correct==str(b)+r'^{-'+str(sum(j*j for j in range(1,n)))+'}'
 assert len(record['choices'])==len({c['math'] for c in record['choices']})==4
 assert digest({k:v for k,v in record.items() if k!='contentHash'})==record['contentHash']
 return {'familyId':FID,'instanceIndex':record['instanceIndex'],'sourceContentHash':record['contentHash'],'status':'passed','checks':checks,'exactCheckCount':len(checks),'scope':'Independent rational elimination verifies every concrete matrix value; written alternating-polynomial argument proves the general identity. No formal-proof or human-review claim.','humanReviewed':False}
if __name__=='__main__':
 rows=[];reports=[]
 for i in range(10):
  r=build(FID,i);reports.append(verify(r));rows.append(r)
 root=Path(__file__).parent;(root/'hankel-candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));(root/'hankel-verification.json').write_text(json.dumps({'instances':10,'newGroups':1,'executedChecks':sum(v['exactCheckCount'] for v in reports),'results':reports},indent=2)+'\n');print('10 independently verified rational determinants')
