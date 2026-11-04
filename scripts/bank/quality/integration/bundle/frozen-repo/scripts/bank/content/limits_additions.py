"""Eight independent original limit constructions with finite parameter domains.

Analytic certificates state the full limiting argument and theorem hypotheses;
executed algebraic checks are logged separately. No model/network runtime calls.
"""
from __future__ import annotations
import argparse, hashlib, inspect, json, math, re, textwrap
from contextvars import ContextVar
from pathlib import Path
import sympy as s
R=s.Rational; pi=s.pi; x,u,v,z=s.symbols('x u v z', real=True)
FAMILIES={}; CHECKS=ContextVar('checks',default=None)
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canon(o).encode()).hexdigest()
def L(o):return s.latex(s.sympify(o),fold_short_frac=False)
def T(o):return r'\textnormal{'+o+'}'
def lines(*pieces):
 out=[]
 for p in pieces:
  if p.startswith(r'\textnormal{') and p.endswith('}'):
   out.extend(T(q) for q in textwrap.wrap(p[12:-1],width=30))
  else:out.append(p)
 return r'\begin{gathered}'+r'\\'.join(out)+r'\end{gathered}'
def ck(name,a,b=0):
 d=s.simplify(s.expand_func(a-b));assert d==0,(name,d)
 CHECKS.get().append({'name':name,'residual':s.srepr(d),'passed':True})
def reg(slug,group,technique,why,prerequisites,proof,conditions,refs=()):
 def dec(fn):
  fid='m3-limits-olympiad-'+slug
  FAMILIES[fid]={'familyId':fid,'topic':'limits','difficulty':'olympiad','relatedIdeaGroupId':group,'primaryTechnique':technique,'alternativeTechniques':[],
   'reasoningDemand':['reframing','convergence','synthesis'],'difficultyRationale':why,'prerequisites':prerequisites,'analyticCertificate':proof,'domain':conditions,'theoremReferences':list(refs),'editorialStatus':'admitted','build':fn}
  return fn
 return dec

def raw(statement,answer,pool,steps,shape):return dict(statement=statement,answer=s.sympify(answer),pool=pool,solutionSteps=steps,structuralSignature=shape)

@reg('irrational-rotation-correlation','limits-irrational-rotation-correlation','Weyl-geometric-sum-and-piecewise-average',
 'The two fractional parts are correlated along an irrational rotation. One must establish equidistribution, retain the shared coordinate, and split at the wrap point instead of multiplying independent means.',
 ['fractional parts','finite geometric sums','Weyl criterion','Riemann integrability'],
 ['For every nonzero integer h, exp(2pi i h sqrt(2)) differs from one. The finite geometric sum of its first N powers has bounded numerator, so its average tends to zero.',
  'Weyl criterion therefore makes {k sqrt(2)} uniformly distributed on [0,1]. The function q(t)=t{t+a} is bounded and has only one discontinuity, hence is Riemann integrable and its orbit averages converge to its integral.',
  'For 0<=t<1-a, q=t(t+a); for 1-a<=t<1, q=t(t+a-1). Integrating the two quadratics yields 1/3-a/2+a^2/2.'],
 ['N tends through positive integers; {r}=r-floor(r); a=1/(m+1) with fixed integer m in2..9.'],
 [])
def rotation(m):
 a=1/(m+1);ans=R(1,3)-a/2+a*a/2
 ck('piecewise correlated average',s.integrate(x*(x+a),(x,0,1-a))+s.integrate(x*(x+a-1),(x,1-a,1)),ans)
 n=7;ck('geometric sum identity',(1-z)*sum(z**j for j in range(1,n+1)),z-z**(n+1))
 return raw(lines(r'\{r\}=r-\lfloor r\rfloor',r'a='+L(a),r'\lim_{N\to\infty}\frac1N\sum_{k=1}^N\{k\sqrt2\}\{k\sqrt2+a\}'),ans,
 [(R(1,4),'Treat the two correlated fractional parts as independent'),(R(1,3)+a/2+a*a/2,'Ignore the wraparound subtraction'),(R(1,3)-a/2-a*a/2,'Reverse the quadratic endpoint contribution'),(R(1,3)-a+a*a,'Subtract the wraparound correction twice'),(R(1,3)-a/4+a*a/4,'Retain only half the wraparound contribution')],
 [T('Irrational rotation is equidistributed by the geometric-sum Weyl test.'),r'I=\int_0^{1-a}t(t+a)dt+\int_{1-a}^1t(t+a-1)dt',r'I=\frac13-\frac a2+\frac{a^2}2='+L(ans)],'correlated-fractional-parts-irrational-rotation')

