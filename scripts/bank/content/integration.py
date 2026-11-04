"""Original executable mathematical assets for the Milestone 3 priority cell.

No downloaded problem code or text is used. These are independently constructed
exercises about classical mathematical facts, not claims to new mathematics.
Exact checks plus explicit parameter-family proofs are the admission route.
Numerical checks, when present, are supplementary and never a proof.
"""
from __future__ import annotations
import argparse, hashlib, inspect, json, re, textwrap
from pathlib import Path
from contextvars import ContextVar
import sympy as s

R=s.Rational; pi=s.pi; x,t,u,z=s.symbols('x t u z', positive=True)
VERSION='integration-ideas-v1'
FAMILIES={}
EXACT_CHECK_LOG=ContextVar("integration_exact_check_log",default=None)

def eq(a,b):
    d=s.simplify(s.expand_func(a-b))
    if d != 0:
        raise AssertionError(f'exact disagreement: {d}')
    log=EXACT_CHECK_LOG.get()
    if log is not None:
        caller=inspect.currentframe().f_back
        source=inspect.getframeinfo(caller).code_context
        log.append({'kind':'exact-symbolic-identity','builder':caller.f_code.co_name,'source':source[0].strip() if source else None,'residual':s.srepr(d),'passed':True})

def tex(value):
    if isinstance(value,s.Basic) and value.func==s.harmonic and len(value.args)==1:
        return 'H_{'+s.latex(value.args[0])+'}'
    if isinstance(value,s.Tuple) and len(value)==2 and isinstance(value[0],s.Symbol):
        return r'\left(\textnormal{'+str(value[0])+r'},\ '+s.latex(value[1],fold_short_frac=False)+r'\right)'
    return s.latex(value,fold_short_frac=False)
def text(value): return r'\textnormal{'+value+'}'
def integral(expr,lo=0,hi=s.oo,var=x): return r'\int_{'+tex(lo)+'}^{'+tex(hi)+'} '+tex(expr)+r'\,d'+tex(var)
def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def digest(o): return hashlib.sha256(canonical(o).encode()).hexdigest()

def family(slug,title,group,technique,alternatives,structure,prerequisites,reasoning,proof,conditions,distractors,seconds=360,notes=None):
    def decorate(fn):
        FAMILIES[slug]={'id':'io3-'+slug,'title':title,'relatedIdeaGroupId':group,
          'primaryTechnique':technique,'alternativeTechniqueTags':alternatives,
          'structuralSignature':structure,'prerequisites':prerequisites,
          'reasoningDemand':reasoning,'certificate':{'id':'cert-'+slug+'-v1','route':'parameter-family-analytic-certificate','proof':proof,'conditions':conditions},
          'distractorMisconceptions':distractors,'estimatedSolveSeconds':seconds,'editorialNotes':notes or [],'build':fn}
        return fn
    return decorate

def result(statement,answer,wrong,steps,parameters,checks,answer_form='exact-real'):
    return {'statement':statement,'answer':answer,'wrong':wrong,'steps':steps,'parameters':parameters,'checks':checks,'answerForm':answer_form}

@family('weighted-complement','Reflection under a singular probability measure','reflection-invariant-measure','measure-preserving-involution',['trigonometric-substitution'],
 'beta-half-weight:complementary-power-ratio',['substitution','improper-integrals'],['recognition','reframing'],
 ['The measure dx/sqrt(x(1-x)) is invariant under x -> 1-x.', 'The two complementary fractions sum identically to one.', 'Each fraction lies between zero and one, so the integrable weight justifies addition and substitution.', 'The weight integrates to pi by x=sin(t)^2.'],
 ['Integer n >= 2; real x in (0,1); endpoints interpreted as improper limits.'],
 ['Forgetting the averaging factor','Using the interval length instead of the weighted measure','Treating the power as a multiplier'],notes=['Shares a recognition group with legacy concealed-reflection; do not count both as globally distinct ideas.'])
def weighted_complement(i):
    n=i+2; f=x**n/(x**n+(1-x)**n)
    eq(f+f.subs(x,1-x),1)
    a=pi/2
    return result(integral(f/s.sqrt(x*(1-x)),0,1),a,[pi,pi/4,pi/(n+3)],
      [text('Reflect the integration variable. The weight is unchanged.'),r'f(x)+f(1-x)=1',r'2I=\int_0^1\frac{dx}{\sqrt{x(1-x)}}=\pi',r'I='+tex(a)],{'n':n},['exact complementary-ratio identity','integrable beta-half majorant'])

@family('reciprocal-quartic','A palindromic quartic becomes a quadratic','reciprocal-rational-fold','reciprocal-substitution',['residues'],
 'positive-palindromic-quartic',['improper-integrals','rational-substitution'],['method-selection','reframing'],
 ['Substituting x=1/t shows that I also equals the integral with numerator x^2.', 'Twice I therefore has numerator 1+x^2.', 'Set u=x-1/x. The denominator divided by x^2 is u^2+2a+2 and du=(1+1/x^2)dx.', 'The transformed integral is the Cauchy kernel on the whole real line.'],
 ['a > -1; denominator positive on the nonnegative axis; tails are O(x^-4).'],
 ['Omitting the factor from the reciprocal average','Replacing 2a+2 by 2a-2','Dropping the square root'])
def reciprocal_quartic(i):
    a=s.Integer(i+2);den=x**4+2*a*x*x+1;v=x-1/x
    eq(den/x**2,v**2+2*a+2);eq(s.diff(v,x),1+1/x**2)
    ans=pi/(2*s.sqrt(2*a+2))
    return result(integral(1/den),ans,[pi/s.sqrt(2*a+2),pi/(2*s.sqrt(2*a-2)),pi/(4*a+4)],
      [text('Pair the integral with its reciprocal substitution.'),r'2I=\int_0^\infty\frac{1+x^2}{x^4+'+tex(2*a)+r'x^2+1}\,dx',r'u=x-x^{-1},\quad 2I=\int_{-\infty}^\infty\frac{du}{u^2+'+tex(2*a+2)+'}',r'I='+tex(ans)],{'a':int(a)},['exact quartic reduction','positive monotone substitution'])

@family('inverse-moment','Integrating an inverse without solving it','inverse-function-change-of-variables','inverse-function-integration',['integration-by-parts'],
 'implicit-monotone-polynomial:inverse-moment',['inverse-functions','substitution'],['recognition','reframing'],
 ['The polynomial f has positive derivative on (0,1) and maps [0,1] bijectively to [0,2].', 'Putting t=f(x) converts the inverse moment into x^r f prime(x).', 'The resulting two monomials have exact elementary antiderivatives.'],
 ['Positive integer exponents n,m,r; inverse is the unique real branch from [0,2] to [0,1].'],
 ['Integrating f rather than its inverse','Forgetting the Jacobian','Applying the unweighted inverse-area identity to a higher moment'])
def inverse_moment(i):
    n=i+4;m=2+(i%2);r=2+(i%3);f=x**n+x**m
    ans=R(n,n+r)+R(m,m+r);eq(s.integrate(x**r*s.diff(f,x),(x,0,1)),ans)
    return result(text('Let g be the inverse of f on [0,1], where ')+r'f(x)='+tex(f)+r'.\quad '+text('Evaluate ')+r'\int_0^2 g(t)^{'+str(r)+r'}\,dt',ans,
      [R(1,n+r+1)+R(1,m+r+1),R(1,n+1)+R(1,m+1),2-R(1,n+1)-R(1,m+1)],
      [text('Set t=f(x), so g(t)=x and dt=f prime(x) dx.'),r'I='+integral(x**r*s.diff(f,x),0,1),r'I='+tex(ans)],{'n':n,'m':m,'r':r},['exact polynomial antiderivative','strict monotonicity on interior'])

@family('chebyshev-absolute','An absolute polynomial is a folded sine wave','orthogonal-polynomial-folding','trigonometric-polynomial-identity',['piecewise-integration'],
 'absolute-chebyshev-second-kind',['trigonometric-substitution','absolute-value'],['recognition','reframing'],
 ['The recurrence U_0=1,U_1=2x,U_{k+1}=2xU_k-U_{k-1} implies U_{n-1}(cos t)=sin(nt)/sin t.', 'For 0<t<pi, sin t is positive; x=cos t cancels the denominator.', 'The n half-periods each contribute 2/n to the integral of |sin(nt)|.'],
 ['Integer n >= 3; the polynomial recurrence defines U everywhere; endpoint values use continuity.'],
 ['Ignoring the absolute value','Counting each half-period without the Jacobian','Integrating the wrong Chebyshev weight'])
def chebyshev_absolute(i):
    n=i+3;T=s.chebyshevu(n-1,x)
    eq(s.chebyshevu(n,x),2*x*T-s.chebyshevu(n-2,x))
    ans=s.Integer(2)
    return result(r'U_0(x)=1,\ U_1(x)=2x,\ U_{k+1}(x)=2xU_k(x)-U_{k-1}(x).\quad '+text('Evaluate ')+r'\int_{-1}^1 |U_{'+str(n-1)+r'}(x)|\,dx',ans,
      [s.Integer(0),s.Integer(2*n),pi],
      [r'x=\cos t,\qquad U_{'+str(n-1)+r'}(\cos t)=\frac{\sin('+str(n)+r't)}{\sin t}',r'I=\int_0^\pi|\sin('+str(n)+r't)|\,dt='+str(n)+r'\frac{2}{'+str(n)+r'}=2'],{'n':n},['exact Chebyshev recurrence','n disjoint half-periods'])

@family('floor-laplace','A discontinuous staircase becomes a tail sum','layer-cake-staircase','layer-cake-representation',['geometric-series'],
 'floor-function:positive-laplace-weight',['tonelli','geometric-series'],['recognition','method-selection'],
 ['For x>=0, floor(x) is the sum of indicators of x>=k, k>=1.', 'All terms are nonnegative, so Tonelli applies without assuming absolute cancellation.', 'Each exponential tail contributes exp(-ak)/a; the remaining sum is geometric.'],
 ['a>0; floor values at integers do not change the integral.'],
 ['Replacing the staircase by x','Omitting the tail integration factor','Starting the geometric series at zero'])
def floor_laplace(i):
    q=s.Integer(i+2);a=s.log(q);ans=1/(a*(q-1))
    eq(s.exp(-a)/(a*(1-s.exp(-a))),ans)
    return result(integral(s.floor(x)*s.exp(-a*x)),ans,[1/a**2,1/(q-1),q/(a*(q-1))],
      [r'\lfloor x\rfloor=\sum_{k=1}^{\infty}\mathbf{1}_{[k,\infty)}(x)',text('Tonelli turns the integral into a sum of exponential tails.'),r'I=\frac1{'+tex(a)+r'}\sum_{k=1}^{\infty}'+tex(q)+r'^{-k}='+tex(ans)],{'q':int(q)},['exact geometric-tail identity','nonnegative interchange'])

@family('gamma-unit-average','Gamma recurrence determines a sliding average','gamma-functional-average','functional-equation-integration',['gamma-reflection'],
 'log-gamma:unit-interval-average',['gamma-function','parameter-differentiation'],['synthesis','method-selection'],
 ['Define F(a)=integral_a^(a+1) log Gamma(x) dx. Leibniz and Gamma(a+1)=a Gamma(a) give F prime(a)=log a.', 'Thus F(a)=a log a-a+C.', 'At a=0 the integrable logarithmic endpoint and Gamma reflection imply 2F(0)=log pi-integral_0^1 log sin(pi x) dx=log(2pi).', 'The standard log-sine integral follows by the double-angle identity and reflection, so C=log(2pi)/2.'],
 ['a>0; Gamma positive on this interval; all logarithms are real.'],
 ['Missing the integration constant','Replacing the integral by a unit-step difference','Dropping the -a term'],seconds=540)
def gamma_average(i):
    a=R(i+2,2);A=s.symbols('A',positive=True);F=A*s.log(A)-A+s.log(2*pi)/2
    eq(s.diff(F,A),s.log(A));ans=F.subs(A,a)
    return result(integral(s.log(s.gamma(x)),a,a+1),ans,[a*s.log(a)-a,s.log(a),a*s.log(a)+s.log(2*pi)/2],
      [text('Let F(a) be the integral over [a,a+1]. Gamma recurrence gives ')+r'F^{\prime}(a)=\log a.',r'F(a)=a\log a-a+C.',text('Reflection and the log-sine integral give ')+r'C=\frac12\log(2\pi).',r'I='+tex(ans)],{'a':[int(a.p),int(a.q)]},['exact derivative of sliding-average formula','gamma recurrence and reflection certificate'])

