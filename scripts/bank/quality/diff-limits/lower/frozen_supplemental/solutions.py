"""Versioned solution-only research for 118 finite Calculus Ninja families.

Consumes a complete original record and returns new solution steps. No original
record is mutated. Numeric builder parameters are instantiated only where used.
Natural logarithms use ln; inverse circular functions use arc notation.
"""
from __future__ import annotations
import copy,hashlib,json,math,re
from pathlib import Path
import sympy as s
R=s.Rational
x,y,z,t,u,v=s.symbols('x y z t u v',real=True)
pi=s.pi

def notation(value):
 value=value.replace(r'\log',r'\ln')
 for old,new in [(r'\operatorname{atan}',r'\arctan'),(r'\operatorname{asin}',r'\arcsin'),(r'\operatorname{acos}',r'\arccos'),(r'\operatorname{atanh}',r'\operatorname{arctanh}')]:value=value.replace(old,new)
 return value

def L(value):return notation(s.latex(s.sympify(value),fold_short_frac=False))
def T(value):
 assert not any(c in value for c in ['^','_','\\','$']),('math belongs outside prose',value)
 return r'\textnormal{'+value+'}'
def answer_math(record):return notation(next(c['math'] for c in record['choices'] if c['choiceId']==record['answerChoiceId']))
def parameter(record):
 m=record['provenance']['authoring']['builderParameters']['m']
 if type(m)is not int or not 2<=m<=11:raise ValueError('unsupported finite parameter')
 return s.Integer(m)
def eq(lhs,rhs):return lhs+'='+L(rhs)

ODE_SLUGS=['field-slope','rate-identification','phase-line-stability','euler-step','primitive-initial-value','doubling-data','cooling-limit','mixing-inflow','constant-acceleration','equation-order','oscillator-initial-data','transfer-conservation','logistic-hitting','finite-blowup','variable-integrating-factor','exact-curve','bernoulli-reciprocal','homogeneous-ratio','harvest-bifurcation','distinct-characteristic-roots','resonant-forcing','critical-damping','repeated-root','periodic-amplitude','riccati-particular','nonlinear-energy-speed','euler-cauchy-resonance','variable-second-order-basis','remove-first-derivative','step-forcing','impulse-jump','rotating-linear-system','jordan-system','linear-stability-bound','mixed-boundary-spectrum','wronskian-transport','quartic-period','power-coordinate-lifetime','pinney-energy','switched-riccati','periodic-product-average','periodic-floquet-multiplier','resonant-boundary-compatibility','sharp-lifetime-comparison','nonlinear-radial-asymptotic','ground-state-variance','schwarzian-ivp','darboux-oscillator']

