"""Independent checks of intermediate identities used by the replacement recipes.

This script does not import original builders. Exact identities below were encoded
from the displayed replacement routes; analytic theorem applications remain AI
mathematical/editorial certificates rather than formal proofs.
"""
from pathlib import Path
import importlib.util,json,hashlib,sys
from reproduction_paths import source_artifact
import sympy as S
R=S.Rational; pi=S.pi
x,y,z,t,u,v,w,a,b,c,d,h=S.symbols('x y z t u v w a b c d h',real=True)
p=S.symbols('p',positive=True); n,k,j=S.symbols('n k j',integer=True,positive=True)
ROOT=Path(__file__).parent

def check(name,lhs,rhs=0):
 lhs=S.sympify(lhs);rhs=S.sympify(rhs)
 residual=S.simplify(S.trigsimp(S.expand_func(lhs-rhs)))
 if residual!=0:residual=S.simplify(S.expand_trig(residual).rewrite(S.exp))
 if residual!=0:raise AssertionError((name,str(residual)))
 return {'name':name,'method':'exact-symbolic-identity','lhs':S.sstr(lhs),'rhs':S.sstr(rhs),'residual':'0'}
def truth(name,condition,evidence):
 if condition is not True and condition!=S.true:raise AssertionError((name,condition))
 return {'name':name,'method':'exact-discrete-or-sign-check','evidence':evidence,'passed':True}