@family('log-fourier-coefficient','Extract one logarithmic harmonic','analytic-log-circle','uniform-fourier-series',['complex-power-series'],
 'log-quadratic-on-circle:nonzero-fourier-mode',['power-series','fourier-orthogonality'],['method-selection','synthesis'],
 ['For |r|<1, the logarithm equals -2 sum_{k>=1} r^k cos(kt)/k.', 'Absolute uniform convergence justifies termwise integration.', 'Orthogonality on [0,pi] kills every term except k=n, whose cosine square integrates to pi/2.'],
 ['0<r<1; positive integer n; the logarithm argument is at least (1-r)^2>0.'],
 ['Missing the factor two in the logarithm expansion','Using the adjacent Fourier coefficient','Using the constant Fourier coefficient'])
def log_fourier(i):
    n=i+2;r=R(2+(i%2),5);ans=-pi*r**n/n
    eq(s.integrate(s.cos(n*t)**2,(t,0,pi)),pi/2)
    expr=s.log(1-2*r*s.cos(x)+r*r)*s.cos(n*x)
    return result(integral(expr,0,pi),ans,[ans/2,-pi*r**(n+2)/(n+2),s.Integer(0)],
      [r'\log(1-2r\cos x+r^2)=-2\sum_{k=1}^{\infty}\frac{r^k\cos(kx)}{k},\quad |r|<1.',text('Uniform convergence permits integration; only the requested harmonic survives.'),r'I=-\frac{\pi r^n}{n}='+tex(ans)],{'n':n,'r':[int(r.p),int(r.q)]},['exact cosine-square integral','uniform absolute Fourier majorant'])

@family('arctan-parameter','An arctangent integral yields to a parameter','arctan-log-transform','differentiation-under-integral',['fubini'],
 'arctan-product:reciprocal-cauchy-weight',['dominated-differentiation','partial-fractions'],['method-selection','reframing'],
 ['For F(a)=integral arctan(ax)/(x(1+x^2)), parameter differentiation gives integral 1/((1+x^2)(1+a^2x^2)).', 'Partial fractions and the arctangent integral give F prime(a)=pi/(2(1+a)), including a=1 by continuity.', 'F(0)=0 by dominated convergence on bounded parameter intervals, determining F(a)=pi log(1+a)/2.'],
 ['a>0; integrand bounded near zero and O(x^-3) at infinity; parameter derivative integrably dominated locally.'],
 ['Confusing the arctangent transform with a log transform','Losing the factor one half','Using a instead of 1+a inside the logarithm'])
def arctan_parameter(i):
    a=R(i+3,2);ans=pi*s.log(1+a)/2
    eq(1/((1+x*x)*(1+a*a*x*x)),1/(1-a*a)/(1+x*x)-a*a/(1-a*a)/(1+a*a*x*x))
    eq(pi/(2*(1-a*a))-a*pi/(2*(1-a*a)),pi/(2*(1+a)))
    return result(integral(s.atan(a*x)/(x*(1+x*x))),ans,[pi*s.atan(a)/2,pi*s.log(1+a),pi*s.log(a)/2],
      [text('Differentiate with respect to the multiplier a.'),r'F^{\prime}(a)=\int_0^\infty\frac{dx}{(1+x^2)(1+a^2x^2)}=\frac{\pi}{2(1+a)}',r'F(0)=0,\quad F(a)=\frac\pi2\log(1+a).',r'I='+tex(ans)],{'a':[int(a.p),int(a.q)]},['exact partial fractions','exact parameter derivative and initial value'])

@family('gaussian-fourier','An oscillatory Gaussian solves an ODE','gaussian-fourier-transform','parameter-ode',['complex-completion-of-square'],
 'gaussian-times-cosine',['integration-by-parts','dominated-differentiation'],['synthesis','method-selection'],
 ['Differentiating in b and integrating by parts gives F prime(b)=-b F(b)/(2a).', 'The Gaussian bounds justify differentiation and kill the boundary term.', 'The initial value F(0)=sqrt(pi)/(2sqrt(a)) comes from squaring the Gaussian integral and using polar coordinates.', 'The unique scalar ODE solution is F(b)=F(0) exp(-b^2/(4a)).'],
 ['a>0; b real; absolute convergence on [0,infinity).'],
 ['Wrong completion-of-square sign','Missing the half-line factor','Dropping the factor four in the exponential'])
def gaussian_fourier(i):
    a=s.Integer(1+i%3);b=s.Integer(i+1);B=s.symbols('B',real=True);F=s.sqrt(pi)/(2*s.sqrt(a))*s.exp(-B*B/(4*a))
    eq(s.diff(F,B)+B*F/(2*a),0);eq(F.subs(B,0),s.sqrt(pi)/(2*s.sqrt(a)));ans=F.subs(B,b)
    return result(integral(s.exp(-a*x*x)*s.cos(b*x)),ans,[s.sqrt(pi)/(2*s.sqrt(a))*s.exp(b*b/(4*a)),2*ans,s.sqrt(pi)/(2*s.sqrt(a))*s.exp(-b*b/a)],
      [r'F(b)=\int_0^\infty e^{-ax^2}\cos(bx)\,dx',r'F^{\prime}(b)=-\frac{b}{2a}F(b),\qquad F(0)=\frac{\sqrt\pi}{2\sqrt a}',r'F(b)=\frac{\sqrt\pi}{2\sqrt a}e^{-b^2/(4a)}',r'I='+tex(ans)],{'a':int(a),'b':int(b)},['exact ODE residual and initial value','Gaussian dominated derivative'])

@family('reciprocal-gaussian','A singular Gaussian closes under inversion','reciprocal-gaussian-transform','parameter-ode-with-involution',['gaussian-substitution'],
 'exponential:quadratic-plus-inverse-quadratic',['improper-integrals','dominated-differentiation'],['reframing','synthesis'],
 ['Let F(b)=integral exp(-a^2 x^2-b^2/x^2) dx.', 'In its b derivative, substitute x=b/(a t). The x^-2 weighted integral becomes (a/b)F(b).', 'Hence F prime(b)=-2aF(b). The b down to zero limit is the ordinary half Gaussian by dominated convergence.', 'Solving yields sqrt(pi) exp(-2ab)/(2a).'],
 ['a,b>0; superexponential decay at zero and infinity; limit b down to zero uses exp(-a^2x^2) majorant.'],
 ['Treating both quadratic terms independently','Missing the inversion factor','Using the full Gaussian instead of half'])
def reciprocal_gaussian(i):
    a=R(1+i%3,2);b=R(i+1,3);B=s.symbols('B',positive=True);F=s.sqrt(pi)*s.exp(-2*a*B)/(2*a)
    eq(s.diff(F,B),-2*a*F);eq((a*a*x*x+b*b/x**2).subs(x,b/(a*t)),a*a*t*t+b*b/t**2)
    ans=F.subs(B,b)
    return result(integral(s.exp(-a*a*x*x-b*b/x**2)),ans,[s.sqrt(pi)*s.exp(-a*b)/(2*a),2*ans,s.sqrt(pi)*s.exp(-2*a*b)/(2*b) if a!=b else ans/2],
      [text('Differentiate in b, then use x=b/(a t) in the derivative integral.'),r'F^{\prime}(b)=-2aF(b),\quad F(0)=\frac{\sqrt\pi}{2a}',r'I=\frac{\sqrt\pi}{2a}e^{-2ab}='+tex(ans)],{'a':[int(a.p),int(a.q)],'b':[int(b.p),int(b.q)]},['exact inversion of exponent','exact parameter ODE'])

@family('sinc-overlap','Two oscillations measure frequency overlap','fourier-interval-overlap','product-to-sum-with-dirichlet',['parseval'],
 'product-sines:inverse-square-weight',['integration-by-parts','dirichlet-integral'],['method-selection','synthesis'],
 ['Twice the sine product is cos((a-b)x)-cos((a+b)x).', 'Integration by parts of each convergent cosine difference reduces to Dirichlet integrals.', 'Integral_0^infinity (1-cos(cx))/x^2 dx=pi |c|/2; subtracting gives pi(a+b-|a-b|)/4.', 'The final value is pi min(a,b)/2.'],
 ['a,b>0; removable finite value at zero; absolute O(x^-2) tail; Dirichlet integral used only with its valid improper interpretation.'],
 ['Using the larger frequency','Adding widths without subtracting nonoverlap','Using frequency difference instead of overlap'])
def sinc_overlap(i):
    a=s.Integer(i+2);b=s.Integer(2+(3*i)%7)
    if a==b:b+=1
    ans=pi*min(a,b)/2;eq(pi*(a+b-abs(a-b))/4,ans)
    return result(integral(s.sin(a*x)*s.sin(b*x)/x**2),ans,[pi*max(a,b)/2,pi*(a+b)/2,pi*abs(a-b)/2 if abs(a-b)!=min(a,b) else pi*min(a,b)/4],
      [r'2\sin(ax)\sin(bx)=\cos((a-b)x)-\cos((a+b)x)',r'\int_0^\infty\frac{1-\cos(cx)}{x^2}\,dx=\frac{\pi|c|}{2}',r'I=\frac\pi4(a+b-|a-b|)='+tex(ans)],{'a':int(a),'b':int(b)},['exact overlap identity','integrable endpoint and tail bounds'])

@family('mixed-beta-log','A mixed logarithmic moment is a beta covariance','beta-parameter-moments','mixed-parameter-differentiation',['finite-polynomial-expansion'],
 'beta-polynomial:two-endpoint-logarithms',['beta-function','parameter-differentiation'],['synthesis','method-selection'],
 ['Differentiate the beta integral once in each positive shape parameter; logarithmic factors remain integrable on compact positive parameter rectangles.', 'Differentiating the gamma quotient yields B(A,B)((psi(A)-psi(A+B))(psi(B)-psi(A+B))-psi1(A+B)).', 'At integer parameters use psi(k)=H_(k-1)-gamma and psi1(k)=zeta(2)-H_(k-1)^(2).'],
 ['Nonnegative integer m,n, in this asset m,n>=1; endpoint logarithms interpreted by integrable limits.'],
 ['Omitting the mixed trigamma term','Using the wrong sign for the mixed derivative','Replacing a product of logs by separate means'],seconds=540,
 notes=['Related to legacy transformed-beta-log, but two endpoint logs require a genuinely mixed derivative; count related-idea diversity conservatively.'])
def beta_mixed(i):
    m=1+i%4;n=2+i//4;N=m+n+1;B=s.factorial(m)*s.factorial(n)/s.factorial(N)
    P=(s.harmonic(m)-s.harmonic(N))*(s.harmonic(n)-s.harmonic(N));Q=pi*pi/6-s.harmonic(N,2)
    ans=B*(P-Q)
    A,C=s.symbols('A C',positive=True);G=s.gamma(A)*s.gamma(C)/s.gamma(A+C)
    eq(s.diff(G,A,C).subs({A:m+1,C:n+1}),ans)
    return result(integral(x**m*(1-x)**n*s.log(x)*s.log(1-x),0,1),ans,[B*P,B*(P+Q),B*Q],
      [text('Differentiate B(A,B) once in each parameter.'),r'\partial_A\partial_B B=B\big((\psi(A)-\psi(A+B))(\psi(B)-\psi(A+B))-\psi_1(A+B)\big)',r'\psi(k)=H_{k-1}-\gamma,\quad\psi_1(k)=\frac{\pi^2}{6}-H_{k-1}^{(2)}',r'I='+tex(ans)],{'m':m,'n':n},['exact mixed gamma-quotient derivative','integrable logarithmic majorants'])

@family('thermal-derivative','A squared thermal denominator encodes weighted frequencies','thermal-geometric-derivative','positive-series-interchange',['integration-by-parts'],
 'exponential-geometric-derivative:polynomial-moment',['tonelli','gamma-integral','zeta-function'],['recognition','convergence','synthesis'],
 ['For x>0, exp(x)/(exp(x)-1)^2=sum_{k>=1} k exp(-kx).', 'The terms are nonnegative, so Tonelli applies.', 'Each degree-n Laplace moment is n!/k^(n+1), leaving n! zeta(n).', 'Near zero the original integrand is O(x^(n-2)); n>1 is exactly the relevant threshold.'],
 ['Integer n>=2; absolute convergence at both endpoints.'],
 ['Omitting the frequency weight k','Using the Bose denominator instead of its derivative','Losing a factorial in the Laplace moment'])
def thermal_derivative(i):
    n=i+2;ans=s.factorial(n)*s.zeta(n)
    q=s.symbols('q');eq(q*s.diff(q/(1-q),q),q/(1-q)**2)
    return result(integral(x**n*s.exp(x)/(s.exp(x)-1)**2),ans,[s.factorial(n)*s.zeta(n+1),s.factorial(n-1)*s.zeta(n),s.factorial(n)*s.zeta(n+2)],
      [r'\frac{e^x}{(e^x-1)^2}=\sum_{k=1}^\infty k e^{-kx}',text('Tonelli is justified by nonnegative terms and n>1.'),r'I='+str(s.factorial(n))+r'\sum_{k=1}^\infty k^{-'+str(n)+r'}='+tex(ans)],{'n':n},['exact differentiated geometric identity','gamma recurrence','endpoint convergence exponent'])

