"""Purposeful mathematical replacements for failed stage04 option forms."""
from core import *
from math import gcd

def product_power(case):
 b=s.Integer(case['b']);p=int(case['power']);A=-R(p,p+1)/s.log(b)**R(1,p)
 H=s.symbols('H',positive=True);J=s.symbols('J',integer=True,nonnegative=True)
 ck('The power sum has its integral leading coefficient',s.Poly(s.summation(k**p,(k,0,J)),J).LC(),R(1,p+1))
 ck('The cutoff main-term coefficient',s.simplify(-1+s.Rational(1,p+1)),-R(p,p+1))
 for v in [1,2,3]:
  condition('Consecutive powers dominate a geometric tail', (v+1)**p-v**p>=1,'This exact finite diagnostic illustrates the general binomial inequality for every nonnegative integer.')
 analytic('Power-spaced infinite-product cutoff',['The base exceeds one, the integer power is at least two, and the positive parameter decreases to zero.'],['For each fixed t the logarithms converge absolutely in the tail, hence the product is positive. Set L=ln(1/t) and J=floor((L/ln b)^(1/p)).','For k<=J the argument u=t*b^(k^p) is at most one, and ln(1-exp(-u))=ln u+O(u) uniformly. Since adjacent k^p differ by at least one, the sum of these errors is bounded by a geometric series independent of t.','For k>J, the first argument exceeds one and subsequent arguments grow at least geometrically. The tail sum of logarithms is uniformly bounded.','Thus ln P=-(J+1)L+ln b*sum(k^p)+O(1). The power sum equals J^(p+1)/(p+1)+O(J^p), and J=(L/ln b)^(1/p)+O(1). Dividing by L^(1+1/p) gives the stated constant.'])
 c=1/s.log(b)**R(1,p)
 pool=[(-c/(p+1),'Keep only the summed powers and reverse their sign'),(-R(p,p+2)*c,'Use the next antiderivative denominator'),(-R(p-1,p)*c,'Use the previous spacing power in the leading coefficient'),(-R(p+1,p+2)*c,'Use the next spacing power in the leading coefficient'),(-R(p,2*p+1)*c,'Double the power in the power-sum integral denominator'),(-R(2*p,2*p+1)*c,'Use the squared spacing power throughout the cutoff cancellation'),(-R(p,(p+1)**2)*c,'Apply the power-sum denominator twice'),(-R(3*p,3*p+1)*c,'Use the cubed spacing power in the cutoff cancellation')]
 for wrong,_ in pool:condition('Every authored alternative survives the elementary cutoff interval',-(1-R(1,2**(p+1)))<s.simplify(wrong/c)<0,'Even the half-cutoff improvement of the elementary lower bound cannot isolate the answer; the power-sum cancellation is required.')

 return candidate(r'P(t)=\prod_{k=0}^{\infty}\left(1-\exp(-t\,'+L(b)+r'^{k^{'+str(p)+r'}})\right)\quad(t>0).'+T('Find ')+r'\lim_{t\downarrow0}\frac{\ln P(t)}{(\ln(1/t))^{'+L(1+R(1,p))+r'}}.',A,pool,[r'L=\ln(1/t),\qquad J=\left\lfloor\left(\frac L{\ln '+L(b)+r'}\right)^{1/'+str(p)+r'}\right\rfloor',r'\ln(1-e^{-u})=\ln u+O(u)\qquad(0<u\le1)',T('Below the cutoff the argument errors sum to a bounded geometric series. Above it the arguments increase at least geometrically, so the logarithmic tail is also uniformly bounded.'),r'\ln P(t)=-(J+1)L+\ln '+L(b)+r'\sum_{k=0}^Jk^{'+str(p)+r'}+O(1)',r'\sum_{k=0}^Jk^{'+str(p)+r'}=\frac{J^{'+str(p+1)+r'}}{'+str(p+1)+r'}+O(J^{'+str(p)+r'}),\qquad J=\left(\frac L{\ln '+L(b)+r'}\right)^{1/'+str(p)+r'}+O(1)',r'\ln P(t)='+L(A)+r'L^{'+L(1+R(1,p))+r'}+O(L)'],'power-spaced-product-moving-cutoff')