def ode(m,q,record):
 out=[]
 def C(name,l,r=0):out.append(check(name,l,r))
 def IVP(f,rhs,ics,order=1):
  C('displayed solution satisfies differential equation',S.diff(f,t,order),rhs(f))
  for order,point,value in ics:C('initial/boundary datum derivative '+str(order)+' at '+str(point),S.diff(f,t,order).subs(t,point),value)
 if q=='field-slope':C('field evaluation from time times state plus time squared',(t*y+t*t).subs({t:m,y:2}),m*m+2*m)
 elif q=='rate-identification':C('differentiate nonzero exponential',S.diff(S.exp(m*t),t)/S.exp(m*t),m)
 elif q=='phase-line-stability':
  C('factor vector field',y*y-m*m,(y-m)*(y+m));C('attracting equilibrium linearization',S.diff(y*y-m*m,y).subs(y,-m),-2*m)
  out.append(truth('neighbor signs point toward negative equilibrium',( (-m-1)**2-m*m>0) and ((-m+1)**2-m*m<0),'probe displacement 1 is inside the simple-root neighborhoods since m>=4'))
 elif q=='euler-step':C('one forward Euler step',m+R(1,m)*(0-m),m-1)
 elif q=='primitive-initial-value':IVP(1+m*t**3/3,lambda f:m*t*t,[(0,0,1)])
 elif q=='doubling-data':
  f=m*2**t;C('exponential constant-rate equation',S.diff(f,t),S.log(2)*f);C('one-day doubling datum',f.subs(t,1),2*m);C('three-day value',f.subs(t,3),8*m)
 elif q=='cooling-limit':
  f=m+10-10*S.exp(-2*t);IVP(f,lambda f:-2*(f-m-10),[(0,0,m)]);C('cooling asymptote',S.limit(f,t,S.oo),m+10)
 elif q=='mixing-inflow':C('rate balance with inflow concentration and outgoing concentration',2*R(3,2)-2*m/(m+2),3-2*m/(m+2))
 elif q=='constant-acceleration':IVP(t+m*t*t/2,lambda f:m,[(0,0,0),(1,0,1)],2)
 elif q=='equation-order':
  # The original question explicitly gives the largest derivative order numerically.
  out.append(truth('concrete highest order is visible in the original statement',('('+str(m-2)+')') in record['statement'] or ('{'+str(m-2)+'}') in record['statement'],'highest derivative order '+str(m-2)+'; nonlinear powers of other derivatives do not alter order'))
 elif q=='oscillator-initial-data':IVP(m*S.cos(t)+(m+1)*S.sin(t),lambda f:-f,[(0,0,m),(1,0,m+1)],2)
 elif q=='transfer-conservation':
  C('sum of transfer vector field is zero',(-2*u+v)+(2*u-v));C('remaining component from conserved total',m+3-(2*m+21)/10,(8*m+9)/10)
 elif q=='logistic-hitting':
  f=1/(1+m*S.exp(-t));IVP(f,lambda f:f*(1-f),[(0,0,1/(m+1))]);C('log-odds derivative',S.diff(S.log(f/(1-f)),t),1);C('hitting target',f.subs(t,S.log(m)),R(1,2))
 elif q=='finite-blowup':IVP(1/(m-t),lambda f:f*f,[(0,0,1/m)]);C('reciprocal derivative',S.diff(m-t,t),-1)
 elif q=='variable-integrating-factor':
  f=(t**(m+2)-1)/((m+2)*t);IVP(f,lambda f:t**m-f/t,[(0,1,0)]);C('integrating-factor product derivative',S.diff(t*f,t),t**(m+1))
 elif q=='exact-curve':
  P=t*t+t*y+y*y;C('potential time derivative',S.diff(P,t),2*t+y);C('potential state derivative',S.diff(P,y),t+2*y);C('potential value at both endpoints',P.subs({t:1,y:m}),P.subs({t:S.sqrt(m*m+m+1),y:0}))
 elif q=='bernoulli-reciprocal':
  f=1/(t+1-(m+1)*S.exp(t));IVP(f,lambda f:t*f*f-f,[(0,0,-1/m)]);C('reciprocal linearization',S.diff(1/f,t)-1/f,-t)
 elif q=='homogeneous-ratio':
  f=-t/(m+S.log(t));IVP(f,lambda f:f/t+(f/t)**2,[(0,1,-1/m)]);C('ratio-separated identity',t*S.diff(f/t,t),(f/t)**2)
 elif q=='harvest-bifurcation':C('complete population square',y*(m-y),m*m/4-(y-m/2)**2);C('maximizing positive equilibrium',(y*(m-y)).subs(y,m/2),m*m/4)
 elif q=='distinct-characteristic-roots':IVP(S.exp(m*t)-S.exp(t),lambda f:(m+1)*S.diff(f,t)-m*f,[(0,0,0),(1,0,m-1)],2)
 elif q=='resonant-forcing':
  f=(S.sin(t)-t*S.cos(t))/2;IVP(f,lambda f:S.sin(t)-f,[(0,0,0),(1,0,0)],2);C('resonant particular forcing',S.diff(-t*S.cos(t)/2,t,2)-t*S.cos(t)/2,S.sin(t))
 elif q=='critical-damping':C('critical characteristic repeated root',z*z+2*m*z+m*m,(z+m)**2)
 elif q=='repeated-root':IVP(t*S.exp(m*t),lambda f:2*m*S.diff(f,t)-m*m*f,[(0,0,0),(1,0,1)],2)
 elif q=='periodic-amplitude':
  A=m/(m*m+1);B=1/(m*m+1);f=A*S.cos(t)+B*S.sin(t);C('periodic forced equation',S.diff(f,t)+m*f,S.cos(t));C('amplitude from two quadratures',A*A+B*B,1/(m*m+1))
 elif q=='riccati-particular':
  f=t+1/(m-t);IVP(f,lambda f:f*f-2*t*f+t*t+1,[(0,0,1/m)]);C('subtracted equation',S.diff(f-t,t),(f-t)**2)
 elif q=='nonlinear-energy-speed':
  E=z*z+y**4;C('energy derivative along flow',S.diff(E,y)*z+S.diff(E,z)*(-2*y**3));C('energy at rest datum',E.subs({y:m,z:0}),m**4);C('turning endpoint is a simple energy zero',S.diff(m**4-y**4,y).subs(y,m),-4*m**3)
 elif q=='euler-cauchy-resonance':
  f=t*t*S.log(t)**2/2;IVP(f,lambda f:(t*t+3*t*S.diff(f,t)-4*f)/t**2,[(0,1,0),(1,1,0)],2)
  W=S.Function('W');g=t*t*W(S.log(t));C('full transformed Euler operator',t*t*S.diff(g,t,2)-3*t*S.diff(g,t)+4*g,t*t*S.Subs(S.diff(W(x),x,2),x,S.log(t)))
 elif q=='variable-second-order-basis':
  f=m*(t+1-S.exp(t-1));IVP(f,lambda f:((t+1)*S.diff(f,t)-f)/t,[(0,1,m),(1,1,0)],2);C('Wronskian in displayed affine-then-exponential order',(t+1)*S.exp(t)-S.exp(t),t*S.exp(t))
 elif q=='remove-first-derivative':
  f=S.exp(-t*t/2)*S.cos(m*t);IVP(f,lambda f:-2*t*S.diff(f,t)-(t*t+1+m*m)*f,[(0,0,1),(1,0,0)],2)
  U=S.Function('U')(t);g=S.exp(-t*t/2)*U;C('Gaussian conjugation operator',(S.diff(g,t,2)+2*t*S.diff(g,t)+(t*t+1+m*m)*g)*S.exp(t*t/2),S.diff(U,t,2)+m*m*U)
 elif q=='step-forcing':IVP(m*(1-S.cos(t-1)),lambda f:m-f,[(0,1,0),(1,1,0)],2)
 elif q=='impulse-jump':IVP(m*(t-1)*S.exp(-(t-1)),lambda f:-2*S.diff(f,t)-f,[(0,1,0),(1,1,m)],2)
 elif q=='rotating-linear-system':
  U=S.exp(-t)*S.cos(m*t);V=S.exp(-t)*S.sin(m*t);C('first component residual',S.diff(U,t),-U-m*V);C('second component residual',S.diff(V,t),m*U-V);C('initial vector',U.subs(t,0)+S.I*V.subs(t,0),1)
 elif q=='jordan-system':
  F=S.exp(m*t)*S.Matrix([t*t/2,t,1]);A=S.Matrix([[m,1,0],[0,m,1],[0,0,m]])
  for idx in range(3):C('triangular system component '+str(idx+1),S.diff(F[idx],t),(A*F)[idx]);C('triangular initial component '+str(idx+1),F[idx].subs(t,0),int(idx==2))
 elif q=='linear-stability-bound':
  # Source matrix [[a,1],[-m,a-2m]].
  A=S.Matrix([[a,1],[-m,a-2*m]]);C('trace',S.trace(A),2*a-2*m);C('determinant',A.det(),a*a-2*m*a+m);C('determinant at threshold',A.det().subs(a,m-S.sqrt(m*m-m)))
 elif q=='mixed-boundary-spectrum':
  lam=pi*pi/(4*m*m);f=S.sin(pi*t/(2*m));IVP(f,lambda f:-lam*f,[(0,0,0),(1,m,0)],2)
 elif q=='wronskian-transport':
  C('Wronskian ODE for arbitrary coefficient',y*(-m/t*w-a*z)-(-m/t*v-a*y)*z,-m/t*(y*w-v*z));IVP(t**(-m),lambda f:-m/t*f,[(0,1,1)])
 elif q=='quartic-period':
  E=z*z/2+m*m*y**4/4;C('quartic period energy derivative',S.diff(E,y)*z+S.diff(E,z)*(-m*m*y**3));C('quarter-arc beta substitution',S.diff(p**R(1,4),p)/S.sqrt(1-p),p**R(-3,4)*(1-p)**R(-1,2)/4);C('turning energy simple zero',S.diff(1-y**4,y).subs(y,1),-4)
 elif q=='power-coordinate-lifetime':
  C('positive-coordinate chain cancellation',R(3,2)*S.sqrt(p)*(-z*z/(2*p)-R(2,3)*m*m*p)+R(3,4)*z*z/S.sqrt(p),-m*m*p**R(3,2));IVP(S.cos(m*t),lambda f:-m*m*f,[(0,0,1),(1,0,0)],2);C('first endpoint transformed zero',S.cos(m*t).subs(t,pi/(2*m)))
 elif q=='pinney-energy':
  E=z*z+y*y+y**-2;C('inverse-cube conserved energy derivative',S.diff(E,y)*z+S.diff(E,z)*(-y+y**-3));f=m*m*S.cos(t)**2+m**-2*S.sin(t)**2;C('squared coordinate equation',S.diff(f,t,2)+4*f,2*(m*m+m**-2));C('positive square root residual cleared exactly',2*f*S.diff(f,t,2)-S.diff(f,t)**2+4*f*f,4);C('initial square and velocity',f.subs(t,0)+S.I*S.diff(f,t).subs(t,0),m*m)
 elif q=='switched-riccati':
  g=z/(1+z*t);IVP(g,lambda f:-f*f,[(0,0,z)]);M=S.Matrix([[1,1],[1,2]])**int(m);C('Fibonacci numerator finite matrix power',M[0,1],S.fibonacci(2*m));C('Fibonacci denominator finite matrix power',M[1,1],S.fibonacci(2*m+1))
 elif q=='periodic-product-average':
  Fu=u*(m-2*v);Fv=v*(3*u-4);C('average identity as total derivatives',m*S.cancel(Fv/v)/6-Fu/2,u*v-2*m/3)
 elif q=='periodic-floquet-multiplier':
  F=(m+S.sin(t))*y-y*y;C('variation vector field',S.diff(F,y),m+S.sin(t)-2*y);C('variation average elimination',S.diff(F,y),-(m+S.sin(t))+2*S.cancel(F/y));C('full-period growth average',S.integrate(m+S.sin(t),(t,0,2*pi)),2*pi*m)
 elif q=='resonant-boundary-compatibility':
  C('forcing projection',S.integrate(t*S.sin(m*t),(t,0,pi)),-pi*(-1)**m/m);C('mode squared norm',S.integrate(S.sin(m*t)**2,(t,0,pi)),pi/2);f=t/m**2-c*t*S.cos(m*t)/(2*m);C('sufficiency witness equation',S.diff(f,t,2)+m*m*f,t+c*S.sin(m*t));C('left boundary',f.subs(t,0));C('right boundary under compatibility',f.subs({t:pi,c:2*(-1)**m/m}))
 elif q=='sharp-lifetime-comparison':C('angle derivative',S.diff(S.atan(y/m),y),m/(m*m+y*y));IVP(m*S.tan(m*t),lambda f:f*f+m*m,[(0,0,0)])
 elif q=='nonlinear-radial-asymptotic':
  U=-u-m*v-u*(u*u+v*v);V=m*u-v-v*(u*u+v*v);C('radial Lie derivative',2*u*U+2*v*V,-2*(u*u+v*v)*(1+u*u+v*v));f=m*m*S.exp(-2*t)/(1+m*m*(1-S.exp(-2*t)));IVP(f,lambda f:-2*f*(1+f),[(0,0,m*m)]);C('renormalized energy limit',S.limit(S.exp(2*t)*f,t,S.oo),m*m/(1+m*m))
 elif q=='ground-state-variance':
  C('square completion differs by exact derivative',(z+m*t*y)**2-(z*z+m*m*t*t*y*y-m*y*y),m*(y*y+2*t*y*z));f=S.exp(-m*t*t/2);C('Gaussian minimizing eigenfunction',-S.diff(f,t,2)+m*m*t*t*f,m*f);C('Gaussian moment derivative',S.diff(t*f*f,t),(1-2*m*t*t)*f*f)
 elif q=='schwarzian-ivp':
  f=S.tanh(m*t);g=-2*m*S.tanh(m*t);C('Riccati reduced equation',S.diff(g,t)-g*g/2,-2*m*m);C('logarithmic derivative recovery',S.diff(f,t,2)/S.diff(f,t),g);C('third-order original residual',S.diff(f,t,3)/S.diff(f,t)-R(3,2)*(S.diff(f,t,2)/S.diff(f,t))**2,-2*m*m)
  for order,value in [(0,0),(1,m),(2,0)]:C('Schwarzian datum '+str(order),S.diff(f,t,order).subs(t,0),value)
 elif q=='darboux-oscillator':
  Z=S.Function('Z')(t);AZ=S.diff(Z,t)-S.tanh(t)*Z;C('full Darboux operator on arbitrary smooth function',S.diff(AZ,t,2)+(m*m+2/S.cosh(t)**2)*AZ,S.diff(S.diff(Z,t,2)+m*m*Z,t)-S.tanh(t)*(S.diff(Z,t,2)+m*m*Z));f=m*S.sin(m*t)+S.tanh(t)*S.cos(m*t);IVP(f,lambda f:-(m*m+2/S.cosh(t)**2)*f,[(0,0,0),(1,0,m*m+1)],2)
 else:raise KeyError(q)
 return out