@family('mellin-cyclotomic','A rational power integral is a beta reflection','mellin-cyclotomic-integral','mellin-substitution',['keyhole-contour'],
 'rational-power:one-plus-monomial',['beta-function','gamma-reflection','improper-integrals'],['method-selection','convergence'],
 ['Set t=x^q to obtain q^-1 integral t^(p/q-1)/(1+t) dt.', 'The exponent is in (0,1), so both endpoints converge.', 'The beta integral is Gamma(p/q)Gamma(1-p/q); reflection gives pi csc(pi p/q).'],
 ['Integers 0<p<q; positive real branches.'],
 ['Forgetting the substitution factor q','Using cosine instead of sine in reflection','Using p rather than q in the scale factor'])
def mellin(i):
    p,q=[(1,3),(3,5),(3,7),(5,7),(3,8),(5,9),(7,11),(3,10)][i];r=R(p,q);ans=pi/(q*s.sin(pi*r))
    eq((x**(p-1)/(1+x**q)).subs(x,t**R(1,q))*s.diff(t**R(1,q),t),t**(r-1)/(q*(1+t)))
    return result(integral(x**(p-1)/(1+x**q)),ans,[pi/(q*q*s.sin(pi*r)),pi/(q*s.cos(pi*r)),pi/(q*s.sin(pi*(r/3)))],
      [r't=x^{'+str(q)+r'},\quad I=\frac1{'+str(q)+r'}B\left('+tex(r)+','+tex(1-r)+r'\right)',r'\Gamma(r)\Gamma(1-r)=\frac\pi{\sin(\pi r)}',r'I='+tex(ans)],{'p':p,'q':q},['exact Mellin change of variables','strict beta-domain check'])

@family('cauchy-convolution','Overlap of shifted rational peaks','cauchy-convolution','residue-pairing',['partial-fractions','fourier-transform'],
 'product-of-shifted-cauchy-kernels',['partial-fractions','residues'],['method-selection','synthesis'],
 ['The upper-half-plane poles are a+ib and -a+ib.', 'The residue sum, multiplied by 2pi i, is pi/(2b(a^2+b^2)).', 'The O(z^-4) bound kills the upper semicircle; no real poles occur.', 'An elementary partial-fraction decomposition supplies an alternative real proof.'],
 ['a,b>0 real; the integral is over the whole real line.'],
 ['Replacing separated peaks by coincident ones','Dropping one pole contribution','Using squared displacement with the wrong sign'])
def cauchy_convolution(i):
    a=s.Integer(i+2 if i%2 else 1+i%3);b=s.Integer(1+i%3 if i%2 else i+3);f=1/(((x-a)**2+b*b)*((x+a)**2+b*b));ans=pi/(2*b*(a*a+b*b))
    zz=s.symbols('zz');fz=f.subs(x,zz)
    eq(2*pi*s.I*(s.residue(fz,zz,a+s.I*b)+s.residue(fz,zz,-a+s.I*b)),ans)
    return result(integral(f,-s.oo,s.oo),ans,[pi/(2*b**3),2*ans,pi/(2*a*(a*a+b*b)) if a!=b else ans/2],
      [text('Use the two poles in the upper half-plane.'),r'z='+tex(a+s.I*b)+r',\quad z='+tex(-a+s.I*b),text('Their residues add; the large semicircle contributes zero.'),r'I='+tex(ans)],{'a':int(a),'b':int(b)},['exact two-residue sum','real-axis pole exclusion','O(z^-4) contour bound'])

@family('binomial-exponential','An exponential saturation integral is a beta moment','exponential-beta-transform','exponential-substitution',['binomial-expansion'],
 'positive-integer-power:exponential-saturation',['substitution','beta-integral'],['recognition','method-selection'],
 ['Set t=exp(-x). The reversed bounds and dx=-dt/t produce t^(a-1)(1-t)^n.', 'The beta value for positive integers is (a-1)! n!/(a+n)!.', 'Direct finite binomial expansion gives an independent rational sum, sum (-1)^k binomial(n,k)/(a+k).'],
 ['Positive integer a,n; exponential tail and O(x^n) behavior at zero.'],
 ['Forgetting the Jacobian t^-1','Dropping the binomial cancellation','Using a+n rather than factorial normalization'],
 notes=['Short recognition problem; proposed Olympiad only as a varied elegant item, difficulty requires editorial calibration.'])
def binomial_exponential(i):
    a=2+i%3;n=i+3;ans=s.factorial(a-1)*s.factorial(n)/s.factorial(a+n)
    eq(sum((-1)**k*s.binomial(n,k)/s.Integer(a+k) for k in range(n+1)),ans)
    return result(integral(s.exp(-a*x)*(1-s.exp(-x))**n),ans,[s.factorial(a)*s.factorial(n)/s.factorial(a+n+1),R(1,a),R(1,a+n)],
      [r't=e^{-x},\quad I=\int_0^1 t^{'+str(a-1)+r'}(1-t)^{'+str(n)+r'}\,dt',r'I=B('+str(a)+','+str(n+1)+r')='+tex(ans)],{'a':a,'n':n},['exact finite binomial sum','beta factorial identity'])

@family('agm-parameter','Find a hidden elliptic invariance','elliptic-agm-invariance','landen-substitution',['arithmetic-geometric-mean'],
 'elliptic-product-root:parameter-identification',['monotone-substitution','improper-integrals'],['reframing','synthesis'],
 ['For I(a,b)=integral_0^infinity dx/sqrt((x^2+a^2)(x^2+b^2)), set u=(x-ab/x)/2.', 'Then u^2+((a+b)/2)^2=((x^2+a^2)(x^2+b^2))/(4x^2) and u^2+ab=(x+ab/x)^2/4.', 'The Jacobian converts the positive half-axis to the entire real line with factor one half. Evenness yields I(a,b)=I((a+b)/2,sqrt(ab)).', 'For fixed first parameter the integral strictly decreases as the positive second parameter increases, proving uniqueness.'],
 ['a,b>0 and a != b; the sought parameter is positive; all square roots are positive.'],
 ['Using the arithmetic mean twice','Using the harmonic mean','Using the root mean square'],seconds=600)
def agm_parameter(i):
    a=s.Integer(i+1);b=a+2;A=(a+b)/2;u0=(x-a*b/x)/2;ans=s.sqrt(a*b)
    eq(u0**2+A*A,((x*x+a*a)*(x*x+b*b))/(4*x*x));eq(u0**2+a*b,(x+a*b/x)**2/4)
    statement=text('Find the unique c>0 such that ')+r'\int_0^\infty\frac{dx}{\sqrt{(x^2+'+tex(a*a)+r')(x^2+'+tex(b*b)+r')}}=\int_0^\infty\frac{dx}{\sqrt{(x^2+'+tex(A*A)+r')(x^2+c^2)}}.'
    return result(statement,ans,[A,2*a*b/(a+b),s.sqrt((a*a+b*b)/2)],
      [r'u=\frac{x-ab/x}{2},\quad A=\frac{a+b}{2}',r'u^2+A^2=\frac{(x^2+a^2)(x^2+b^2)}{4x^2},\quad u^2+ab=\frac{(x+ab/x)^2}{4}',r'I(a,b)=I\left(\frac{a+b}{2},\sqrt{ab}\right)',text('Strict decrease in c makes the solution unique.'),r'c='+tex(ans)],{'a':int(a),'b':int(b)},['exact two Landen identities','positive monotone Jacobian','strict parameter monotonicity'])

@family('abel-recovery','Recover an integral from a square-root convolution','abel-integral-inversion','double-integral-order-swap',['fractional-calculus'],
 'unknown-function:abel-half-integral',['fubini','beta-integral'],['reframing','synthesis'],
 ['Multiply the given Abel transform F(t) by (1-t)^-1/2 and integrate t from zero to one.', 'Swap order on 0<=x<=t<=1. Continuity of f and the integrable positive kernel justify absolute Fubini.', 'The inner integral in t equals B(1/2,1/2)=pi, independent of x.', 'Therefore integral f=pi^-1 integral F(t)(1-t)^-1/2 dt.'],
 ['f continuous on [0,1]; specified Abel identity holds for every t in [0,1].'],
 ['Forgetting the beta factor pi','Confusing f with its Abel transform','Using a full derivative rather than a half integral'],seconds=540)
def abel_recovery(i):
    n=i+2;ans=s.factorial(n)/(s.sqrt(pi)*s.gamma(n+R(3,2)))
    # The unique monomial inverse satisfies the stated integral by the beta identity.
    c=s.gamma(n+1)/(s.sqrt(pi)*s.gamma(n+R(1,2)))
    eq(c*s.gamma(n+R(1,2))*s.gamma(R(1,2))/s.gamma(n+1),1);eq(c/(n+R(1,2)),ans)
    return result(text('A continuous real f satisfies ')+r'\int_0^t\frac{f(x)}{\sqrt{t-x}}\,dx=t^{'+str(n)+r'}\ (0\le t\le1).\quad '+text('Find ')+r'\int_0^1f(x)\,dx.',ans,[pi*ans,R(1,n+1),c],
      [text('Apply the same square-root kernel a second time and change integration order.'),r'\int_x^1\frac{dt}{\sqrt{(t-x)(1-t)}}=\pi',r'\pi\int_0^1 f(x)\,dx=\int_0^1\frac{t^{'+str(n)+r'}}{\sqrt{1-t}}\,dt',r'I='+tex(ans)],{'n':n},['exact beta inversion coefficient','continuous-function absolute Fubini bound'])

@family('boundary-asymptotic','Find the scale of an integral boundary layer','integral-boundary-layer','laplace-rescaling',['beta-asymptotics'],
 'large-power:degenerate-endpoint-maximum',['dominated-convergence','gamma-integral'],['method-selection','convergence','synthesis'],
 ['Substitute x=n^(-1/p)u. Extend the transformed integrand by zero beyond u=n^(1/p).', 'For fixed u it converges to exp(-u^p).', 'The inequality (1-v/n)^n<=exp(-v), 0<=v<=n, supplies an integrable majorant.', 'The remaining integral is Gamma(1+1/p).'],
 ['Integer p>=2; the limit is through positive integers n.'],
 ['Ignoring the boundary layer and returning zero','Missing the Jacobian factor 1/p','Using the wrong gamma argument'],seconds=420)
def boundary_asymptotic(i):
    p=i+2;r=R(1,p);ans=s.gamma(1+r);eq(ans,r*s.gamma(r))
    return result(r'\lim_{n\to\infty} n^{1/'+str(p)+r'}\int_0^1(1-x^{'+str(p)+r'})^n\,dx',ans,[s.Integer(0),s.gamma(r),s.gamma(1+R(2,p))],
      [r'x=n^{-1/'+str(p)+r'}u',r'(1-u^{'+str(p)+r'}/n)^n\longrightarrow e^{-u^{'+str(p)+r'}},\quad 0\le(1-v/n)^n\le e^{-v}',text('Dominated convergence now applies to the rescaled integral.'),r'I=\int_0^\infty e^{-u^{'+str(p)+r'}}\,du='+tex(ans)],{'p':p},['exact gamma recurrence','uniform exponential domination'])

@family('integral-equation','An integral equation hides boundary conditions','green-kernel-integral-equation','differentiate-integral-equation',['green-function'],
 'min-kernel:fredholm-equation',['leibniz-rule','linear-ode','boundary-values'],['reframing','synthesis'],
 ['For Kf(x)=integral_0^1 min(x,t)f(t)dt, differentiate the split integral to obtain (Kf) prime=integral_x^1 f(t)dt and (Kf) double-prime=-f(x).', 'Thus f+k^2 Kf=x implies f double-prime=k^2 f, f(0)=0 and f prime(1)=1.', 'The unique solution is sinh(kx)/(k cosh k). For the residual R=f+k^2 Kf-x, R double-prime=0, R(0)=0 and R prime(1)=0, so R identically vanishes. This establishes sufficiency for the original equation.', 'Integrating this solution gives (cosh k-1)/(k^2 cosh k).'],
 ['k>0; f continuous on [0,1]; equation holds for every x in [0,1].'],
 ['Wrong sign when differentiating the Green kernel','Using an initial instead of endpoint derivative','Forgetting the constant term when integrating sinh'],seconds=600)
def integral_equation(i):
    k=R(i+1,2);f=s.sinh(k*x)/(k*s.cosh(k));ans=(s.cosh(k)-1)/(k*k*s.cosh(k))
    eq(s.diff(f,x,2),k*k*f);eq(f.subs(x,0),0);eq(s.diff(f,x).subs(x,1),1);eq(s.integrate(f,(x,0,1)),ans)
    return result(text('A continuous f on [0,1] satisfies ')+r'f(x)+'+tex(k*k)+r'\int_0^1\min(x,t)f(t)\,dt=x.\quad '+text('Find ')+r'\int_0^1 f(x)\,dx.',ans,
      [(s.cosh(k)-1)/(k*k),s.tanh(k)/k,1/(k*k*s.cosh(k))],
      [r'(Kf)^{\prime}(x)=\int_x^1 f(t)\,dt,\quad(Kf)^{\prime\prime}(x)=-f(x)',r'f^{\prime\prime}=k^2f,\quad f(0)=0,\quad f^{\prime}(1)=1',r'f(x)=\frac{\sinh(kx)}{k\cosh k}',r'I='+tex(ans)],{'k':[int(k.p),int(k.q)]},['exact ODE residual','two exact endpoint conditions','exact final integral'])