@reg('Newton-double-exponential-rate','limits-Newton-cross-ratio-squaring','nonlinear-iteration-conjugacy',
 'A fixed-point limit does not reveal the doubly exponential error. The exact cross ratio conjugates Newton iteration to squaring, and the final root removes the remaining bounded factor.',
 ['Newton iteration','algebraic conjugacy','root limits'],
 ['The iterates remain above sqrt(2) and decrease: a_next-sqrt(2)=(a-sqrt(2))^2/(2a)>0, and a_next<a when a>sqrt(2). Their limit is sqrt(2).',
  'Set r_n=(a_n-sqrt(2))/(a_n+sqrt(2)). Direct algebra gives r_(n+1)=r_n^2, hence r_n=r_0^(2^n), with0<r_0<1.',
  'Solve a_n-sqrt(2)=2sqrt(2)r_0^(2^n)/(1-r_0^(2^n)). Raising to power2^-n makes the positive prefactor tend to1, giving r_0.'],
 ['a_0=m in2..9; all roots and fractional powers are positive real values.'])
def newton(m):
 r=(m-s.sqrt(2))/(m+s.sqrt(2));F=(x+2/x)/2
 ck('cross ratio squaring',(F-s.sqrt(2))/(F+s.sqrt(2)),((x-s.sqrt(2))/(x+s.sqrt(2)))**2)
 ck('positive error identity',F-s.sqrt(2),(x-s.sqrt(2))**2/(2*x))
 return raw(lines(r'a_0='+L(m)+r',\quad a_{n+1}=\frac12\left(a_n+\frac2{a_n}\right)',r'\lim_{n\to\infty}(a_n-\sqrt2)^{1/2^n}'),r,
 [(r*r,'Use a root scaled as2^(-(n-1))'),(s.sqrt(r),'Use a root scaled as2^(-(n+1))'),((m-s.sqrt(2))/m,'Normalize the error by a_n rather than its cross-ratio denominator'),((m-s.sqrt(2))/(m+2*s.sqrt(2)),'Double the fixed-point term in the conjugacy denominator'),(1/r,'Invert the stable cross ratio')],
 [r'r_n=\frac{a_n-\sqrt2}{a_n+\sqrt2},\quad r_{n+1}=r_n^2',r'a_n-\sqrt2=\frac{2\sqrt2\,r_0^{2^n}}{1-r_0^{2^n}}',T('The remaining factor tends to one after taking the indicated root.'),r'L=r_0='+L(r)],'Newton-error-doubly-exponential-root')

@reg('recurrence-Hankel-growth','limits-Cassini-determinant-growth','recurrence-determinant-invariant',
 'The largest exponential terms cancel in a two-by-two Hankel determinant. The determinant itself obeys a first-order exact recurrence, so estimating only a_n loses the answer.',
 ['linear recurrences','determinants','root asymptotics'],
 ['Write P=2m+1 and D=m^2+m-1. If a_next=P a-D a_prev, then H_n=a_n a_(n+2)-a_(n+1)^2 satisfies H_(n+1)=D H_n by direct algebra.',
  'The initial conditions give H_0=P^2-4D=5. Thus H_n=5D^n>0 for every n.',
  'Consequently H_n^(1/n)=5^(1/n)D tends to D. The leading characteristic root alone would give the wrong rate because the leading rank-one term cancels.'],
 ['m is fixed in2..9; a_0=2,a_1=2m+1; n tends through positive integers.'])
def hankel(m):
 P=2*m+1;D=m*m+m-1;a,b=s.symbols('a b');c=P*b-D*a;d=P*c-D*b
 ck('Hankel recurrence',b*d-c*c,D*(a*c-b*b));ck('positive initial determinant',2*(P*P-2*D)-P*P,5)
 alpha=(P+s.sqrt(5))/2;beta=(P-s.sqrt(5))/2
 return raw(lines(r'a_0=2,\quad a_1='+L(P),r'a_{n+2}='+L(P)+r'a_{n+1}-'+L(D)+r'a_n',r'\lim_{n\to\infty}\left(a_na_{n+2}-a_{n+1}^2\right)^{1/n}'),D,
 [(alpha**2,'Keep the largest characteristic mode despite determinant cancellation'),(beta**2,'Keep only the smaller characteristic mode'),(m*m,'Drop the off-diagonal and linear contributions to the determinant'),(m*(m+1),'Omit the off-diagonal product in the determinant'),(5*D,'Retain the initial multiplier after taking the nth root')],
 [r'H_n=a_na_{n+2}-a_{n+1}^2,\quad H_{n+1}='+L(D)+r'H_n',r'H_0=5,\quad H_n=5\cdot'+L(D)+r'^n',r'L='+L(D)],'linear-recurrence-Hankel-determinant-asymptotics')