def ode(record,m,slug):
 if slug=='field-slope':
  return [T('Evaluate the right-hand side at the given time and state.'),r'y\prime('+L(m)+r')='+L(m)+r'\cdot2+'+L(m)+r'^2='+L(m*m+2*m)],m*m+2*m
 if slug=='rate-identification':
  return [r'y\prime(t)='+L(m)+r'e^{'+L(m)+r't}',T('The exponential is never zero, so the equation forces the constant rate to equal the derivative divided by the function.'),r'k=\frac{y\prime(t)}{y(t)}='+L(m)],m
 if slug=='phase-line-stability':
  return [r'y^2-'+L(m*m)+r'=(y-'+L(m)+r')(y+'+L(m)+r')',T('The equilibria are the two roots. Below the negative root the derivative is positive; just above it the derivative is negative. Both nearby directions point toward that root.'),r'y=-'+L(m)],-m
 if slug=='euler-step':
  return [T('Forward Euler adds the step size times the initial slope to the initial value.'),r'y_1='+L(m)+r'+'+L(1/m)+r'(0-'+L(m)+r')='+L(m-1)],m-1
 if slug=='primitive-initial-value':
  return [T('Integrate the prescribed derivative from the initial time.'),r'y(t)=1+\int_0^t '+L(m)+r's^2\,ds=1+\frac{'+L(m)+r'}3t^3',r'y(1)='+L(1+m/3)],1+m/3
 if slug=='doubling-data':
  return [r'y(t)=y(0)e^{kt},\qquad e^k=\frac{y(1)}{y(0)}=2',T('Each unit of time multiplies the value by two.'),r'y(3)='+L(m)+r'\cdot2^3='+L(8*m)],8*m
 if slug=='cooling-limit':
  return [T('Subtract the constant environmental temperature to obtain a decaying exponential.'),r'T(t)-'+L(m+10)+r'=-10e^{-2t}',r'\lim_{t\to\infty}T(t)='+L(m+10)],m+10
 if slug=='mixing-inflow':
  return [T('The rate of salt accumulation is inflow of salt minus outflow of salt. The outgoing concentration equals the current amount divided by the tank volume.'),r'S\prime=2\left(\frac32\right)-2\left(\frac{'+L(m)+r'}{'+L(m+2)+r'}\right)='+L(3-2*m/(m+2)),T('The result is measured in grams per minute.')],3-2*m/(m+2)
 if slug=='constant-acceleration':
  return [T('Integrate twice, using the velocity and position initial values in that order.'),r's\prime(t)=1+'+L(m)+r't,\qquad s(t)=t+\frac{'+L(m)+r'}2t^2',r's(1)='+L(1+m/2)],1+m/2
 if slug=='equation-order':
  return [T('The order is the highest number of differentiations of the unknown function appearing in the equation. A power of a lower derivative does not increase its order.'),r'\textnormal{order}='+L(m-2)],m-2
 if slug=='oscillator-initial-data':
  return [r'y(0)=A='+L(m)+r',\qquad y\prime(0)=B='+L(m+1),r'y(\pi/2)=A\cos(\pi/2)+B\sin(\pi/2)='+L(m+1)],m+1
 if slug=='transfer-conservation':
  later=(2*m+21)/10;ans=(8*m+9)/10
  return [T('Add the two equations; transfer between the components cancels.'),r'(u+v)\prime=0,\qquad u+v=u(0)+v(0)='+L(m+3),r'u='+L(m+3)+r'-'+L(later)+r'='+L(ans)],ans
 if slug=='logistic-hitting':
  return [T('Separate variables, or differentiate the logarithm of the odds.'),r'\left(\ln\frac{y}{1-y}\right)\prime=1,\qquad \frac{y}{1-y}=\frac{e^t}{'+L(m)+r'}',T('At the requested value the odds equal one. The solution increases between zero and one, so this is the first such time.'),r'e^t='+L(m)+r'\quad\Longrightarrow\quad t=\ln '+L(m)],s.log(m)
 if slug=='finite-blowup':
  return [r'\left(\frac1y\right)\prime=-1,\qquad \frac1{y(t)}='+L(m)+r'-t',r'y(t)=\frac1{'+L(m)+r'-t}',T('This solution diverges at the first forward zero of its denominator, so it cannot be continued there as a finite classical solution.'),r't='+L(m)],m
 if slug=='variable-integrating-factor':
  f=(t**(m+2)-1)/((m+2)*t)
  return [T('Multiply the equation by the positive independent variable to form a product derivative.'),r'(ty)\prime=t^{'+L(m+1)+r'},\qquad ty=\int_1^t s^{'+L(m+1)+r'}\,ds=\frac{t^{'+L(m+2)+r'}-1}{'+L(m+2)+r'}',r'y(t)='+L(f),r'y(2)='+L(f.subs(t,2))],f.subs(t,2)
 if slug=='exact-curve':
  c=m*m+m+1
  return [T('The left-hand side is the total derivative of a quadratic potential.'),r'\frac{d}{dt}(t^2+ty+y^2)=(2t+y)+(t+2y)y\prime=0',r't^2+ty+y^2=1+'+L(m)+r'+'+L(m*m)+r'='+L(c),T('At the specified intersection, set the dependent variable to zero and choose the positive time.'),r't^2='+L(c)+r',\quad t='+L(s.sqrt(c))],s.sqrt(c)
 if slug=='bernoulli-reciprocal':
  f=t+1-(m+1)*s.exp(t)
  return [r'v=\frac1y\quad\Longrightarrow\quad v\prime-v=-t,\qquad v(0)=-'+L(m),r'(e^{-t}v)\prime=-te^{-t},\qquad v(t)='+L(f),T('This reciprocal stays negative on the requested interval, so inversion is valid.'),r'y(1)=\frac1{v(1)}='+L(1/f.subs(t,1))],1/f.subs(t,1)
 if slug=='homogeneous-ratio':
  return [r'v(t)=\frac{y(t)}t\quad\Longrightarrow\quad tv\prime=v^2',r'-\frac1v=\ln t+'+L(m)+r',\qquad y(t)=-\frac{t}{'+L(m)+r'+\ln t}',T('The denominator remains positive between the initial and requested times.'),r'y(e)='+L(-s.E/(m+1))],-s.E/(m+1)
 if slug=='harvest-bifurcation':
  return [r'y('+L(m)+r'-y)=\frac{'+L(m*m)+r'}4-\left(y-\frac{'+L(m)+r'}2\right)^2',T('An equilibrium requires the removal rate to equal this quadratic. Its greatest value is attained at a positive population.'),r'h_{\max}='+L(m*m/4)+r',\qquad y='+L(m/2)],m*m/4
 if slug=='distinct-characteristic-roots':
  return [r'r^2-'+L(m+1)+r'r+'+L(m)+r'=(r-1)(r-'+L(m)+r')',r'y(t)=Ae^t+Be^{'+L(m)+r't}',r'A+B=0,\quad A+'+L(m)+r'B='+L(m-1)+r'\quad\Longrightarrow\quad A=-1,\ B=1',r'y(1)='+L(s.exp(m)-s.E)],s.exp(m)-s.E
 if slug=='resonant-forcing':
  ans=(-1)**(m+1)*m*pi/2
  return [T('The forcing is a homogeneous mode, so a resonant particular solution needs an extra factor of time.'),r'y_p(t)=-\frac12t\cos t,\qquad y_p\prime\prime+y_p=\sin t',T('The initial derivative is corrected by a homogeneous sine term.'),r'y(t)=\frac{\sin t-t\cos t}{2}',r'y('+L(m)+r'\pi)='+L(ans)],ans
 if slug=='critical-damping':
  return [T('Critical damping occurs when the characteristic polynomial has a repeated negative real root.'),r'r^2+cr+'+L(m*m)+r'=0,\qquad c^2-4\cdot'+L(m*m)+r'=0',T('The stated positive damping condition selects the positive root.'),r'c='+L(2*m)],2*m
 if slug=='repeated-root':
  return [r'r^2-'+L(2*m)+r'r+'+L(m*m)+r'=(r-'+L(m)+r')^2',r'y(t)=(A+Bt)e^{'+L(m)+r't}',r'y(0)=0\Rightarrow A=0,\qquad y\prime(0)=1\Rightarrow B=1',r'y(1)='+L(s.exp(m))],s.exp(m)
 if slug=='periodic-amplitude':
  A=m/(m*m+1);B=1/(m*m+1)
  return [r'y_p(t)=A\cos t+B\sin t',r'B+'+L(m)+r'A=1,\qquad -A+'+L(m)+r'B=0',r'A='+L(A)+r',\quad B='+L(B)+r',\quad \textnormal{amplitude}=\sqrt{A^2+B^2}='+L(1/s.sqrt(m*m+1)),T('Every other solution differs by a decaying exponential, so this is the steady periodic amplitude.')],1/s.sqrt(m*m+1)
 if slug=='riccati-particular':
  return [T('Subtract the simple particular solution equal to the independent variable.'),r'z(t)=y(t)-t\quad\Longrightarrow\quad z\prime=z^2,\qquad z(0)=\frac1{'+L(m)+r'}',r'z(t)=\frac1{'+L(m)+r'-t},\qquad y(t)=t+\frac1{'+L(m)+r'-t}',r'y(1)='+L(1+1/(m-1))],1+1/(m-1)
 if slug=='nonlinear-energy-speed':
  return [T('Multiply the equation by the velocity and integrate to obtain an energy invariant.'),r'\frac{d}{dt}\big((y\prime)^2+y^4\big)=2y\prime(y\prime\prime+2y^3)=0',r'(y\prime)^2+y^4='+L(m**4)+r'\quad\Longrightarrow\quad |y\prime|\le '+L(m*m),T('Starting from the positive turning point, the negative acceleration initiates motion toward zero. The travel time is'),r'\int_0^{'+L(m)+r'}\frac{dy}{\sqrt{'+L(m**4)+r'-y^4}}<\infty',T('At the turning point the denominator has a simple zero before taking the square root, so the singularity is an integrable inverse square root. The solution reaches zero in finite time and attains the speed bound there.')],m*m
 if slug=='euler-cauchy-resonance':
  return [r's=\ln t,\qquad y(t)=t^2w(s)',r't^2y\prime\prime-3ty\prime+4y=t^2\frac{d^2w}{ds^2}',r'w\prime\prime(s)=1,\quad w(0)=w\prime(0)=0\quad\Longrightarrow\quad w(s)=\frac{s^2}{2}',r'y(t)=\frac12t^2(\ln t)^2,\qquad y('+L(s.exp(1/m))+r')='+L(s.exp(2/m)/(2*m*m))],s.exp(2/m)/(2*m*m)
 if slug=='variable-second-order-basis':
  f=m*(t+1-s.exp(t-1))
  return [T('Substitution shows that the following two functions solve the homogeneous equation.'),r'y_1(t)=t+1,\qquad y_2(t)=e^t,\qquad y_1y_2\prime-y_1\prime y_2=te^t\ne0\quad(t>0)',r'y(t)=A(t+1)+Be^t,\quad 2A+Be='+L(m)+r',\quad A+Be=0',r'y(t)='+L(f)+r',\qquad y(2)='+L(f.subs(t,2))],f.subs(t,2)
 if slug=='remove-first-derivative':
  return [r'y(t)=e^{-t^2/2}u(t)',T('Differentiate this product twice and substitute; the first-derivative terms cancel.'),r'u\prime\prime+'+L(m*m)+r'u=0,\qquad u(0)=1,\quad u\prime(0)=0',r'y(t)=e^{-t^2/2}\cos('+L(m)+r't)',r'y('+L(pi/m)+r')='+L(-s.exp(-pi*pi/(2*m*m)))],-s.exp(-pi*pi/(2*m*m))
 if slug=='step-forcing':
  return [T('Before the switch, the zero initial data give the zero solution. Continuity of the function and its first derivative supplies zero initial data at the switch.'),r'y(t)='+L(m)+r'\bigl(1-\cos(t-1)\bigr)\quad(t\ge1)',T('This function has the required forcing and the two matching values.'),r'y(1+\pi)='+L(m)+r'(1-\cos\pi)='+L(2*m)],2*m
 if slug=='impulse-jump':
  return [T('A jump in the function would create a derivative of the Dirac impulse, which is absent. Thus the function is continuous. Integrating across the impulse gives its velocity jump.'),r'y(1^+)=y(1^-)=0,\qquad y\prime(1^+)-y\prime(1^-)='+L(m),r'y(t)='+L(m)+r'(t-1)e^{-(t-1)}\quad(t>1)',r'y(2)='+L(m/s.E)],m/s.E
 if slug=='rotating-linear-system':
  return [r'z(t)=u(t)+iv(t)\quad\Longrightarrow\quad z\prime=(-1+'+L(m)+r'i)z,\quad z(0)=1',r'u(t)=e^{-t}\cos('+L(m)+r't),\qquad v(t)=e^{-t}\sin('+L(m)+r't)',r'u('+L(pi/m)+r')='+L(-s.exp(-pi/m))],-s.exp(-pi/m)
 if slug=='jordan-system':
  return [T('Solve the triangular system from the last component upward; each step uses the previous component as its forcing.'),r'u_3(t)=e^{'+L(m)+r't}',r'(e^{-'+L(m)+r't}u_2)\prime=1\quad\Longrightarrow\quad u_2(t)=te^{'+L(m)+r't}',r'(e^{-'+L(m)+r't}u_1)\prime=t\quad\Longrightarrow\quad u_1(t)=\frac{t^2}{2}e^{'+L(m)+r't}',r'u_1(1)='+L(s.exp(m)/2)],s.exp(m)/2
 if slug=='linear-stability-bound':
  ans=m-s.sqrt(m*m-m)
  return [T('Let ')+r'A'+T(' denote the coefficient matrix of the given system.'),T('A real two-dimensional linear system is asymptotically stable exactly when its coefficient matrix has negative trace and positive determinant.'),r'\operatorname{tr}A=2a-'+L(2*m)+r',\qquad \det A=a^2-'+L(2*m)+r'a+'+L(m),r'\operatorname{tr}A<0\iff a<'+L(m),r'\det A>0\iff a<'+L(ans)+r'\ \textnormal{or}\ a>'+L(m+s.sqrt(m*m-m)),T('Only the lower determinant branch meets the trace condition.')],ans
 if slug=='mixed-boundary-spectrum':
  return [T('Zero spectral parameter gives an affine solution, and negative spectral parameter gives a hyperbolic sine after the left boundary condition. Neither can satisfy the right derivative condition unless the solution is zero.'),r'\lambda>0:\quad y(t)=C\sin(\sqrt\lambda\,t),\quad C\ne0',r'y\prime('+L(m)+r')=0\quad\Longrightarrow\quad \cos('+L(m)+r'\sqrt\lambda)=0',r'\lambda_{\min}=\left(\frac{\pi}{'+L(2*m)+r'}\right)^2='+L(pi*pi/(4*m*m))],pi*pi/(4*m*m)
 if slug=='wronskian-transport':
  return [T('Differentiate the determinant defining the Wronskian. The products of first derivatives cancel.'),r'W\prime=y_1y_2\prime\prime-y_1\prime\prime y_2=-\frac{'+L(m)+r'}t W',T('The terms involving the unknown coefficient cancel because both functions solve the same equation.'),r'W(t)=t^{-'+L(m)+r'}\quad\textnormal{from }W(1)=1',r'W(2)='+L(2**(-m))],2**(-m)
 if slug=='quartic-period':
  ans=s.sqrt(2*pi)*s.gamma(R(1,4))/(m*s.gamma(R(3,4)))
  return [T('Let ')+r'P'+T(' denote the full period.'),r'\frac12(y\prime)^2+\frac{'+L(m*m)+r'}4y^4=\frac{'+L(m*m)+r'}4',T('One quarter of the oscillation travels from the positive turning point to zero. Symmetry gives four equal legs.'),r'P=\frac{4\sqrt2}{'+L(m)+r'}\int_0^1\frac{dy}{\sqrt{1-y^4}}',r'u=y^4\quad\Longrightarrow\quad P=\frac{\sqrt2}{'+L(m)+r'}\int_0^1u^{-3/4}(1-u)^{-1/2}\,du',T('Both endpoint powers are integrable. Euler beta integration expresses this integral through the gamma function.'),r'P=\frac{\sqrt2}{'+L(m)+r'}\frac{\Gamma(1/4)\Gamma(1/2)}{\Gamma(3/4)}='+L(ans)],ans
 if slug=='power-coordinate-lifetime':
  return [r'u(t)=y(t)^{3/2}\quad\Longrightarrow\quad u\prime\prime+'+L(m*m)+r'u=0',r'u(0)=1,\quad u\prime(0)=0\quad\Longrightarrow\quad u(t)=\cos('+L(m)+r't)',r'y(t)=\bigl(\cos('+L(m)+r't)\bigr)^{2/3}\quad\textnormal{while the cosine is positive}',T('The positive change of variable is invertible up to the first cosine zero. At that endpoint the solution reaches zero and its derivative becomes unbounded, so a positive classical continuation is impossible.'),r't='+L(pi/(2*m))],pi/(2*m)
 if slug=='pinney-energy':
  q=m*m*s.cos(t)**2+m**(-2)*s.sin(t)**2
  return [r'E=(y\prime)^2+y^2+y^{-2}='+L(m*m+m**(-2)),T('Multiplication of the equation by the first derivative proves that this energy is constant.'),r'q(t)=y(t)^2\quad\Longrightarrow\quad q\prime\prime+4q=2E',r'q(t)='+L(q),T('This expression is strictly positive. Choose its positive square root, as required by the original problem.'),r'y(\pi/2)=\sqrt{'+L(m**(-2))+r'}='+L(1/m)],1/m
 if slug=='switched-riccati':
  ans=s.fibonacci(2*m)/s.fibonacci(2*m+1)
  return [T('During the first unit interval the value increases by one. During the second, solve the reciprocal differential equation.'),r'z\longmapsto z+1\longmapsto\frac{z+1}{z+2}',T('Write the value after each complete cycle as a numerator divided by a denominator.'),r'y(2j)=p_j/q_j',r'\binom{p_{j+1}}{q_{j+1}}=\begin{pmatrix}1&1\\1&2\end{pmatrix}\binom{p_j}{q_j},\quad(p_0,q_0)=(0,1)',r'F_0=0,\quad F_1=1,\quad F_{k+1}=F_k+F_{k-1}\ (k\ge1)',T('The Fibonacci recurrence gives the numerator and denominator after each cycle.'),r'(p_j,q_j)=(F_{2j},F_{2j+1}),\qquad y('+L(2*m)+r')=\frac{F_{'+L(2*m)+r'}}{F_{'+L(2*m+1)+r'}}='+L(ans)],ans
 if slug=='periodic-product-average':
  return [T('Positivity allows a logarithmic derivative. Integrating a derivative of a periodic function over its period gives zero.'),r'0=\int_0^T(\ln v)\prime\,dt=3\int_0^T u\,dt-4T',r'0=\int_0^T u\prime\,dt='+L(m)+r'\int_0^T u\,dt-2\int_0^Tuv\,dt',r'\frac1T\int_0^Tuv\,dt=\frac{'+L(m)+r'}2\cdot\frac43='+L(2*m/3)],2*m/3
 if slug=='periodic-floquet-multiplier':
  return [T('Integrate the logarithmic derivative of the positive periodic solution.'),r'0=\int_0^{2\pi}(\ln y_*)\prime\,dt=\int_0^{2\pi}('+L(m)+r'+\sin t-y_*)\,dt',r'\int_0^{2\pi}y_*\,dt='+L(2*pi*m),T('Let ')+r'\eta'+T(' denote the derivative of the solution with respect to its initial value, evaluated on the periodic solution.'),r'\eta\prime=('+L(m)+r'+\sin t-2y_*)\eta,\qquad \eta(0)=1',r'P\prime(y_*(0))=\eta(2\pi)=\exp\!\left(\int_0^{2\pi}('+L(m)+r'+\sin t-2y_*)\,dt\right)='+L(s.exp(-2*pi*m))],s.exp(-2*pi*m)
 if slug=='resonant-boundary-compatibility':
  ans=2*(-1)**m/m
  return [T('Multiply the equation by its homogeneous sine mode and integrate twice by parts. The zero boundary values make both boundary terms vanish.'),r'0=\int_0^\pi t\sin('+L(m)+r't)\,dt+c\int_0^\pi\sin^2('+L(m)+r't)\,dt',r'0='+L(-pi*(-1)**m/m)+r'+c\frac\pi2\quad\Longrightarrow\quad c='+L(ans),T('This necessary condition is sufficient: the following particular solution obeys the equation and both endpoints for this value.'),r'y(t)=\frac{t}{'+L(m*m)+r'}-\frac{ct\cos('+L(m)+r't)}{'+L(2*m)+r'}'],ans
 if slug=='sharp-lifetime-comparison':
  return [r'\theta(t)=\arctan\!\left(\frac{y(t)}{'+L(m)+r'}\right)',r'\theta\prime(t)=\frac{'+L(m)+r'y\prime(t)}{'+L(m*m)+r'+y(t)^2}\ge '+L(m)+r',\quad \theta(0)=0',r''+L(m)+r't\le\theta(t)<\frac\pi2\quad\Longrightarrow\quad T\le '+L(pi/(2*m)),T('The bound is sharp because equality in the differential inequality is attained throughout this interval by the following solution.'),r'y(t)='+L(m)+r'\tan('+L(m)+r't),\qquad 0\le t<'+L(pi/(2*m))],pi/(2*m)
 if slug=='nonlinear-radial-asymptotic':
  q=m*m*s.exp(-2*t)/(1+m*m*(1-s.exp(-2*t)))
  return [r'E(t)=u(t)^2+v(t)^2\quad\Longrightarrow\quad E\prime=-2E(1+E),\quad E(0)='+L(m*m),T('The rotational terms cancel in this derivative. The nonincreasing energy bounds the trajectory and gives a global forward solution.'),r'E(t)='+L(q),r'\lim_{t\to\infty}e^{2t}E(t)='+L(m*m/(1+m*m))],m*m/(1+m*m)
 if slug=='ground-state-variance':
  return [T('Integrate the equation against the solution and complete a nonnegative square. The stated decay makes the boundary terms vanish.'),r'\int_{\mathbb R}(y\prime+'+L(m)+r'ty)^2\,dt=(\lambda-'+L(m)+r')\int_{\mathbb R}y^2\,dt\ge0',r'\lambda\ge '+L(m)+r',\quad \lambda='+L(m)+r'\iff y\prime+'+L(m)+r'ty=0',r'y(t)=Ce^{-'+L(m)+r't^2/2},\quad C\ne0',T('For this minimizing solution, integrate the derivative of a Gaussian times the independent variable.'),r'0=\int_{\mathbb R}(te^{-'+L(m)+r't^2})\prime\,dt=\int_{\mathbb R}(1-'+L(2*m)+r't^2)e^{-'+L(m)+r't^2}\,dt',r'\frac{\int t^2y^2\,dt}{\int y^2\,dt}='+L(1/(2*m))],1/(2*m)
 if slug=='schwarzian-ivp':
  return [r'q(t)=\frac{y\prime\prime(t)}{y\prime(t)}\quad\Longrightarrow\quad q\prime-\frac12q^2=-'+L(2*m*m)+r',\quad q(0)=0',r'q(t)=-'+L(2*m)+r'\tanh('+L(m)+r't)',T('The positive first derivative permits a logarithm. Integrate its logarithmic derivative and use the initial slope.'),r'(\ln y\prime)\prime=q,\qquad y\prime(t)='+L(m)+r'\operatorname{sech}^2('+L(m)+r't)',r'y(t)=\tanh('+L(m)+r't),\qquad y(1)='+L(s.tanh(m))],s.tanh(m)
 if slug=='darboux-oscillator':
  at=pi/(4*m);ans=s.sqrt(2)*(m+s.tanh(at))/2
  return [T('Let the operator denote differentiation with respect to time. The product rule gives the following identity.'),r'D=\frac{d}{dt}',r'(D^2+'+L(m*m)+r'+2\operatorname{sech}^2t)(D-\tanh t)=(D-\tanh t)(D^2+'+L(m*m)+r')',T('Apply it to a cosine solution of the constant-coefficient equation, with the sign chosen to match the initial slope.'),r'y(t)=-(D-\tanh t)\cos('+L(m)+r't)='+L(m)+r'\sin('+L(m)+r't)+\tanh t\cos('+L(m)+r't)',r'y(0)=0,\qquad y\prime(0)='+L(m*m+1),r'y('+L(at)+r')='+L(ans)],ans
 raise KeyError(slug)