@family('convolution-laplace','A recursive density becomes a transform power','compact-convolution-transform','laplace-convolution-theorem',['probability-independence'],
 'recursive-unit-box-convolution',['fubini','laplace-transform'],['recognition','synthesis'],
 ['The base function is the indicator of [0,1]. Each recurrence is convolution with that indicator.', 'All functions are nonnegative and compactly supported, so Tonelli allows splitting the exponential of a sum.', 'The transform of the n-fold convolution is the nth power of (1-exp(-a))/a.'],
 ['Integer n>=2; a>0; each f_n is zero outside [0,n].'],
 ['Multiplying transforms by n instead of taking a power','Forgetting one convolution','Using the transform of an infinite exponential tail'])
def convolution_laplace(i):
    n=i+2;a=s.log(2+i%3);L=(1-s.exp(-a))/a;ans=L**n
    eq(s.integrate(s.exp(-a*x),(x,0,1)),L)
    return result(r'f_1(t)=\mathbf1_{[0,1]}(t),\quad f_{j+1}(t)=\int_0^1 f_j(t-u)\,du.\quad '+text('Evaluate ')+r'\int_0^{'+str(n)+r'} e^{-'+tex(a)+r't}f_{'+str(n)+r'}(t)\,dt.',ans,[n*L,L**(n-1),1/a**n],
      [text('The recursion is repeated convolution by the unit interval indicator.'),r'\mathcal L(f_{j+1})(a)=\mathcal L(f_j)(a)\frac{1-e^{-a}}a',r'I=\left(\frac{1-e^{-a}}a\right)^{'+str(n)+r'}='+tex(ans)],{'n':n,'base':2+i%3},['exact base transform','compact-support Tonelli convolution certificate'])

@family('poisson-log-potential','A logarithm propagates through a Cauchy kernel','harmonic-poisson-extension','poisson-integral',['parameter-differentiation','residue-convolution'],
 'shifted-quadratic-log:cauchy-weight',['harmonic-functions','residues'],['method-selection','synthesis'],
 ['The function log|z-b+ic|^2 is harmonic in the upper half-plane because its zero is below the boundary.', 'The Poisson integral at ia therefore equals log(b^2+(a+c)^2). The logarithmic growth is integrable against the Cauchy kernel.', 'Alternatively differentiate in c, evaluate a rational Cauchy convolution, and determine the constant from c tending to infinity.'],
 ['a,c>0; b real; the real logarithm argument is strictly positive.'],
 ['Using a-c instead of a+c','Evaluating the logarithm at the boundary','Forgetting the kernel normalization'],seconds=540)
def poisson_log(i):
    a=s.Integer(1+i%3);b=s.Integer(i+1);c=s.Integer(2+i%2);ans=pi/a*s.log(b*b+(a+c)**2)
    # Independently check the parameter derivative with exact residues.
    zz=s.symbols('zz');der=2*c/(((zz-b)**2+c*c)*(zz*zz+a*a))
    residue_value=2*pi*s.I*(s.residue(der,zz,s.I*a)+s.residue(der,zz,b+s.I*c))
    eq(residue_value,2*pi*(a+c)/(a*(b*b+(a+c)**2)))
    return result(integral(s.log((x-b)**2+c*c)/(x*x+a*a),-s.oo,s.oo),ans,
      [pi/a*s.log(b*b+(a-c)**2),pi/a*s.log(b*b+c*c),pi*s.log(b*b+(a+c)**2) if a!=1 else ans/2],
      [text('Use the upper-half-plane Poisson kernel with height a.'),r'\frac a\pi I=\log|ia-b+ic|^2=\log(b^2+(a+c)^2)',text('The logarithmic growth is allowed because the kernel decays quadratically.'),r'I='+tex(ans)],{'a':int(a),'b':int(b),'c':int(c)},['exact rational parameter-derivative residues','Poisson domain and logarithmic growth'])

@family('jensen-radius','A unit-circle logarithm changes regime','analytic-log-circle','jensen-zero-count',['fourier-series'],
 'circle-logarithm:zero-crosses-unit-boundary',['complex-logarithm','fourier-series'],['recognition','convergence','reframing'],
 ['For 0<r<1 the logarithm has an absolutely convergent Fourier series with zero constant term.', 'For r>1, factor r^2 from the logarithm argument and apply the inside-disk case to 1/r.', 'The resulting mean is 4pi log r for r>1 and zero for r<1.'],
 ['r>0, r!=1 in this asset; argument remains positive.'],
 ['Using the inside-disk formula outside','Forgetting the squared-modulus factor','Treating log r as its reciprocal'],
 notes=['Shares relatedIdeaGroupId with logarithmic Fourier coefficients; not a second globally independent log-series idea.'])
def jensen_radius(i):
    r=R(i+3,2);ans=4*pi*s.log(r)
    eq(1-2*r*s.cos(x)+r*r,r*r*(1-2/r*s.cos(x)+1/(r*r)))
    return result(integral(s.log(1-2*r*s.cos(x)+r*r),0,2*pi),ans,[s.Integer(0),2*pi*s.log(r),4*pi*s.log(1/r)],
      [text('The radius exceeds one; factor r squared before expanding.'),r'\log(1-2r\cos x+r^2)=2\log r+\log(1-2r^{-1}\cos x+r^{-2})',text('The remaining Fourier series has zero constant coefficient.'),r'I=4\pi\log r='+tex(ans)],{'r':[int(r.p),int(r.q)]},['exact reciprocal factorization','inside-disk absolute Fourier convergence'])

@family('fresnel','An oscillatory square needs a branch choice','fresnel-analytic-continuation','gaussian-analytic-continuation',['contour-rotation'],
 'conditionally-convergent:quadratic-phase',['complex-square-root','improper-integrals'],['convergence','synthesis'],
 ['For epsilon>0, the complex Gaussian integral equals sqrt(pi)/(2 sqrt(epsilon-ia)), using the square root with positive real part.', 'Take its real part and let epsilon decrease to zero.', 'Integrate exp(iax^2) against the monotone amplitude exp(-epsilon x^2)/x: integration by parts gives absolute tail bound 1/(aR) for every epsilon>=0. This uniform bound permits the regulator limit to agree with the ordinary improper Fresnel integral.', 'The branch factor exp(i pi/4) contributes 1/sqrt(2) to the real part.'],
 ['a>0; ordinary improper limit at infinity, not an absolutely convergent integral.'],
 ['Taking the complex magnitude instead of its real part','Choosing the wrong square-root branch','Missing the half-line factor'],seconds=540)
def fresnel(i):
    a=R(i+1,2);ans=s.sqrt(pi)/(2*s.sqrt(2*a));eq(s.re(s.sqrt(pi)/(2*s.sqrt(-s.I*a))),ans)
    return result(integral(s.cos(a*x*x)),ans,[s.sqrt(pi)/(2*s.sqrt(a)),-ans,2*ans],
      [r'\int_0^\infty e^{-(\varepsilon-ia)x^2}\,dx=\frac{\sqrt\pi}{2\sqrt{\varepsilon-ia}}',text('Use the branch with positive real part and then take real parts.'),text('Integration by parts controls the oscillatory tail, so the regulator limit equals the improper integral.'),r'I='+tex(ans)],{'a':[int(a.p),int(a.q)]},['exact principal-branch real part','analytic Gaussian continuation','oscillatory tail certificate'])

@family('bessel-laplace','Angular averaging removes a Bessel function','bessel-angular-transform','angular-representation-and-fubini',['laplace-transform-ode'],
 'bessel-J0:exponential-weight',['bessel-functions','fubini','trigonometric-substitution'],['recognition','synthesis'],
 ['Use J0(y)=pi^-1 integral_0^pi cos(y sin theta) dtheta.', 'The exponential majorant exp(-ax) makes Fubini absolute.', 'The x integral is a/(a^2+b^2 sin^2 theta). Symmetry and t=tan theta evaluate the angular integral.', 'The answer is 1/sqrt(a^2+b^2).'],
 ['a>0, b>=0; J0 is the Bessel function of the first kind of order zero.'],
 ['Replacing circular by hyperbolic frequency','Dropping the square root','Ignoring the Bessel oscillation'],seconds=480)
def bessel_laplace(i):
    a=s.Integer(i+2);b=s.Integer(i+1);ans=1/s.sqrt(a*a+b*b)
    # Angular rationalization identity, with t=tan(theta).
    eq(a/(a*a+b*b*t*t/(1+t*t))/(1+t*t),a/(a*a+(a*a+b*b)*t*t))
    return result(integral(s.exp(-a*x)*s.besselj(0,b*x))+r',\quad J_0'+text(' denotes the Bessel function of the first kind.'),ans,
      [1/s.sqrt(a*a-b*b),1/(a*a+b*b),1/a],
      [r'J_0(y)=\frac1\pi\int_0^\pi\cos(y\sin\theta)\,d\theta',text('Absolute Fubini is justified by the exponential weight.'),r'I=\frac1\pi\int_0^\pi\frac{a\,d\theta}{a^2+b^2\sin^2\theta}=\frac1{\sqrt{a^2+b^2}}',r'I='+tex(ans)],{'a':int(a),'b':int(b)},['exact angular rationalization','exponential Fubini majorant'])

@family('rodrigues-moment','Move all derivatives before expanding','rodrigues-orthogonal-moment','repeated-integration-by-parts',['polynomial-expansion'],
 'rodrigues-polynomial:off-diagonal-moment',['integration-by-parts','beta-integral'],['method-selection','reframing'],
 ['Integrate by parts n times. Every endpoint term vanishes because (x^2-1)^n has zero order n at both endpoints.', 'The nth derivative of x^(n+2k) is (n+2k)! x^(2k)/(2k)!.', 'The two signs from integration by parts and (x^2-1)^n cancel.', 'Substituting t=x^2 in the remaining even integral gives B(k+1/2,n+1).'],
 ['Integers n>=2,k>=1.'],
 ['Assuming all moments vanish by orthogonality','Missing the derivative factorial','Retaining a spurious sign'],seconds=420)
def rodrigues(i):
    n=i+2;k=1+i%2;expr=x**(n+2*k)*s.diff((x*x-1)**n,x,n)
    ans=s.factorial(n+2*k)/s.factorial(2*k)*s.gamma(k+R(1,2))*s.factorial(n)/s.gamma(k+n+R(3,2))
    eq(s.integrate(s.expand(expr),(x,-1,1)),ans)
    return result(r'\int_{-1}^1 x^{'+str(n+2*k)+r'}\frac{d^{'+str(n)+r'}}{dx^{'+str(n)+r'}}(x^2-1)^{'+str(n)+r'}\,dx',ans,
      [s.Integer(0),ans*s.factorial(2*k)/s.factorial(n+2*k),-ans],
      [text('Integrate by parts '+str(n)+' times; the endpoint terms vanish.'),r'I=\frac{('+str(n+2*k)+r')!}{('+str(2*k)+r')!}\int_{-1}^1 x^{'+str(2*k)+r'}(1-x^2)^{'+str(n)+r'}\,dx',r'I=\frac{('+str(n+2*k)+r')!}{('+str(2*k)+r')!}B\left('+tex(k+R(1,2))+','+str(n+1)+r'\right)='+tex(ans)],{'n':n,'k':k},['independent exact polynomial integral','endpoint zero multiplicities'])

@family('bernoulli-product','A polynomial product collapses through endpoint recurrence','bernoulli-endpoint-recurrence','orthogonal-recurrence-integration',['exact-polynomial-integration'],
 'bernoulli-polynomial-product',['generating-functions','integration-by-parts'],['recognition','synthesis'],
 ['Bernoulli polynomials are defined by t exp(xt)/(exp(t)-1)=sum B_j(x)t^j/j!.', 'Their derivative recurrence is B_j prime=j B_(j-1), and B_j(1)=B_j(0) except j=1.', 'Repeated integration by parts leaves only the final B1 endpoint jump.', 'For m,n>=1 the value is (-1)^(m-1)m!n! B_(m+n)/(m+n)!.'],
 ['Positive integer m,n; B1(x)=x-1/2 convention; no endpoint singularities.'],
 ['Missing the endpoint jump','Dropping the factorial ratio','Using the wrong sign in repeated integration by parts'],seconds=540)