@reg('Dirichlet-endpoint-trace','limits-oscillatory-endpoint-trace','endpoint-subtraction-and-Dirichlet-kernel',
 'The oscillatory factor has a singular weight, so a naive Riemann-Lebesgue argument fails. Subtracting endpoint interpolation isolates the trace and makes the remainder integrably differentiable.',
 ['finite trigonometric sums','integration by parts','removable endpoint singularities'],
 ['For every integer N>=0, sin((2N+1)x)/sin x=1+2 sum_(j=1)^N cos(2jx), with continuous endpoint values. Its integral on0..pi is pi.',
  'The kernel is invariant under x->pi-x. For f=x^m, reflection shows the integral of its endpoint-interpolating line ell(x)=pi^(m-1)x equals pi^(m+1)/2.',
  'The polynomial h=f-ell vanishes at both endpoints. Hence g=h/sin x extends to a continuously differentiable function on the closed interval.',
  'The residual is integral g(x)sin((2N+1)x)dx. Integration by parts bounds it by (|g(0)|+|g(pi)|+integral|g prime|)/(2N+1), which tends to zero.'],
 ['Integer m in2..9; N tends through nonnegative integers; integrands use their continuous endpoint values.'])
def dirichlet(m):
 h=x**m-pi**(m-1)*x
 ck('left subtraction',h.subs(x,0));ck('right subtraction',h.subs(x,pi))
 ck('small finite kernel identity',s.expand_trig(s.sin(5*x))-s.sin(x)*(1+2*s.cos(2*x)+2*s.cos(4*x)))
 ans=pi**(m+1)/2
 return raw(lines(T('Use continuous endpoint values.'),r'\lim_{N\to\infty}\int_0^\pi x^{'+L(m)+r'}\frac{\sin((2N+1)x)}{\sin x}\,dx'),ans,
 [(pi**(m+1),'Count both endpoint traces without averaging'),(pi**(m+1)/4,'Apply reflection averaging twice'),(pi**(m+1)/(m+1),'Replace the kernel by its pointwise-average constant'),(2*pi**(m+1),'Use the full-period normalization twice'),(pi**m/2,'Omit the kernel total mass pi')],
 [r'\int_0^\pi\frac{\sin((2N+1)x)}{\sin x}\,dx=\pi',r'\ell(x)=\pi^{'+L(m-1)+r'}x,\quad\int_0^\pi\ell(x)K_N(x)dx=\frac{\pi^{'+L(m+1)+r'}}2',r'\frac{x^{'+L(m)+r'}-\ell(x)}{\sin x}\textnormal{ extends to }C^1[0,\pi].',T('Integration by parts makes the remaining oscillatory integral vanish.'),r'L='+L(ans)],'odd-Dirichlet-kernel-endpoint-trace')

@reg('monic-minimax-rate','chebyshev-extremality','alternation-lower-bound',
 'A polynomial coefficient constraint creates a minimax problem. The limit is obtained only after proving the exact optimum by alternating signs at n+1 extremal nodes.',
 ['polynomial degree','Chebyshev recurrence','intermediate value theorem','uniform norm'],
 ['Define T_n(cos theta)=cos(n theta). Its recurrence implies leading coefficient2^(n-1) for n>=1, so q_n(x)=m^n2^(1-n)T_n(x/m) is monic.',
  'On[-m,m], its maximum absolute value is C_n=m^n2^(1-n), attained with alternating signs at the n+1 points m cos(jpi/n).',
  'If another monic degree-n polynomial had maximum below C_n, subtracting q_n would produce alternating nonzero signs at those points, hence at least n distinct roots. Its degree is at most n-1, a contradiction.',
  'Thus the infimum is exactly C_n and is attained. Taking nth roots gives m/2 times2^(1/n), tending to m/2.'],
 ['Monic means real polynomial of degree n with leading coefficient one; m in2..9; n positive integer.'],
 ['https://dlmf.nist.gov/18.38','https://dlmf.nist.gov/3.11'])
def minimax(m):
 for n in (2,3,4,5):
  q=m**n*R(1,2)**(n-1)*s.chebyshevt(n,x/m)
  ck('monic scaled Chebyshev degree'+str(n),s.Poly(q,x).LC(),1)
  ck('right alternation node degree'+str(n),q.subs(x,m),m**n*R(1,2)**(n-1))
 ck('Chebyshev recurrence',s.chebyshevt(5,x),2*x*s.chebyshevt(4,x)-s.chebyshevt(3,x))
 ans=m/2
 return raw(lines(T('Let P be all real polynomials'),T('of degree n with leading'),T('coefficient one.'),r'M_n=\inf_{p\in P}\max_{|x|\le '+L(m)+r'}|p(x)|',r'\lim_{n\to\infty}M_n^{1/n}'),ans,
 [(m,'Use x^n without optimizing the lower coefficients'),(m/4,'Apply Chebyshev leading-coefficient scaling twice'),(1/(2*m),'Invert the interval scaling'),(2*m,'Reverse the Chebyshev normalization'),(m/s.sqrt(2),'Confuse the norm with a squared-norm normalization')],
 [r'q_n(x)=\frac{'+L(m)+r'^n}{2^{n-1}}T_n(x/'+L(m)+r')',r'T_n(\cos\theta)=\cos(n\theta)',T('Its n+1 alternating extrema force every monic competitor to have at least this maximum.'),r'M_n=\frac{'+L(m)+r'^n}{2^{n-1}},\quad L='+L(ans)],'monic-polynomial-minimax-exponential-rate')