def multivariable(m,q,record):
 out=[]
 def C(name,l,r=0):out.append(check(name,l,r))
 if q=='partial-hold-fixed':C('first partial holding second input fixed',S.diff(x*x*y+y**3,x),2*x*y);C('gradient component at point',(2*x*y).subs({x:m,y:1}),2*m)
 elif q=='mixed-partial':C('successive mixed derivative',S.diff(x*x*y**m,x,y),2*m*x*y**(m-1))
 elif q=='directional-unit':C('direction unit norm',R(3,5)**2+R(4,5)**2,1);C('directional derivative by gradient',S.diff(x*x+y*y,x).subs({x:m,y:0})*R(3,5)+S.diff(x*x+y*y,y).subs({x:m,y:0})*R(4,5),6*m/5)
 elif q=='tangent-plane':C('normal gradient at point',sum(S.diff(x*x+y*y+z*z,var).subs({x:1,y:1,z:m})*(var-value) for var,value in [(x,1),(y,1),(z,m)]),2*(x+y+m*z-m*m-2))
 elif q=='linearization-two-inputs':C('linear terms from exact product expansion',(m+h)*(2+h)-h*h,2*m+(m+2)*h)
 elif q=='rectangle-integral':C('inner integration',S.integrate(x+y,(y,0,m)),m*x+m*m/2);C('outer integration',S.integrate(m*x+m*m/2,(x,0,1)),m*(m+1)/2)
 elif q=='triangular-region':C('inner triangular height',S.integrate(1,(y,0,m-x)),m-x);C('area antiderivative and endpoints',S.integrate(m-x,(x,0,m)),m*m/2)
 elif q=='polar-area':C('polar Jacobian',S.Matrix([u*S.cos(v),u*S.sin(v)]).jacobian([u,v]).det(),u);C('polar disk integral',S.integrate(2*pi*u,(u,0,m)),pi*m*m)
 elif q=='chain-curve':C('chain curve composition derivative',S.diff(t*t+t**4,t),2*t+4*t**3)
 elif q=='divergence':C('sum diagonal field partials',S.diff(x*x,x)+S.diff(x*y,y)+S.diff(m*z,z),3*x+m)
 elif q=='potential-endpoints':C('potential first component',S.diff(x*x+y*y,x),2*x);C('potential second component',S.diff(x*x+y*y,y),2*y);C('potential endpoint difference',(x*x+y*y).subs({x:m,y:1})-(x*x+y*y).subs({x:0,y:0}),m*m+1)
 elif q=='box-average':C('triple integral normalized by box volume',S.integrate(x+y+z,(z,0,2),(y,0,1),(x,0,m))/(2*m),m/2+R(3,2))
 elif q=='gradient-max-direction':
  f=S.exp(x+2*y);C('gradient magnitude squared at point',sum(S.diff(f,var).subs({x:S.log(m),y:0})**2 for var in [x,y]),5*m*m);C('unit equality direction',R(1,5)+R(4,5),1)
 elif q=='quadratic-critical-value':
  f=(x+y-m)**2+(x-y-1)**2;at={x:(m+1)/2,y:(m-1)/2};C('zero value at feasible square minima',f.subs(at));C('both partials vanish',S.diff(f,x).subs(at)+S.I*S.diff(f,y).subs(at))
 elif q=='Lagrange-circle-linear':
  at={x:m/S.sqrt(m*m+1),y:1/S.sqrt(m*m+1)};C('sharpness unit constraint',(x*x+y*y).subs(at),1);C('objective at equality direction',(m*x+y).subs(at),S.sqrt(m*m+1))
 elif q=='change-order':C('reversed iterated integral',S.integrate(m*y**(m-1),(x,0,y),(y,0,1)),S.integrate(m*y**(m-1),(y,x,1),(x,0,1)))
 elif q=='ellipse-transform':C('ellipse pullback',((x/m)**2+y*y).subs({x:m*u,y:v}),u*u+v*v);C('ellipse transform determinant',S.Matrix([m*u,v]).jacobian([u,v]).det(),m)
 elif q=='polar-moment':C('radial moment integral',S.integrate(2*pi*u**(2*m+1),(u,0,1)),pi/(m+1))
 elif q=='Green-circulation':C('Green curl',S.diff(x,x)-S.diff(-y,y),2);C('direct boundary parametrization',(-y*(-m*S.sin(t))+x*(m*S.cos(t))).subs({x:m*S.cos(t),y:m*S.sin(t)}),m*m)
 elif q=='divergence-flux':C('divergence of position field',S.diff(x,x)+S.diff(y,y)+S.diff(z,z),3);C('radial-volume density integral',S.integrate(12*pi*u*u,(u,0,m)),4*pi*m**3)
 elif q=='surface-graph-area':C('graph area density squared',1+S.diff(m*x+y,x)**2+S.diff(m*x+y,y)**2,m*m+2)
 elif q=='implicit-surface-partial':C('implicit gradient relation after solving',2*x+2*z*(-x/z));C('branch derivative at specified positive point',(-x/z).subs({x:1,z:m}),-1/m)
 elif q=='density-centroid':C('mass integral',S.integrate(x**m,(x,0,1)),1/(m+1));C('first moment integral',S.integrate(x**(m+1),(x,0,1)),1/(m+2))
 elif q=='spherical-moment':C('angular full solid angle',S.integrate(S.sin(v),(v,0,pi))*2*pi,4*pi);C('radial spherical moment',S.integrate(4*pi*u**(2*m+2),(u,0,1)),4*pi/(2*m+3))
 elif q=='quadratic-eigenconstraint':
  A=S.Matrix([[m,1],[1,m+1]]);C('quadratic matrix representation',(S.Matrix([[x,y]])*A*S.Matrix([x,y]))[0],m*x*x+2*x*y+(m+1)*y*y);C('largest eigenvalue root',(A-(m+R(1,2)+S.sqrt(5)/2)*S.eye(2)).det())
 elif q=='moving-domain-derivative':C('radial primitive',S.diff(pi*(S.exp(a*a)-1),a),2*pi*a*S.exp(a*a));C('zero radius integral initial value',(pi*(S.exp(a*a)-1)).subs(a,0))
 elif q=='ellipsoid-inertia':C('ellipsoid Jacobian',S.Matrix([m*u,v,w]).jacobian([u,v,w]).det(),m);C('coordinate second moment',R(1,3)*S.integrate(4*pi*u**4,(u,0,1)),4*pi/15)
 elif q=='nonlinear-Jacobian':
  U,V=S.symbols('U V',positive=True);xx=S.sqrt(U*V);yy=S.sqrt(U/V);C('inverse product',xx*yy,U);C('inverse ratio',xx/yy,V);C('inverse determinant with negative orientation',S.Matrix([xx,yy]).jacobian([U,V]).det(),-1/(2*V));C('ratio-direction area integral',S.integrate(1/(2*V),(V,1,S.E**2)),1)
 elif q=='simplex-beta':C('inner simplex power integral',S.integrate(x**m*y**(m+1),(y,0,1-x)),x**m*(1-x)**(m+2)/(m+2));C('remaining beta polynomial integral',S.integrate(x**m*(1-x)**(m+2)/(m+2),(x,0,1)),S.factorial(m)*S.factorial(m+1)/S.factorial(2*m+3))
 elif q=='nonconservative-hole':C('boundary one-form parametrization',(m*m*S.sin(t)**2+m*m*S.cos(t)**2)/(m*m),1)
 elif q=='Stokes-tilted-surface':
  rr=S.Matrix([x,y,m*x+y]);normal=rr.diff(x).cross(rr.diff(y));C('upward vector area first component',normal[0],-m);C('upward vector area second component',normal[1],-1);C('curl dot area element',S.Matrix([0,0,2]).dot(normal),2)
 elif q=='boundary-versus-interior':C('global bound square decomposition',m*x*y-x*x-y*y,(m-2)*x*y-(x-y)**2);C('corner attains bound',(m*x*y-x*x-y*y).subs({x:1,y:1}),m-2)
 elif q=='surface-flux-graph':
  rr=S.Matrix([x,y,1-x*x-y*y]);normal=rr.diff(x).cross(rr.diff(y));C('upward graph flux density',rr.dot(normal),1+x*x+y*y);C('radial graph flux',S.integrate(2*pi*(1+u*u)*u,(u,0,1/S.sqrt(m))),pi/m+pi/(2*m*m))
 elif q=='mixed-Hessian-coordinate':C('changed-coordinate mixed derivative',S.diff((u+v)**2+m*(u-v)**2,u,v),2-2*m)
 elif q=='path-dependent-directional':C('punctured curved-path substitution',S.cancel((x**m*y/(x**(2*m)+y*y)).subs(y,x**m)),R(1,2))
 elif q=='Gaussian-precision':C('Gaussian square completion',m*x*x+2*x*y+y*y,(y+x)**2+(m-1)*x*x);C('whitening absolute determinant squared',S.Matrix([y+x,x]).jacobian([x,y]).det()**2,1)
 elif q=='Vandermonde-extremum':
  C('zero-sum discriminant identity',((x-y)**2*(y-z)**2*(z-x)**2-((x*x+y*y+z*z)**3/2-27*x*x*y*y*z*z)).subs(z,-x-y));at={x:S.sqrt(m/2),y:0,z:-S.sqrt(m/2)};C('attaining triple squared norm',(x*x+y*y+z*z).subs(at),m);C('attaining triple objective',((x-y)**2*(y-z)**2*(z-x)**2).subs(at),m**3/2)
 elif q=='anisotropic-integrability':
  aa=S.symbols('alpha',real=True);C('anisotropic integrand and Jacobian scaling',p**aa/(p*p+(p**(1/m)*v)**(2*m))*p**(1/m),p**(aa+1/m-2)/(1+v**(2*m)));C('integrable comparison tail',S.integrate(v**(-2*m),(v,1,S.oo)),1/(2*m-1))
 elif q=='Gaussian-wedge':
  th=pi/m;C('whitening quadratic identity',(x-S.cos(th)*y)**2+(S.sin(th)*y)**2,x*x-2*S.cos(th)*x*y+y*y);C('whitening determinant',S.Matrix([x-S.cos(th)*y,S.sin(th)*y]).jacobian([x,y]).det(),S.sin(th));C('radial Gaussian integral',S.integrate(p*S.exp(-p*p),(p,0,S.oo)),R(1,2))
 elif q=='planar-log-potential':
  aa=1/m;C('split radial circle-mean integral',2*pi*(S.integrate(p*S.log(aa),(p,0,aa))+S.integrate(p*S.log(p),(p,aa,1))),pi*(aa*aa-1)/2);C('local logarithmic primitive derivative',S.diff(p*p*S.log(p)/2-p*p/4,p),p*S.log(p))
 elif q=='two-centre-resolvent':
  A=1+x*x+y*y;B=1+(x-m)**2+y*y;c0=1+m*m*u*(1-u);C('parameter square completion',u*A+(1-u)*B,(x-m*(1-u))**2+y*y+c0);C('Feynman primitive derivative',S.diff(-1/(a-b)/(b+u*(a-b)),u),1/(u*a+(1-u)*b)**2);C('plane radial primitive',S.diff(-1/(2*(p*p+c)),p),p/(p*p+c)**2);F=2/(m*S.sqrt(m*m+4))*S.atanh(m*(2*u-1)/S.sqrt(m*m+4));C('last one-dimensional antiderivative',S.diff(F,u),1/c0)
 elif q=='simplex-log-partition':
  Z=1+S.exp(x)+S.exp(y);f=S.log(Z)-x/m-2*y/m;P=S.exp(x)/Z;Q=S.exp(y)/Z;RR=1/Z;H=S.hessian(f,(x,y));C('Hessian top diagonal',H[0,0],P*(1-P));C('Hessian off diagonal',H[0,1],-P*Q);C('positive determinant factorization',H.det(),P*Q*RR);at={x:S.log(1/(m-3)),y:S.log(2/(m-3))};C('critical gradient first',S.diff(f,x).subs(at));C('critical gradient second',S.diff(f,y).subs(at))
 elif q=='high-dimensional-lp-ball':C('one-coordinate positive Jacobian',S.diff(p**(1/m),p),p**(1/m-1)/m);C('Dirichlet total exponent',sum([1/m]*int(m)),1);C('gamma shift coefficient',2**m*S.gamma(1/m)**m/m**m,2**m*S.gamma(1+1/m)**m)
 elif q=='log-simplex-moment':
  aa,bb=S.symbols('aa bb',positive=True);M=S.gamma(aa)*S.gamma(bb)/S.gamma(aa+bb+1);C('mixed parameter derivative of gamma moment',S.diff(M,aa,bb)/M,(S.polygamma(0,aa)-S.polygamma(0,aa+bb+1))*(S.polygamma(0,bb)-S.polygamma(0,aa+bb+1))-S.polygamma(1,aa+bb+1));C('moment normalization at concrete exponents',M.subs({aa:m+1,bb:2}),1/((m+1)*(m+2)*(m+3)));C('digamma recurrence difference',S.polygamma(0,m+1)-S.polygamma(0,m+4),S.harmonic(m)-S.harmonic(m+3));C('classical trigamma initial value via exact special-function evaluation',S.polygamma(1,1),pi*pi/6)
 elif q=='lemniscate-petal-area':C('polar modulus-square identity',(p**m*S.cos(m*t)-1)**2+(p**m*S.sin(m*t))**2-1,p**(2*m)-2*p**m*S.cos(m*t));C('petal multiplicity angular Jacobian',m*R(1,m),1);C('radial area primitive',S.diff(p*p/2,p),p)
 elif q=='squared-log-disk':
  C('summand partial fraction identity',1/(n*n*(n+1)),1/n**2-1/n+1/(n+1));C('radial Fourier-square moment',S.integrate(p**(2*m+1),(p,0,1)),1/(2*m+2));C('cosine orthogonality diagonal representative',S.integrate(S.cos(m*t)**2,(t,0,2*pi)),pi);C('cosine orthogonality unequal representative',S.integrate(S.cos(m*t)*S.cos((m+1)*t),(t,0,2*pi)))
 elif q=='cube-simplex-cap':
  C('simplex dimension recursion at concrete dimension',S.integrate((c-p)**(m-1)/S.factorial(m-1),(p,0,c)),c**m/S.factorial(m));C('translated coordinate sum',sum([x+1]*2+[x]*(int(m)-2)),m*x+2)
  # Every boundary multiplicity vanishes when at least one upper constraint fails.
  for count in range(1,int(m)+1):C('inclusion-exclusion cancellation for '+str(count)+' violated bounds',sum((-1)**j*S.binomial(count,j) for j in range(count+1)))
 elif q=='polynomial-image-winding':
  Q=sum((m-1-j)*z**j for j in range(int(m)-1));C('polynomial double-root factorization',(z-1)**2*Q,z**m-m*z+m-1);radius=1+1/m;rp=(radius+(m-1)/(m-2))/2;bs=[(m-1-j)*rp**j for j in range(int(m)-1)];out.append(truth('strict scaled coefficient decrease at explicit radius',all(bs[i]>bs[i+1]>0 for i in range(len(bs)-1)),{'radius':str(radius),'largerRadius':str(rp),'coefficients':list(map(str,bs))}));C('coefficient telescope after multiplication by one minus w',sum(bs[i]-bs[i+1] for i in range(len(bs)-1))+bs[-1],bs[0])
 else:raise KeyError(q)
 return out