def bernoulli_product(i):
    m,n=[(2,2),(2,4),(3,3),(2,6),(3,5),(4,4),(2,8),(4,6)][i];N=m+n;expr=s.bernoulli(m,x)*s.bernoulli(n,x)
    ans=(-1)**(m-1)*s.factorial(m)*s.factorial(n)*s.bernoulli(N)/s.factorial(N)
    eq(s.integrate(s.expand(expr),(x,0,1)),ans)
    return result(r'\frac{t e^{xt}}{e^t-1}=\sum_{j=0}^{\infty}B_j(x)\frac{t^j}{j!}.\quad '+text('Evaluate ')+r'\int_0^1B_{'+str(m)+r'}(x)B_{'+str(n)+r'}(x)\,dx.',ans,
      [s.Integer(0),(-1)**(m-1)*s.bernoulli(N),-ans],
      [r'B_j^{\prime}=jB_{j-1},\quad B_j(1)=B_j(0)\ (j\ne1),\quad B_1(1)-B_1(0)=1',text('Repeated integration by parts leaves the B1 endpoint jump.'),r'I=(-1)^{'+str(m-1)+r'}\frac{'+str(m)+r'!'+str(n)+r'!}{'+str(N)+r'!}B_{'+str(N)+r'}='+tex(ans)],{'m':m,'n':n},['independent exact Bernoulli-polynomial integration','specified B1 convention'])

@family('principal-value','A finite principal value is not an improper integral','interior-pole-convergence','principal-value-splitting',['digamma-reflection'],
 'simple-real-pole:mellin-weight',['improper-integrals','cauchy-principal-value'],['convergence','reframing'],
 ['Near x=1 the integrand has a nonzero simple-pole residue, so the two one-sided improper integrals diverge.', 'For the principal value put t=x^q, then split at one and substitute t=1/u on the upper piece.', 'The combined integrable expression is q^-1 integral_0^1 (u^(p/q-1)-u^(-p/q))/(1-u) du.', 'The digamma reflection identity gives pi cot(pi p/q)/q. Under symmetric x cutoffs 1 plus/minus delta, the transformed cutoff ratio ((1+delta)^q-1)/(1-(1-delta)^q) tends to one; the possible logarithmic correction therefore vanishes.'],
 ['0<p<q; p/q!=1/2 in this asset; PV uses symmetric x cutoffs at the sole pole x=1.'],
 ['Reporting principal value as an ordinary convergent integral','Reversing the reflection sign','Using the no-pole csc identity'],seconds=540)
def principal_value(i):
    p,q=[(1,3),(2,5),(3,7),(2,7),(3,8),(4,9),(5,11),(3,10)][i];r=R(p,q);pv=pi/s.Integer(q)*s.cot(pi*r)
    eq(s.limit((x-1)*x**(p-1)/(1-x**q),x,1),-R(1,q))
    delta=s.symbols('delta',positive=True);eq(s.limit(((1+delta)**q-1)/(1-(1-delta)**q),delta,0),1)
    # Labels carry the convergence assertion; all values are kept exact.
    ans=s.Tuple(s.Symbol('divergent'),pv)
    return result(text('For ')+r'I=\int_0^\infty\frac{x^{'+str(p-1)+r'}}{1-x^{'+str(q)+r'}}\,dx'+text(', choose (ordinary integral, Cauchy principal value at x=1).'),ans,
      [s.Tuple(s.Symbol('convergent'),pv),s.Tuple(s.Symbol('divergent'),-pv),s.Tuple(s.Symbol('divergent'),pi/(q*s.sin(pi*r)))],
      [r'\lim_{x\to1}(x-1)\frac{x^{'+str(p-1)+r'}}{1-x^{'+str(q)+r'}}=-\frac1{'+str(q)+r'}\ne0',text('Thus the ordinary one-sided definition diverges.'),r'\operatorname{PV}I=\frac1{'+str(q)+r'}\int_0^1\frac{u^{'+tex(r-1)+r'}-u^{'+tex(-r)+r'}}{1-u}\,du',r'\operatorname{PV}I='+tex(pv)],{'p':p,'q':q},['exact nonzero pole residue','digamma-reflection parameter domain','PV cutoff equivalence'],'convergence-and-value')

@family('oscillatory-regularization','A damping limit cannot repair an ordinary divergence','oscillatory-tail-convergence','primitive-and-abel-regularization',['laplace-transform'],
 'nonconvergent-phase:abel-damped-pair',['improper-integrals','substitution','laplace-transform'],['convergence','reframing'],
 ['Set u=x^p. The ordinary cutoff integral becomes (1-cos(R^p))/p and therefore has no limit.', 'For epsilon>0 the damped integral is p^-1 integral exp(-epsilon u) sin u du=1/(p(1+epsilon^2)).', 'The damping limit is 1/p, which must not be called the ordinary integral.'],
 ['Positive integer p>=2; damping is exp(-epsilon x^p); ordinary cutoff tends to positive infinity.'],
 ['Confusing Abel regularization with convergence','Concluding zero from oscillation','Omitting the power-substitution Jacobian'])
def oscillatory_regularization(i):
    p=i+2;eps=s.symbols('epsilon',positive=True);primitive=(1-s.cos(x**p))/p
    eq(s.diff(primitive,x),x**(p-1)*s.sin(x**p))
    ans=s.Tuple(s.Symbol('divergent'),R(1,p))
    return result(text('Choose (ordinary convergence, damping limit) for ')+r'I=\int_0^\infty x^{'+str(p-1)+r'}\sin(x^{'+str(p)+r'})\,dx,\quad L=\lim_{\varepsilon\downarrow0}\int_0^\infty e^{-\varepsilon x^{'+str(p)+r'}}x^{'+str(p-1)+r'}\sin(x^{'+str(p)+r'})\,dx.',ans,
      [s.Tuple(s.Symbol('convergent'),R(1,p)),s.Tuple(s.Symbol('divergent'),s.Integer(0)),s.Tuple(s.Symbol('divergent'),s.Integer(1))],
      [r'\int_0^R x^{'+str(p-1)+r'}\sin(x^{'+str(p)+r'})\,dx=\frac{1-\cos(R^{'+str(p)+r'})}{'+str(p)+r'}',text('The cutoff oscillates and has no limit.'),r'L=\lim_{\varepsilon\downarrow0}\frac1{'+str(p)+r'(1+\varepsilon^2)}=\frac1{'+str(p)+r'}'],{'p':p},['exact cutoff primitive','two nonmatching cutoff subsequences','Laplace sine identity'],'convergence-and-value')

@family('concentration','An integrable spike defeats limit interchange','integral-boundary-layer','concentration-rescaling',['dominated-convergence-counterexample'],
 'shrinking-boundary-spike:fixed-total-mass',['pointwise-convergence','improper-integrals'],['convergence','reframing'],
 ['For each fixed x>0, n x^(p-1)/(1+n^2x^(2p)) tends to zero.', 'With u=n x^p, the integral is pi/(2p) for every positive n.', 'The mass is concentrated in a shrinking neighborhood of zero; no common integrable majorant can justify exchanging the limit.'],
 ['Integer p>=2; positive integers n; integration over the positive half-line.'],
 ['Interchanging limit and integral','Dropping the substitution derivative p','Doubling the half-line Cauchy integral'],
 notes=['Shares a broad boundary-layer group with Laplace asymptotics, while testing the opposite limit-interchange conclusion.'])
def concentration(i):
    p=i+2;N=s.symbols('N',positive=True);f=N*x**(p-1)/(1+N*N*x**(2*p));ans=pi/(2*p)
    eq(s.diff(s.atan(N*x**p)/p,x),f);eq(s.limit(f,N,s.oo),0)
    return result(r'\lim_{n\to\infty}\int_0^\infty\frac{n x^{'+str(p-1)+r'}}{1+n^2x^{'+str(2*p)+r'}}\,dx',ans,[s.Integer(0),pi/2,pi/(p+1)],
      [text('Pointwise convergence to zero does not justify exchanging the limit.'),r'\int\frac{nx^{'+str(p-1)+r'}}{1+n^2x^{'+str(2*p)+r'}}\,dx=\frac1{'+str(p)+r'}\arctan(nx^{'+str(p)+r'})',r'I_n=\frac\pi{'+str(2*p)+r'}'+text(' for every n, hence the same limit.')],{'p':p},['exact antiderivative','exact pointwise limit','endpoint mass calculation'])

@family('binary-product','A product records every binary exponent once','binary-product-combinatorics','finite-product-telescoping',['binary-expansion'],
 'dyadic-exponent-product',['geometric-series','binary-representation'],['recognition','reframing'],
 ['The product over k=0,...,n-1 of (1+x^(2^k)) equals sum_{j=0}^{2^n-1}x^j.', 'This follows inductively by multiplying by 1-x, or by uniqueness of binary expansion.', 'Termwise integration of the finite polynomial gives the harmonic number H_(2^n).'],
 ['Integer n>=2; H_m=sum_{j=1}^m 1/j.'],
 ['Multiplying the integrals of individual factors','Counting terms without integrating their powers','Using H_n instead of H_(2^n)'])
def binary_product(i):
    n=i+2;N=2**n;poly=s.prod(1+x**(2**k) for k in range(n));eq(s.expand((1-x)*poly),1-x**N)
    ans=s.harmonic(N,evaluate=False)
    return result(r'H_m=\sum_{j=1}^m\frac1j.\quad '+text('Evaluate ')+r'\int_0^1\prod_{k=0}^{'+str(n-1)+r'}(1+x^{2^k})\,dx',ans,
      [s.prod(1+R(1,2**k+1) for k in range(n)),s.harmonic(N-1,evaluate=False),s.harmonic(N+1,evaluate=False)],
      [r'(1-x)\prod_{k=0}^{'+str(n-1)+r'}(1+x^{2^k})=1-x^{'+str(N)+r'}',r'I=\sum_{j=0}^{'+str(N-1)+r'}\frac1{j+1}=H_{'+str(N)+r'}',r'H_m=\sum_{j=1}^m\frac1j'],{'n':n},['exact product polynomial identity','finite sum integration'])

@family('fejer-fourth','An oscillatory fourth power counts additive pairs','fourier-autocorrelation-count','parseval-and-convolution',['laurent-constant-term'],
 'dirichlet-geometric-kernel:fourth-power',['complex-geometric-series','fourier-orthogonality'],['reframing','synthesis'],
 ['The modulus of sum_{j=0}^{n-1} exp(ijx) is |sin(nx/2)/sin(x/2)|.', 'Its squared modulus has Fourier coefficient n-|k| for |k|<n.', 'Parseval gives 2pi(n^2+2 sum_{k=1}^{n-1}(n-k)^2)=2pi n(2n^2+1)/3.', 'At multiples of 2pi the quotient is extended continuously; there is no singularity.'],
 ['Integer n>=2; continuous endpoint extension of the quotient.'],
 ['Using the second moment instead of fourth','Ignoring off-diagonal autocorrelations','Counting ordered pairs without their frequency constraint'],seconds=420)
def fejer_fourth(i):
    n=i+2;ans=2*pi*n*(2*n*n+1)/3
    P=sum(z**j for j in range(n));Q=s.expand(P*P*P.subs(z,1/z)*P.subs(z,1/z));eq(2*pi*Q.coeff(z,0),ans)
    return result(r'\int_0^{2\pi}\left(\frac{\sin('+str(n)+r'x/2)}{\sin(x/2)}\right)^4\,dx'+text(' (continuous endpoint values).'),ans,
      [2*pi*n,2*pi*n*n,2*pi*n**3],
      [r'\left|\sum_{j=0}^{'+str(n-1)+r'}e^{ijx}\right|^2=\sum_{k=-'+str(n-1)+r'}^{'+str(n-1)+r'}('+str(n)+r'-|k|)e^{ikx}',text('Parseval squares the triangular Fourier coefficients.'),r'I=2\pi\left('+str(n*n)+r'+2\sum_{k=1}^{'+str(n-1)+r'}k^2\right)='+tex(ans)],{'n':n},['independent exact Laurent constant coefficient','finite Fourier orthogonality'])

@family('scaled-frullani','A cancellation survives nonlinear scaling','frullani-scaling-cancellation','frullani-with-power-substitution',['parameter-differentiation'],
 'difference-of-stretched-exponentials:log-measure',['fubini','improper-integrals'],['method-selection','convergence'],
 ['Set t=x^p, giving dx/x=dt/(pt).', 'The exponential difference divided by t equals the integral of exp(-ut) over the parameter interval between a and b.', 'Fubini applies to this sign-consistent integrand; the remaining parameter integral is integral_a^b du/u.', 'The grouped expression, not either separate term, converges at zero.'],
 ['Positive integer p; 0<a<b; positive real powers.'],
 ['Reversing the logarithm ratio','Forgetting the power Jacobian','Integrating the divergent terms separately'],
 notes=['Same related group as legacy frullani-cancellation; count once globally.'])