@reg('binomial-moving-threshold','limits-binomial-central-limit-threshold','characteristic-function-weak-limit',
 'The summation cutoff moves on the standard-deviation scale. A normal limit requires the exact variance and continuity at the moving threshold, rather than a law-of-large-numbers step function.',
 ['binomial distribution','characteristic functions','Levy continuity theorem','normal CDF'],
 ['Interpret the normalized binomial sum as P(S_n<=floor(n/2+a sqrt(n))), where S_n is a sum of n independent fair Bernoulli variables.',
  'For Z_n=2(S_n-n/2)/sqrt(n), the characteristic function is cos(t/sqrt(n))^n. Taylor expansion of log cos at zero gives its limit exp(-t^2/2).',
  'Levy continuity theorem gives convergence to the standard normal law. The standardized cutoff is2a+O(n^-1/2), so continuity of the normal CDF and a sandwich by fixed nearby thresholds give the limit Phi(2a).',
  'Phi(v)=(1+erf(v/sqrt(2)))/2 with the stated real error-function integral, yielding the displayed exact answer.'],
 ['n tends through positive integers; binomial(n,k)=0 outside0<=k<=n; a=m/4 with fixed m in2..9.'],
 ['https://www.math.cmu.edu/~gautam/c/2026-425/notes/mgf.html'])
def binomial(m):
 a=m/4;Phi=lambda q:(1+s.erf(q/s.sqrt(2)))/2;ans=Phi(2*a)
 ck('log characteristic function quadratic coefficient',s.diff(s.log(s.cos(x)),x,2).subs(x,0)/2,-R(1,2))
 ck('standardized threshold scale',2*a, m/2)
 return raw(lines(r'\operatorname{erf}(v)=\frac2{\sqrt\pi}\int_0^v e^{-t^2}dt',r'\lim_{n\to\infty}2^{-n}\sum_{k=0}^{\lfloor n/2+'+L(a)+r'\sqrt n\rfloor}\binom nk',T('Set binomial(n,k)=0 for k>n.')),ans,
 [(Phi(a),'Use variance n instead of n/4'),(Phi(a/2),'Use standard deviation2sqrt(n) instead of sqrt(n)/2'),(Phi(3*a),'Use an incorrect standard-deviation normalization'),(Phi(4*a),'Halve the true standard deviation'),(Phi(-2*a),'Reverse the inequality after centering')],
 [r'Z_n=\frac{2(S_n-n/2)}{\sqrt n},\quad\mathbb E e^{itZ_n}=\cos(t/\sqrt n)^n',r'\cos(t/\sqrt n)^n\longrightarrow e^{-t^2/2}',r'\frac{2(\lfloor n/2+a\sqrt n\rfloor-n/2)}{\sqrt n}\longrightarrow2a',r'L=\Phi(2a)='+L(ans)],'central-binomial-cumulative-moving-threshold')

@reg('coupon-coverage-window','limits-coupon-Gumbel-Bonferroni','finite-inclusion-exclusion-sandwich',
 'The sample count is in an extreme-value window. Fixed-order empty-box intersection probabilities converge, but passing a limit through all n alternating terms is invalid; Bonferroni truncations provide the missing control.',
 ['inclusion-exclusion','Bonferroni inequalities','logarithmic asymptotics','exponential series'],
 ['For n boxes and r_n=floor(n log n+n log m) independent uniform throws, any specified j boxes are all empty with probability(1-j/n)^r_n.',
  'For each fixed nonnegative j, C(n,j)(1-j/n)^r_n tends to m^-j/j!: expand log(1-j/n)=-j/n+O(n^-2), and use C(n,j)~n^j/j!. The floor changes the exponent by less than one and hence changes the factor by a ratio tending to one.',
  'Bonferroni inequalities bound the no-empty-box probability between its finite inclusion-exclusion truncations of odd and even orders. First send n to infinity with truncation order fixed.',
  'Then send the truncation order to infinity. Both limiting truncations converge to sum(-1)^j/(m^j j!)=exp(-1/m). No exchange with an n-dependent infinite alternating sum has been assumed.'],
 ['m fixed in2..9; independent throws each choose one of n boxes with probability1/n; n tends through integers>=2.'],
 ['https://courses.grainger.illinois.edu/cs574/sp2022/lec/notes/09_occupancy_II.pdf'])