def limits(m,q,record):
 out=[]
 def C(name,l,r=0):out.append(check(name,l,r))
 if q=='irrational-rotation-correlation':
  aa=1/(m+1);C('piecewise correlated orbit integral',S.integrate(t*(t+aa),(t,0,1-aa))+S.integrate(t*(t+aa-1),(t,1-aa,1)),R(1,3)-aa/2+aa*aa/2)
  C('finite geometric Fourier numerator',sum(z**j for j in range(1,int(m)+1))*(1-z),z-z**(m+1))
 elif q=='Newton-double-exponential-rate':
  N=(a+2/a)/2;C('cross-ratio squares exactly',(N-S.sqrt(2))/(N+S.sqrt(2)),((a-S.sqrt(2))/(a+S.sqrt(2)))**2);C('cross-ratio inverse error',S.sqrt(2)*(1+u)/(1-u)-S.sqrt(2),2*S.sqrt(2)*u/(1-u))
 elif q=='recurrence-Hankel-growth':
  P=2*m+1;D=m*m+m-1;A=a;B=b;C2=P*B-D*A;C3=P*C2-D*B;C('consecutive determinant recurrence',B*C3-C2*C2,D*(A*C2-B*B));C('initial Hankel determinant',2*(P*P-2*D)-P*P,5)
 elif q=='Dirichlet-endpoint-trace':
  # Finite trig identity checked at the concrete parameter; induction is its general proof.
  C('finite Dirichlet sine kernel via trig recurrence',S.sin((2*m+1)*x),S.sin(x)*(1+2*sum(S.cos(2*j*x) for j in range(1,int(m)+1))))
  num=x**m-pi**(m-1)*x;C('left quotient endpoint via simple-zero ratio',S.diff(num,x).subs(x,0),-pi**(m-1));C('right quotient endpoint via simple-zero ratio',S.diff(num,x).subs(x,pi)/(-1),-(m-1)*pi**(m-1));C('linear endpoint-interpolant integral against finite kernel',S.integrate(pi**(m-1)*x*(1+2*sum(S.cos(2*j*x) for j in range(1,int(m)+1))),(x,0,pi)),pi**(m+1)/2)
 elif q=='monic-minimax-rate':
  T=S.chebyshevt(m,x);poly=m**m*T.subs(x,x/m)/2**(m-1);C('scaled Chebyshev polynomial is monic',S.Poly(poly,x).LC(),1);C('Chebyshev recurrence at concrete degree',S.chebyshevt(m+1,x),2*x*S.chebyshevt(m,x)-S.chebyshevt(m-1,x));C('endpoint alternating value',T.subs(x,-1),(-1)**m)
 elif q=='binomial-moving-threshold':C('centered Bernoulli characteristic factor', (S.exp(S.I*t)+S.exp(-S.I*t))/2,S.cos(t));C('quadratic logarithmic-cosine coefficient',S.diff(S.log(S.cos(t)),t,2).subs(t,0)/2,-R(1,2))
 elif q=='coupon-coverage-window':C('fixed occupancy logarithmic expansion first coefficient',S.diff(S.log(1-j*x),x).subs(x,0),-j);C('fixed occupancy logarithmic expansion second coefficient',S.diff(S.log(1-j*x),x,2).subs(x,0)/2,-j*j/2);C('factorial combinatorial leading coefficient',S.Poly(S.prod(x-j for j in range(int(m)))/S.factorial(m),x).LC(),1/S.factorial(m))
 elif q=='gcd-pair-density':
  for g in range(1,int(m)+7):C('Möbius divisor identity g='+str(g),sum(S.mobius(d) for d in S.divisors(g)),int(g==1))
  N=3*int(m)+4;direct=sum(S.gcd(a,b)==m for a in range(1,N+1) for b in range(1,N+1));count=sum(S.mobius(d)*(N//(int(m)*d))**2 for d in range(1,N//int(m)+1));C('exact finite coprime-pair inversion',direct,count)
 elif q=='floor-integer-approach':
  f=m*S.sin(x)/x if int(m)%2==0 else m*x/S.sin(x);C('approach direction quadratic coefficient',S.limit((f-m)/x**2,x,0),-m/6 if int(m)%2==0 else m/6)
 elif q=='implicit-inverse-increment':C('strict inverse derivative denominator',S.diff(t**3+m*t,t),3*t*t+m);C('inverse basepoint', (t**3+m*t).subs(t,1),m+1)
 elif q=='Lp-maximum-limit':
  f=x**m*(1-x);C('factor derivative used for maximum',S.diff(f,x),x**(m-1)*(m-(m+1)*x));C('interior critical point',S.diff(f,x).subs(x,m/(m+1)));C('maximum attained value',f.subs(x,m/(m+1)),m**m/(m+1)**(m+1))
 elif q=='log-phase-average-limsup':
  F=x*(S.cos(m*S.log(x))+m*S.sin(m*S.log(x)))/(1+m*m);C('log-phase antiderivative',S.diff(F,x),S.cos(m*S.log(x)));C('maximizing phase amplitude',(S.cos(t)+m*S.sin(t)).subs(t,S.atan(m))/(1+m*m),1/S.sqrt(1+m*m))
 else:raise KeyError(q)
 return out

def differentiation(m,q,record):
 out=[]
 def C(name,l,r=0):out.append(check(name,l,r))
 if q=='sharp-endpoint-derivative':
  C('Chebyshev recurrence',(S.chebyshevt(m+1,x)),2*x*S.chebyshevt(m,x)-S.chebyshevt(m-1,x));C('sharp polynomial endpoint derivative',S.diff(S.chebyshevt(m,x),x).subs(x,1),m*m)
  for deg in range(1,int(m)+1):C('endpoint derivative recurrence step '+str(deg),2+2*deg**2-(deg-1)**2,(deg+1)**2)
 elif q=='cyclic-determinant-second-derivative':
  M=S.zeros(int(m))
  for idx in range(int(m)):M[idx,idx]=2;M[idx,(idx+1)%int(m)]=-1;M[idx,(idx-1)%int(m)]=-1
  total=0
  for gap in range(1,int(m)):
   keep=[i for i in range(int(m)) if i not in(0,gap)];minor=M.extract(keep,keep).det();C('deleted cycle vertices gap '+str(gap),minor,gap*(m-gap));total+=minor
  C('quadratic column selection sum',m*total/2,m*m*(m*m-1)/12)
 elif q=='oscillatory-regularity-pair':
  # Encode exact punctured derivative amplitudes A_k sin(1/x)+B_k cos(1/x).
  A=x**(2*m+2);B=S.Integer(0)
  for order in range(int(m)+2):
   expectedPower=2*int(m)+2-2*order
   terms=[]
   for amp in [A,B]:
    for term in S.Add.make_args(S.expand(amp)):
     if term!=0:terms.append((int(term.as_powers_dict().get(x,0)),term/x**term.as_powers_dict().get(x,0)))
   minpow=min(power for power,coef in terms);out.append(truth('exact derivative leading power at order '+str(order),minpow==expectedPower,{'minimumExponent':minpow,'requiredExponent':expectedPower}))
   leading=[coef for power,coef in terms if power==minpow];out.append(truth('unit sine/cosine leading coefficient order '+str(order),len(leading)==1 and leading[0] in(-1,1),{'coefficients':list(map(str,leading))}))
   if order<=int(m):out.append(truth('next origin difference quotient exponent positive order '+str(order+1),minpow-1>0,{'powerAfterDividingByInput':minpow-1}))
   A,B=S.expand(S.diff(A,x)+B/x**2),S.expand(S.diff(B,x)-A/x**2)
 elif q=='newton-iteration-jet':
  N=((m-1)*x+x**(1-m))/m;C('Newton fixed point',N.subs(x,1),1);C('Newton first derivative vanishes',S.diff(N,x).subs(x,1));C('Newton quadratic coefficient',S.diff(N,x,2).subs(x,1)/2,(m-1)/2)
  jets=[S.diff(N,x,order).subs(x,1)/S.factorial(order) for order in range(2,9)];err=z
  for iteration in range(3):
   err=S.Poly(S.expand(sum(jets[order-2]*err**order for order in range(2,9))),z)
   err=S.Add(*(coef*z**power[0] for power,coef in err.terms() if power[0]<=8))
  C('independent eighth-order composition jet',err,((m-1)/2)**7*z**8)
 elif q=='moving-endpoint-parameter-second':
  boundary=m*x**(m-1)*S.exp(x**(m+1))-S.exp(x*x);C('first boundary contribution derivative',S.diff(boundary,x).subs(x,1),(2*m*m-2)*S.E);C('collapsing integral boundary derivative',(m*x**(m-1)*(x**m)*S.exp(x*x**m)-x*S.exp(x*x)).subs(x,1),(m-1)*S.E)
  # Integrating the original integrand first independently validates all Leibniz terms.
  F=(S.exp(x**(m+1))-S.exp(x*x))/x;C('closed original integral second derivative',S.diff(F,x,2).subs(x,1),(2*m*m+m-3)*S.E)
 else:raise KeyError(q)
 return out

def series_easy(m,q,record):
 out=[]
 def C(name,l,r=0):out.append(check(name,l,r))
 if q in ['p-series-pair','alternating-absolute-conditional']:
  pairs=([(R(1,2),R(1,3)),(1,2),(2,1),(R(3,2),R(5,2)),(R(3,4),1),(R(4,3),R(2,3)),(R(3,5),R(7,6)),(R(7,4),R(9,4))] if q=='p-series-pair' else [(R(1,2),1),(R(3,4),R(3,2)),(2,R(1,2)),(R(3,2),2),(1,R(3,4)),(R(3,5),R(7,5)),(R(9,5),1),(R(11,5),R(8,5))])
  for label,exponent in zip(['A','B'],pairs[int(m)-4]):
   exponent=S.sympify(exponent);primitive=S.log(p) if exponent==1 else p**(1-exponent)/(1-exponent);C('integral comparison primitive '+label,S.diff(primitive,p),p**(-exponent));out.append(truth('positive decreasing benchmark '+label,exponent>0,{'exponent':str(exponent),'derivative':'-p*x^(-p-1)<0 for x>0'}));C('benchmark tends to zero '+label,S.limit(p**(-exponent),p,S.oo))
 elif q=='direct-comparison-information':
  i=int(m)-4;exponent=m/8 if i%4==0 else m/16 if i%4==1 else m/4;primitive=S.log(p) if exponent==1 else p**(1-exponent)/(1-exponent);C('benchmark integral primitive',S.diff(primitive,p),p**(-exponent));out.append(truth('nonnegative decreasing benchmark',exponent>0,{'exponent':str(exponent),'n>=1 implies 0<n^(-p)<=1':True}));C('benchmark at first integer',(p**(-exponent)).subs(p,1),1)
 elif q=='taylor-coefficient-derivative':
  coefficient=(-1)**m*(m-3)/(m+2);C('concrete Taylor monomial derivative at center',S.diff(coefficient*(x-2)**m,x,int(m)).subs(x,2),S.factorial(m)*coefficient)
  for order in [m-1,m+1]:C('adjacent monomial contributes zero at center order '+str(order),S.diff((x-2)**order,x,int(m)).subs(x,2))
 elif q=='linearity-given-convergent-sums':C('finite coefficient distribution before limits',sum(2*(a+j)-m*(b-j) for j in range(int(m))),2*sum(a+j for j in range(int(m)))-m*sum(b-j for j in range(int(m))));C('given limiting sums combined',2*(m-2)-m*(m+1),-m*m+m-4)
 else:raise KeyError(q)
 return out

def main():
 manifest=json.loads((ROOT/'manifest.json').read_text());bank=source_artifact();records=[json.loads(line) for line in bank.read_text().splitlines()];records=[r for r in records if r['familyId'] in manifest['families']]
 spec=importlib.util.spec_from_file_location('corrected_solutions',ROOT/'solutions.py');sol=importlib.util.module_from_spec(spec);spec.loader.exec_module(sol)
 results=[]
 dispatch={'ode':ode,'multivariable':multivariable,'limits':limits,'differentiation':differentiation,'series_easy':series_easy}
 for record in records:
  fn,slug=sol._route(record);m=sol.parameter(record)
  try:
   checks=dispatch[fn.__name__](m,slug,record)
   if not checks:raise AssertionError('no substantive intermediate check')
   result={'problemId':record['problemId'],'familyId':record['familyId'],'sourceContentHash':record['contentHash'],'passed':True,'checks':checks}
  except Exception as exc:result={'problemId':record['problemId'],'familyId':record['familyId'],'passed':False,'error':repr(exc)}
  results.append(result)
  if len(results)%8==0:print(record['familyId'],sum(r['passed'] for r in results[-8:]),flush=True)
 report={'artifactSha256':hashlib.sha256(bank.read_bytes()).hexdigest(),'moduleSha256':hashlib.sha256((ROOT/'solutions.py').read_bytes()).hexdigest(),'checkCodeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'recordCount':len(results),'familyCount':len({r['familyId'] for r in results}),'executedChecks':sum(len(r.get('checks',[])) for r in results),'failureCount':sum(not r['passed'] for r in results),'results':results,'scope':'Exact symbolic, finite combinatorial, and sign checks of newly displayed intermediate routes, independently encoded without importing original constructors. Analytic convergence, existence/uniqueness, theorem applications, sharpness and level fit also require the separate AI editorial mathematical certificate; this is not a formal proof or human review.'}
 (ROOT/'substantive-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('FINISHED',report['recordCount'],report['executedChecks'],report['failureCount'])
 if report['failureCount']:sys.exit(1)
if __name__=='__main__':main()