def frullani(i):
    p=2+i%4;a=s.Integer(i+1);b=a+2;ans=s.log(b/a)/p
    eq(s.integrate(s.exp(-u*t),(u,a,b)),(s.exp(-a*t)-s.exp(-b*t))/t)
    return result(integral((s.exp(-a*x**p)-s.exp(-b*x**p))/x),ans,
      [-ans,s.log(b/a),R(1,p)*(1/a-1/b)],
      [r't=x^{'+str(p)+r'},\quad\frac{dx}{x}=\frac{dt}{'+str(p)+r't}',r'\frac{e^{-at}-e^{-bt}}{t}=\int_a^b e^{-ut}\,du',r'I=\frac1{'+str(p)+r'}\int_a^b\frac{du}{u}='+tex(ans)],{'p':p,'a':int(a),'b':int(b)},['exact finite parameter integral','sign-consistent Fubini and endpoint cancellation'])

@family('sech-fourier','A hyperbolic kernel is its own transform','hyperbolic-fourier-beta','complex-mellin-transform',['rectangular-residue-contour'],
 'hyperbolic-secant:cosine-transform',['complex-beta-integral','gamma-reflection'],['synthesis','method-selection'],
 ['Use evenness to replace the cosine half-integral by half of the whole-line exponential transform.', 'Set t=exp(2pi x). The whole-line integral becomes pi^-1 integral_0^infinity t^(1/2+ib/(2pi)-1)/(1+t) dt.', 'The real part of the beta parameter is 1/2, so the beta integral is absolutely convergent.', 'Reflection gives 1/cosh(b/2) for the whole line and half that for the requested integral.'],
 ['b real; absolute exponential decay; positive-real t power uses its real logarithm.'],
 ['Forgetting the half-line factor','Using cos instead of cosh','Missing the half in the transformed frequency'],seconds=540)
def sech_fourier(i):
    q=s.Integer(i+2);b=2*s.log(q);ans=q/(q*q+1)
    eq(1/(2*s.cosh(s.log(q))).rewrite(s.exp),ans)
    return result(integral(s.cos(b*x)/s.cosh(pi*x)),ans,
      [2*ans,q*q/(q**4+1),q/(q*q-1)],
      [r'2I=\int_{-\infty}^{\infty}\frac{e^{ibx}}{\cosh(\pi x)}\,dx',r't=e^{2\pi x},\quad 2I=\frac1\pi B\left(\frac12+\frac{ib}{2\pi},\frac12-\frac{ib}{2\pi}\right)',r'I=\frac1{2\cosh(b/2)}='+tex(ans)],{'q':int(q)},['exact hyperbolic simplification','complex beta real-part domain check'])

@family('variational-energy','An integral minimum is a boundary-value problem','variational-dirichlet-energy','complete-the-energy-square',['euler-lagrange-equation'],
 'derivative-energy:fixed-endpoint-minimum',['integration-by-parts','hyperbolic-functions','quadratic-forms'],['method-selection','synthesis'],
 ['Take g(x)=sinh(kx)/sinh(k). It satisfies the endpoint data and g double-prime=k^2g.', 'For f=g+h with h zero at both endpoints, integration by parts makes the cross term in the energy zero.', 'The remaining difference is integral(h prime^2+k^2 h^2)>=0, with equality only for h=0.', 'The energy of g is the boundary value [g g prime]_0^1=k coth(k).'],
 ['k>0; admissible real functions f are continuously differentiable on [0,1], with f(0)=0 and f(1)=1.'],
 ['Using the wrong endpoint derivative','Ignoring the derivative term','Missing the endpoint normalization'],seconds=540)
def variational_energy(i):
    k=R(i+2,2);g=s.sinh(k*x)/s.sinh(k);ans=k*s.coth(k)
    eq(s.diff(g,x,2),k*k*g);eq(g.subs(x,0),0);eq(g.subs(x,1),1);eq((g*s.diff(g,x)).subs(x,1),ans)
    return result(text('Among real continuously differentiable f on [0,1] with f(0)=0, f(1)=1, find the minimum of ')+r'\int_0^1\left(f^{\prime}(x)^2+'+tex(k*k)+r'f(x)^2\right)\,dx.',ans,
      [k*s.tanh(k),k*k,k*s.cosh(k)],
      [r'g(x)=\frac{\sinh(kx)}{\sinh k},\quad g^{\prime\prime}=k^2g',r'E(g+h)-E(g)=\int_0^1(h^{\prime2}+k^2h^2)\,dx\ge0,\quad h(0)=h(1)=0',text('The cross term vanishes by integration by parts.'),r'E(g)=[gg^{\prime}]_0^1=k\coth k='+tex(ans)],{'k':[int(k.p),int(k.q)]},['exact Euler equation','exact boundary constraints','nonnegative energy difference'])

@family('moment-projection','Two moment constraints determine a least-energy function','hilbert-moment-projection','orthogonal-projection',['gram-matrix','cauchy-schwarz'],
 'two-moment-constraints:L2-minimum',['quadratic-forms','integral-inner-product'],['reframing','synthesis'],
 ['Set mu=integral x^m=1/(m+1), V=integral(x^m-mu)^2=1/(2m+1)-mu^2>0.', 'The function g=1+(c-mu)(x^m-mu)/V satisfies both moment constraints.', 'For any other admissible f=g+h, h is orthogonal to both 1 and x^m, hence to g.', 'Thus integral f^2=integral g^2+integral h^2>=1+(c-mu)^2/V, with equality at g.'],
 ['Integer m>=2; c real; f continuous real on [0,1]; no nonnegativity constraint on f.'],
 ['Applying Cauchy-Schwarz to only one moment','Using a raw moment instead of variance','Failing to center the moment'],seconds=480)
def moment_projection(i):
    m=i+2;c=R(1+i%3,4);mu=R(1,m+1);V=R(1,2*m+1)-mu*mu;g=1+(c-mu)*(x**m-mu)/V;ans=1+(c-mu)**2/V
    assert V>0;eq(s.integrate(g,(x,0,1)),1);eq(s.integrate(x**m*g,(x,0,1)),c);eq(s.integrate(s.expand(g*g),(x,0,1)),ans)
    return result(text('Among continuous real f on [0,1] satisfying ')+r'\int_0^1 f(x)\,dx=1,\quad\int_0^1x^{'+str(m)+r'}f(x)\,dx='+tex(c)+r',\quad '+text('find the minimum of ')+r'\int_0^1 f(x)^2\,dx.',ans,
      [c*c*(2*m+1),1+(c-mu)**2/(mu*mu),1+(c+mu)**2/V],
      [r'\mu=\frac1{'+str(m+1)+r'},\quad V=\frac1{'+str(2*m+1)+r'}-\mu^2',r'g(x)=1+\frac{c-\mu}{V}(x^{'+str(m)+r'}-\mu)',text('For any admissible f=g+h, both moments of h vanish, so the energy cross term is zero.'),r'\min\int_0^1f^2=1+\frac{(c-\mu)^2}{V}='+tex(ans)],{'m':m,'c':[int(c.p),int(c.q)]},['exact two moment constraints','exact candidate squared norm','positive variance and orthogonality'])

@family('quadrature-defect','Two point values almost determine a quartic integral','gaussian-quadrature-defect','orthogonal-polynomial-division',['gauss-legendre-quadrature'],
 'quartic:two-gaussian-nodes-and-leading-coefficient',['polynomial-division','orthogonality'],['recognition','reframing'],
 ['Let q(x)=x^2-x+1/6; its roots are the two specified nodes.', 'The average of the two node values integrates every polynomial of degree at most three exactly, verified on the monomial basis.', 'Subtract c q(x)^2 from the quartic. The remainder is cubic and unchanged at the nodes.', 'The correction is c integral_0^1 q^2 dx=c/180.'],
 ['p is a real polynomial of degree four with specified nonzero leading coefficient c; the two node values are finite and real.'],
 ['Treating the two-node rule as exact for quartics','Doubling the quadrature defect','Using the opposite defect sign'],seconds=480)
def quadrature_defect(i):
    c=s.Integer((-1)**i*(i+1));A=s.Integer(i-2);B=s.Integer(3-i%4);nodes=[R(1,2)-s.sqrt(3)/6,R(1,2)+s.sqrt(3)/6];q=x*x-x+R(1,6)
    for d in range(4):eq((nodes[0]**d+nodes[1]**d)/2,R(1,d+1))
    eq(s.integrate(q*q,(x,0,1)),R(1,180));G=(A+B)/2;ans=G+c/180
    return result(text('A real quartic p has leading coefficient ')+tex(c)+r',\quad p\left(\frac12-\frac{\sqrt3}{6}\right)='+tex(A)+r',\quad p\left(\frac12+\frac{\sqrt3}{6}\right)='+tex(B)+r'.\quad '+text('Find ')+r'\int_0^1p(x)\,dx.',ans,
      [G,G+c/90,G-c/180],
      [r'q(x)=x^2-x+\frac16,\quad\int_0^1q(x)^2\,dx=\frac1{180}',text('Subtract the leading coefficient times q squared; the remainder is cubic and its node values are unchanged.'),r'\int_0^1p=\frac{p(r_1)+p(r_2)}2+\frac{c}{180}='+tex(ans)],{'c':int(c),'A':int(A),'B':int(B)},['exact quadrature on all four monomials','exact squared-node-polynomial integral'])

@family('rearrangement','Distribution fixes the extreme first moments','rearrangement-extremal-integral','layer-cake-rearrangement',['hardy-littlewood-inequality'],
 'equimeasurable-function:first-moment-extrema',['layer-cake','measurable-sets','integral-inequalities'],['reframing','synthesis'],
 ['The given tail lengths say f has the same distribution as x^n on the unit interval.', 'Layer cake writes integral x f(x) dx as integral over t of integral over {f>t} x dx.', 'Among sets of a fixed length ell, the left interval minimizes the inner integral at ell^2/2; the right interval maximizes it at ell-ell^2/2.', 'These nested extreme sets are realized by f=(1-x)^n and f=x^n respectively. Exact beta/power integration gives the stated extrema.'],
 ['f is measurable from [0,1] to [0,1]; the specified tail-length equality holds for every 0<t<1; n is a positive integer.'],
 ['Using an independent average as a minimum','Shifting the distribution exponent','Optimizing only one endpoint'],seconds=600)
def rearrangement(i):
    n=i+2;low=R(1,(n+1)*(n+2));high=R(1,n+2);ans=s.Tuple(low,high)
    eq(s.integrate(x*(1-x)**n,(x,0,1)),low);eq(s.integrate(x*x**n,(x,0,1)),high)
    return result(text('Let measurable f:[0,1] to [0,1] satisfy ')+r'\operatorname{length}\{x:f(x)>t\}=1-t^{1/'+str(n)+r'}\ (0<t<1).\quad '+text('Find (minimum, maximum) of ')+r'\int_0^1x f(x)\,dx.',ans,
      [s.Tuple(R(1,(n+1)*(n+3)),R(1,n+3)),s.Tuple(R(1,(n+2)*(n+3)),high),s.Tuple(R(1,2*(n+1)),high)],
      [text('Layer cake reduces each level set to a set of prescribed length.'),text('Placing every level set on the left minimizes the moment; placing it on the right maximizes it.'),r'f_{\min}(x)=(1-x)^{'+str(n)+r'},\quad f_{\max}(x)=x^{'+str(n)+r'}',r'(I_{\min},I_{\max})='+tex(ans)],{'n':n},['exact extremizing-function integrals','nested-level-set realization','bounded Tonelli'],'ordered-real-pair')

def _different(a,b):
    if isinstance(a,s.Tuple) or isinstance(b,s.Tuple):
        if not isinstance(a,s.Tuple) or not isinstance(b,s.Tuple):return True
        return len(a)!=len(b) or any(_different(v,w) for v,w in zip(a,b))
    if isinstance(a,s.Symbol) or isinstance(b,s.Symbol):return a!=b
    d=s.simplify(a-b)
    if d==0:return False
    if d.is_zero is False:return True
    # Symbolic numeric constants need an exact nonidentity decision, not merely a float tolerance.
    verdict=d.equals(0)
    if verdict is None:raise AssertionError('unresolved choice equivalence: '+str(d))
    return not verdict