MV_SLUGS=['partial-hold-fixed','mixed-partial','directional-unit','tangent-plane','linearization-two-inputs','rectangle-integral','triangular-region','polar-area','chain-curve','divergence','potential-endpoints','box-average','gradient-max-direction','quadratic-critical-value','Lagrange-circle-linear','change-order','ellipse-transform','polar-moment','Green-circulation','divergence-flux','surface-graph-area','implicit-surface-partial','density-centroid','spherical-moment','quadratic-eigenconstraint','moving-domain-derivative','ellipsoid-inertia','nonlinear-Jacobian','simplex-beta','nonconservative-hole','Stokes-tilted-surface','boundary-versus-interior','surface-flux-graph','mixed-Hessian-coordinate','path-dependent-directional','Gaussian-precision','Vandermonde-extremum','anisotropic-integrability','Gaussian-wedge','planar-log-potential','two-centre-resolvent','simplex-log-partition','high-dimensional-lp-ball','log-simplex-moment','lemniscate-petal-area','squared-log-disk','cube-simplex-cap','polynomial-image-winding']

def multivariable(record,m,slug):
 if slug=='partial-hold-fixed':
  return [T('Hold the second coordinate fixed while differentiating with respect to the first.'),r'f_x(x,y)=2xy,\qquad f_x('+L(m)+r',1)=2\cdot'+L(m)+r'\cdot1='+L(2*m)],2*m
 if slug=='mixed-partial':
  return [r'f_x(x,y)=2xy^{'+L(m)+r'},\qquad f_{xy}(x,y)='+L(2*m)+r'xy^{'+L(m-1)+r'}',r'f_{xy}(1,1)='+L(2*m)],2*m
 if slug=='directional-unit':
  return [r'\nabla f(x,y)=(2x,2y),\qquad \nabla f('+L(m)+r',0)=('+L(2*m)+r',0)',T('The supplied direction has length one, so take its dot product with the gradient.'),r'D_{(3/5,4/5)}f('+L(m)+r',0)=('+L(2*m)+r',0)\cdot(3/5,4/5)='+L(6*m/5)],6*m/5
 if slug=='tangent-plane':
  return [r'F(x,y,z)=x^2+y^2+z^2,\qquad \nabla F(1,1,'+L(m)+r')=(2,2,'+L(2*m)+r')',T('This gradient is normal to the tangent plane. Use the given point to fix its offset.'),r'(x-1)+(y-1)+'+L(m)+r'(z-'+L(m)+r')=0',r'x+y+'+L(m)+r'z='+L(m*m+2)],m*m+2
 if slug=='linearization-two-inputs':
  ans=2*m+(m+2)/10
  return [r'f('+L(m)+r',2)='+L(2*m)+r',\quad f_x('+L(m)+r',2)=2,\quad f_y('+L(m)+r',2)='+L(m),r'\Delta x=\Delta y=\frac1{10}',r'f('+L(m+R(1,10))+r',2.1)\approx '+L(2*m)+r'+2\left(\frac1{10}\right)+'+L(m)+r'\left(\frac1{10}\right)='+L(ans),T('This is the linear estimate; the product of the two increments is a second-order term and is omitted.')],ans
 if slug=='rectangle-integral':
  return [r'\int_0^{'+L(m)+r'}(x+y)\,dy='+L(m)+r'x+'+L(m*m/2),r'\int_0^1\left('+L(m)+r'x+'+L(m*m/2)+r'\right)dx='+L(m*(m+1)/2)],m*(m+1)/2
 if slug=='triangular-region':
  return [T('The inner integral gives the height of the triangular region at each horizontal coordinate.'),r'\int_0^{'+L(m)+r'-x}1\,dy='+L(m)+r'-x',r'\int_0^{'+L(m)+r'}('+L(m)+r'-x)\,dx=\left['+L(m)+r'x-\frac{x^2}{2}\right]_0^{'+L(m)+r'}='+L(m*m/2)],m*m/2
 if slug=='polar-area':
  return [r'x=r\cos\theta,\quad y=r\sin\theta,\quad dA=r\,dr\,d\theta',r'0\le r\le '+L(m)+r',\qquad 0\le\theta\le2\pi',r'\iint1\,dA=\int_0^{2\pi}\int_0^{'+L(m)+r'}r\,dr\,d\theta='+L(pi*m*m)],pi*m*m
 if slug=='chain-curve':
  return [T('Substitute the parameterized coordinates before differentiating.'),r'f(x(t),y(t))=t^2+t^4',r'\frac{d}{dt}f(x(t),y(t))=2t+4t^3',r'\left.\frac{d}{dt}f(x(t),y(t))\right|_{t='+L(m)+r'}='+L(2*m+4*m**3)],2*m+4*m**3
 if slug=='divergence':
  return [T('Differentiate each vector component with respect to its matching coordinate and add.'),r'\nabla\cdot\mathbf F=\partial_x(x^2)+\partial_y(xy)+\partial_z('+L(m)+r'z)=2x+x+'+L(m),r'(\nabla\cdot\mathbf F)(1,1,1)='+L(m+3)],m+3
 if slug=='potential-endpoints':
  return [r'\Phi(x,y)=x^2+y^2,\qquad\mathbf F=\nabla\Phi',T('The fundamental theorem for line integrals gives the difference of potential values at the endpoints.'),r'\int_{(0,0)}^{('+L(m)+r',1)}\mathbf F\cdot d\mathbf r=\Phi('+L(m)+r',1)-\Phi(0,0)='+L(m*m+1)],m*m+1
 if slug=='box-average':
  return [T('The volume average of a sum is the sum of the coordinate averages. Each coordinate is uniformly averaged over its own interval.'),r'\overline{x}=\frac{'+L(m)+r'}2,\qquad\overline{y}=\frac12,\qquad\overline{z}=1',r'\overline{f}=\overline{x}+\overline{y}+\overline{z}='+L(m/2+R(3,2))],m/2+R(3,2)
 if slug=='gradient-max-direction':
  return [r'\nabla f(x,y)=e^{x+2y}(1,2),\qquad\nabla f(\ln '+L(m)+r',0)=('+L(m)+r','+L(2*m)+r')',T('Cauchy–Schwarz bounds the dot product with a unit direction by the gradient norm. Equality holds in the gradient direction.'),r'\max_{\|u\|=1}D_uf=\|\nabla f\|='+L(m*s.sqrt(5))],m*s.sqrt(5)
 if slug=='quadratic-critical-value':
  return [T('Both squared terms are nonnegative. The lower bound is attained if both vanish.'),r'x+y='+L(m)+r',\qquad x-y=1',r'(x,y)=\left('+L((m+1)/2)+r','+L((m-1)/2)+r'\right)',T('At this point the objective equals zero, so zero is the global minimum.')],s.Integer(0)
 if slug=='Lagrange-circle-linear':
  ans=s.sqrt(m*m+1)
  return [r''+L(m)+r'x+y=('+L(m)+r',1)\cdot(x,y)\le\sqrt{'+L(m*m+1)+r'}\sqrt{x^2+y^2}',T('The constraint makes the second factor one. Equality is attained by the unit vector parallel to the coefficient vector.'),r'(x,y)=\frac{('+L(m)+r',1)}{\sqrt{'+L(m*m+1)+r'}},\qquad\max='+L(ans)],ans
 if slug=='change-order':
  return [r'0\le x\le1,\ x\le y\le1\quad\Longleftrightarrow\quad0\le y\le1,\ 0\le x\le y',r'\int_0^1\int_0^y '+L(m)+r'y^{'+L(m-1)+r'}\,dx\,dy='+L(m)+r'\int_0^1y^{'+L(m)+r'}\,dy='+L(m/(m+1))],m/(m+1)
 if slug=='ellipse-transform':
  return [r'x='+L(m)+r'u,\qquad y=v',T('This maps the ellipse to the unit disk. The absolute Jacobian is the horizontal scale factor.'),r'\left|\frac{\partial(x,y)}{\partial(u,v)}\right|='+L(m),r'\textnormal{area}='+L(m)+r'\iint_{u^2+v^2\le1}du\,dv='+L(pi*m)],pi*m
 if slug=='polar-moment':
  return [r'x=r\cos\theta,\quad y=r\sin\theta,\quad x^2+y^2=r^2,\quad dA=r\,dr\,d\theta',r'\int_0^{2\pi}\int_0^1r^{'+L(2*m+1)+r'}\,dr\,d\theta='+L(pi/(m+1))],pi/(m+1)
 if slug=='Green-circulation':
  return [T('The counterclockwise orientation agrees with the positive orientation in Green’s theorem.'),r'P(x,y)=-y,\quad Q(x,y)=x,\quad Q_x-P_y=2',r'\oint_C(P\,dx+Q\,dy)=\iint_{x^2+y^2\le '+L(m*m)+r'}2\,dA='+L(2*pi*m*m)],2*pi*m*m
 if slug=='divergence-flux':
  return [r'\nabla\cdot(x,y,z)=3',T('Use the divergence theorem with the outward orientation. The enclosed ball has the stated radius.'),r'\iint\mathbf F\cdot\mathbf n\,dS=3\left(\frac{4\pi}{3}('+L(m)+r')^3\right)='+L(4*pi*m**3)],4*pi*m**3
 if slug=='surface-graph-area':
  return [r'z_x='+L(m)+r',\qquad z_y=1',r'dS=\sqrt{1+z_x^2+z_y^2}\,dx\,dy=\sqrt{'+L(m*m+2)+r'}\,dx\,dy',T('The projected unit square has area one, so integrating the constant area density gives the result.')],s.sqrt(m*m+2)
 if slug=='implicit-surface-partial':
  return [T('Differentiate the constraint with the second coordinate fixed.'),r'2x+2z\,z_x=0,\qquad z_x=-\frac{x}{z}',T('The specified branch has nonzero positive height at the point, so this derivative is locally well-defined.'),r'z_x(1,1)=-\frac1{'+L(m)+r'}'],-1/m
 if slug=='density-centroid':
  return [T('The horizontal centroid coordinate is the horizontal first moment divided by total mass.'),r'M=\int_0^1\int_0^1x^{'+L(m)+r'}\,dy\,dx=\frac1{'+L(m+1)+r'}',r'M_y=\int_0^1\int_0^1x^{'+L(m+1)+r'}\,dy\,dx=\frac1{'+L(m+2)+r'}',r'\bar x=\frac{M_y}{M}='+L((m+1)/(m+2))],(m+1)/(m+2)
 if slug=='spherical-moment':
  return [T('In spherical coordinates the integrand is a radial power. The volume element contributes two further radial powers, and the angular integral is the full solid angle.'),r'r=\sqrt{x^2+y^2+z^2},\qquad\int_0^{2\pi}\int_0^\pi\sin\phi\,d\phi\,d\theta=4\pi',r'\iiint r^{'+L(2*m)+r'}\,dV=4\pi\int_0^1r^{'+L(2*m+2)+r'}\,dr='+L(4*pi/(2*m+3))],4*pi/(2*m+3)
 if slug=='quadratic-eigenconstraint':
  ans=m+R(1,2)+s.sqrt(5)/2
  return [r'A=\begin{pmatrix}'+L(m)+r'&1\\1&'+L(m+1)+r'\end{pmatrix},\qquad\textnormal{objective}=(x,y)A\binom{x}{y}',T('Let ')+r'I'+T(' denote the identity matrix.'),T('A real symmetric matrix has an orthonormal eigenbasis. On the unit circle, its quadratic form is at most its largest eigenvalue, attained at a corresponding unit eigenvector.'),r'\det(A-\lambda I)=('+L(m)+r'-\lambda)('+L(m+1)+r'-\lambda)-1',r'\lambda_{\pm}='+L(m+R(1,2))+r'\pm\frac{\sqrt5}{2},\qquad\max=\lambda_+='+L(ans)],ans
 if slug=='moving-domain-derivative':
  return [T('First express the moving disk integral in polar coordinates, so its varying boundary is an ordinary upper limit.'),r'I(a)=2\pi\int_0^a e^{r^2}r\,dr=\pi(e^{a^2}-1)',r'I\prime(a)=2\pi ae^{a^2},\qquad I\prime('+L(m)+r')='+L(2*pi*m*s.exp(m*m))],2*pi*m*s.exp(m*m)
 if slug=='ellipsoid-inertia':
  return [r'x='+L(m)+r'u,\quad y=v,\quad z=w,\quad dV='+L(m)+r'\,du\,dv\,dw',T('The ellipsoid becomes the unit ball. The squared first coordinate supplies two additional scale factors.'),r'\iiint x^2\,dV='+L(m**3)+r'\iiint_{u^2+v^2+w^2\le1}u^2\,du\,dv\,dw',T('Rotational symmetry makes the three coordinate-square integrals equal; their sum is the radial-square integral.'),r'\iiint u^2\,dV=\frac13\,4\pi\int_0^1r^4\,dr=\frac{4\pi}{15}',r'\iiint x^2\,dV='+L(4*pi*m**3/15)],4*pi*m**3/15
 if slug=='nonlinear-Jacobian':
  return [r'u=xy,\quad v=x/y,\quad x=\sqrt{uv},\quad y=\sqrt{u/v}',T('Positivity makes this inverse single-valued. The product and ratio bounds become a rectangle.'),r'1\le u\le '+L(m)+r',\quad1\le v\le e^2,\qquad\left|\frac{\partial(x,y)}{\partial(u,v)}\right|=\frac1{2v}',r'\textnormal{area}=\int_1^{'+L(m)+r'}\int_1^{e^2}\frac{dv\,du}{2v}=('+L(m)+r'-1)\frac{\ln(e^2)}2='+L(m-1)],m-1
 if slug=='simplex-beta':
  ans=s.factorial(m)*s.factorial(m+1)/s.factorial(2*m+3)
  return [r'\int_0^{1-x}x^{'+L(m)+r'}y^{'+L(m+1)+r'}\,dy=\frac{x^{'+L(m)+r'}(1-x)^{'+L(m+2)+r'}}{'+L(m+2)+r'}',T('For nonnegative integer exponents, repeated integration by parts gives the factorial beta integral.'),r'\int_0^1x^a(1-x)^b\,dx=\frac{a!b!}{(a+b+1)!}\quad(a,b\in\mathbb Z_{\ge0})',r'I=\frac1{'+L(m+2)+r'}\frac{'+L(m)+r'!\,'+L(m+2)+r'!}{'+L(2*m+3)+r'!}='+L(ans)],ans
 if slug=='nonconservative-hole':
  return [r'x='+L(m)+r'\cos t,\quad y='+L(m)+r'\sin t,\quad dx=-'+L(m)+r'\sin t\,dt,\quad dy='+L(m)+r'\cos t\,dt',r'\frac{-y\,dx+x\,dy}{x^2+y^2}=\frac{'+L(m*m)+r'(\sin^2t+\cos^2t)}{'+L(m*m)+r'}\,dt=dt',r'\oint_C\frac{-y\,dx+x\,dy}{x^2+y^2}=\int_0^{2\pi}dt=2\pi',T('A zero curl away from the origin does not justify Green’s theorem on the enclosed disk, because the field is undefined at its center.')],2*pi
 if slug=='Stokes-tilted-surface':
  return [r'\mathbf F=(-y,x,z),\qquad\nabla\times\mathbf F=(0,0,2)',r'\mathbf r(x,y)=(x,y,'+L(m)+r'x+y),\quad\mathbf r_x\times\mathbf r_y=(-'+L(m)+r',-1,1)',T('This vector area element points upward, matching the boundary orientation.'),r'\oint_C\mathbf F\cdot d\mathbf r=\int_0^1\int_0^1(0,0,2)\cdot(-'+L(m)+r',-1,1)\,dx\,dy=2'],s.Integer(2)
 if slug=='boundary-versus-interior':
  return [r''+L(m)+r'xy-x^2-y^2='+L(m-2)+r'xy-(x-y)^2',r'0\le x,y\le1\quad\Longrightarrow\quad '+L(m-2)+r'xy-(x-y)^2\le '+L(m-2),T('At the upper-right corner both inequalities become equalities, so the bound is the global maximum.'),r'(x,y)=(1,1)'],m-2
 if slug=='surface-flux-graph':
  ans=pi/m+pi/(2*m*m)
  return [r'\mathbf r(x,y)=(x,y,1-x^2-y^2),\quad\mathbf r_x\times\mathbf r_y=(2x,2y,1)',r'\mathbf F(\mathbf r)\cdot(\mathbf r_x\times\mathbf r_y)=2x^2+2y^2+1-x^2-y^2=1+x^2+y^2',T('The area vector has positive vertical component. Integrate this flux density over the projected disk.'),r'2\pi\int_0^{'+L(1/s.sqrt(m))+r'}(1+r^2)r\,dr='+L(ans)],ans
 if slug=='mixed-Hessian-coordinate':
  return [T('Substitute the new coordinates before taking the mixed derivative.'),r'f(u+v,u-v)=(u+v)^2+'+L(m)+r'(u-v)^2',r'f(u+v,u-v)='+L(m+1)+r'u^2+'+L(2-2*m)+r'uv+'+L(m+1)+r'v^2',r'\partial_u\partial_v f='+L(2-2*m)],2-2*m
 if slug=='path-dependent-directional':
  return [T('Use the curved path with the same exponent as the first-coordinate power in the numerator.'),r'y=x^{'+L(m)+r'},\quad x>0',r'f(x,x^{'+L(m)+r'})=\frac{x^{'+L(m)+r'}x^{'+L(m)+r'}}{x^{'+L(2*m)+r'}+x^{'+L(2*m)+r'}}=\frac12',T('The value is constant along this punctured path, so its path limit equals that constant. This does not claim a two-dimensional limit exists.')],R(1,2)
 if slug=='Gaussian-precision':
  return [r''+L(m)+r'x^2+2xy+y^2=(y+x)^2+'+L(m-1)+r'x^2',r'u=y+x,\quad v=x,\qquad \left|\frac{\partial(u,v)}{\partial(x,y)}\right|=1',T('The positive squared coefficients give absolute integrability, so the transformed integral separates.'),r'\int_{\mathbb R}e^{-u^2}\,du\int_{\mathbb R}e^{-'+L(m-1)+r'v^2}\,dv=\sqrt\pi\sqrt{\frac\pi{'+L(m-1)+r'}}='+L(pi/s.sqrt(m-1))],pi/s.sqrt(m-1)
 if slug=='Vandermonde-extremum':
  return [T('Under the zero-sum constraint, expansion gives the following discriminant identity.'),r'(x-y)^2(y-z)^2(z-x)^2=\frac{(x^2+y^2+z^2)^3}{2}-27x^2y^2z^2',r'(x-y)^2(y-z)^2(z-x)^2=\frac{'+L(m**3)+r'}2-27(xyz)^2\le '+L(m**3/2),T('The following feasible triple makes the product of the coordinates zero and attains the bound.'),r'(x,y,z)=\left('+L(s.sqrt(m/2))+r',0,-'+L(s.sqrt(m/2))+r'\right)'],m**3/2
 if slug=='anisotropic-integrability':
  return [T('For each positive first coordinate, rescale the second coordinate to match the two denominator terms.'),r'y=x^{1/'+L(m)+r'}v,\qquad I(\alpha)=\int_0^1x^{\alpha+'+L(1/m-2)+r'}J(x)\,dx',r'J(x)=\int_0^{x^{-1/'+L(m)+r'}}\frac{dv}{1+v^{'+L(2*m)+r'}}',T('For first coordinates at most one, the upper limit is at least one. Bound the integral on the first unit interval below, and bound its tail above by a power.'),r'\frac12\le J(x)\le 1+\int_1^\infty v^{-'+L(2*m)+r'}\,dv=1+\frac1{'+L(2*m-1)+r'}',r'I(\alpha)<\infty\iff \alpha+'+L(1/m-2)+r'>-1\iff\alpha>'+L(1-1/m),T('At equality the comparison integral is logarithmically divergent.')],1-1/m
 if slug=='Gaussian-wedge':
  theta=pi/m;ans=pi*(m-1)/(2*m*s.sin(theta))
  return [T('Use the angle appearing in the cross term to define a whitening transformation.'),r'\theta='+L(theta)+r',\qquad u=x-\cos\theta\,y,\quad v=\sin\theta\,y',r'x^2-2\cos\theta\,xy+y^2=u^2+v^2,\qquad dx\,dy=\frac{du\,dv}{\sin\theta}',T('The positive quadrant maps to an oblique wedge. Its angular width is the angle between the positive horizontal ray and the image of the positive vertical ray.'),r'0<\arg(u+iv)<\pi-\theta',r'I=\frac{\pi-\theta}{\sin\theta}\int_0^\infty re^{-r^2}\,dr=\frac{\pi-\theta}{2\sin\theta}='+L(ans)],ans
 if slug=='planar-log-potential':
  a=1/m;ans=pi*(a*a-1)/2
  return [T('In polar coordinates, average the logarithm on each circle centered at the disk center.'),r'\frac1{2\pi}\int_0^{2\pi}\ln|re^{i\theta}-'+L(a)+r'|\,d\theta=\ln\max\left(r,'+L(a)+r'\right)',T('This circle mean follows by factoring out the larger radius and using the zero mean of the remaining convergent harmonic logarithm. Split the radial integral at the source radius.'),r'I=2\pi\left[\int_0^{'+L(a)+r'}r\ln('+L(a)+r')\,dr+\int_{'+L(a)+r'}^1r\ln r\,dr\right]='+L(ans),T('The point singularity is integrable because a radial logarithmic singularity has a finite area integral near its center.')],ans
 if slug=='two-centre-resolvent':
  c=1+m*m*u*(1-u);F=2/(m*s.sqrt(m*m+4))*s.atanh(m*(2*u-1)/s.sqrt(m*m+4));ans=4*pi*s.atanh(m/s.sqrt(m*m+4))/(m*s.sqrt(m*m+4))
  return [r'A=1+x^2+y^2,\quad B=1+(x-'+L(m)+r')^2+y^2',r'\frac1{AB}=\int_0^1\frac{du}{[uA+(1-u)B]^2}',r'uA+(1-u)B=(x-'+L(m)+r'(1-u))^2+y^2+c(u),\quad c(u)='+L(c),T('Translation and polar integration evaluate the plane integral. Nonnegativity justifies the order interchange.'),r'\iint_{\mathbb R^2}\frac{dx\,dy}{(x^2+y^2+c)^2}=2\pi\int_0^\infty\frac{r\,dr}{(r^2+c)^2}=\frac\pi c\quad(c>0)',r'I=\pi\int_0^1\frac{du}{c(u)},\qquad F(u)='+L(F)+r',\quad F\prime(u)=\frac1{c(u)}',r'\operatorname{arctanh}w=\frac12\ln\frac{1+w}{1-w}\quad(|w|<1)',r'I=\pi[F(1)-F(0)]='+L(ans)],ans
 if slug=='simplex-log-partition':
  a=1/m;b=2/m;c=1-a-b;ans=-a*s.log(a)-b*s.log(b)-c*s.log(c)
  return [T('Define the three positive normalized weights of the logarithmic partition function.'),r'Z=1+e^x+e^y,\qquad p=\frac{e^x}{Z},\quad q=\frac{e^y}{Z},\quad r=\frac1Z,\quad p+q+r=1',T('Vanishing first derivatives require the following weights and therefore give an explicit critical point.'),r'p='+L(a)+r',\quad q='+L(b)+r',\quad r='+L(c)+r',\qquad x=\ln\frac{p}{r},\quad y=\ln\frac{q}{r}',r'H=\begin{pmatrix}p(1-p)&-pq\\-pq&q(1-q)\end{pmatrix},\quad H_{11}>0,\quad\det H=pqr>0',T('This Hessian is positive definite everywhere, so the critical point is the unique global minimum.'),r'\min=-p\ln p-q\ln q-r\ln r='+L(ans)],ans
 if slug=='high-dimensional-lp-ball':
  ans=2**m*s.gamma(1+1/m)**m
  return [T('Let ')+r'V'+T(' denote the requested volume.'),T('Treat each coordinate orthant separately and transform coordinate magnitudes into nonnegative simplex variables.'),r'u_j=|x_j|^{'+L(m)+r'},\qquad dx_1\cdots dx_{'+L(m)+r'}='+L(m**(-m))+r'\prod_{j=1}^{'+L(m)+r'}u_j^{'+L(1/m-1)+r'}\,du_1\cdots du_{'+L(m)+r'}',r'\Gamma(a)=\int_0^\infty t^{a-1}e^{-t}\,dt\quad(a>0)',T('The Dirichlet simplex integral has positive exponents whose sum is one. Multiply by the number of orthants.'),r'V=\frac{2^{'+L(m)+r'}}{'+L(m)+r'^{'+L(m)+r'}}\frac{\Gamma('+L(1/m)+r')^{'+L(m)+r'}}{\Gamma(2)}',r'\Gamma(1+a)=a\Gamma(a),\quad\Gamma(2)=1\quad\Longrightarrow\quad V='+L(ans)],ans
 if slug=='log-simplex-moment':
  denom=(m+1)*(m+2)*(m+3);ans=((s.harmonic(m)-s.harmonic(m+3))*(1-s.harmonic(m+3))-(pi*pi/6-s.harmonic(m+3,2)))/denom
  return [T('Introduce a moment with two positive parameters. Differentiating once in each parameter supplies the two logarithms.'),r'M(a,b)=\iint_{x,y>0,\ x+y<1}x^{a-1}y^{b-1}\,dA=\frac{\Gamma(a)\Gamma(b)}{\Gamma(a+b+1)}',r'\psi(s)=\frac{d}{ds}\ln\Gamma(s),\qquad\psi_1(s)=\psi\prime(s)',r'\frac{M_{ab}}{M}=[\psi(a)-\psi(a+b+1)][\psi(b)-\psi(a+b+1)]-\psi_1(a+b+1)',r'a='+L(m+1)+r',\quad b=2,\qquad M(a,b)=\frac1{'+L(denom)+r'}',r'H_n=\sum_{j=1}^n\frac1j,\qquad H_n^{(2)}=\sum_{j=1}^n\frac1{j^2}',r'\psi('+L(m+1)+r')-\psi('+L(m+4)+r')=H_{'+L(m)+r'}-H_{'+L(m+3)+r'},\quad\psi(2)-\psi('+L(m+4)+r')=1-H_{'+L(m+3)+r'}',r'\psi_1('+L(m+4)+r')=\frac{\pi^2}{6}-H_{'+L(m+3)+r'}^{(2)}',r'\psi_1(s)=\sum_{k=0}^{\infty}\frac1{(s+k)^2}\quad(s>0),\qquad\psi_1(1)=\frac{\pi^2}{6}',T('The differentiated gamma recurrence and this classical trigamma series give the displayed harmonic values. Positive parameter neighborhoods dominate the logarithmic factors, justifying differentiation under the integral.'),r'I='+L(ans)],ans
 if slug=='lemniscate-petal-area':
  ans=2**(2/m-1)*s.sqrt(pi)*s.gamma(R(1,2)+1/m)/s.gamma(1+1/m)
  return [T('Let ')+r'A'+T(' denote the requested area.'),r'z=re^{i\theta},\qquad |z^{'+L(m)+r'}-1|^2\le1\iff r^{'+L(2*m)+r'}-2r^{'+L(m)+r'}\cos('+L(m)+r'\theta)\le0',r'0\le r\le[2\cos('+L(m)+r'\theta)]^{1/'+L(m)+r'}\quad\textnormal{on cosine-positive sectors}',T('There are equally many petals as the polynomial degree. The angular change of variable cancels this multiplicity.'),r'\phi='+L(m)+r'\theta,\qquad A=2^{'+L(2/m-1)+r'}\int_{-\pi/2}^{\pi/2}(\cos\phi)^{'+L(2/m)+r'}\,d\phi',T('Euler beta integration evaluates this finite cosine moment; both endpoint exponents are positive.'),r'\int_{-\pi/2}^{\pi/2}\cos^{2a}\phi\,d\phi=\frac{\sqrt\pi\,\Gamma(a+1/2)}{\Gamma(a+1)}\quad(a>-1/2)',r'A='+L(ans)],ans
 if slug=='squared-log-disk':
  q=1/(m*m);ans=pi/2*(s.polylog(2,q)+(1-1/q)*s.log(1-q)-1)
  return [r'z=re^{i\theta},\qquad \ln|1-z/'+L(m)+r'|=-\sum_{n=1}^\infty\frac{(r/'+L(m)+r')^n}{n}\cos(n\theta)',T('The ratio is uniformly less than one on the disk, so squaring and integrating the series is justified. Angular orthogonality removes terms with distinct frequencies.'),r'\int_0^{2\pi}\cos(n\theta)\cos(k\theta)\,d\theta=\begin{cases}\pi,&n=k,\\0,&n\ne k,\end{cases}\quad n,k\ge1',r'I=\frac\pi2\sum_{n=1}^\infty\frac{q^n}{n^2(n+1)},\qquad q='+L(q),r'\frac1{n^2(n+1)}=\frac1{n^2}-\frac1n+\frac1{n+1}',r'\operatorname{Li}_2(q)=\sum_{n=1}^\infty\frac{q^n}{n^2},\quad\sum_{n=1}^\infty\frac{q^n}{n}=-\ln(1-q),\quad\sum_{n=1}^\infty\frac{q^n}{n+1}=\frac{-\ln(1-q)-q}{q}',r'I=\frac\pi2\left[\operatorname{Li}_2(q)+(1-q^{-1})\ln(1-q)-1\right]='+L(ans)],ans
 if slug=='cube-simplex-cap':
  cut=m/3;upper=int(s.floor(cut));ans=sum((-1)**j*s.binomial(m,j)*(cut-j)**m for j in range(upper+1))/s.factorial(m)
  return [T('Let ')+r'V'+T(' denote the requested volume, and ')+r'V_0'+T(' the volume before imposing the coordinate upper bounds.'),T('Without the coordinate upper bounds, the nonnegative simplex has the following volume, where the cutoff is the sum bound in the question.'),r'c='+L(cut)+r',\qquad V_0=\frac{c^{'+L(m)+r'}}{'+L(m)+r'!}',T('For a chosen set of coordinates exceeding one, translate each chosen coordinate down by one. The remaining region is a simplex with the cutoff reduced by the size of that set.'),r'V=\frac1{'+L(m)+r'!}\sum_{j=0}^{'+str(upper)+r'}(-1)^j\binom{'+L(m)+r'}j(c-j)^{'+L(m)+r'}',T('Inclusion–exclusion counts each admissible point once. Zero-cutoff boundary regions have zero volume.'),r'V='+L(ans)],ans
 if slug=='polynomial-image-winding':
  radius=1+1/m;critical=(m-1)/(m-2)
  return [r'P(z)=(z-1)^2Q(z),\qquad Q(z)=\sum_{j=0}^{'+L(m-2)+r'}('+L(m-1)+r'-j)z^j',T('The input circle has the following radius. Choose a slightly larger radius below the coefficient-ratio bound.'),r'R='+L(radius)+r',\qquad R<R\prime<'+L(critical),T('The coefficients of the polynomial after scaling by the larger radius are positive and strictly decreasing.'),r'Q(R\prime w)=\sum_{j=0}^{'+L(m-2)+r'}b_jw^j,\qquad b_j=('+L(m-1)+r'-j)(R\prime)^j',T('Multiply this polynomial by one minus its variable. The constant coefficient equals the sum of the magnitudes of all other coefficients. Inside the unit disk, the strict triangle inequality therefore excludes a zero.'),T('Thus the remaining factor has no zero on or inside the input circle. The polynomial has exactly its double root at one inside that circle.'),r'\oint_\gamma\frac{-v\,du+u\,dv}{u^2+v^2}=2\pi\times\textnormal{winding number}=2\pi\cdot2=4\pi'],4*pi
 raise KeyError(slug)