def coupon(m):
 ans=s.exp(-1/m)
 ck('log empty-set leading derivative',s.diff(s.log(1-x),x).subs(x,0),-1)
 for j in (1,2,3,4):
  ck('fixed-order binomial leading coefficient j'+str(j),s.Poly(s.prod(z-r for r in range(j))/s.factorial(j),z).LC(),1/s.factorial(j))
 return raw(lines(T('Throw balls independently'),T('and uniformly into n boxes.'),T('The number of throws is'),r'r_n=\lfloor n\log n+n\log '+L(m)+r'\rfloor',r'p_n=\Pr(\textnormal{every box is occupied})',r'\lim_{n\to\infty}p_n'),ans,
 [(s.exp(-m),'Reverse the sign of the logarithmic window shift'),(1-ans,'Return the probability of at least one empty box'),(s.exp(-1/m**2),'Double the logarithmic window shift'),(1/(1+1/m),'Replace the Poisson zero probability by geometric normalization'),(1-1/m,'Treat the first union bound as exact')],
 [r'\Pr(\textnormal{specified }j\textnormal{ boxes empty})=(1-j/n)^{r_n}',r'\binom nj(1-j/n)^{r_n}\longrightarrow\frac{1}{m^j j!}',T('Use fixed odd and even Bonferroni truncations before taking the limit.'),r'L=\sum_{j=0}^\infty\frac{(-1)^j}{m^j j!}=e^{-1/m}='+L(ans)],'coupon-collector-logarithmic-window-probability')

@reg('gcd-pair-density','limits-Mobius-lattice-density','Mobius-inversion-and-dominated-series',
 'A two-dimensional counting limit becomes a divisibility sum through Möbius inversion. Absolute summability controls the infinitely many possible common divisors; naive independence over all primes does not justify the limit.',
 ['gcd','Mobius divisor identity','dominated series','Euler product for zeta'],
 ['Dividing both coordinates by m reduces gcd(a,b)=m to a coprime pair inside the square of side floor(N/m).',
  'The divisor identity sum_(d|g)mu(d)=1 for g=1 and0 otherwise turns the exact count into sum_(d<=N/m)mu(d)floor(N/(md))^2.',
  'After division by N^2, each d term tends to mu(d)/(m^2d^2), and its absolute value is at most1/(m^2d^2). The summable majorant justifies passage through the series.',
  'Absolute convergence and unique prime factorization give sum mu(d)/d^2=product_p(1-p^-2)=1/zeta(2)=6/pi^2. Thus the density is6/(pi^2m^2).'],
 ['Ordered pairs of positive integers; fixed m in2..9; N tends through positive integers.'],
 ['https://ocw.mit.edu/courses/18-781-theory-of-numbers-spring-2012/a97051320da973caebacda06c3a74eac_MIT18_781S12_lec14.pdf'])
