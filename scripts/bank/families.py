"""Original template definitions. Kernels are code-owned SymPy objects, never parsed TeX.
Each published instance varies three real coefficients, not wording or option order.
The independent verifier applies the declared calculus operation to each basis.
"""
import sympy as s
x,y,t,n = s.symbols('x y t n', real=True)
a,b,c = s.symbols('a b c', positive=True, integer=True)
FAMILIES=[]

def add(id,topic,level,kind,kernels,expected=None,**kw):
    FAMILIES.append(dict(id=id,topic=topic,level=level,kind=kind,kernels=list(map(s.sympify,kernels)),expected=None if expected is None else list(map(s.sympify,expected)),**kw))

def integral(id,level,kernels,expected,lo=0,hi=1,tags=('definite-integral',)):
    add(id,'integration',level,'integral',kernels,expected,lo=s.sympify(lo),hi=s.sympify(hi),tags=list(tags))

integral('polynomial-area','easy',[x,x**2,x**3],[s.Rational(1,2),s.Rational(1,3),s.Rational(1,4)],tags=['power-rule'])
integral('exponential-area','easy',[s.exp(x),s.exp(2*x),s.exp(3*x)],[s.E-1,(s.exp(2)-1)/2,(s.exp(3)-1)/3],tags=['exponentials'])
integral('trig-area','easy',[s.sin(x),s.cos(x),s.sin(2*x)],[1,1,1],hi=s.pi/2,tags=['trigonometric-identities'])
integral('polynomial-exponential','medium',[x*s.exp(x),x**2*s.exp(x),x**3*s.exp(x)],[1,s.E-2,6-2*s.E],tags=['integration-by-parts'])
integral('quadratic-substitution','medium',[2*x/(1+x**2),4*x/(1+x**2)**2,6*x/(1+x**2)**3],[s.log(2),1,s.Rational(9,8)],tags=['substitution'])
integral('rational-decomposition','medium',[1/((x+1)*(x+2)),1/((x+1)*(x+3)),1/((x+2)*(x+4))],[s.log(s.Rational(4,3)),s.log(s.Rational(3,2))/2,s.log(s.Rational(6,5))/2],tags=['partial-fractions'])
integral('log-moments','hard',[s.log(x),x*s.log(x),x**2*s.log(x)],[-1,-s.Rational(1,4),-s.Rational(1,9)],tags=['improper-integral','integration-by-parts'])
integral('trig-products','hard',[s.sin(x)**2*s.cos(x)**2,s.sin(x)**4*s.cos(x)**2,s.sin(x)**6*s.cos(x)**2],[s.pi/16,s.pi/32,5*s.pi/256],hi=s.pi/2,tags=['trigonometric-identities','symmetry'])
integral('improper-rational','hard',[1/(1+x)**2,x/(1+x)**3,x**2/(1+x)**4],[1,s.Rational(1,2),s.Rational(1,3)],hi=s.oo,tags=['improper-integral','substitution'])

def derivative(id,level,kernels,expected=None,point=1,order=1,tags=('derivatives',)):
    add(id,'differentiation',level,'derivative',kernels,expected,point=s.sympify(point),order=order,tags=list(tags))
derivative('polynomial-slope','easy',[x**2,x**3,x**4],[2,3,4],tags=['power-rule'])
derivative('trig-slope','easy',[s.sin(x),s.cos(x),s.sin(2*x)],[1,0,2],point=0,tags=['trigonometric-derivatives'])
derivative('exp-log-slope','easy',[s.exp(x),s.log(x),s.sqrt(x)],[s.E,1,s.Rational(1,2)],tags=['chain-rule'])
derivative('product-rule','medium',[x*s.exp(x),x**2*s.log(x),x*s.sin(x)],tags=['product-rule'])
derivative('quotient-rule','medium',[x/(1+x**2),s.exp(x)/(1+x),s.log(x)/(1+x)],tags=['quotient-rule'])
derivative('nested-chain','medium',[s.exp(x**2),s.log(1+x**2),s.sin(x**2)],tags=['chain-rule'])
derivative('fourth-derivative','hard',[x**3*s.exp(x),x**2*s.cos(x),s.log(1+x)],point=0,order=4,tags=['leibniz-rule'])
derivative('log-differentiation','hard',[x**x,x**(x**2),(1+x)**x],tags=['logarithmic-differentiation'])
derivative('parametric-curvature','hard',[s.sin(x)**3,s.cos(x)**3,s.exp(x)*s.cos(x)],point=s.pi/4,order=3,tags=['higher-derivatives','product-rule'])