LIMIT_SLUGS=['irrational-rotation-correlation','Newton-double-exponential-rate','recurrence-Hankel-growth','Dirichlet-endpoint-trace','monic-minimax-rate','binomial-moving-threshold','coupon-coverage-window','gcd-pair-density','floor-integer-approach','implicit-inverse-increment','Lp-maximum-limit','log-phase-average-limsup']

def limits(record,m,slug):
 if slug=='irrational-rotation-correlation':
  a=1/(m+1);ans=R(1,3)-a/2+a*a/2
  return [T('The fixed shift in the question is'),r'a='+L(a),T('For every nonzero integer frequency, the orbit has a vanishing exponential average: the geometric-sum numerator stays bounded and its denominator is nonzero.'),r'\frac1N\sum_{k=1}^N e^{2\pi i h k\sqrt2}\longrightarrow0\quad(h\in\mathbb Z\setminus\{0\})',T('Weyl’s criterion therefore makes the fractional parts uniformly distributed. Their correlated product is a Riemann-integrable function of the same orbit coordinate.'),r'q(t)=t\{t+a\}=\begin{cases}t(t+a),&0\le t<1-a,\\t(t+a-1),&1-a\le t<1,\end{cases}',r'\lim_{N\to\infty}\frac1N\sum_{k=1}^Nq(\{k\sqrt2\})=\int_0^1q(t)\,dt',r'\int_0^{1-a}t(t+a)\,dt+\int_{1-a}^1t(t+a-1)\,dt=\frac13-\frac a2+\frac{a^2}2='+L(ans)],ans
 if slug=='Newton-double-exponential-rate':
  r=(m-s.sqrt(2))/(m+s.sqrt(2))
  return [T('The iterates stay above the positive fixed point and decrease toward it. Normalize the error by a cross ratio.'),r'r_n=\frac{a_n-\sqrt2}{a_n+\sqrt2},\qquad r_{n+1}=r_n^2,\qquad r_0='+L(r),r'0<r_0<1,\quad r_n=r_0^{2^n},\quad a_n-\sqrt2=\frac{2\sqrt2\,r_0^{2^n}}{1-r_0^{2^n}}',r'(a_n-\sqrt2)^{1/2^n}=r_0\left(\frac{2\sqrt2}{1-r_0^{2^n}}\right)^{1/2^n}',T('The factor in parentheses tends to a finite positive constant, so its shrinking positive power tends to one.')],r
 if slug=='recurrence-Hankel-growth':
  P=2*m+1;D=m*m+m-1
  return [r'H_n=a_na_{n+2}-a_{n+1}^2',T('Substitute the given recurrence into two consecutive determinants. The leading products cancel, leaving a scalar recurrence.'),r'H_{n+1}='+L(D)+r'H_n',r'a_2='+L(P*P-2*D)+r',\qquad H_0=2\cdot'+L(P*P-2*D)+r'-'+L(P)+r'^2=5',r'H_n=5\cdot'+L(D)+r'^n,\qquad H_n^{1/n}=5^{1/n}\cdot'+L(D)+r'\longrightarrow '+L(D)],D
 if slug=='Dirichlet-endpoint-trace':
  ans=pi**(m+1)/2
  return [r'K_N(x)=\frac{\sin((2N+1)x)}{\sin x}=1+2\sum_{j=1}^N\cos(2jx)',r'\int_0^\pi K_N(x)\,dx=\pi,\qquad K_N(\pi-x)=K_N(x)',T('Subtract the line interpolating the two endpoint values of the polynomial.'),r'\ell(x)=\pi^{'+L(m-1)+r'}x,\qquad g(x)=\frac{x^{'+L(m)+r'}-\ell(x)}{\sin x}',T('The numerator vanishes at both endpoints. Dividing by the simple sine zeros gives a continuously differentiable extension of this quotient.'),r'\int_0^\pi\ell(x)K_N(x)\,dx=\frac{\pi^{'+L(m+1)+r'}}2',r'\left|\int_0^\pi g(x)\sin((2N+1)x)\,dx\right|\le\frac{|g(0)|+|g(\pi)|+\int_0^\pi|g\prime(x)|\,dx}{2N+1}\longrightarrow0',T('The remaining integral tends to zero by this integration-by-parts bound, leaving only the endpoint-line contribution.')],ans
 if slug=='monic-minimax-rate':
  return [r'T_n(\cos\theta)=\cos(n\theta),\qquad T_{n+1}(x)=2xT_n(x)-T_{n-1}(x)',T('These Chebyshev polynomials have leading coefficient given by the recurrence. Scaling produces a monic polynomial on the stated interval.'),r'q_n(x)=\frac{'+L(m)+r'^n}{2^{n-1}}T_n(x/'+L(m)+r'),\qquad C_n=\frac{'+L(m)+r'^n}{2^{n-1}}',T('The maximum absolute value of this polynomial is the displayed amplitude, attained with alternating signs at one more point than its degree.'),T('If a monic competitor had a smaller maximum, subtracting this polynomial would give alternating signs at those points. The difference would have at least as many distinct roots as the original degree, although its degree is smaller. This is impossible.'),r'M_n=C_n,\qquad M_n^{1/n}=\frac{'+L(m)+r'}2\,2^{1/n}\longrightarrow '+L(m/2)],m/2
 if slug=='binomial-moving-threshold':
  a=m/4;ans=(1+s.erf((2*a)/s.sqrt(2)))/2
  return [T('Interpret the normalized sum as the probability that a binomial count lies below the displayed cutoff.'),r'S_n\sim\operatorname{Binomial}(n,1/2),\qquad Z_n=\frac{2(S_n-n/2)}{\sqrt n}',r'\phi_n(t)=\mathbb E[e^{itZ_n}]=\cos(t/\sqrt n)^n\longrightarrow e^{-t^2/2}\quad(t\in\mathbb R)',T('The quadratic expansion of the logarithm of cosine proves this characteristic-function limit. Lévy’s continuity theorem gives a standard normal limit.'),r'\frac{2(\lfloor n/2+'+L(a)+r'\sqrt n\rfloor-n/2)}{\sqrt n}\longrightarrow '+L(2*a),T('The normal distribution function is continuous, so fixed nearby thresholds sandwich the moving cutoff.'),r'\Phi(z)=\frac1{\sqrt{2\pi}}\int_{-\infty}^{z}e^{-u^2/2}\,du=\frac{1+\operatorname{erf}(z/\sqrt2)}2',r'\lim=\Phi('+L(2*a)+r')='+L(ans)],ans
 if slug=='coupon-coverage-window':
  ans=s.exp(-1/m)
  return [T('For a fixed number of specified boxes, all of them remain empty exactly when every throw avoids that set.'),r'E_j(n)=\binom nj\left(1-\frac jn\right)^{r_n}\quad(j\ge0\textnormal{ fixed})',T('The quantity just defined is the sum of the probabilities over all sets of that size. The logarithmic expansion and the given number of throws give its limit.'),r'\ln(1-j/n)=-j/n+O(n^{-2}),\qquad E_j(n)\longrightarrow\frac{1}{'+L(m)+r'^j j!}',r'S_K(n)=\sum_{j=0}^{K}(-1)^jE_j(n),\qquad S_{2K+1}(n)\le p_n\le S_{2K}(n)',T('These are the finite Bonferroni bounds. First take the number of boxes to infinity with the truncation fixed; only then let the truncation grow.'),r'\lim_{n\to\infty}p_n=\sum_{j=0}^\infty\frac{(-1)^j}{'+L(m)+r'^j j!}=e^{-1/'+L(m)+r'}='+L(ans)],ans
 if slug=='gcd-pair-density':
  ans=6/(pi*pi*m*m)
  return [T('After dividing both coordinates by the prescribed greatest common divisor, count coprime pairs.'),T('Let the Möbius function be zero for integers with a repeated prime factor, and otherwise the sign determined by the number of distinct prime factors.'),r'\mu(d)=(-1)^k\quad\textnormal{when }d\textnormal{ is a product of }k\textnormal{ distinct primes},\qquad\mu(1)=1',r'\sum_{d\mid g}\mu(d)=\begin{cases}1,&g=1,\\0,&g>1,\end{cases}',r'C_N=\sum_{d\le N/'+L(m)+r'}\mu(d)\left\lfloor\frac{N}{'+L(m)+r'd}\right\rfloor^2',r'\frac{|\mu(d)|}{N^2}\left\lfloor\frac{N}{'+L(m)+r'd}\right\rfloor^2\le\frac1{'+L(m*m)+r'd^2}',T('The divisor identity follows by choosing subsets of the distinct prime factors: for a nonunit integer the signs sum to a positive power of zero.'),T('The right-hand side is summable, so dominated convergence for series passes the limit through the divisor sum.'),r'\lim\frac{C_N}{N^2}=\frac1{'+L(m*m)+r'}\sum_{d=1}^\infty\frac{\mu(d)}{d^2}=\frac1{'+L(m*m)+r'}\prod_{p\ \mathrm{prime}}(1-p^{-2})',T('Absolute convergence permits expansion of the Euler products into prime factorizations. The two reciprocal Euler products cancel.'),r'\zeta(2)=\sum_{n=1}^\infty n^{-2}=\frac{\pi^2}{6}\quad\Longrightarrow\quad\lim='+L(ans)],ans
 if slug=='floor-integer-approach':
  below=int(m)%2==0;ratio=s.sin(x)/x if below else x/s.sin(x);ans=m-1 if below else m
  return [r'\frac{\sin x}{x}<1<\frac{x}{\sin x}\quad(0<x<\pi/2)',T('The chosen ratio tends to one from a fixed side. Therefore, sufficiently near zero, its scaled value lies in the following open interval.'),r''+L(m-1 if below else m)+r'<'+L(m*ratio)+r'<'+L(m if below else m+1),r'\left\lfloor '+L(m*ratio)+r'\right\rfloor='+L(ans)],ans
 if slug=='implicit-inverse-increment':
  return [r'f(t)=t^3+'+L(m)+r't,\qquad f\prime(t)=3t^2+'+L(m)+r'>0',T('The function is strictly increasing and onto the real line, so its inverse exists. Differentiate their composition at the relevant point.'),r'f(1)='+L(m+1)+r',\qquad f(g(u))=u\quad\Longrightarrow\quad g\prime(u)=\frac1{f\prime(g(u))}',r'\lim_{h\to0}\frac{g('+L(m+1)+r'+h)-g('+L(m+1)+r')}{h}=g\prime('+L(m+1)+r')=\frac1{'+L(m+3)+r'}'],1/(m+3)
 if slug=='Lp-maximum-limit':
  ans=m**m/(m+1)**(m+1)
  return [r'f(x)=x^{'+L(m)+r'}(1-x),\qquad f\prime(x)=x^{'+L(m-1)+r'}('+L(m)+r'-'+L(m+1)+r'x)',r'M=\max_{[0,1]}f=f\left('+L(m/(m+1))+r'\right)='+L(ans),T('For any ')+r'0<\varepsilon<M'+T(', continuity gives an interval of length ')+r'\delta>0'+T(' on which ')+r'f\ge M-\varepsilon'+T('.'),r'\delta(M-\varepsilon)^n\le\int_0^1 f(x)^n\,dx\le M^n',T('Take positive nth roots and pass to the limit. The interval-length factor tends to one; then let the error decrease to zero.'),r'\lim_{n\to\infty}\left(\int_0^1f^n\right)^{1/n}=M='+L(ans)],ans
 if slug=='log-phase-average-limsup':
  ans=1/s.sqrt(1+m*m)
  return [r'f(x)=\cos('+L(m)+r'\ln x),\qquad |f\prime(x)|\le\frac{'+L(m)+r'}x',T('Comparing each unit interval with its endpoint bounds the sum–integral discrepancy by a constant plus a logarithm.'),r'\sum_{k=1}^n f(k)=\int_1^n f(x)\,dx+O(\ln n)',r'F(x)=\frac{x[\cos('+L(m)+r'\ln x)+'+L(m)+r'\sin('+L(m)+r'\ln x)]}{'+L(1+m*m)+r'},\qquad F\prime(x)=\cos('+L(m)+r'\ln x)\quad(x>0)',r'\frac1n\sum_{k=1}^nf(k)=\frac{\cos('+L(m)+r'\ln n)+'+L(m)+r'\sin('+L(m)+r'\ln n)}{'+L(1+m*m)+r'}+o(1)',T('The oscillating expression has the following amplitude. It is approached along integer subsequences whose logarithmic phase approaches its maximizing angle.'),r'\theta_0=\arctan '+L(m)+r',\qquad n_j=\left\lfloor\exp\left(\frac{2\pi j+\theta_0}{'+L(m)+r'}\right)+\frac12\right\rfloor',r''+L(m)+r'\ln n_j-(2\pi j+\theta_0)\longrightarrow0,\qquad\limsup='+L(ans)],ans
 raise KeyError(slug)