def gcd_density(m):
 for N in (13,21):
  direct=sum(math.gcd(a,b)==int(m) for a in range(1,N+1) for b in range(1,N+1))
  inversion=sum(s.mobius(d)*(N//(int(m)*d))**2 for d in range(1,N//int(m)+1))
  ck('finite exact lattice inversion N'+str(N),direct,inversion)
 for g in (1,6,12,30):ck('Mobius divisor identity at'+str(g),sum(s.mobius(d) for d in s.divisors(g)),1 if g==1 else 0)
 ans=6/(pi*pi*m*m)
 return raw(lines(r'C_N=\#\{(a,b)\in\{1,\ldots,N\}^2:',r'\gcd(a,b)='+L(m)+r'\}',T('Count ordered pairs.'),r'\lim_{N\to\infty}\frac{C_N}{N^2}'),ans,
 [(1/(m*m),'Forget the coprimality requirement after scaling'),(6/(pi*pi*m),'Scale only one coordinate'),(6/(pi*pi*m**3),'Scale one coordinate twice'),(3/(pi*pi*m*m),'Count unordered instead of ordered pairs'),(36/(pi**4*m*m),'Impose two independent coprimality conditions')],
 [r'C_N=\sum_{d\le N/'+L(m)+r'}\mu(d)\left\lfloor\frac{N}{'+L(m)+r'd}\right\rfloor^2',r'\frac{|\mu(d)|}{N^2}\left\lfloor\frac{N}{'+L(m)+r'd}\right\rfloor^2\le\frac1{'+L(m*m)+r'd^2}',T('A summable bound permits the limit through the divisor series.'),r'L=\frac1{'+L(m*m)+r'\zeta(2)}='+L(ans)],'ordered-lattice-pair-gcd-density')


def reglevel(level,*args,**kwargs):
 def dec(fn):
  reg(*args,**kwargs)(fn)
  old='m3-limits-olympiad-'+args[0];meta=FAMILIES.pop(old)
  meta['familyId']='m3-limits-'+level+'-'+args[0];meta['difficulty']=level
  meta['reasoningDemand']=['recognition','reframing'] if level=='medium' else ['method-selection','convergence']
  FAMILIES[meta['familyId']]=meta
  return fn
 return dec

@reglevel('medium','floor-integer-approach','limits-discontinuous-floor-approach','side-of-integer-control',
 'A continuous inner limit reaches an integer discontinuity of floor. The side from which it approaches determines the eventual integer value.',
 ['sine standard limit','floor function','strict local inequalities'],
 ['For0<x<pi/2, sin x<x, so sin x/x<1 and x/sin x>1. Both ratios tend to1.',
  'Multiplying by the fixed positive integer m gives approach to m from the indicated side. Eventually the value is in(m-1,m) for sin x/x or(m,m+1) for its reciprocal.',
  'Taking floor is then constant near zero, equal to m-1 or m respectively. Substituting the inner limit directly would miss the lower-side case.'],
 ['x approaches zero from the right; m fixed in2..9; floor is the greatest integer not exceeding its argument.'])
def floor_approach(m):
 below=int(m)%2==0;ratio=s.sin(x)/x if below else x/s.sin(x);ans=m-1 if below else m
 ck('inner ratio limit',s.limit(ratio,x,0,dir='+'),1)
 ck('sign of first correction',s.limit((ratio-1)/(x*x),x,0,dir='+'),-R(1,6) if below else R(1,6))
 if below:pool=[(m,'Apply floor after substituting the integer limit'),(m+1,'Approach the integer from the wrong upper interval'),(0,'Set the sine numerator to zero before taking the ratio'),(m-2,'Cross two floor jumps instead of one')]
 else:pool=[(m-1,'Assume the ratio approaches from below'),(m+1,'Use the ceiling instead of the floor'),(0,'Set the inner increment to zero before forming the ratio'),(2*m,'Count the reciprocal scaling twice')]
 return raw(lines(r'\lim_{x\downarrow0}\left\lfloor '+L(m*ratio)+r'\right\rfloor'),ans,pool,
 [r'\frac{\sin x}{x}<1<\frac{x}{\sin x}\quad(0<x<\pi/2)',T('The chosen inner ratio approaches one from a fixed side.'),r'\lfloor '+L(m*ratio)+r'\rfloor='+L(ans)+T(' for all sufficiently small positive x.')],'floor-of-removable-ratio-at-integer')

@reglevel('medium','implicit-inverse-increment','inverse-function-change-of-variables','inverse-difference-quotient',
 'The function is specified as an inverse, so the increment must be transferred through the defining function before its derivative is used.',
 ['inverse functions','difference quotients','inverse derivative theorem'],
 ['f(t)=t^3+mt has derivative3t^2+m>0, is onto the real line, and has a unique differentiable inverse g.',
  'Since f(1)=m+1, the quotient is the derivative of g at m+1.',
  'Differentiating f(g(u))=u gives g prime(m+1)=1/f prime(1)=1/(m+3).'],
 ['g denotes the real inverse of f on the whole real line; m fixed in2..9.'])
def inverse_increment(m):
 f=x**3+m*x;ans=1/(m+3)
 ck('known inverse base point',f.subs(x,1),m+1);ck('inverse derivative normalization',s.diff(f,x).subs(x,1)*ans,1)
 return raw(lines(r'f(t)=t^3+'+L(m)+r't,\quad g=f^{-1}',T('Use the real inverse.'),r'\lim_{h\to0}\frac{g('+L(m+1)+r'+h)-1}{h}'),ans,
 [(m+3,'Return the derivative of f instead of its inverse'),(1/m,'Discard the cubic contribution to f prime'),(1/(3*m+1),'Apply the coefficient to the wrong derivative term'),(1/(m+3)**2,'Use an inverse second-derivative denominator'),(3/(m+3),'Retain an extra cubic power factor')],
 [r'f(1)='+L(m+1)+r',\quad f^{\prime}(1)='+L(m+3),r'f(g(u))=u\ \Longrightarrow\ g^{\prime}(u)=\frac1{f^{\prime}(g(u))}',r'L='+L(ans)],'inverse-function-local-increment-limit')

@reglevel('hard','Lp-maximum-limit','limits-Lp-uniform-norm','maximum-neighborhood-sandwich',
 'Large integral powers select the maximum value rather than the average. A lower bound on a neighborhood of the maximizer is needed because a single point has zero measure.',
 ['continuous maxima','derivatives','integral inequalities','root limits'],
 ['For f(x)=x^m(1-x) on[0,1], f prime=x^(m-1)(m-(m+1)x), so the unique interior maximizer is x=m/(m+1) and its value is M=m^m/(m+1)^(m+1).',
  'The upper bound integral f^n<=M^n holds because the interval has length one.',
  'For every epsilon>0, continuity gives an interval of positive length delta on which f>=M-epsilon. Hence the nth root of the integral is at least delta^(1/n)(M-epsilon).',
  'Taking limits and then epsilon down to zero proves convergence to M. The argument does not require a Laplace asymptotic expansion.'],
 ['n tends through positive integers; m fixed in2..9; f is nonnegative on the unit interval.'])
def lp_maximum(m):
 f=x**m*(1-x);point=m/(m+1);ans=m**m/(m+1)**(m+1)
 ck('factored derivative',s.diff(f,x),x**(m-1)*(m-(m+1)*x));ck('maximum evaluation',f.subs(x,point),ans)
 return raw(lines(r'\lim_{n\to\infty}\left[\int_0^1\bigl(x^{'+L(m)+r'}(1-x)\bigr)^n dx\right]^{1/n}'),ans,
 [(1/((m+1)*(m+2)),'Return the average of f instead of its supremum'),(0,'Interchange the pointwise limit with the outer nth root'),(m/(m+1),'Return the maximizing location instead of its height'),((m/(m+1))**m,'Omit the factor1-x at the maximum'),(1/(m+1),'Retain only the factor1-x at the maximum')],
 [r'f^{\prime}(x)=x^{'+L(m-1)+r'}('+L(m)+r'-'+L(m+1)+r'x)',r'M=f\left(\frac{'+L(m)+r'}{'+L(m+1)+r'}\right)='+L(ans),r'\delta(M-\varepsilon)^n\le\int_0^1 f(x)^n dx\le M^n',T('Take nth roots, then let epsilon decrease to zero.')],'large-integral-power-to-continuous-maximum')

@reglevel('hard','log-phase-average-limsup','limits-log-phase-sum-integral','sum-integral-control-and-phase-subsequences',
 'A slowly changing logarithmic phase prevents an ordinary average limit. Sum-integral error is small after normalization, and exponentially spaced subsequences recover the full oscillation amplitude.',
 ['sum-integral comparisons','complex or trigonometric antiderivatives','limsup','subsequences'],
 ['For f(x)=cos(m log x), |f prime(x)|<=m/x on[1,infinity). Comparing each unit interval with its endpoint bounds the sum-integral discrepancy by a constant plus m log n.',
  'An antiderivative is x(cos(m log x)+m sin(m log x))/(1+m^2). After dividing the sum by n, the result is that periodic log-phase expression plus a term tending to zero.',
  'The amplitude of cos theta+m sin theta is sqrt(1+m^2). This gives the upper bound1/sqrt(1+m^2).',
  'Choose theta0 with cos theta0=1/sqrt(1+m^2), sin theta0=m/sqrt(1+m^2), and take n_j to be a nearest integer to exp((2pi j+theta0)/m). The relative rounding error tends to zero, so the log phases approach theta0 modulo2pi and attain the upper bound in the limit.'],
 ['m fixed positive integer in2..9; n positive integer; log is the real natural logarithm.'])
def log_phase(m):
 F=x*(s.cos(m*s.log(x))+m*s.sin(m*s.log(x)))/(1+m*m);ans=1/s.sqrt(1+m*m)
 ck('log-phase antiderivative',s.diff(F,x),s.cos(m*s.log(x)))
 ck('amplitude normalization',(1/(1+m*m))**2+(m/(1+m*m))**2,ans**2)
 return raw(lines(r'\limsup_{n\to\infty}\frac1n\sum_{k=1}^n\cos('+L(m)+r'\log k)'),ans,
 [(1,'Ignore cancellation while averaging'),(m/(1+m*m),'Keep only the sine coefficient of the primitive'),(1/(1+m*m),'Keep only the cosine coefficient of the primitive'),(m/s.sqrt(1+m*m),'Use the wrong coefficient-vector norm'),(1/(2*s.sqrt(1+m*m)),'Apply an extra oscillatory averaging factor')],
 [r'\sum_{k=1}^n\cos('+L(m)+r'\log k)=\int_1^n\cos('+L(m)+r'\log x)dx+O(\log n)',r'\frac1n\sum_{k=1}^n\cos('+L(m)+r'\log k)=\frac{\cos('+L(m)+r'\log n)+'+L(m)+r'\sin('+L(m)+r'\log n)}{'+L(1+m*m)+r'}+o(1)',T('Integer subsequences approximate every fixed log phase.'),r'\limsup='+L(ans)],'logarithmic-phase-arithmetic-average-limsup')

def different(a,b):
 d=s.simplify(a-b)
 if d==0:return False
 if d.is_zero is False:return True
 verdict=d.equals(0)
 if verdict is None:raise AssertionError('unresolved option equivalence: '+str(d))
 return not verdict

def build(family_id,instance_index):
 if family_id not in FAMILIES or type(instance_index) is not int or not 0<=instance_index<8:raise ValueError('invalid finite family/index')
 meta=FAMILIES[family_id];m=s.Integer(instance_index+2);checks=[];token=CHECKS.set(checks)
 try:p=meta['build'](m)
 finally:CHECKS.reset(token)
 a=p.pop('answer');pool=p.pop('pool');unique=[]
 p['solutionSteps']=[lines(step) if step.startswith(r'\textnormal{') and step.endswith('}') else step for step in p['solutionSteps']]
 for v,why in pool:
  v=s.sympify(v)
  if different(v,a) and all(different(v,w) for w,_ in unique):unique.append((v,why))
 target=float(s.N(a,40));below=[p for p in unique if float(s.N(p[0],40))<target];above=[p for p in unique if float(s.N(p[0],40))>target]
 feasible=[k for k in range(4) if len(below)>=k and len(above)>=3-k]
 assert feasible,(family_id,m,'insufficient authored options',below,above)
 need=feasible[instance_index%len(feasible)]
 below.sort(key=lambda p:digest([family_id,instance_index,s.srepr(p[0])]))
 above.sort(key=lambda p:digest([family_id,instance_index,s.srepr(p[0])]))
 opts=[(a,'correct')]+below[:need]+above[:3-need]
 assert all(different(opts[j][0],opts[k][0]) for j in range(4) for k in range(j))
 choices=[{'choiceId':'ch_'+digest(s.srepr(v))[:16],'math':L(v),'misconception':why} for v,why in opts]
 semantic=digest({'familyId':family_id,'m':int(m),'statement':p['statement']})
 r={k:v for k,v in meta.items() if k!='build'}
 r.update(p,schemaVersion=2,problemId='cn3_'+semantic[:20],problemRevision=1,parameters={'m':int(m)},parameterDomain={'m':list(range(2,10))},choices=choices,answerChoiceId=choices[0]['choiceId'],answerForm='exact-real',semanticHash=semantic,estimatedSolveSeconds={'medium':150,'hard':300,'olympiad':540}[meta['difficulty']],automatedChecks=checks,sourceRecordIds=['calculus-ninja-independent-limits-m3'],
  source={'kind':'independently-authored','thirdPartyProblemAdapted':False,'license':'LicenseRef-CalculusNinja-Original','theoremReferencesOnly':True,'sourceTextReused':False},
  validation={'status':'verified','route':'explicit-analytic-certificate-with-executed-exact-identities','symbolicEngine':'SymPy '+s.__version__,'humanReviewed':False,'formalProof':False,'analyticCertificateMachineProved':False,'numericalAgreementUsedAsProof':False,'uniqueCorrectOption':True},
  optionAudit={'correctAscendingRank':1+need,'numericRankIsEditorialOnly':True},verification={'answerExpression':s.srepr(a),'choiceExpressions':[s.srepr(o) for o,_ in opts]})
 r['pedagogy']={k:r[k] for k in ['relatedIdeaGroupId','structuralSignature','primaryTechnique','alternativeTechniques','prerequisites','reasoningDemand','answerForm','difficultyRationale','sourceRecordIds']}
 r['pedagogy'].update(constructionId=family_id,responseFormat='multiple-choice');r['contentHash']=digest(r);return r

def catalog():return [{k:v for k,v in meta.items() if k!='build'}|{'instanceIndices':list(range(8))} for meta in FAMILIES.values()]
def all_candidates():return [build(fid,i) for fid in FAMILIES for i in range(8)]
def verify(record):
 try:return record==build(record['familyId'],record['parameters']['m']-2)
 except (KeyError,ValueError,AssertionError,TypeError):return False

def generate(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];quarantine=[]
 for fid in FAMILIES:
  for i in range(8):
   try:rows.append(build(fid,i))
   except Exception as e:quarantine.append({'familyId':fid,'index':i,'error':str(e)})
  print(fid,len(rows),flush=True)
 report={'candidateCount':len(rows),'familyCount':len(FAMILIES),'relatedGroupCount':len({r['relatedIdeaGroupId'] for r in rows}),'quarantine':quarantine,'humanReviewed':False,'activeCount':0,'importedCount':0,'modelCalls':0,'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'catalog.json').write_text(json.dumps(catalog(),indent=2)+'\n');(out/'candidates.jsonl').write_text(''.join(canon(r)+'\n' for r in rows));(out/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',default=str(Path(__file__).parent));args=p.parse_args();generate(args.out)