def limit(id,level,kernels,expected,point=0,tags=('limits',)):
    add(id,'limits',level,'limit',kernels,expected,point=s.sympify(point),tags=list(tags))
limit('polynomial-continuity','easy',[x**2,x**3,x**4],[1,1,1],point=1,tags=['continuity'])
limit('removable-factor','easy',[(x**2-1)/(x-1),(x**3-1)/(x-1),(x**4-1)/(x-1)],[2,3,4],point=1,tags=['factorization'])
limit('standard-trig-limits','easy',[s.sin(x)/x,s.sin(2*x)/x,s.sin(3*x)/x],[1,2,3],tags=['standard-limits'])
limit('exponential-cancellation','medium',[(s.exp(x)-1)/x,(s.exp(2*x)-1)/x,(s.exp(3*x)-1)/x],[1,2,3],tags=['lhopital'])
limit('rational-at-infinity','medium',[(x**2+1)/(2*x**2+3),(x**3-1)/(3*x**3+x),(x**4+x)/(4*x**4+1)],[s.Rational(1,2),s.Rational(1,3),s.Rational(1,4)],point=s.oo,tags=['dominant-balance'])
limit('logarithmic-cancellation','medium',[s.log(1+x)/x,s.log(1+2*x)/x,s.log(1+3*x)/x],[1,2,3],tags=['lhopital'])
limit('third-order-exponential','hard',[(s.exp(x)-1-x-x**2/2)/x**3,(s.exp(2*x)-1-2*x-2*x**2)/x**3,(s.exp(3*x)-1-3*x-s.Rational(9,2)*x**2)/x**3],[s.Rational(1,6),s.Rational(4,3),s.Rational(9,2)],tags=['taylor-remainder'])
limit('trig-cancellation','hard',[(x-s.sin(x))/x**3,(s.tan(x)-x)/x**3,(s.sin(x)-x*s.cos(x))/x**3],[s.Rational(1,6),s.Rational(1,3),s.Rational(1,3)],tags=['taylor-remainder'])
limit('radical-cancellation','hard',[(s.sqrt(1+x)-1-x/2)/x**2,((1+x)**s.Rational(1,3)-1-x/3)/x**2,((1+x)**s.Rational(1,4)-1-x/4)/x**2],[-s.Rational(1,8),-s.Rational(1,9),-s.Rational(3,32)],tags=['binomial-series'])

def series(id,level,kernels,expected,start=0,tags=('series',)):
    add(id,'series',level,'series',kernels,expected,start=start,tags=list(tags))
series('geometric-series','easy',[s.Rational(1,2)**n,s.Rational(1,3)**n,s.Rational(1,4)**n],[2,s.Rational(3,2),s.Rational(4,3)],tags=['geometric-series'])
series('telescoping-series','easy',[1/((n+1)*(n+2)),1/((n+2)*(n+3)),1/((n+3)*(n+4))],[1,s.Rational(1,2),s.Rational(1,3)],tags=['telescoping'])
series('even-geometric-series','easy',[s.Rational(1,2)**(2*n),s.Rational(1,3)**(2*n),s.Rational(1,4)**(2*n)],[s.Rational(4,3),s.Rational(9,8),s.Rational(16,15)],tags=['geometric-series'])
series('weighted-geometric','medium',[n/2**n,n/3**n,n/4**n],[2,s.Rational(3,4),s.Rational(4,9)],tags=['termwise-differentiation'])
series('exponential-series','medium',[1/s.factorial(n),2**n/s.factorial(n),3**n/s.factorial(n)],[s.E,s.exp(2),s.exp(3)],tags=['taylor-series'])
series('alternating-log-series','medium',[(-1)**(n+1)/n,(-1)**(n+1)/(n*2**n),(-1)**(n+1)/(n*3**n)],[s.log(2),s.log(s.Rational(3,2)),s.log(s.Rational(4,3))],start=1,tags=['alternating-series','endpoint-convergence'])
series('quadratic-geometric','hard',[n**2/2**n,n**2/3**n,n**2/4**n],[6,s.Rational(3,2),s.Rational(20,27)],tags=['termwise-differentiation'])
series('cubic-telescoping','hard',[1/((n+1)*(n+2)*(n+3)),1/((n+2)*(n+3)*(n+4)),1/((n+3)*(n+4)*(n+5))],[s.Rational(1,4),s.Rational(1,12),s.Rational(1,24)],tags=['partial-fractions','telescoping'])
series('zeta-even','hard',[1/n**2,1/n**4,1/n**6],[s.pi**2/6,s.pi**4/90,s.pi**6/945],start=1,tags=['fourier-series','absolute-convergence'])