def authored_distractors(slug,raw,seed,descriptions):
    """Choose among mathematical mistakes, balancing magnitude tells offline.

    Numeric ranking is only an editorial filter. Exact non-equivalence is still
    required by make(). No generic integer-offset distractors are manufactured.
    """
    a=raw['answer'];p=raw['parameters'];pool=list(zip(raw['wrong'],descriptions))
    def add(value,why):pool.append((value,why))
    def rat(key):return R(*p[key]) if isinstance(p[key],list) else s.Integer(p[key])
    if slug=='weighted-complement':
        add(pi*p['n'],'Treating the power as a multiplicity of weighted periods')
        add(pi/(2*p['n']),'Dividing by the exponent although no power substitution was made')
    elif slug=='reciprocal-quartic':
        add(pi/(4*s.sqrt(2*p['a']+2)),'Applying the reciprocal averaging factor twice')
    elif slug=='inverse-moment':
        n,m,r=p['n'],p['m'],p['r']
        add(R(n,n-r)+R(m,m+r),'Subtracting rather than adding the moment exponent in one primitive')
        add(R(n,n+r-1)+R(m,m+r-1),'Forgetting the final increment in both power antiderivatives')
    elif slug=='chebyshev-absolute':
        add(R(2,p['n']),'Integrating only one half-period after substitution')
        add(R(2,p['n']+1),'Using the neighboring Chebyshev degree to count periods')
    elif slug=='floor-laplace':
        q=p['q'];add(1/(q*s.log(q)),'Replacing the geometric tail by its first term')
        add(1/((q+1)*s.log(q)),'Using an alternating rather than positive tail series')
    elif slug=='gamma-unit-average':
        A=rat('a');base=A*s.log(A)-A
        pool=[(base+s.log(pi)/2,'Omitting the factor two in the log-sine normalization'),
              (base+s.log(2*pi),'Failing to divide the reflected Gamma average by two'),
              (base-s.log(2*pi)/2,'Reversing the reflection constant sign'),
              (base+s.log(pi),'Combining both log-sine and averaging normalization mistakes')]
    elif slug=='log-fourier-coefficient':
        n=p['n'];r=rat('r');add(-2*pi*r**n/n,'Using the full-period cosine norm on a half period')
        add(-pi*r**n/(n-1),'Using the neighboring reciprocal coefficient after integrating a power series')
    elif slug=='arctan-parameter':
        A=rat('a');add(pi*s.log(1+A)/4,'Applying the half-line normalization twice')
        add(pi*s.log(1+A*A)/2,'Treating the differentiated scale a as a squared parameter')
    elif slug=='gaussian-fourier':
        A=p['a'];b=p['b'];add(s.sqrt(pi)/(2*s.sqrt(A))*s.exp(-b*b/(2*s.Integer(A))),'Losing a factor two when solving the parameter ODE')
    elif slug=='reciprocal-gaussian':
        A=rat('a');b=rat('b');add(s.sqrt(pi)*s.exp(-4*A*b)/(2*A),'Counting the reciprocal contribution twice in the ODE')
        add(s.sqrt(pi)*s.exp(-2*A*b)/(4*A),'Applying half-line symmetry twice')
    elif slug=='sinc-overlap':
        A,B=p['a'],p['b'];add(pi*min(A,B)/4,'Applying product-to-sum twice')
        add(pi*R(min(A,B),2*max(A,B)),'Normalizing the overlap by a frequency instead of measuring its width')
    elif slug=='mixed-beta-log':
        m,n=p['m'],p['n'];N=m+n+1;B=s.factorial(m)*s.factorial(n)/s.factorial(N)
        P=(s.harmonic(m)-s.harmonic(N))*(s.harmonic(n)-s.harmonic(N));Q=pi*pi/6-s.harmonic(N,2)
        add(B*(P-2*Q),'Differentiating the mixed trigamma contribution twice')
        add(a/2,'Mistaking the mixed derivative for a Taylor coefficient with a factor two')
    elif slug=='thermal-derivative':
        n=p['n'];add(s.factorial(n+1)*s.zeta(n),'Using the next Gamma moment without changing the frequency power')
        add(s.factorial(n+1)*s.zeta(n+1),'Increasing the polynomial degree after differentiating the geometric series')
    elif slug=='mellin-cyclotomic':
        P,Q=p['p'],p['q'];r=R(P,Q)
        pool=[(pi/(Q*Q*s.sin(pi*r)),'Applying the power-substitution Jacobian twice'),
              (pi/s.sin(pi*r),'Forgetting the power-substitution Jacobian'),
              (pi/(Q*s.cos(pi*r)),'Using cosine instead of sine in Gamma reflection'),
              (pi/(P*s.sin(pi*r)),'Using the numerator exponent as the substitution scale'),
              (pi/(Q*s.sin(pi*r/2)),'Halving the beta reflection argument')]
    elif slug=='binomial-exponential':
        A,n=p['a'],p['n'];add(s.factorial(A-1)*s.factorial(n+1)/s.factorial(A+n+1),'Increasing the saturation exponent by one')
    elif slug=='agm-parameter':
        add(s.Integer(min(p['a'],p['b'])),'Choosing the limiting lower bound instead of the transformed parameter')
    elif slug=='abel-recovery':
        n=p['n'];c=s.gamma(n+1)/(s.sqrt(pi)*s.gamma(n+R(1,2)))
        pool=[(c/(n+1),'Losing the half power when taking the final primitive'),
              (c/(n+R(3,2)),'Adding a half power instead of subtracting it during inversion'),
              (c/n,'Dropping the residual half in the inverse power'),
              (c/(n-R(1,2)),'Counting the inverse half-order twice')]
    elif slug=='boundary-asymptotic':
        P=p['p'];add(s.gamma(R(1,P))/(P+1),'Using p+1 for the rescaling Jacobian')
        add(s.gamma(R(1,P))/(P-1),'Using p-1 for the rescaling Jacobian')
    elif slug=='integral-equation':
        k=rat('k');ch=s.cosh(k);sh=s.sinh(k)
        pool=[((ch+1)/(k*k*ch),'Using the wrong constant when integrating sinh'),
              ((ch-1)/(k*k*sh),'Using a value boundary condition in place of a derivative boundary condition'),
              ((sh-1)/(k*k*ch),'Interchanging sinh and cosh in the primitive'),
              ((ch-1)/(k*k*(1+ch)),'Adding the inhomogeneous term to the boundary normalization')]
    elif slug=='convolution-laplace':
        n=p['n'];A=s.log(p['base']);L=(1-s.exp(-A))/A
        add(L**(n+1),'Including one extra box convolution')
        add(L**n/s.factorial(n),'Confusing a full product region with an ordered simplex')
    elif slug=='poisson-log-potential':
        A,B,C=p['a'],p['b'],p['c']
        add(pi/A*s.log(B*B+(2*A+C)**2),'Doubling the Poisson evaluation height')
        add(pi/A*s.log(2*B*B+(A+C)**2),'Double-counting the horizontal displacement in the squared modulus')
    elif slug=='jensen-radius':
        r=rat('r');add(8*pi*s.log(r),'Counting both the modulus square and full period twice')
        add(4*pi*s.log(r*r+1),'Replacing the mean logarithm by a logarithm of an averaged quadratic')
    elif slug=='fresnel':
        A=rat('a');add(s.sqrt(pi)/(4*s.sqrt(A)),'Taking the real component factor twice')
        add(a/2,'Applying the half-line factor twice')
    elif slug=='bessel-laplace':
        add(R(1,p['a']+p['b']),'Adding decay and oscillation scales linearly instead of quadratically')
    elif slug=='rodrigues-moment':
        n,k=p['n'],p['k'];add(a*s.factorial(2*k),'Forgetting the denominator in the transferred nth derivative')
        add(a*(k+n+R(1,2)),'Using the preceding Gamma denominator in the beta integral')
    elif slug=='concentration':
        P=p['p'];add(pi/(2*P*P),'Applying the substitution factor twice')
        add(pi/(2*(P+1)),'Using the wrong power in the arctangent primitive')
    elif slug=='binary-product':
        add(s.harmonic(2**(p['n']+1),evaluate=False),'Including the next dyadic factor')
    elif slug=='fejer-fourth':
        n=p['n'];add(2*pi*(n*n+2*sum(k*k for k in range(1,n+1))),'Including the forbidden endpoint frequency in the autocorrelation')
    elif slug=='scaled-frullani':
        P=p['p'];A,B=p['a'],p['b'];add(P*s.log(R(B,A)),'Reversing the power-substitution Jacobian')
    elif slug=='sech-fourier':
        q=p['q'];add(R(q,2*(q*q+1)),'Applying half-line evenness twice')
    # Additional authored misconceptions; insert before the Tuple guard in
    # authored_distractors, after the existing per-family pool construction.
    if slug=='bernoulli-product':
        m,n=p['m'],p['n']
        add(a/m,'Omitting the factor m from differentiating the first Bernoulli polynomial in integration by parts')
        add((m+n)*a,'Omitting the final primitive divisor m+n in the Bernoulli endpoint calculation')
    elif slug=='cauchy-convolution':
        A,B=s.Integer(p['a']),s.Integer(p['b'])
        pool[1]=(pool[1][0],'Counting both upper and lower half-plane residue sums for the same real integral')
        pool[2]=(pool[2][0],'Using the peak displacement in place of the Cauchy width in the normalization')
        add(a/2,'Keeping only the real part of one upper-half-plane pole contribution')
        add(pi/(2*B*(4*A*A+B*B)),'Using the full distance between the peaks where the half-separation belongs')
    elif slug=='moment-projection':
        m=p['m'];c=rat('c');mu=R(1,m+1);M2=R(1,2*m+1);V=M2-mu*mu
        pool[1]=(pool[1][0],'Using the squared mean of x^m in place of its variance')
        add(1+(c-mu)**2/M2,'Using the uncentered second moment in place of the variance of the centered basis')
        add((c-mu)**2/V,'Keeping only the centered moment component and omitting the required unit-mean energy')
        add(1+c*c/V,'Centering the basis but failing to center the prescribed moment')
    elif slug=='quadrature-defect':
        C=s.Integer(p['c']);G=R(p['A']+p['B'],2)
        add(G+C/360,'Applying the interval-rescaling Jacobian twice to the squared-node-polynomial correction')
        add(G+R(7,360)*C,'Omitting the cross term when squaring (x-1/2)^2-1/12')
    elif slug=='variational-energy':
        k=rat('k')
        add(1+k*k/3,'Mistaking the energy of the admissible linear trial function f(x)=x for the minimum')
        add((k*s.coth(k)-k*k/s.sinh(k)**2)/2,'Integrating only the potential energy of the minimizing hyperbolic function')
        add(s.Integer(1),'Using the sharp derivative-only Cauchy bound while dropping the nonzero potential energy')
    if isinstance(a,s.Tuple):return raw['wrong'],descriptions,{'rankingApplicable':False}
    unique=[]
    for value,why in pool:
        value=s.sympify(value)
        if not _different(value,a) or any(not _different(value,v) for v,_ in unique):continue
        unique.append((value,why))
    target=float(s.N(a,40))
    below=[v for v in unique if float(s.N(v[0],40))<target]
    above=[v for v in unique if float(s.N(v[0],40))>target]
    # Different substantive misconception subsets produce both under- and over-
    # estimates. The rank check is not used to certify their incorrectness.
    below.sort(key=lambda v:digest([slug,seed,s.srepr(v[0])]))
    above.sort(key=lambda v:digest([slug,seed,s.srepr(v[0])]))
    feasible=[k for k in range(4) if len(below)>=k and len(above)>=3-k]
    assert feasible,'Need three distinct authored misconceptions'
    want=feasible[seed%len(feasible)]
    chosen=below[:want]+above[:3-want]
    assert len(chosen)==3
    return [v for v,_ in chosen],[why for _,why in chosen],{'rankingApplicable':True,'correctAscendingRank':1+want,'feasibleAscendingRanks':[k+1 for k in feasible],'fixedRankRisk':len(feasible)==1,'authoredPoolSize':len(unique),'method':'Choose among authored misconceptions across all feasible ranks; numerical rank is an editorial audit, not mathematical proof.'}