DIFF_SLUGS=['sharp-endpoint-derivative','cyclic-determinant-second-derivative','oscillatory-regularity-pair','newton-iteration-jet','moving-endpoint-parameter-second']

def differentiation(record,m,slug):
 if slug=='sharp-endpoint-derivative':
  return [T('Interpolate the polynomial at the extrema of the Chebyshev polynomial of the allowed degree.'),r'x_k=\cos\left(\frac{k\pi}{'+L(m)+r'}\right),\quad0\le k\le '+L(m),r'\ell_k(x)=\prod_{j\ne k}\frac{x-x_j}{x_k-x_j},\qquad P\prime(1)=\sum_{k=0}^{'+L(m)+r'}P(x_k)\ell_k\prime(1)',T('At the right endpoint, the derivative of the first cardinal polynomial is positive. For every other cardinal polynomial, its numerator derivative is positive and its denominator has exactly as many negative factors as its index.'),r'\operatorname{sgn}(\ell_k\prime(1))=(-1)^k,\qquad P\prime(1)\le\sum_{k=0}^{'+L(m)+r'}|\ell_k\prime(1)|',r'T_{'+L(m)+r'}(\cos\theta)=\cos('+L(m)+r'\theta),\qquad T_{'+L(m)+r'}(x_k)=(-1)^k',T('Thus the bound is exactly the endpoint derivative of the Chebyshev polynomial. Its unit uniform norm also makes equality attainable.'),r'\sum_k|\ell_k\prime(1)|=T_{'+L(m)+r'}\prime(1)='+L(m*m),T('For completeness, differentiate the Chebyshev recurrence at the endpoint and denote its derivative sequence by ')+r'a_n'+T('.'),r'T_0(x)=1,\quad T_1(x)=x,\quad T_{n+1}(x)=2xT_n(x)-T_{n-1}(x)',r'a_n=T_n\prime(1),\quad a_0=0,\quad a_1=1,\quad a_{n+1}=2+2a_n-a_{n-1}',r'a_n=n^2\quad(n\ge0)'],m*m
 if slug=='cyclic-determinant-second-derivative':
  ans=m*m*(m*m-1)/6
  return [T('In the determinant expansion by column multilinearity, the quadratic coefficient selects two diagonal increments. Each selection leaves the principal minor obtained by deleting those two coordinates.'),T('A tridiagonal path block of length ')+r'k'+T(' with diagonal entries two and neighbor entries minus one has determinant ')+r'D_k'+T('.'),r'D_0=1,\quad D_1=2,\quad D_k=2D_{k-1}-D_{k-2}\quad\Longrightarrow\quad D_k=k+1',T('Deleting two cycle vertices at cyclic distance ')+r'r'+T(' leaves path lengths ')+r'r-1'+T(' and ')+r''+L(m)+r'-r-1'+T('. Their determinant product is ')+r'r('+L(m)+r'-r)'+T('.'),r'[x^2]\det A(x)=\frac{'+L(m)+r'}2\sum_{r=1}^{'+L(m-1)+r'}r('+L(m)+r'-r)=\frac{'+L(m*m*(m*m-1))+r'}{12}',T('Each unordered pair was counted twice by starting vertex and cyclic distance. Finally convert the quadratic coefficient to a second derivative.'),r'(\det A)\prime\prime(0)=2!\,[x^2]\det A(x)='+L(ans)],ans
 if slug=='oscillatory-regularity-pair':
  return [T('For nonzero inputs, repeated differentiation has a leading oscillatory term whose power drops by two at each step.'),r'f^{(k)}(x)=x^{'+L(2*m+2)+r'-2k}\bigl(\varepsilon_k\phi_k(1/x)+O(x)\bigr)',T('Here ')+r'\phi_k'+T(' is sine or cosine, and ')+r'\varepsilon_k\in\{-1,1\}'+T('. The chain rule cycles the leading trigonometric factor and its sign.'),r'\frac{f^{(k-1)}(x)-f^{(k-1)}(0)}x=O\!\left(|x|^{'+L(2*m+3)+r'-2k}\right)\longrightarrow0\quad(1\le k\le '+L(m+1)+r')',T('Induction therefore gives all these derivatives at zero, each equal to zero. Through the preceding order, the punctured derivatives also tend to zero and are continuous.'),r'f^{('+L(m+1)+r')}(x)=\varepsilon_{'+L(m+1)+r'}\phi_{'+L(m+1)+r'}(1/x)+O(x)',T('Reciprocal-phase sequences make the leading term approach opposite nonzero values. This derivative is discontinuous, and dividing it by the input also prevents the next derivative at zero from existing.'),r'(r,s)=('+L(m+1)+r','+L(m)+r')'],s.Tuple(m+1,m)
 if slug=='newton-iteration-jet':
  c=(m-1)/2;ans=s.factorial(8)*c**7
  return [T('Expand the Newton map about its fixed point, using a small displacement from that point.'),r'N(1+z)-1=cz^2+O(z^3),\qquad c=\frac{N\prime\prime(1)}2='+L(c),r'N(1)=1,\qquad N\prime(1)=0',T('Composing the map squares the previous leading error and multiplies its coefficient by the same quadratic coefficient.'),r'N^{\circ2}(1+z)-1=c^3z^4+O(z^5)',r'H(1+z)-1=c^7z^8+O(z^9)',T('The eighth derivative is the eighth Taylor coefficient multiplied by the factorial of its order.'),r'H^{(8)}(1)=8!\,c^7='+L(ans)],ans
 if slug=='moving-endpoint-parameter-second':
  ans=(2*m*m+m-3)*s.E
  return [T('Apply Leibniz’s rule, retaining both moving endpoints and the explicit parameter derivative of the integrand.'),r'F\prime(x)='+L(m)+r'x^{'+L(m-1)+r'}e^{x^{'+L(m+1)+r'}}-e^{x^2}+\int_x^{x^{'+L(m)+r'}}te^{xt}\,dt',T('Differentiating the first two terms and evaluating at the common endpoint gives'),r'\left.\frac{d}{dx}\left('+L(m)+r'x^{'+L(m-1)+r'}e^{x^{'+L(m+1)+r'}}-e^{x^2}\right)\right|_{x=1}='+L((2*m*m-2)*s.E),T('Although the remaining integral has zero length at this point, its derivative has a moving-boundary contribution. Its interior integral still has zero length.'),r'\left.\frac{d}{dx}\int_x^{x^{'+L(m)+r'}}te^{xt}\,dt\right|_{x=1}=('+L(m)+r'-1)e',r'F\prime\prime(1)='+L((2*m*m-2)*s.E)+r'+'+L((m-1)*s.E)+r'='+L(ans)],ans
 raise KeyError(slug)

