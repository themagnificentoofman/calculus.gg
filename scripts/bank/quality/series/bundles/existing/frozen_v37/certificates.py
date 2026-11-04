"""Derivation checks and explicit theorem conditions for analytic candidates.
These checks certify symbolic steps; they do not claim CAS proved the referenced
analytic theorems. All theorem applications are AI-assisted editorial reviews.
"""
import sympy as s
x,u,z=s.symbols('x u z',real=True)
n=s.symbols('n',integer=True,positive=True)
R=s.Rational

def install(core):
 E=core['equal'];L=core['latex'];T=core['text'];families=core['FAMILIES']
 def check(lhs,rhs,why):
  assert E(lhs,rhs),why
  return {'reason':why,'left':L(lhs),'right':L(rhs),'result':'exact-equality'}
 def wrap(f,old):
  def b(m):
   p=old(m);shape=p['structuralSignature'];cs=[];hyp=[];theorems=[]
   if shape in ['inverse-slope-data','inverse-second-derivative-data']:p['statement']=T('Assume f is twice continuously differentiable and has a local inverse near the indicated point. ')+p['statement']
   if shape=='variable-upper-bound-FTC':p['statement']=r'F(x)=\int_0^{x^2}(t^{'+L(m)+r'}+1)\,dt.\quad F\prime(1)=?'
   if shape=='two-moving-integral-endpoints':p['statement']=r'F(x)=\int_x^{'+L(m)+r'x}e^t\,dt.\quad F\prime(0)=?'
   if shape=='endpoint-data-FTC':p['statement']=T('Let F be continuously differentiable on [1,3]. ')+p['statement']
   if shape in ['harmonic-weight-geometric','Euler-sum-shifted-denominator','harmonic-square-dilogarithm','mixed-logarithmic-simplex-moment']:
    p['statement']+=r'\quad H_n=\sum_{j=1}^n\frac1j,\quad H_n^{(2)}=\sum_{j=1}^n\frac1{j^2}.'
   if shape=='Gauss-half-parameter-hypergeometric':p['statement']+=r'\quad (a)^{\overline{k}}=a(a+1)\cdots(a+k-1),\ (a)^{\overline0}=1.'
   if shape=='complete-elliptic-integral-series':p['statement']+=r'\quad K(p)=\int_0^{\pi/2}(1-p\sin^2t)^{-1/2}\,dt.'+T('Here p is the parameter, not the modulus.')
   if shape=='harmonic-square-dilogarithm':p['statement']+=r'\quad \operatorname{Li}_2(r)=\sum_{j=1}^\infty r^j/j^2\quad(|r|<1).'
   if any('\\Gamma' in L(v) for v,_ in p['options']) or '\\Gamma' in p['statement']:
    p['statement']+=r'\quad\Gamma(a)=\int_0^\infty t^{a-1}e^{-t}\,dt\quad(a>0).'

   def c(lhs,rhs,why):cs.append(check(lhs,rhs,why))
   if shape=='arc-length-perfect-square':
    c(s.integrate(x/(2*m)+m/(2*x),(x,1,2)),p['answer'],'Integrate the independently verified positive speed over the stated interval')
    hyp=['x>0 fixes the positive square root of the perfect-square speed.'];theorems=['arc-length integral of a continuously differentiable graph']
   elif shape=='quarter-circle-area':
    c((m*s.cos(u))**2,m*m*(1-s.sin(u)**2),'Circle norm under x=m sin u')
    c(s.diff(m*s.sin(u),u),m*s.cos(u),'Substitution Jacobian')
    c(s.integrate(m*m*s.cos(u)**2,(u,0,s.pi/2)),p['answer'],'Compute the transformed quarter-disk integral')
    hyp=['0<=u<=pi/2 makes cos u nonnegative, fixing the principal square-root branch.'];theorems=['one-dimensional change of variables']
   elif shape=='piecewise-continuity-parameter':
    c(s.solve(s.Eq(m*x+1,u+x*x).subs(x,1),u)[0],m,'Solve matching branch limits for the unknown constant')
   elif shape=='monotone-square-root-recurrence':
    c(m*m-m+u-u*u,(m-u)*(m+u-1),'Factor the square difference controlling monotonicity')
    c(s.sqrt(m*m-m+m),m,'Verify invariant upper endpoint')
    c(s.factor(u*u-u-(m*m-m)),(u-m)*(u+m-1),'Factor the fixed-point equation')
    hyp=['For 0<=u<=m and m>=4, both factors in (m-u)(m+u-1) are nonnegative.','The square-root map is increasing and maps [0,m] into [0,m]. Starting at zero, iterates increase and are bounded.','Continuity passes the monotone limit into the equation; the other root 1-m is negative.'];theorems=['monotone convergence of bounded real sequences']
   elif shape=='shifted-Stirling-logarithm':
    approx=(x+m-R(1,2))*s.log(x+m)-(x+m)
    c(s.limit((approx-x*s.log(x)+x)/s.log(x),x,s.oo),m-R(1,2),'Stirling main term evaluated at the fixed shift')
    hyp=['Stirling log-Gamma remainder is O(1) here, and O(1)/log n tends to zero.'];theorems=['NIST DLMF 5.11.1 log-Gamma asymptotic, positive real argument']
   elif shape=='logarithmic-singular-Riemann-sum':
    approx=(x+R(1,2))*s.log(x)-x
    c(s.limit(approx/x-s.log(x)-s.log(m),x,s.oo),-1-s.log(m),'Reduce log(n!) to its Stirling main term')
    hyp=['The discarded O(1) log-factorial remainder divided by n tends to zero.'];theorems=['NIST DLMF 5.11.1 plus Gamma(n+1)=n!']
   elif shape=='degenerate-endpoint-Laplace-rescaling':
    v=s.symbols('v',positive=True)
    c(s.diff(v**(1/m),v),v**(1/m-1)/m,'Jacobian of t=u^m')
    c(s.expand_func(s.gamma(1+1/m)),s.gamma(1/m)/m,'Gamma recurrence gives the exact limiting integral')
    hyp=['The rescaling u=n^(1/m)x maps [0,1] to [0,n^(1/m)].','The positive integrand exp(-u^m) increases in domain to an integrable function; use monotone convergence.','Gamma exponent 1/m>0.'];theorems=['monotone convergence and Euler Gamma integral']
   elif shape=='nonstationary-phase-bound':
    N=s.symbols('N',positive=True)
    F=-x**m*s.cos(N*x)/N
    c(s.diff(F,x)+m*x**(m-1)*s.cos(N*x)/N,x**m*s.sin(N*x),'Integration-by-parts integrand decomposition')
    c(1/N+m/N*s.integrate(x**(m-1),(x,0,1)),2/N,'Uniform absolute bound')
    hyp=['For m>=4 the lower boundary term vanishes and |sin|,|cos|<=1.'];theorems=['integration by parts and squeeze theorem']
   elif shape=='log-Laplace-integral-high-derivative':
    c(s.integrate(x**m*s.exp(-x),(x,0,s.oo)),s.factorial(m),'Evaluate the independently encoded dominating Gamma moment')
    hyp=['For a>=0 the m-th logarithmic derivative is bounded by (m-1)! t^m; multiplication by e^-t is integrable.'];theorems=['one-sided differentiation under an integrable dominating function']
   elif shape=='harmonic-weight-geometric':
    r=1/m
    c(s.summation(r**n,(n,u,s.oo)),r**u/(1-r),'Sum the geometric tail of the reversed triangular region')
    c(-s.log(1-r)/(1-r),p['answer'],'Apply the logarithmic Taylor series after the reversal')
    hyp=['Nonnegative terms justify Tonelli; 0<r<1 makes the final log series finite.'];theorems=['Tonelli and -log(1-r)=sum r^j/j']
   elif shape=='central-binomial-series':
    F=(1-z)**(-R(1,2))
    c(2*(1-z)*s.diff(F,z)-F,0,'Generating function differential equation')
    c(s.combsimp(s.binomial(2*n+2,n+1)/(4*s.binomial(2*n,n))),(2*n+1)/(2*n+2),'Coefficient ratio from factorials')
    c(F.subs(z,0),1,'Initial coefficient selects unique analytic solution')
    c(F.subs(z,1/m),p['answer'],'Specialize inside the disk of convergence')
    hyp=['The coefficient ratio gives radius one; the ODE recurrence and initial coefficient identify every coefficient.'];theorems=['uniqueness of analytic power-series coefficient recurrence']
   elif shape=='Catalan-series':
    F=(1-s.sqrt(1-4*z))/(2*z)
    c(s.diff(z*F,z),(1-4*z)**(-R(1,2)),'Integration relation produces the Catalan denominator k+1')
    c(s.limit(F,z,0),1,'Select the branch analytic at zero')
    c(F.subs(z,1/(4*m)),p['answer'],'Specialize at radius-safe argument')
    hyp=['0<1/(4m)<1/4; termwise integration holds in the convergence disk.'];theorems=['binomial power series and termwise integration']
   elif shape=='trigonometric-geometric-weight':
    c(s.re(1/(1-s.exp(s.I*s.pi/3)/m)).expand(complex=True).simplify(),p['answer'],'Independent real-part rationalization of the complex geometric sum')
    hyp=['The complex ratio has modulus 1/m<1; taking real parts commutes with absolutely convergent summation.'];theorems=['complex geometric series']
   elif shape=='arctangent-difference-series':
    c(s.cancel(((u+1)-u)/(1+u*(u+1))),1/(u*u+u+1),'Arctangent subtraction ratio')
    c(s.limit(s.atan(x+1)-s.atan(m),x,s.oo),p['answer'],'Endpoint of telescoped finite sums')
    hyp=['For u>=m>=4, atan(u+1)-atan(u) lies in (0,pi/2), so the principal arctangent addition law has no pi correction.'];theorems=['arctangent subtraction identity with branch control']
   elif shape=='cube-root-exponential-filter':
    w=-R(1,2)+s.sqrt(3)*s.I/2
    for j in [0,1,2]:c(s.simplify(sum(w**(r*j) for r in range(3))),3 if j==0 else 0,'Root-of-unity coefficient filter residue '+str(j))
    c((s.exp(m)+2*s.exp(-m/2)*s.re(s.exp(s.I*s.sqrt(3)*m/2)))/3,p['answer'],'Real representation of the filtered exponential sum')
    hyp=['All exponential Taylor series converge absolutely at the three selected arguments.'];theorems=['entire exponential Taylor series']
   elif shape=='dyadic-trigonometric-telescope':
    c(s.together(s.cos(z)/s.sin(z)-(s.cos(z)**2-s.sin(z)**2)/(s.sin(z)*s.cos(z))-s.sin(z)/s.cos(z)),0,'Cotangent doubling identity')
    c(s.limit(x*s.cot(x/m),x,0),m,'Nonzero boundary term under dyadic scaling')
    c(m-s.cot(1/m),p['answer'],'Difference of telescoping endpoint terms')
    hyp=['All finite-sum arguments lie in (0,1/m]; none meet a sine zero.','The finite sum equals 2^-N cot(1/(m2^N))-cot(1/m).'];theorems=['finite telescoping and standard sine/cosine limits']
   elif shape=='inverse-binomial-arcsine-square':
    F=2*s.asin(z/2)**2
    c((4-z*z)*s.diff(F,z,2)-z*s.diff(F,z),4,'Closed form satisfies the power-series differential equation')
    an=1/(n*n*s.binomial(2*n,n));an1=an.subs(n,n+1)
    c(s.combsimp(4*(2*n+2)*(2*n+1)*an1-4*n*n*an),0,'All coefficients satisfy the same exact recurrence')
    c(F.subs(z,0),0,'Initial value');c(s.diff(F,z).subs(z,0),0,'Initial derivative')
    c(2*s.asin(s.sin(s.pi/m))**2,p['answer'],'Branch-safe evaluation of the closed form')
    hyp=['Coefficient ratio gives radius two.','0<pi/m<=pi/4 lies in the principal arcsine range.'];theorems=['analytic uniqueness for the nonsingular second-order ODE on |z|<2']
   elif shape=='Gauss-half-parameter-hypergeometric':
    c(s.hyperexpand(s.hyper([R(1,2),R(1,2)],[m+1],1))/s.factorial(m),p['answer'],'Independent Gauss hypergeometric evaluation')
    c(s.factorial(m+n),s.factorial(m)*s.rf(m+1,n),'Convert shifted factorial to the hypergeometric coefficient')
    hyp=['Gauss condition Re(c-a-b)=m>0 and c=m+1 is not a nonpositive integer.'];theorems=['NIST DLMF 15.4.20 Gauss summation']
   elif shape=='logarithm-of-Euler-product':
    c(s.limit(x*x*s.log(1+m*m/(s.pi*s.pi*x*x)),x,s.oo),m*m/s.pi**2,'Convergence by finite positive quadratic tail comparison')
    hyp=['Every factor 1+m^2/(pi^2 k^2)>0, so real logarithms convert finite products to sums.','The sum of positive logarithms converges by the displayed comparison; continuity of log passes to the positive product limit.'];theorems=['NIST DLMF 4.36.1: sinh(z)/z=product(1+z^2/(pi^2n^2)), evaluated at real z=m']
   elif shape=='positive-lattice-resolvent':
    A=(s.coth(s.pi*m)-1/(s.pi*m))*s.pi/(2*m)
    c(A,p['answer'],'Solve coth partial fraction identity for the requested one-sided sum')
    c(s.pi*m/(s.pi*s.pi*(m*m+n*n)),m/(s.pi*(m*m+n*n)),'Specialize each denominator at z=pi m')
    hyp=['m>0 avoids every imaginary pole; the sum converges absolutely by k^-2 comparison.'];theorems=['NIST DLMF 4.36.3 coth partial fractions']
   elif shape=='alternating-lattice-resolvent':
    c((1/s.sinh(s.pi*m)-1/(s.pi*m))*s.pi/(2*m),p['answer'],'Solve csch partial fraction identity for the alternating one-sided sum')
    hyp=['m>0 avoids poles; |(-1)^k/(k^2+m^2)|<=k^-2 ensures absolute convergence.'];theorems=['NIST DLMF 4.36.5 csch partial fractions']
   elif shape=='Fourier-sine-fourth-moment':
    c(s.expand_trig((3-4*s.cos(2*z)+s.cos(4*z))/8).simplify(),s.sin(z)**4,'Fourier reduction of the fourth power')
    C=lambda v:s.pi**2/6-s.pi*v/2+v*v/4
    c((3*C(0)-4*C(2*s.pi/m)+C(4*s.pi/m))/8,p['answer'],'Combine the quadratic cosine series at all three arguments')
    hyp=['All three angles lie in [0,2pi], including m=4 boundary theta=pi/4.','The cosine-series identity converges absolutely because coefficients are 1/k^2.'];theorems=['Fourier series sum cos(kt)/k^2=pi^2/6-pi t/2+t^2/4 on [0,2pi]']
   elif shape=='complete-elliptic-integral-series':
    c(s.combsimp(s.rf(R(1,2),n)/s.factorial(n)),s.binomial(2*n,n)/4**n,'Half-integer binomial coefficients')
    c(s.combsimp(s.sqrt(s.pi)*s.gamma(n+R(1,2))/(2*s.gamma(n+1))),s.pi*s.binomial(2*n,n)/(2*4**n),'Wallis sine moment supplies the second coefficient')
    hyp=['Define K(p)=integral_0^(pi/2)(1-p sin^2 t)^(-1/2)dt: p is the parameter, not the modulus.','0<p=1/m<1 gives uniform binomial convergence on the whole integration interval.'];theorems=['NIST DLMF 19.5.1 with modulus sqrt(p), plus the Wallis beta moment']
   elif shape=='harmonic-square-dilogarithm':
    H=s.symbols('H');r=s.symbols('r',positive=True)
    c((H+1/n)**2-H*H,2*H/n+1/(n*n),'Discrete harmonic-square difference')
    c(s.diff(s.log(1-r)**2/2,r),-s.log(1-r)/(1-r),'Integrated harmonic generating function')
    c((s.polylog(2,1/m)+s.log(1-1/m)**2)/(1-1/m),p['answer'],'Reassemble the difference generating function')
    hyp=['|r|<1 ensures absolute convergence of all harmonic-weighted series and legitimizes termwise integration.','Li_2(r)=sum_(j>=1)r^j/j^2.'];theorems=['harmonic generating function, proved by Tonelli, and termwise integration']
   elif shape=='Euler-sum-shifted-denominator':
    # Reduce the original sum by partial fractions after H_k expansion. For j>=1,
    # sum_(k>=j)1/[k(k+m)]=(H_(j+m-1)-H_(j-1))/m.
    c(1/(x*(x+m)),(1/x-1/(x+m))/m,'Partial fractions in the inner tail')
    c(sum(s.harmonic(j)/j for j in range(1,int(m))),(s.harmonic(m-1)**2+s.harmonic(m-1,2))/2,'Finite triangular harmonic identity')
    # Direct integral derivation is independent: H_k integral (1-t^k)/(1-t), then shifted telescope.
    # Registered Euler identity S_m-S_(m-1) recurrence follows by comparing rational kernels.
    Sm=(s.pi**2/6+sum(s.harmonic(j)/j for j in range(1,int(m))))/m
    c(Sm,p['answer'],'Evaluate the Euler sum after the tail decomposition')
    hyp=['Tonelli applies to H_k/[k(k+m)]>=0.','Reversal yields (1/m) sum_(j>=1)(1/j) sum_(r=0)^(m-1)1/(j+r).','The r=0 term is zeta(2); for r>=1 the inner sum is H_r/r by finite shifted telescoping.'];theorems=['Tonelli, Basel sum zeta(2)=pi^2/6, and finite shifted telescoping']
   if cs or theorems:
    p['certificate']={'kind':'analytic-theorem-with-exact-symbolic-steps','exactChecks':cs,'hypotheses':hyp,'theorems':theorems,'review':'AI-assisted mathematical review; no human review claimed','scope':'Symbolic checks verify the encoded derivation steps. Referenced analytic theorems are applied with the stated hypotheses, not independently proved by CAS.'}
    p['verificationRoute']='analytic-certificate-plus-exact-symbolic-derivation'
   return p
  return b
 for f in families:f['build']=wrap(f,f['build'])