def ode(id,level,kernels,operator,point=1,initial=0,tags=('differential-equations',)):
    add(id,'differential equations',level,'ode',kernels,None,operator=list(map(s.sympify,operator)),point=s.sympify(point),initial=s.sympify(initial),tags=list(tags))
ode('polynomial-initial-value','easy',[x,x**2,x**3],[0,1],tags=['initial-value','power-rule'])
ode('exponential-initial-value','easy',[s.exp(x),s.exp(2*x),s.exp(3*x)],[0,1],tags=['initial-value','exponentials'])
ode('trig-initial-value','easy',[s.sin(x),s.cos(x),s.sin(2*x)],[0,1],point=s.pi/2,tags=['initial-value','trigonometric-identities'])
ode('linear-integrating-factor','medium',[x*s.exp(x),x**2*s.exp(x),x**3*s.exp(x)],[-1,1],tags=['integrating-factor'])
ode('variable-integrating-factor','medium',[s.exp(-x**2),x*s.exp(-x**2),x**2*s.exp(-x**2)],[2*x,1],tags=['integrating-factor','substitution'])
ode('linear-trig-forcing','medium',[s.sin(x),s.cos(2*x),s.sin(3*x)],[1,1],point=s.pi/4,tags=['integrating-factor','integration-by-parts'])
ode('resonant-second-order','hard',[x*s.exp(x),x**2*s.exp(x),x**3*s.exp(x)],[1,-2,1],tags=['resonance','linear-ode'])
ode('oscillator-resonance','hard',[x*s.sin(x),x*s.cos(x),x**2*s.sin(x)],[1,0,1],point=s.pi/2,tags=['resonance','linear-ode'])
ode('euler-cauchy','hard',[x**2,x**2*s.log(x),x**2*s.log(x)**2],[4,-3*x,x**2],initial=1,point=2,tags=['euler-cauchy','substitution'])

def multi(id,level,kind,kernels,expected=None,tags=('multivariable',),**kw):
    add(id,'multivariable',level,kind,kernels,expected,tags=list(tags),**kw)
multi('partial-x','easy','partial',[x**2*y,x*y**2,x**3*y**2],[2,1,3],dx=1,dy=0,px=1,py=1,tags=['partial-derivatives'])
multi('partial-y','easy','partial',[x*y**2,x**2*y**3,x*y**4],[2,3,4],dx=0,dy=1,px=1,py=1,tags=['partial-derivatives'])
multi('rectangle-area','easy','double',[x,y,x*y],[s.Rational(1,2),s.Rational(1,2),s.Rational(1,4)],yhi=1,tags=['iterated-integrals'])
multi('mixed-partials','medium','partial',[x**2*y**3,s.exp(x*y),s.log(1+x*y)],dx=1,dy=1,px=1,py=1,tags=['mixed-partials'])
multi('triangle-integral','medium','double',[x*y,x**2*y,x*y**2],[s.Rational(1,8),s.Rational(1,10),s.Rational(1,15)],yhi=x,tags=['iterated-integrals','nonrectangular-domain'])
multi('laplacian','medium','laplacian',[x**2*y**2,s.exp(x)*s.cos(y),x**4+y**4],[4,0,24],px=1,py=1,tags=['laplacian'])
multi('high-mixed-partials','hard','partial',[s.exp(x*y),s.log(1+x+y),s.sin(x)*s.cos(y)],dx=2,dy=2,px=0,py=0,tags=['higher-partials'])
multi('curved-domain-integral','hard','double',[x*y,x**2*y**2,x**3*y],[s.Rational(1,12),s.Rational(1,27),s.Rational(1,16)],yhi=x**2,tags=['iterated-integrals','nonrectangular-domain'])
multi('laplacian-products','hard','laplacian',[s.exp(x*y),s.log(1+x**2+y**2),(x*y)**3],px=1,py=1,tags=['laplacian','chain-rule'])

# Olympiad definitions are appended in olympiad.py; operations remain independently verified.
from olympiad import add_olympiad
add_olympiad(add,integral,derivative,limit,series,ode,multi,x,y,n,s)
assert len(FAMILIES)==72