# Coverage is deliberately stricter than the raw family count. These exclusions
# remain useful catalog items, but are not claimed as new independent Olympiad
# decisions in the priority target.
PRIORITY_EXCLUSIONS={
 'weighted-complement':'Related to the existing concealed-reflection construction.',
 'scaled-frullani':'Related to the existing Frullani cancellation construction.',
 'mixed-beta-log':'Related to the existing transformed beta-log construction.',
 'inverse-moment':'A useful inverse-function substitution, but too routine for the strict priority count.',
 'binomial-exponential':'A direct beta substitution; retained as useful fluency content, excluded from the strict count.',
 'floor-laplace':'A short staircase-tail application; excluded conservatively from the advanced priority count.',
 'jensen-radius':'Shares logarithmic Fourier-series recognition with log-fourier-coefficient.',
 'concentration':'Shares boundary rescaling with boundary-asymptotic; retain the distinct convergence lesson without double-counting the group.',
}
DIFFICULTY_DECISIONS={
 'reciprocal-quartic':'The decisive step is to average a reciprocal substitution before using a monotone whole-line substitution; direct partial fractions hides that structure.',
 'chebyshev-absolute':'The absolute polynomial must be converted into a folded sine; recognizing the recurrence and counting signed intervals is more useful than expansion.',
 'gamma-unit-average':'The sliding average is determined by a functional equation only up to a constant; reflection and log-sine symmetry recover the missing normalization.',
 'log-fourier-coefficient':'One must justify the logarithmic Fourier expansion and isolate a single harmonic; treating the logarithm pointwise gives no elementary primitive.',
 'arctan-parameter':'Differentiating an internal parameter creates a simpler rational integral; the initial value is required to recover the integral itself.',
 'gaussian-fourier':'A parameter derivative and integration by parts close an ODE; the half-line normalization and decaying exponential sign are essential.',
 'reciprocal-gaussian':'The singular exponential is closed under inversion only after parameter differentiation, giving an ODE with a Gaussian boundary value.',
 'sinc-overlap':'Two oscillations interact through frequency overlap; product-to-sum must preserve cancellation at zero before using Dirichlet integrals.',
 'thermal-derivative':'The differentiated geometric series exposes a zeta moment, and positivity is the justification for interchanging the infinite sum and improper integral.',
 'mellin-cyclotomic':'The endpoint restrictions and power substitution select the beta-reflection identity; choosing the wrong trigonometric branch gives a different value.',
 'cauchy-convolution':'The displaced double Cauchy kernel requires coordinating both upper-half-plane poles or recognizing a normalized Cauchy convolution.',
 'agm-parameter':'The invariant parameter is identified by a two-to-one elliptic substitution and then proved unique by monotonicity; a mere algebraic mean guess is insufficient.',
 'abel-recovery':'Applying the singular integral operator a second time turns its triangular kernel into the constant pi; this inversion avoids solving pointwise for f.',
 'boundary-asymptotic':'Direct pointwise convergence loses the mass; rescaling reveals a boundary layer and permits an exponential dominated-convergence bound.',
 'integral-equation':'Differentiating the nonlocal equation creates boundary conditions at opposite endpoints; the residual must be checked to recover the original equation.',
 'convolution-laplace':'A recursively defined density is recognized as convolution before its transform is taken, avoiding expansion of a growing piecewise polynomial.',
 'poisson-log-potential':'A logarithmic boundary function must be interpreted as a harmonic extension with its zero in the correct half-plane and the kernel normalization retained.',
 'fresnel':'The ordinary conditional integral is recovered from a complex Gaussian only after a consistent square-root branch and a uniform oscillatory-tail bound are supplied.',
 'bessel-laplace':'The special function is replaced by an angular average, with absolute Fubini and a rationalizing substitution doing the actual evaluation.',
 'rodrigues-moment':'Moving all derivatives by parts exposes endpoint zero multiplicities and a beta moment; orthogonality alone does not annihilate the off-diagonal moment.',
 'bernoulli-product':'Repeated integration by parts hinges on the sole Bernoulli endpoint jump; factorial and sign bookkeeping encode that exceptional boundary term.',
 'principal-value':'The ordinary integral and symmetric principal value have different existence conclusions; a transformed cutoff correction must be controlled.',
 'oscillatory-regularization':'A finite damping limit coexists with a nonconvergent cutoff primitive, so the task tests which limiting definition is actually being used.',
 'binary-product':'The exponents encode unique binary representations; finite telescoping converts an enormous apparent product into a harmonic sum.',
 'fejer-fourth':'A fourth power of an oscillatory quotient becomes an additive-pair count through autocorrelation and Parseval, rather than repeated trigonometric expansion.',
 'sech-fourier':'Evenness and an exponential substitution convert a Fourier integral into a beta integral with a complex parameter whose real part guarantees convergence.',
 'variational-energy':'The minimizing function is discovered from a boundary-value ODE, and a completed quadratic energy proves global minimality.',
 'moment-projection':'Two moment constraints require centering and projecting onto a polynomial subspace; the orthogonal residual proves a sharp attainable lower bound.',
 'quadrature-defect':'The given nodes suggest subtracting a squared orthogonal polynomial, which lowers degree and isolates the one coefficient missed by a two-node rule.',
 'rearrangement':'A distribution constraint fixes level-set sizes but not positions; layer cake and nested extreme sets give two attainable moment bounds.',
}

THEOREM_REFERENCES={
 'gamma-unit-average':['https://dlmf.nist.gov/5.5.E1','https://dlmf.nist.gov/5.5.E3'],
 'mixed-beta-log':['https://dlmf.nist.gov/5.12.E1','https://dlmf.nist.gov/5.5.E4'],
 'mellin-cyclotomic':['https://dlmf.nist.gov/5.12.E3','https://dlmf.nist.gov/5.5.E3'],
 'binomial-exponential':['https://dlmf.nist.gov/5.12.E1'],
 'agm-parameter':['https://dlmf.nist.gov/19.8.E1','https://dlmf.nist.gov/19.8.E4'],
 'abel-recovery':['https://dlmf.nist.gov/5.12.E1'],
 'bessel-laplace':['https://dlmf.nist.gov/3.5.E40'],
 'principal-value':['https://dlmf.nist.gov/5.5.E4'],
 'sech-fourier':['https://dlmf.nist.gov/5.12.E3','https://dlmf.nist.gov/5.5.E3'],
}
NOTATION_DEFINITIONS={
 'gamma-unit-average':r'\Gamma(s)=\int_0^\infty t^{s-1}e^{-t}\,dt\ (s>0).\quad ',
 'boundary-asymptotic':r'\Gamma(s)=\int_0^\infty t^{s-1}e^{-t}\,dt\ (s>0).\quad ',
 'thermal-derivative':r'\zeta(s)=\sum_{k=1}^\infty k^{-s}\ (s>1).\quad ',
 'bessel-laplace':r'J_0(z)=\sum_{k=0}^\infty\frac{(-1)^k(z/2)^{2k}}{(k!)^2}.\quad ',
}

def display_statement(statement):
    """Split givens and prose into short KaTeX lines without changing meaning."""
    pieces=re.split(r'(\\textnormal\{[^{}]*\}|\\quad\s*)',statement)
    lines=[]
    for piece in pieces:
        piece=piece.strip()
        if not piece or piece.startswith(r'\quad'):continue
        if piece.startswith(r'\textnormal{') and piece.endswith('}'):
            content=piece[len(r'\textnormal{'):-1]
            lines.extend(text(part) for part in textwrap.wrap(content,width=30))
        else:
            lines.append(piece)
    return statement if len(lines)<2 else r'\begin{gathered}'+r'\\'.join(lines)+r'\end{gathered}'

def make(slug,seed):
    if slug not in FAMILIES or type(seed) is not int or not 0<=seed<8:raise ValueError('Unsupported family/seed')
    f=FAMILIES[slug];exact_checks=[];check_token=EXACT_CHECK_LOG.set(exact_checks)
    try:raw=f['build'](seed)
    finally:EXACT_CHECK_LOG.reset(check_token)
    raw['statement']=NOTATION_DEFINITIONS.get(slug,'')+raw['statement']
    if slug=='agm-parameter':raw['statement']=raw['statement'].replace(r'}=\int',r'}\quad =\int')
    raw['statement']=display_statement(raw['statement'])
    a=raw['answer'];wrong,misconceptions,option_audit=authored_distractors(slug,raw,seed,f['distractorMisconceptions']);opts=[a]+wrong
    assert len(opts)==4
    assert all(_different(opts[j],opts[k]) for j in range(4) for k in range(j)), (slug,seed,opts)
    # Each record is reconstructed from trusted source; parameter/statement/answer tampering is not admitted.
    expression_record={'familyId':f['id'],'parameters':raw['parameters'],'statement':raw['statement']}
    semantic=digest(expression_record);record={
      'schemaVersion':2,'problemId':'cn3_'+semantic[:20],'problemRevision':1,
      'familyId':f['id'],'relatedIdeaGroupId':f['relatedIdeaGroupId'],'topic':'integration','difficulty':'olympiad',
      'structuralSignature':f['structuralSignature'],'primaryTechnique':f['primaryTechnique'],
      'alternativeTechniqueTags':f['alternativeTechniqueTags'],'techniqueTags':[f['primaryTechnique']]+f['alternativeTechniqueTags'],
      'reasoningDemand':f['reasoningDemand'],'prerequisites':f['prerequisites'],'parameters':{'seed':seed,**raw['parameters']},
      'statement':raw['statement'],'choices':[{'choiceId':'ch_'+digest(s.srepr(o))[:16],'math':tex(o)} for o in opts],
      'answerChoiceId':'ch_'+digest(s.srepr(a))[:16],'answerForm':raw['answerForm'],'solutionSteps':raw['steps'],
      'assumptions':f['certificate']['conditions'],'estimatedSolveSeconds':f['estimatedSolveSeconds'],
      'difficultyRationale':DIFFICULTY_DECISIONS.get(slug,PRIORITY_EXCLUSIONS.get(slug,''))+' Solve-time and difficulty estimates are editorial, not measured player calibration.',
      'priorityCoverageEligible':slug not in PRIORITY_EXCLUSIONS,
      'priorityCoverageExclusionReason':PRIORITY_EXCLUSIONS.get(slug),
      'semanticHash':semantic,'templateVersion':VERSION,
      'verification':{'status':'certificate-checked','route':f['certificate']['route'],'certificateId':f['certificate']['id'],
        'proofSteps':f['certificate']['proof'],
        'automatedChecks':['executed '+str(len(exact_checks))+' exact symbolic identity checks','exact pairwise choice non-equivalence','deterministic canonical reconstruction'],
        'exactChecks':exact_checks,'analyticCertificateObligations':raw['checks'],
        'verificationSeparation':'Exact checks record only executed symbolic identities. Proof steps and analytic obligations require the stated classical theorems and hypotheses; they are explicit mathematical certificates, not automated proofs of measure theory or complex analysis.',
        'answerExpression':s.srepr(a),'choiceExpressions':[s.srepr(o) for o in opts],
        'symbolicEngine':'SymPy '+s.__version__,'numericalAgreementUsedAsProof':False,'formalProofAssistantChecked':False,'humanReviewed':False},
      'provenance':{'kind':'original','intendedUse':'independent-original','license':'LicenseRef-CalculusNinja-Original',
        'attribution':'Independently authored Calculus Ninja exercise about classical mathematics. AI-assisted authored proof and code; exact automated checks; no human-review claim.',
        'sourceItem':None,'sourceTextReused':False,'sourceReferencePurpose':'Theorem/method reference only, never a content reuse license.',
        'theoremReferenceURLs':THEOREM_REFERENCES.get(slug,[]),'referenceVersion':'DLMF1.2.8(2026-09-15) where listed; accessed2026-11-03','copiedSourceTextOrAssets':False},
      'editorialNotes':f['editorialNotes'],'distractorMisconceptions':misconceptions,'optionAudit':option_audit}
    record['pedagogy']={
      'constructionId':f['id'],'relatedIdeaGroupId':f['relatedIdeaGroupId'],
      'structuralSignature':f['structuralSignature'],'primaryTechnique':f['primaryTechnique'],
      'alternativeTechniques':f['alternativeTechniqueTags'],'prerequisites':f['prerequisites'],
      'reasoningDemand':f['reasoningDemand'],'answerForm':raw['answerForm'],
      'difficultyRationale':record['difficultyRationale'],
      'sourceRecordIds':['calculus-ninja-independent-integration-m3'],'responseFormat':'multiple-choice'}
    record['contentHash']=digest(record)
    return record

def verify(record):
    slug=record.get('familyId','').removeprefix('io3-');seed=record.get('parameters',{}).get('seed')
    if record!=make(slug,seed):raise ValueError('Record differs from reconstructed and checked mathematical asset')
    return True

def build(family_id,instance_index):
    return make(family_id.removeprefix('io3-'),instance_index)

def all_candidates():
    return [make(slug,seed) for slug in FAMILIES for seed in range(8)]

def catalog():
    return [{k:v for k,v in f.items() if k!='build'} for f in FAMILIES.values()]

def generate(out):
    out.mkdir(parents=True,exist_ok=True);rows=[];counts={};quarantine=[]
    for slug,f in FAMILIES.items():
        for i in range(8):
            try:rows.append(make(slug,i));counts[f['id']]=counts.get(f['id'],0)+1
            except Exception as e:quarantine.append({'familyId':f['id'],'seed':i,'reason':str(e)})
        print(f['id'],counts.get(f['id'],0),flush=True)
    catalog={k:{kk:vv for kk,vv in f.items() if kk!='build'} for k,f in FAMILIES.items()}
    report={'version':VERSION,'generatedCount':len(rows),'familyCount':len(counts),'completeEightItemFamilies':sum(n==8 for n in counts.values()),
      'distinctRelatedIdeaGroups':len({p['relatedIdeaGroupId'] for p in rows}),'conservativeNewPriorityFamilies':len({p['familyId'] for p in rows if p['priorityCoverageEligible']}),'priorityCoverageExclusions':PRIORITY_EXCLUSIONS,'families':counts,'quarantined':quarantine,
      'verificationScope':'Explicit classical analytic certificates with exact algebraic/recurrence/residue checks; not formal proof-assistant verification. All source candidates reconstructed; no human review.',
      'importedCount':0,'activeCount':0,'humanReviewedCount':0,'modelCalls':0}
    (out/'constructions.json').write_text(json.dumps({'version':VERSION,'families':catalog,'report':report},indent=2)+'\n')
    (out/'candidates.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
    (out/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path(__file__).parent);args=parser.parse_args()
    print(json.dumps(generate(args.out),indent=2))