SERIES_SLUGS=['p-series-pair','alternating-absolute-conditional','direct-comparison-information','taylor-coefficient-derivative','linearity-given-convergent-sums']

def series_easy(record,m,slug):
 if slug=='p-series-pair':
  pairs=[(R(1,2),R(1,3)),(1,2),(2,1),(R(3,2),R(5,2)),(R(3,4),1),(R(4,3),R(2,3)),(R(3,5),R(7,6)),(R(7,4),R(9,4))];p,q=map(s.sympify,pairs[int(m)-4]);a='converges' if p>1 else 'diverges';b='converges' if q>1 else 'diverges'
  return [T('For positive exponents, the integral comparison gives the convergence threshold for a positive p-series.'),r'\int_1^\infty x^{-p}\,dx=\begin{cases}1/(p-1),&p>1,\\+\infty,&0<p\le1,\end{cases}',r'\sum_{n=1}^\infty n^{-p}\textnormal{ converges }\iff p>1',r'p_A='+L(p)+r',\qquad p_B='+L(q),T('The first series '+a+' and the second '+b+'.')],a+'|'+b
 if slug=='alternating-absolute-conditional':
  pairs=[(R(1,2),1),(R(3,4),R(3,2)),(2,R(1,2)),(R(3,2),2),(1,R(3,4)),(R(3,5),R(7,5)),(R(9,5),1),(R(11,5),R(8,5))];p,q=map(s.sympify,pairs[int(m)-4]);a='absolute' if p>1 else 'conditional';b='absolute' if q>1 else 'conditional'
  return [T('Both displayed exponents are positive. In each series the term magnitudes decrease to zero, so the alternating-series test proves convergence.'),r'p_A='+L(p)+r',\quad p_B='+L(q)+r',\qquad\sum_{n=1}^\infty|(-1)^{n-1}n^{-p}|=\sum_{n=1}^\infty n^{-p}',T('This absolute-value series converges exactly when its exponent exceeds one. Otherwise the already established alternating convergence is conditional.'),T('The first series is '+a+' and the second is '+b+'.')],a+'|'+b
 if slug=='direct-comparison-information':
  i=int(m)-4;upper=i%4 in(0,2);p=m/8 if i%4==0 else m/16 if i%4==1 else m/4;conv=p>1
  first=[r'b_n=n^{-'+L(p)+r'},\qquad\sum_{n=1}^\infty b_n\textnormal{ '+('converges' if conv else 'diverges')+r'}',T('This benchmark classification follows from the positive p-series exponent threshold.')]
  if upper and conv:return first+[T('All terms are nonnegative and bounded above by this convergent benchmark. Their partial sums are increasing and bounded, so convergence is forced.')],'forced-convergence'
  if not upper and not conv:return first+[T('The original terms are bounded below by this divergent positive benchmark. Their partial sums are therefore unbounded, so divergence is forced.')],'forced-divergence'
  if upper:return first+[T('The bound allows both of the following sequences.'),r'a_n=0\quad\textnormal{gives convergence},\qquad a_n=b_n\quad\textnormal{gives divergence}',T('The bound alone therefore does not determine convergence.')],'both-possible'
  return first+[T('The bound allows the convergent benchmark and also the divergent constant sequence.'),r'a_n=b_n\quad\textnormal{or}\quad a_n=1,\qquad b_n\le1\quad(n\ge1)',T('Thus either behavior is possible under the same bound.')],'both-possible'
 if slug=='taylor-coefficient-derivative':
  c=(-1)**m*(m-3)/(m+2);ans=s.factorial(m)*c
  return [T('A power series with positive radius can be differentiated term by term near its center. At the center, every power except the differentiated order contributes zero.'),r'f^{('+L(m)+r')}(2)='+L(m)+r'!\,a_{'+L(m)+r'}',r'f^{('+L(m)+r')}(2)='+L(m)+r'!\left('+L(c)+r'\right)='+L(ans)],ans
 if slug=='linearity-given-convergent-sums':
  A=m-2;B=m+1;ans=-m*m+m-4
  return [T('For every finite endpoint, distribute the coefficients across the two partial sums.'),r'\sum_{n=1}^N(2a_n-'+L(m)+r'b_n)=2\sum_{n=1}^Na_n-'+L(m)+r'\sum_{n=1}^Nb_n',T('Both component sums converge by hypothesis, so taking the limit preserves this finite linear combination.'),r'\sum_{n=1}^\infty(2a_n-'+L(m)+r'b_n)=2\left('+L(A)+r'\right)-'+L(m)+r'\left('+L(B)+r'\right)='+L(ans)],ans
 raise KeyError(slug)