f=FAMILIES['q1-limits-olympiad-dyadic-log-product']
f.update(build=product_power,finiteDomain=[{'caseId':f'power-{p}-base-{b}','power':p,'b':b,'normalizedTaskKey':f'power-spaced-log-product:p{p}','purpose':'Change the dimensionless exponent of the moving cutoff; every retained exponent is distinct; a base-only change receives no additional capacity.'} for p,b in [(2,2),(3,2),(4,3),(5,3),(6,5),(7,5),(8,7),(9,7)]],centralDecision='The nonlinear spacing changes both the moving cutoff scale and the power-sum cancellation. A uniform tail estimate is essential before normalization; choices all retain the same logarithmic factor.',instanceCount=8)

def gauss_linear(case):
 a=int(case['a']);b=int(case['b'])
 def contribution(r,ignorediv=False,ignoreparity=False,ignoreg=False):
  g=gcd(a,r) if r else a
  if not ignorediv and b%g:return s.Integer(0)
  # At N=1 the parity class of the reduced modulus is already the eventual class.
  m=(4*a+r)//g;ap=a//g;bp=b//g
  mult=1 if m%2 else (2 if ignoreparity else 1+(-1)**(ap*(m//2)+bp))
  return s.Integer(mult*(1 if ignoreg else g))
 terms=[contribution(r) for r in range(4)];A=sum(terms)
 for N in [1,2,3]:
  for r in range(4):
   mod=4*a*N+r;g=gcd(a,mod)
   if b%g:expected=0
   else:
    mm=mod//g;aa=a//g;bb=b//g
    expected=g if mm%2 else g*(1+(-1)**(aa*(mm//2)+bb))
   ck('Independent gcd-reduced character formula at modulus '+str(mod),expected,terms[r])
   # Direct character orthogonality after h=j-k gives an exact polynomial
   # in a primitive mod-th root, independently reduced modulo Phi_mod.
   poly=0
   for h in range(mod):
    if (2*a*h)%mod==0:poly+=z**((a*h*h+b*h)%mod)
   rem=s.rem(s.Poly(poly-terms[r],z),s.Poly(s.cyclotomic_poly(mod,z),z)).as_expr()
   ck('Cyclotomic reduction of squared-modulus character sum at modulus '+str(mod),rem,0)
 analytic('Quadratic sums with a linear character',['All four moduli are positive integers, the leading and linear coefficients are the stated integers, and n tends through positive integers.'],['If g=gcd(a,m) does not divide b, shifting by m/g gives a nontrivial geometric character and the sum vanishes. Otherwise split into g identical periods, obtaining g times the reduced sum with modulus m/g and coefficients a/g,b/g.','For coprime leading coefficient, square the modulus and set the index difference to h. Character orthogonality leaves only h=0 for odd modulus, and additionally h=m/2 for even modulus. The extra phase is(-1)^(a*m/2+b).','After dividing by the original modulus, the value is g for odd reduced modulus, and g(1+(-1)^(a_reduced*m_reduced/2+b_reduced)) for even reduced modulus. In each displayed congruence class the gcd and phase parity are independent of n.'])
 pool=[(sum(contribution(r,ignorediv=True) for r in range(4)),'Ignore the divisibility obstruction of the linear coefficient'),(sum(contribution(r,ignoreparity=True) for r in range(4)),'Reinforce every surviving even-modulus character'),(sum(contribution(r,ignoreg=True) for r in range(4)),'Forget the gcd multiplicity after reducing the period'),(sum(terms[1:]),'Omit the modulus divisible by the full fourfold leading coefficient'),(sum(gcd(a,r) if r else a for r in range(4)),'Use the odd-modulus value in every class'),(2*A,'Count both index differences twice'),(A/2,'Halve the squared-modulus normalization'),(sum((gcd(a,r) if r else a)**2 for r in range(4)),'Square the period count without dividing by the original modulus'),(sum(gcd(a,r) if r else a for r in range(4))**2,'Square the total period count after summing congruence classes instead of summing their normalized squares'),(terms[0],'Retain only the congruence class divisible by the full fourfold leading coefficient'),(terms[1],'Retain only the primitive odd congruence class')]
 # No arbitrary offset padding: every alternative comes from an explicit missed arithmetic condition.
 out=candidate(r'G(m)=\sum_{k=0}^{m-1}\exp\!\left(\frac{2\pi i('+L(s.expand(a*x*x+b*x)).replace('x','k')+r')}{m}\right),\qquad i^2=-1.'+T('Find ')+r'\lim_{n\to\infty}\sum_{r=0}^{3}\frac{|G('+str(4*a)+r'n+r)|^2}{'+str(4*a)+r'n+r}.',A,pool,[r'g=\gcd('+str(a)+r',m)',T('A shift by one reduced period makes the sum vanish unless the gcd divides the linear coefficient. When it does divide, reduce the modulus and split into identical periods.'),r'g\nmid'+str(b)+r'\Longrightarrow G(m)=0,\qquad g\mid'+str(b)+r'\Longrightarrow G(m)=g\sum_{k=0}^{m/g-1}e^{2\pi i(('+str(a)+r'/g)k^2+('+str(b)+r'/g)k)/(m/g)}',T('For a reduced sum with coprime leading coefficient, square the modulus and use character orthogonality. Only zero shift survives for odd modulus; half the modulus is an additional shift in the even case.'),r'\left|\sum_{k=0}^{M-1}e^{2\pi i(Ak^2+Bk)/M}\right|^2=\begin{cases}M&M\textnormal{ odd}\\M(1+(-1)^{AM/2+B})&M\textnormal{ even}\end{cases}\quad(\gcd(A,M)=1)',r'\left(\frac{|G('+str(4*a)+r'n+r)|^2}{'+str(4*a)+r'n+r}\right)_{r=0}^{3}='+L(s.Matrix(1,4,terms)),T('These four values are independent of the positive integer n; sum them.'),L(A)],'quadratic-Gauss-linear-character-four-congruence-classes','nonnegative-integer')
 # The competing square is itself a concrete arithmetic error. Varying its
 # mechanism avoids teaching that the square/minimum/maximum form is correct.
 if (a,b)==(3,2):required=sum(gcd(a,r) if r else a for r in range(4))**2
 elif (a,b) in [(4,2),(4,4),(5,5)]:required=terms[1]
 elif (a,b)==(6,3):required=sum(gcd(a,r) if r else a for r in range(4))**2
 else:required=None
 if required is not None:
  condition('A genuine competing square survives in every square-answer menu',required!=A and int(s.sqrt(required))**2==required,'The alternative comes from a dropped congruence class or an incorrect period-count square, never an arbitrary offset.')
  out['mandatoryWrongExpressions']=[s.srepr(required)]
 return out
g=FAMILIES['q1-limits-olympiad-quadratic-gauss-magnitude']
g.update(build=gauss_linear,finiteDomain=[{'caseId':f'quadratic-{a}-linear-{b}','a':a,'b':b,'normalizedTaskKey':f'four-congruence-Gauss:{a}:{b}','purpose':'Different gcd divisibility and parity obstructions, with a nonzero linear character.'} for a,b in [(3,2),(3,3),(4,2),(4,4),(6,3),(6,6),(5,5),(5,10)]],instanceCount=8,centralDecision='The linear character creates a gcd divisibility obstruction in addition to even-modulus interference. Squaring and exact character orthogonality are needed in four coupled congruence classes; all alternatives are plain counts from plausible omitted conditions.')