def _route(record):
 fid=record.get('familyId','')
 for level in ['easy','medium','hard','olympiad']:
  stem='m3-differential-equations-'+level+'-'
  if fid.startswith(stem) and fid[len(stem):] in ODE_SLUGS:return ode,fid[len(stem):]
  stem='m3-multivariable-'+level+'-'
  if fid.startswith(stem) and fid[len(stem):] in MV_SLUGS:return multivariable,fid[len(stem):]
  stem='m3-limits-'+level+'-'
  if fid.startswith(stem) and fid[len(stem):] in LIMIT_SLUGS:return limits,fid[len(stem):]
  stem='m3-differentiation-'+level+'-'
  if fid.startswith(stem) and fid[len(stem):] in DIFF_SLUGS:return differentiation,fid[len(stem):]
  stem='m3-series-'+level+'-'
  if level=='easy' and fid.startswith(stem) and fid[len(stem):] in SERIES_SLUGS:return series_easy,fid[len(stem):]
 raise ValueError('family is outside this supplemental correction module')

def supports(record):
 try:_route(record);parameter(record);return True
 except (ValueError,KeyError,TypeError):return False

def derived_solution(record):
 fn,slug=_route(record);steps,value=fn(record,parameter(record),slug)
 steps=[notation(step) for step in steps]
 if any(r'I(\alpha)' in step for step in steps):steps.insert(0,T('Let ')+r'I(\alpha)'+T(' denote the integral in the question as a function of its exponent.'))
 elif any(r'I=' in step for step in steps):steps.insert(0,T('Let ')+r'I'+T(' denote the integral requested in the question.'))
 if any(r'\operatorname{sech}' in step for step in steps):steps.insert(0,r'\operatorname{sech}t=1/\cosh t')
 if any(r'\Gamma' in q for q in steps) and not any(r'\Gamma(a)=\int' in q for q in steps):
  steps.insert(0,r'\Gamma(a)=\int_0^\infty t^{a-1}e^{-t}\,dt\quad(a>0)')
 return {'steps':steps,'expectedResult':value,'familyId':record['familyId'],'sourceContentHash':record['contentHash'],'symbolPolicy':'Concrete builder parameters; any auxiliary variable is introduced in the derivation; no blanket parameter preface.'}

def corrected_solution(record):
 data=derived_solution(record)
 return data['steps']+[answer_math(record)]

# Statement corrections are opt-in and source-hash guarded. The guard table is
# generated from the reviewed immutable artifact by validate.py, then embedded.
STATEMENT_GUARDS={'cn_732134a8cdbe89e622fe': '2f9c9b4924e7a7b6b9d66fee45f9f9e9eec743acd9f5ceb19578b31efcf970bd', 'cn_8f731584fa6103dee356': 'b22c8bb5b58c35e5d6b660752ba797df418ef72c93e0f0b63db0ae318e0dd7b0', 'cn_5a693125814cccb9be36': 'a5ed4f57d01a737064d92fe9058c5104e70339951e994c6a23622e53d320c304', 'cn_70778bbef92a5761931d': 'd8ea98c7fa66b8d49a6d303a6e28b8b7a5c1a270d9242a5f4b8d238642fb11ab', 'cn_3961d25e0e645e67aad0': 'c7c539891c4b784139a4c11f7a8b88d9186ff1622acf01a1b5910d8bcf241881', 'cn_1fa956463768aafb3721': '3b6e5f2b21aa4f935ab75544f6c79ccf9b6230eb8b634c7ba5bbbb5bf2f3f7da', 'cn_aec89cdbfd9494ac4533': 'c36b0cd320bbdbafc377a924066a2a9d937b23041e630b0cb6bafe6600373584', 'cn_5fe4993d19acb789c851': '51d38e348035b2e8148a51671fcb72a80dac42a42008482f010fce3c72a35efb', 'cn_4e2c34b53ab54cf68b45': 'a51de74fb9d333d0e726522e04915da9e61f0b917075ee2118c4de7bb28613f0', 'cn_b9dc58f46ede74585d82': '3c5ed73fd45bea0503689474efe83590d296e0934cd96e0034e28558a89522a5', 'cn_2bd6768a9d4c82f49778': '6933fb9fb271084329353493011f81b5c8ad224fa83b9b07189d252b3e648e13', 'cn_cff22339f8a1acb8515a': 'fed850ebf036e0991c6bea932bfdfc1e577507da7b19d8398c454ab1dcc6ff41', 'cn_cc6a7800cc7fe25ba947': '046a4d6719a2abe020935cbebdb70a478d9703f16f9359feba1e997a8022bbc4', 'cn_05100d0c201ee53ca05f': '2b3bc7fa88811dc742011f2638f6e3909368d76a776978eb7e5371240c8a002a', 'cn_976d5c86ca127de71dd3': 'a0fd9b1076e48b148aed80359d1c616eaee371298daf7024280410cb12aad8b5', 'cn_4cfdead51d72498d54bd': 'e4223d367eb949c75454362d8c9fc7ddc9b41010cda8c84018f9dfa4fde33ad6', 'cn_1885f9bf681641dcde4d': 'fee5654be89b603afa7710a7158423b4903c4c9f61abbfe0a20fee38691b3606', 'cn_14916b106f2a4b4f8e28': '248da14c67fa22b417db86c5f493e1006efcad9c4ed28bef2730ebc5dacc0c17', 'cn_2238739e679a73a7f4a7': '07becae65657fbf5ad23359d9c6c908c35f386813a1a72e65ece0b258b9529f4', 'cn_506ef2c678160ef90947': '650baa25347743ce483bd1fc8e2cbe15c4b55a771bca7c24d9f11852a0025ed2', 'cn_48911a4c927884860ad0': 'b91f37b5436e62dfd7d7d646e56d46d277871ea85988b3b3cbbe57352b9afdfc', 'cn_39db9abac4dab02851dd': '028d7c86fd8e3cd954558169c0f523731d94b84e7f3c106b5a8a16736f2c6841', 'cn_ef3c228e56b5b40ddcae': 'f6d91f9cdf45dabed7a14a3328210b04c3c9491de0808c5ee6d13aa2c0894267', 'cn_526c44447e2f0db51f30': 'b206c435c1d1ade333745d3d955f59f94e429d2a02d2757cd3d246bff6c79844', 'cn_14d220244aa2b2c309e4': '5236270e11d48a873e8508e4690f310caa5ca280aa139b7a1d8130ecde3002ca', 'cn_f600c9c0c569ca8d4c88': '552f5d8ba32a829ce5e61cebb860f55e7d27f32b622edb9e7d1720bb26369d50', 'cn_aec58252cc80bc5671bc': 'cceb3918e5cb0d49894479e3ec231ddcd7e67117448f10e5546b01f95ffc33e3', 'cn_017ca37c71412d54feee': 'd3faddfcda50857d3e0c229c6d5ad30e40a7fd604f197c55a48eaf471846a0be', 'cn_82ae0d612854d38aca52': 'cebfaa615d4959c47aaa5b998facca272cbe83b6bacc473bd9ae30079543728d', 'cn_6c03cd108e90ea951b35': '40d6dee2611a141772c4984ccdb3477ea2370d90a81b702fdd6d39bfd4df2b7e', 'cn_0bd27a80ebd0fb8d0395': 'e1685918b63b6538453d3e60f7733b641271d49de855c0239fb49248febaa3bd', 'cn_7abe58dff881a2299f41': 'e5f935035b5d01f08c10e85d3ddbecd404fff321e961d69fb31712f38eee0187', 'cn_59149487a051afd9f83c': 'dadb58968489c590610dc058b93fbb214a541eb1a2ce10eeaf45933acb0db03b', 'cn_dc917114afd341eaf1e8': 'dd1d7bb8da46047cb5c685d2fa3874289700fee6759047163eeda2472c9a585f', 'cn_0457365b5bd58cf359cb': '412a674d45a796cb663a190687f0bf10e9bee64cf45720a7d4868853bf02e106', 'cn_152e4d861a6a3be4cca3': '124289a9277885970b5ec20ebc59f803b13ff41e36c463fb0c9b5b4d1fce6ed4', 'cn_04a71e215111695c872c': 'dd520c1b76ff539290a380cce2af379ba6fabd89de252e1f05e60698dd76a770', 'cn_33d43be16b313548afe4': '3050ee34869237321c03ef9c43fa275a22a7c30664a4d89451f0fa433ba53588', 'cn_ffea6cc82f6bfd748900': '81a404e02a0383929a8908ef59748d47f66411ca4fd119ff8268546a02dc4e32', 'cn_911489e299970ea91f76': '9d2c31b7e7ab43af7295f7175bc5699f629acde183acfcce42aa3c82c29cfc5d', 'cn_7eba366f84aed2c76b44': '07265e614a579cd36c1f45f13cedecb3f346e3cd349d1381ee86a983d35c8397', 'cn_c5fc14b0e2e3b127bf5b': '33c2adf37f46dc5f6a5f7a6f0a100073f36cd003ab9470c5d7d8a9c88a679c53', 'cn_5cd26fc18a0d90833ce7': '05463589ef9ef5c19db6db42a8e430ef14daa85cc2f902f7c90b5dd4aa11b36f', 'cn_501d352db65ded206940': '39f30887531314c49d044e1ffad1ad79a56f6d9ef2979d04667b9012385d9246', 'cn_33aa6acfe25c89de2a4e': '83ee2edb761b36f217092214aabf37b3e7c5de340736233a4c44645e40c0377d', 'cn_fc65b448dc320d3af124': '138cdefd9555dd5121dc233f89d64521d762968625ee2b28768740c4e2e848ea', 'cn_06cbbe31ff4c21620c80': '3c35b818296bd97191016183f972e650725182e2c4c77422e512793802dd08b2', 'cn_b8c6bc699fc512dc802b': '8efa8f394ae1ad811d3edff62d3c0bf77a4a6e2313f9256d3749a0e67a0fd8ed'}
def corrected_statement(record):
 if STATEMENT_GUARDS.get(record.get('problemId'))!=record.get('contentHash'):return None
 fn,slug=_route(record);m=parameter(record)
 if fn is multivariable and slug=='path-dependent-directional':
  return r'f(x,y)=\frac{x^{'+L(m)+r'}y}{x^{'+L(2*m)+r'}+y^2},\quad(x,y)\ne(0,0).\quad'+T('Find the limit along ')+r'y=x^{'+L(m)+r'}'+T(' as ')+r'x\downarrow0'+T('.')
 if fn is ode and slug=='nonlinear-energy-speed':
  return r'y\prime\prime=-2y^3,\quad y(0)='+L(m)+r',\quad y\prime(0)=0.\quad'+T('Find the maximum speed ')+r'|y\prime|'+T(' during the oscillation.')
 if fn is ode and slug=='periodic-floquet-multiplier':
  return r'y\prime=('+L(m)+r'+\sin t)y-y^2.\quad'+T('Let ')+r'y_*'+T(' be a positive ')+r'2\pi'+T('-periodic solution, and let ')+r'P'+T(' map the initial value ')+r'y(0)'+T(' to ')+r'y(2\pi)'+T('. Find ')+r'P\prime(y_*(0))'+T('.')
 if fn is ode and slug=='sharp-lifetime-comparison':
  return T('A real ')+r'C^1'+T(' function on ')+r'[0,T)'+T(' satisfies ')+r'y(0)=0,\quad y\prime(t)\ge y(t)^2+'+L(m*m)+r'.\quad'+T('Find the least universal upper bound on ')+r'T'+T('; the bound must be attainable.')
 if fn is ode and slug=='schwarzian-ivp':
  return r'\frac{y\prime\prime\prime}{y\prime}-\frac32\left(\frac{y\prime\prime}{y\prime}\right)^2=-'+L(2*m*m)+r',\quad y(0)=0,\quad y\prime(0)='+L(m)+r',\quad y\prime\prime(0)=0.\quad'+T('Take the real solution with ')+r'y\prime>0'+T('. Find ')+r'y(1)'+T('.')
 if fn is ode and slug=='darboux-oscillator':
  return r'y\prime\prime+('+L(m*m)+r'+2\operatorname{sech}^2t)y=0,\quad y(0)=0,\quad y\prime(0)='+L(m*m+1)+r'.\quad y('+L(pi/(4*m))+r')=?\quad\operatorname{sech}t=\frac1{\cosh t}.'
 return None
