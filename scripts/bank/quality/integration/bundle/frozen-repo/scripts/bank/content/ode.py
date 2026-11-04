#!/usr/bin/env python3
"""Independent original ODE constructions; finite parameter domain, no network or model calls.
Each executed check evaluates a residual, initial datum, invariant or independent
finite derivation. Analytic obligations are recorded separately from machine checks.
"""
from __future__ import annotations
import argparse, hashlib, json, re, textwrap
from pathlib import Path
import sympy as s
from authored_options import select_authored_triple, supplement_differentiation_pool
R=s.Rational
x=s.symbols('t', real=True)
X,Y,D,D2=s.symbols('X Y D D2',real=True)
pi=s.pi
FAMILIES={}
def L(a):return s.latex(s.sympify(a),fold_short_frac=False)
def T(a):return r'\textnormal{'+a+'}'
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def exact(a,b):return s.simplify(s.trigsimp(s.expand_func(a-b)))==0
def ck(name,a,b=0):
 assert exact(a,b),name+': '+str(s.simplify(a-b))
 return {'name':name,'passed':True}
def reg(level,slug,group,method,reason,why,prereq=(),alternatives=(),refs=()):
 def dec(fn):
  fid='m3-differential-equations-'+level+'-'+slug.lower()
  FAMILIES[fid]=dict(familyId=fid,topic='differential equations',difficulty=level,relatedIdeaGroupId=group,primaryTechnique=method,reasoningDemand=reason,difficultyRationale=why,prerequisites=list(prereq),alternativeTechniques=list(alternatives),sourceRecordIds=list(refs),editorialStatus='admitted',build=fn)
  return fn
 return dec

def pack(m,statement,answer,pool,steps,checks,conditions,analytic,structure,answer_form='exact-real'):
 answer=s.sympify(answer)
 assert checks and all(c['passed'] is True for c in checks)
 assert not answer.has(s.nan,s.zoo,s.oo,-s.oo,s.Integral,s.Sum,s.Limit)
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
   delta=s.simplify(a-b)
   assert delta.is_zero is False or delta.equals(0) is False, 'unresolved option inequivalence'
 return dict(statement=statement,answer=answer,wrongs=chosen,solutionSteps=steps+[r'\boxed{'+L(answer)+'}'],automatedChecks=checks,domain=conditions,analyticCertificate=analytic,structuralSignature=structure,answerForm=answer_form)

def values(a,items):return [(s.sympify(v),why) for v,why in items]

# EASY: twelve separate elementary decisions, including field interpretation,
# numerical stepping, physical modeling, invariants and initial data.
@reg('easy','field-slope','ode-field-local-data','evaluate-vector-field','recognition','Reads a local slope from the equation and a supplied state; no solution formula is needed.')
def e_field(m):
 f=x*Y+x*x;ans=m*m+2*m
 return pack(m,T('A solution satisfies ')+r'y\prime=ty+t^2,\quad y('+L(m)+r')=2.\quad y\prime('+L(m)+r')=?',ans,[(m*m,'omit ty'),(2*m,'omit t squared'),(2*m*m,'replace y by t'),(m*m+2,'lose the t factor')],[T('Insert the given time and state into the right-hand side.')],[ck('field evaluated at prescribed state',f.subs({x:m,Y:2}),ans)],['The right-hand side is smooth on the real plane.'],['The ODE defines the derivative at every point of a solution.'],'nonautonomous-field-at-given-state')

@reg('easy','rate-identification','ode-exponential-parameter','solution-substitution','execution','Determines an unknown rate by requiring a proposed function to satisfy an ODE.')
def e_rate(m):
 k=s.symbols('k');f=s.exp(m*x);ans=m
 return pack(m,T('For which constant k does ')+r'y(t)=e^{'+L(m)+r't}'+T(' satisfy ')+r'y\prime=ky\textnormal{ for every real t?}',ans,[(1/m,'invert the rate'),(m*m,'differentiate exponent twice'),(-m,'reverse growth sign'),(1,'ignore the exponent coefficient')],[r'y\prime='+L(s.diff(f,x)),T('The exponential is never zero, so divide by y.')],[ck('candidate function satisfies recovered equation',s.diff(f,x)-ans*f),ck('coefficient after cancellation',s.simplify(s.diff(f,x)/f),ans)],['Real t; e^(mt)>0.'],['Since y never vanishes, k=y prime/y is uniquely determined.'],'unknown-rate-from-nonvanishing-solution')

@reg('easy','phase-line-stability','ode-equilibrium-phase-line','sign-chart','recognition','Identifies which equilibrium attracts from both sides, rather than just solving for zeros.')
def e_stability(m):
 f=Y*Y-m*m;ans=-m
 return pack(m,T('For ')+r'y\prime=y^2-'+L(m*m)+T(', which equilibrium is asymptotically stable?'),ans,[(m,'choose the repelling root'),(0,'confuse midpoint with equilibrium'),(-m*m,'forget the square root'),(m*m,'square the equilibrium')],[r'f(y)=(y-'+L(m)+r')(y+'+L(m)+r')',T('Below -m the velocity is positive; between the roots it is negative. Both arrows point toward -m.')],[ck('stable point is a root',f.subs(Y,ans)),ck('linearized rate at stable point',s.diff(f,Y).subs(Y,ans),-2*m)],['Autonomous scalar equation; m>0.'],['For a simple equilibrium, a negative derivative of the vector field gives local asymptotic stability. The displayed signs verify that conclusion directly.'],'two-simple-equilibria-phase-arrows')

@reg('easy','euler-step','ode-numerical-local-step','forward-Euler','execution','Uses the initial slope over one prescribed step and keeps time and state distinct.')
def e_euler(m):
 h=1/m;ans=m-1
 return pack(m,T('Use one forward Euler step for ')+r'y\prime=t-y,\ y(0)='+L(m)+r',\ h='+L(h)+T('. What is the approximate new y?'),ans,[(m+1,'wrong slope sign'),(m-m*m,'multiply by reciprocal step'),(-1,'return only the increment'),(m,'leave the state unchanged')],[r'y_1=y_0+h(0-y_0)',r'y_1='+L(m)+r'+'+L(h)+r'(-'+L(m)+r')'],[ck('Euler recurrence',m+h*(0-m),ans)],['This asks for a numerical Euler value, not the exact ODE solution.'],['Forward Euler uses the old-time slope exactly once.'],'one-step-numerical-slope-update')

@reg('easy','primitive-initial-value','ode-direct-accumulation','integrate-and-use-initial-value','execution','An additive constant is fixed by an initial value after one elementary integration.')
def e_primitive(m):
 f=1+m*x**3/3;ans=1+m/3
 return pack(m,r'y\prime='+L(m)+r't^2,\quad y(0)=1.\quad y(1)=?',ans,[(m/3,'drop initial value'),(1+m,'forget power denominator'),(1+m/2,'use wrong power'),(m,'use the final slope')],[r'y(t)=1+\int_0^t '+L(m)+r's^2\,ds='+L(f)],[ck('primitive residual',s.diff(f,x)-m*x*x),ck('initial value',f.subs(x,0),1),ck('requested evaluation',f.subs(x,1),ans)],['All real t.'],['The derivative equation determines y up to a constant, and the initial value fixes it.'],'single-integration-with-initial-offset')

@reg('easy','doubling-data','ode-exponential-observation','multiplicative-growth','recognition','Infers repeated equal-time growth from two observations without finding the rate explicitly.')
def e_doubling(m):
 f=m*2**x;ans=8*m
 return pack(m,T('A positive solution of ')+r'y\prime=ky'+T(' has ')+r'y(0)='+L(m)+r',\ y(1)='+L(2*m)+r'.\quad y(3)=?',ans,[(4*m,'add the same amount each time'),(6*m,'multiply time by doubling factor'),(2*m,'use one elapsed interval'),(16*m,'count one extra interval')],[r'\frac{y(t+1)}{y(t)}=e^k=2',r'y(3)=y(0)2^3'],[ck('exponential law residual',s.diff(f,x)-s.log(2)*f),ck('first observation',f.subs(x,0),m),ck('second observation',f.subs(x,1),2*m),ck('three-step observation',f.subs(x,3),ans)],['Constant real k; y>0.'],['The unique solution is y(0)exp(kt); equal time intervals have equal ratios.'],'constant-growth-rate-inferred-from-data')

@reg('easy','cooling-limit','ode-affine-attractor','equilibrium-plus-decay','recognition','Separates an environmental equilibrium from a decaying temperature difference.')
def e_cooling(m):
 ambient=m+10;f=ambient-10*s.exp(-2*x);ans=ambient
 return pack(m,r'T\prime=-2(T-'+L(ambient)+r'),\ T(0)='+L(m)+r'.\quad\lim_{t\to\infty}T(t)=?',ans,[(m,'keep initial temperature'),(0,'decay the whole temperature'),(10,'return the initial difference'),(2*ambient,'multiply equilibrium by rate')],[T('The difference from ambient temperature obeys u prime=-2u.'),r'T(t)='+L(f)],[ck('cooling residual',s.diff(f,x)+2*(f-ambient)),ck('initial temperature',f.subs(x,0),m),ck('long-time limit',s.limit(f,x,s.oo),ans)],['t>=0; constant environment.'],['The exponential difference tends to zero because the decay rate is positive.'],'affine-relaxation-long-time-state')

@reg('easy','mixing-inflow','ode-physical-balance','inflow-minus-outflow','modeling','Converts concentration and flow rate into an amount derivative with consistent units.')
def e_mixing(m):
 V=m+2;S=m;qin=R(3,2);rate=2;ans=3-2*m/V
 return pack(m,T('A well-mixed tank contains ')+L(V)+T(' liters and ')+L(S)+T(' grams of salt. Brine of concentration 3/2 g/L enters at 2 L/min; mixture leaves at 2 L/min. Find the current salt-amount derivative in g/min.'),ans,[(3-m/V,'forget outflow rate'),(R(3,2)-m/V,'subtract concentrations rather than amounts'),(3+2*m/V,'add outflow'),(3-2*m,'ignore tank volume')],[r'S\prime=(2)(3/2)-2S/V',T('Outflow concentration is amount divided by current volume.')],[ck('mass-balance substitution',rate*qin-rate*S/V,ans),ck('constant-volume balance',rate-rate)],['Perfect mixing; equal inflow and outflow; no salt reaction.'],['Concentration times volumetric flow has units mass/time. Conservation gives inflow minus outflow.'],'tank-mass-balance-with-units')

@reg('easy','constant-acceleration','ode-position-second-order','two-integrations','execution','Uses both position and velocity initial data in a second-order equation.')
def e_acceleration(m):
 f=x+m*x*x/2;ans=1+m/2
 return pack(m,r's\prime\prime='+L(m)+r',\quad s(0)=0,\quad s\prime(0)=1.\quad s(1)=?',ans,[(m/2,'discard initial velocity'),(1+m,'confuse velocity and position'),(m,'use acceleration as displacement'),(1+2*m,'double instead of halve the quadratic contribution')],[r's\prime(t)=1+'+L(m)+r't',r's(t)='+L(f)],[ck('acceleration',s.diff(f,x,2),m),ck('initial position',f.subs(x,0)),ck('initial velocity',s.diff(f,x).subs(x,0),1),ck('final position',f.subs(x,1),ans)],['All real t.'],['Two initial conditions fix the two integration constants.'],'constant-second-derivative-position-and-velocity')

@reg('easy','equation-order','ode-order-versus-degree','highest-derivative-order','recognition','Distinguishes the order of a derivative from powers of lower derivatives; a foundational classification family.')
def e_order(m):
 n=int(m)-2;z=s.Function('y')(x);equation=s.diff(z,x,n)+s.diff(z,x)**(m+1)+z;ans=s.Integer(n)
 return pack(m,r'\frac{d^{'+str(n)+r'}y}{dt^{'+str(n)+r'}}+(y\prime)^{'+L(m+1)+r'}+y=0.\quad'+T('What is the order of this differential equation?'),ans,[(m+1,'confuse derivative power with order'),(1,'look only at y prime'),(m,'read the wrong index'),(2*m,'multiply the orders')],[T('Order is the largest number of differentiations of y that appears. Powers do not raise order.')],[ck('order extracted from symbolic differential expression',s.ode_order(equation,z),ans)],['The equation is written in the displayed unsimplified derivative form; n>=2.'],['The coefficient of the nth derivative is one, so that highest derivative does not disappear.'],'highest-derivative-versus-algebraic-power')

@reg('easy','oscillator-initial-data','ode-fundamental-basis-data','initial-data-in-basis','execution','Finds two coefficients from independent value and derivative data, then evaluates at a quarter period.')
def e_oscillator(m):
 f=m*s.cos(x)+(m+1)*s.sin(x);ans=m+1
 return pack(m,r'y(t)=A\cos t+B\sin t,\quad y(0)='+L(m)+r',\ y\prime(0)='+L(m+1)+r'.\quad y(\pi/2)=?',ans,[(m,'exchange the initial conditions'),(2*m+1,'add both basis coefficients'),(1,'subtract coefficients'),(-m-1,'differentiate sine with wrong sign')],[r'A=y(0)='+L(m)+r',\quad B=y\prime(0)='+L(m+1),r'\cos(\pi/2)=0,\ \sin(\pi/2)=1'],[ck('basis solves oscillator',s.diff(f,x,2)+f),ck('initial value',f.subs(x,0),m),ck('initial derivative',s.diff(f,x).subs(x,0),m+1),ck('quarter-period evaluation',f.subs(x,pi/2),ans)],['Real A and B.'],['The value and derivative at zero independently determine the two basis coefficients.'],'two-coefficients-from-oscillator-initial-data')

@reg('easy','transfer-conservation','ode-conserved-total','add-equations','recognition','Recognizes a conserved total in a coupled transfer model without solving either component.')
def e_transfer(m):
 f=-2*X+3*Y;g=2*X-3*Y;later=(2*m+21)/10;ans=(8*m+9)/10
 equilibrium=2*(m+3)/5;v=equilibrium+(3-equilibrium)*s.exp(-5*x)
 return pack(m,r'u\prime=-2u+3v,\quad v\prime=2u-3v,\quad u(0)='+L(m)+r',\ v(0)=3.\quad'+T('At a later time v=')+L(later)+T('. Find u.'),ans,[(m,'keep u constant'),(m+3+later,'add rather than subtract later v'),(3-later,'return the change only'),((m+3)/2,'split the total equally')],[r'(u+v)\prime=0,\quad u+v='+L(m+3),r'u='+L(m+3)+r'-'+L(later)],[ck('zero derivative of total',f+g),ck('later state respects conserved total',ans+later,m+3),ck('specified later state is actually reached',v.subs(x,s.log(2)/5),later)],['Both equations hold on a common time interval; the stated later v occurs at t=log(2)/5.'],['A zero derivative makes the total constant. Substitution gives v prime=2(m+3)-5v; its solution reaches the prescribed midpoint between initial and equilibrium values at the positive time log(2)/5.'],'coupled-transfer-conserved-sum')

# MEDIUM: equation forms and model decisions with genuinely different reductions.
@reg('medium','logistic-hitting','ode-logistic-threshold-time','separation-and-log-odds','method-selection','Finds a hitting time by linearizing the odds rather than treating growth as exponential.')
def m_logistic(m):
 f=1/(1+m*s.exp(-x));ans=s.log(m)
 return pack(m,r'y\prime=y(1-y),\ y(0)=\frac1{'+L(m+1)+r'}.\quad'+T('When does y first reach 1/2?'),ans,[(s.log(m+1),'use initial denominator as odds'),(1/m,'invert the population scale'),(m,'replace logarithm by its argument'),(2*s.log(m),'double the logistic time')],[r'\frac{y}{1-y}=\frac{e^t}{'+L(m)+'}',T('At one half the odds equal one, so ')+r'e^t='+L(m)],[ck('logistic residual',s.diff(f,x)-f*(1-f)),ck('initial population',f.subs(x,0),1/(m+1)),ck('threshold attained',f.subs(x,ans),R(1,2))],['0<y(0)<1; t>=0.'],['The vector field is positive between zero and one, making this first hitting time unique.'],'logistic-log-odds-hitting-time')

@reg('medium','finite-blowup','ode-separable-lifespan','reciprocal-linearization','convergence','Determines the maximal interval from the first pole of a solution, not merely its formula.')
def m_blowup(m):
 f=1/(m-x);ans=m
 return pack(m,r'y\prime=y^2,\quad y(0)=\frac1{'+L(m)+r'}.\quad'+T('Find the finite right endpoint of its maximal solution interval.'),ans,[(1/m,'use initial height as time'),(-m,'choose the left-direction sign'),(m*m,'square the pole location'),(2*m,'double the existence interval')],[r'(1/y)\prime=-1,\quad y(t)=\frac1{'+L(m)+r'-t}',T('The solution diverges as t approaches m from below.')],[ck('nonlinear residual',s.diff(f,x)-f*f),ck('initial value',f.subs(x,0),1/m),ck('denominator first vanishes',m-ans)],['Initial solution is positive; maximal interval is (-infinity,m).'],['The polynomial vector field gives local uniqueness. The explicit pole prevents any finite continuous extension across t=m.'],'nonlinear-solution-pole-maximal-interval')

@reg('medium','variable-integrating-factor','ode-nonconstant-linear-factor','integrating-factor','method-selection','A variable coefficient requires a nonconstant integrating factor and a changed initial endpoint.')
def m_factor(m):
 f=(x**(m+2)-1)/((m+2)*x);ans=(2**(m+2)-1)/(2*(m+2))
 return pack(m,r'y\prime+\frac yt=t^{'+L(m)+r'},\quad y(1)=0.\quad y(2)=?',ans,[(2**(m+2)/(2*(m+2)),'drop initial endpoint'),((2**(m+2)-1)/(m+2),'forget to divide by integrating factor'),((2**(m+1)-1)/(m+1),'omit the multiplying t'),(-ans,'reverse the integration limits')],[r'(ty)\prime=t^{'+L(m+1)+r'}',r'ty=\frac{t^{'+L(m+2)+r'}-1}{'+L(m+2)+r'}'],[ck('linear ODE residual',s.diff(f,x)+f/x-x**m),ck('initial datum',f.subs(x,1)),ck('evaluation',f.subs(x,2),ans)],['t>0; the initial point lies away from the coefficient singularity.'],['Multiplication by t is reversible on the stated interval; the linear initial-value problem is unique.'],'variable-factor-power-forcing-positive-domain')

@reg('medium','exact-curve','ode-exact-potential','potential-function','reframing','Uses an implicit conserved potential and selects the positive branch from an initial point.')
def m_exact(m):
 P=x*x+x*Y+Y*Y;ans=s.sqrt(m*m+m+1)
 return pack(m,r'(2t+y)+(t+2y)y\prime=0,\quad y(1)='+L(m)+r'.\quad'+T('At a point on this implicit solution curve with y=0 and t>0, find t.'),ans,[(m+1,'complete the square incorrectly'),(s.sqrt(m*m+1),'omit the mixed term'),(-ans,'use the negative branch'),(m*m+m+1,'forget the square root')],[r'd(t^2+ty+y^2)=(2t+y)dt+(t+2y)dy',r't^2+ty+y^2='+L(m*m+m+1),T('At y=0 choose the positive square root.')],[ck('potential t partial',s.diff(P,x),2*x+Y),ck('potential y partial',s.diff(P,Y),x+2*Y),ck('initial potential',P.subs({x:1,Y:m}),m*m+m+1),ck('target point on same curve',P.subs({x:ans,Y:0}),m*m+m+1)],['Implicit solution curve; requested intersection has t>0.'],['The differential form is the exact differential of P. The connected upper arc from the initial point reaches the stated positive-axis intersection.'],'exact-differential-potential-and-branch')

@reg('medium','bernoulli-reciprocal','ode-Bernoulli-substitution','reciprocal-substitution','method-selection','A quadratic nonlinear term becomes a linear equation after inversion; the solution remains nonzero.')
def m_bernoulli(m):
 v=x+1-(m+1)*s.exp(x);f=1/v;ans=1/(2-(m+1)*s.E)
 return pack(m,r'y\prime+y=ty^2,\quad y(0)=-\frac1{'+L(m)+r'}.\quad y(1)=?',ans,[(1/(2+(m+1)*s.E),'wrong homogeneous sign'),(2-(m+1)*s.E,'forget to invert back'),(1/(1-m*s.E),'omit forcing contribution'),(-ans,'lose sign of initial value')],[r'v=1/y:\quad v\prime-v=-t',r'v(t)=t+1-'+L(m+1)+r'e^t',r'y=1/v'],[ck('linear reciprocal equation',s.diff(v,x)-v,-x),ck('original nonlinear residual',s.diff(f,x)+f-x*f*f),ck('initial datum',f.subs(x,0),-1/m),ck('evaluation',f.subs(x,1),ans)],['0<=t<=1; v<0 because e^t>=1+t and m>=4.'],['The reciprocal is valid throughout the interval and the smooth nonlinear field gives uniqueness.'],'quadratic-nonlinearity-reciprocal-linearization')

@reg('medium','homogeneous-ratio','ode-homogeneous-ratio','scale-ratio-substitution','reframing','The ratio y/t separates an equation whose terms share a scale.')
def m_homogeneous(m):
 f=-x/(m+s.log(x));ans=-s.E/(m+1)
 return pack(m,r'y\prime=\frac yt+\left(\frac yt\right)^2,\quad y(1)=-\frac1{'+L(m)+r'}.\quad y(e)=?',ans,[(s.E/(m+1),'wrong sign'),(-1/(m+1),'forget y=tv'),(-s.E/(m-1),'wrong sign in reciprocal integral'),(-m*s.E,'invert initial ratio')],[r'v=y/t:\quad tv\prime=v^2',r'-1/v=\log t+'+L(m),r'y(t)=-\frac{t}{'+L(m)+r'+\log t}'],[ck('homogeneous ODE residual',s.diff(f,x)-f/x-(f/x)**2),ck('initial datum',f.subs(x,1),-1/m),ck('evaluation',f.subs(x,s.E),ans)],['1<=t<=e; denominator remains positive.'],['The substitution is reversible for t>0, and the explicit branch contains the initial point.'],'homogeneous-y-over-t-logarithmic-reduction')

@reg('medium','harvest-bifurcation','ode-parameter-equilibrium-collision','complete-square','recognition','Finds the threshold at which two positive equilibria merge and disappear.')
def m_harvest(m):
 h=s.symbols('h');f=Y*(m-Y)-h;ans=m*m/4
 return pack(m,r'y\prime=y('+L(m)+r'-y)-h,\ h\ge0.\quad'+T('Find the largest h for which a positive equilibrium exists.'),ans,[(m*m,'omit the vertex factor'),(m/2,'return the equilibrium location'),(m*m/2,'halve only once'),(m*m/8,'halve once too often')],[r'y('+L(m)+r'-y)=\frac{'+L(m*m)+r'}4-\left(y-\frac{'+L(m)+r'}2\right)^2',T('The maximum sustainable removal equals this parabola maximum.')],[ck('square completion',Y*(m-Y),m*m/4-(Y-m/2)**2),ck('threshold equilibrium',f.subs({Y:m/2,h:ans}))],['h>=0; equilibrium population must be positive.'],['For h above the maximum no root exists; at the maximum y=m/2>0 supplies one.'],'parameter-threshold-equilibrium-collision')

@reg('medium','distinct-characteristic-roots','ode-linear-distinct-roots','characteristic-equation','execution','Selects and combines two independent modes using both initial conditions.')
def m_roots(m):
 f=s.exp(m*x)-s.exp(x);ans=s.exp(m)-s.E
 return pack(m,r'y\prime\prime-'+L(m+1)+r'y\prime+'+L(m)+r'y=0,\ y(0)=0,\ y\prime(0)='+L(m-1)+r'.\quad y(1)=?',ans,[(s.exp(m)+s.E,'wrong initial cancellation'),(s.exp(m)-1,'replace slow exponential by constant'),((s.exp(m)-s.E)/(m-1),'renormalize derivative twice'),(s.E-s.exp(m),'reverse coefficients')],[r'r^2-'+L(m+1)+r'r+'+L(m)+r'=(r-1)(r-'+L(m)+r')',r'y(t)=e^{'+L(m)+r't}-e^t'],[ck('second-order residual',s.diff(f,x,2)-(m+1)*s.diff(f,x)+m*f),ck('initial value',f.subs(x,0)),ck('initial slope',s.diff(f,x).subs(x,0),m-1),ck('evaluation',f.subs(x,1),ans)],['m>=4 ensures distinct roots.'],['A constant-coefficient linear ODE with these two initial data has a unique global solution.'],'two-independent-characteristic-modes')

@reg('medium','resonant-forcing','ode-resonance-linear-growth','resonant-particular-solution','method-selection','Resonance requires a time factor and the initial derivative contributes a homogeneous correction.')
def m_resonance(m):
 f=(s.sin(x)-x*s.cos(x))/2;ans=(-1)**(m+1)*m*pi/2
 return pack(m,r'y\prime\prime+y=\sin t,\ y(0)=y\prime(0)=0.\quad y('+L(m)+r'\pi)=?',ans,[(-ans,'wrong resonant sign'),(0,'assume forcing-period cancellation'),(2*ans,'omit factor two in resonance'),(ans/m,'omit secular growth factor')],[T('A particular solution is -t cos(t)/2; enforce initial derivative zero with sin(t)/2.'),r'y(t)=\frac{\sin t-t\cos t}{2}'],[ck('forced residual',s.diff(f,x,2)+f,s.sin(x)),ck('initial value',f.subs(x,0)),ck('initial slope',s.diff(f,x).subs(x,0)),ck('evaluation',f.subs(x,m*pi),ans)],['All real t; integer m.'],['The proposed function satisfies the forced equation and both initial conditions, proving it is the unique solution.'],'resonant-secular-term-with-initial-correction')

@reg('medium','critical-damping','ode-damping-regime','discriminant-condition','recognition','Finds a regime boundary from repeated characteristic roots rather than solving the motion.')
def m_damping(m):
 c=s.symbols('c');ans=2*m
 return pack(m,r'y\prime\prime+cy\prime+'+L(m*m)+r'y=0,\ c>0.\quad'+T('Find c for critical damping.'),ans,[(m,'use natural frequency directly'),(m*m,'use stiffness directly'),(4*m,'double the damping threshold'),(2*m*m,'confuse frequency with squared frequency')],[r'\Delta=c^2-4('+L(m*m)+r')=0',T('Choose the positive root because c>0.')],[ck('repeated-root discriminant',(ans**2-4*m*m)),ck('critical polynomial factors',(D*D+ans*D+m*m),(D+m)**2)],['Positive damping c.'],['Critical damping is the double-real-root boundary between distinct negative real roots and a complex conjugate pair.'],'critical-damping-characteristic-discriminant')

@reg('medium','repeated-root','ode-linear-repeated-root','generalized-exponential-mode','method-selection','A repeated root requires t exp(rt), which is fixed by the derivative datum.')
def m_repeated(m):
 f=x*s.exp(m*x);ans=s.exp(m)
 return pack(m,r'y\prime\prime-'+L(2*m)+r'y\prime+'+L(m*m)+r'y=0,\ y(0)=0,\ y\prime(0)=1.\quad y(1)=?',ans,[(m*s.exp(m),'differentiate instead of evaluate'),(s.exp(m)/m,'divide by root incorrectly'),(2*s.exp(m),'double the generalized mode'),(s.exp(2*m),'use doubled root')],[r'(D-'+L(m)+r')^2y=0,\quad y=(A+Bt)e^{'+L(m)+r't}',r'A=0,\quad B=1'],[ck('repeated-root residual',s.diff(f,x,2)-2*m*s.diff(f,x)+m*m*f),ck('initial value',f.subs(x,0)),ck('initial slope',s.diff(f,x).subs(x,0),1),ck('evaluation',f.subs(x,1),ans)],['All real t.'],['The two independent modes are exp(mt) and t exp(mt). Initial data uniquely select their combination.'],'repeated-characteristic-root-polynomial-prefactor')

@reg('medium','periodic-amplitude','ode-forced-steady-response','sin-cos-coefficient-system','method-selection','Separates the steady periodic response from the transient and computes its amplitude.')
def m_amplitude(m):
 A=m/(m*m+1);B=1/(m*m+1);f=A*s.cos(x)+B*s.sin(x);ans=1/s.sqrt(m*m+1)
 return pack(m,r'y\prime+'+L(m)+r'y=\cos t.\quad'+T('Find the amplitude of its steady periodic solution.'),ans,[(s.sqrt(m*m-1)/(m*m+1),'subtract the squared quadrature coefficients'),(s.sqrt(2/(m*m+1)),'double the mean-square conversion factor'),(s.sqrt(m*m+1)/(m*m-1),'use the wrong sign when solving the coefficient system'),(1/(m*m+1),'return amplitude squared'),(m/s.sqrt(m*m+1),'return normalized phase cosine instead of amplitude')],[r'y_p=A\cos t+B\sin t',r'B+'+L(m)+r'A=1,\quad -A+'+L(m)+r'B=0',r'\textnormal{amplitude}=\sqrt{A^2+B^2}'],[ck('periodic forced residual',s.diff(f,x)+m*f,s.cos(x)),ck('amplitude squared',A*A+B*B,ans*ans)],['m>0, so the transient exp(-mt) decays.'],['Every solution differs from this periodic one by a decaying exponential; positive amplitude is sqrt(A^2+B^2).'],'steady-response-phase-amplitude')

# HARD: nonlinear reductions, weak forcing, systems and boundary theory.
@reg('hard','Riccati-particular','ode-Riccati-known-branch','subtract-particular-solution','reframing','A nonautonomous Riccati equation becomes separable after discovering a simple particular solution.')
def h_riccati(m):
 f=x+1/(m-x);ans=1+1/(m-1)
 return pack(m,r'y\prime=y^2-2ty+t^2+1,\quad y(0)=\frac1{'+L(m)+r'}.\quad y(1)=?',ans,[(1+1/(m+1),'wrong reciprocal sign'),(1/(m-1),'forget the particular solution'),(1+m,'invert the initial value incorrectly'),(1-1/(m-1),'wrong perturbation sign')],[T('The function y=t is a particular solution.'),r'y=t+v\ \Longrightarrow\ v\prime=v^2',r'v(t)=\frac1{'+L(m)+r'-t}'],[ck('particular solution residual',s.diff(x,x)-(x*x-2*x*x+x*x+1)),ck('full Riccati residual',s.diff(f,x)-(f*f-2*x*f+x*x+1)),ck('initial value',f.subs(x,0),1/m),ck('evaluation',f.subs(x,1),ans)],['0<=t<=1<m; the pole lies outside the requested interval.'],['Subtraction is reversible, and the locally Lipschitz field gives uniqueness until the pole.'],'nonautonomous-Riccati-particular-subtraction')

@reg('hard','nonlinear-energy-speed','ode-conservative-quartic-energy','energy-first-integral','reframing','A nonlinear oscillator yields a speed from energy, avoiding a non-elementary time solution.')
def h_energy(m):
 energy=D*D+Y**4;ans=m*m
 return pack(m,r'y\prime\prime=-2y^3,\quad y(0)='+L(m)+r',\quad y\prime(0)=0.\quad'+T('Find the maximum speed |y prime| on its oscillation.'),ans,[(m,'use amplitude as speed'),(2*m*m,'lose the kinetic factor'),(m*m/2,'halve energy rather than speed'),(m**4,'return speed squared')],[r'\frac d{dt}\big((y\prime)^2+y^4\big)=0',r'(y\prime)^2='+L(m**4)+r'-y^4',T('The speed is largest at y=0, which the oscillation reaches.')],[ck('energy derivative along the flow',s.diff(energy,Y)*D+s.diff(energy,D)*(-2*Y**3)),ck('initial energy',energy.subs({Y:m,D:0}),m**4),ck('speed squared at center',ans*ans,m**4)],['Real conservative solution.'],['Energy confines y to [-m,m]. Starting at the right turning point, negative acceleration initiates descent; the finite integral to zero establishes that the maximum is attained.'],'quartic-restoring-force-energy-extremum')

@reg('hard','Euler-Cauchy-resonance','ode-Euler-Cauchy-log-resonance','log-time-substitution','synthesis','Logarithmic time converts a variable-coefficient repeated-root operator into a double integration.')
def h_euler(m):
 f=x*x*s.log(x)**2/2;point=s.exp(1/m);ans=s.exp(2/m)/(2*m*m)
 return pack(m,r't^2y\prime\prime-3ty\prime+4y=t^2,\quad y(1)=y\prime(1)=0.\quad y(e^{'+L(1/m)+r'})=?',ans,[(s.exp(2/m)/(m*m),'omit repeated-integration factor'),(1/(2*m*m),'forget outer t squared'),(s.exp(2/m)/(2*m),'use one logarithm'),(-ans,'wrong transformed forcing sign')],[r's=\log t,\quad y=t^2v(s)',r't^2y\prime\prime-3ty\prime+4y=t^2v\prime\prime(s)',r'v(0)=v\prime(0)=0,\quad v(s)=s^2/2'],[ck('Euler-Cauchy forced residual',x*x*s.diff(f,x,2)-3*x*s.diff(f,x)+4*f,x*x),ck('initial value',f.subs(x,1)),ck('initial slope',s.diff(f,x).subs(x,1)),ck('evaluation',f.subs(x,point),ans)],['t>0; real logarithm.'],['The change s=log t is a smooth bijection on the positive time axis, so the transformed initial problem is equivalent.'],'Euler-Cauchy-repeated-root-resonance')

@reg('hard','variable-second-order-basis','ode-reduction-order-known-mode','second-solution-recognition','method-selection','Recognizes two independent modes of a variable-coefficient second-order equation and avoids its singular point.')
def h_basis(m):
 f=m*(x+1-s.exp(x-1));ans=m*(3-s.E)
 return pack(m,r'ty\prime\prime-(t+1)y\prime+y=0,\quad y(1)='+L(m)+r',\quad y\prime(1)=0.\quad y(2)=?',ans,[(m*(3+s.E),'wrong exponential coefficient'),(m*(2-s.E),'omit affine constant'),(3*m-s.E,'forget scale on exponential'),(-ans,'reverse basis coefficients')],[T('Two solutions are exp(t) and t+1. Their Wronskian is -t exp(t), nonzero for t>0.'),r'y(t)='+L(f)],[ck('exponential mode residual',x*s.diff(s.exp(x),x,2)-(x+1)*s.diff(s.exp(x),x)+s.exp(x)),ck('affine mode residual',x*0-(x+1)*1+(x+1)),ck('Wronskian',s.exp(x)-(x+1)*s.exp(x),-x*s.exp(x)),ck('full residual',x*s.diff(f,x,2)-(x+1)*s.diff(f,x)+f),ck('initial value',f.subs(x,1),m),ck('initial slope',s.diff(f,x).subs(x,1)),ck('evaluation',f.subs(x,2),ans)],['t>0; leading coefficient is nonzero there.'],['The nonzero Wronskian makes the two modes a basis; the given initial data select a unique solution.'],'variable-leading-coefficient-two-mode-basis')

@reg('hard','remove-first-derivative','ode-normal-form-conjugation','Gaussian-conjugation','reframing','A Gaussian factor removes the nonconstant first-derivative term and exposes a harmonic oscillator.')
def h_normal(m):
 f=s.exp(-x*x/2)*s.cos(m*x);point=pi/m;ans=-s.exp(-pi*pi/(2*m*m))
 return pack(m,r'y\prime\prime+2ty\prime+(t^2+'+L(1+m*m)+r')y=0,\ y(0)=1,\ y\prime(0)=0.\quad y('+L(point)+r')=?',ans,[(s.exp(-pi*pi/(2*m*m)),'miss half-period sign'),(-s.exp(-pi*pi/(m*m)),'double Gaussian exponent'),(-1,'omit Gaussian envelope'),(-s.exp(-pi*pi/(4*m*m)),'halve Gaussian exponent')],[r'y=e^{-t^2/2}v\ \Longrightarrow\ v\prime\prime+'+L(m*m)+r'v=0',r'v(0)=1,\quad v\prime(0)=0,\quad v=\cos('+L(m)+r't)'],[ck('normal-form residual',s.diff(f,x,2)+2*x*s.diff(f,x)+(x*x+1+m*m)*f),ck('initial value',f.subs(x,0),1),ck('initial slope',s.diff(f,x).subs(x,0)),ck('evaluation',f.subs(x,point),ans)],['All real t; smooth coefficients.'],['The nonvanishing Gaussian factor makes the transformation reversible. Linear IVP uniqueness completes verification.'],'Gaussian-conjugated-variable-coefficient-oscillator')

@reg('hard','step-forcing','ode-piecewise-input-response','match-at-input-switch','synthesis','Constructs a delayed response and enforces continuity of both state and velocity when forcing jumps.')
def h_step(m):
 r=m*(1-s.cos(x-1));ans=2*m
 return pack(m,r'y\prime\prime+y=\begin{cases}0,&0\le t<1,\\'+L(m)+r',&t>1,\end{cases}\quad y(0)=y\prime(0)=0.\quad \textnormal{Take y and y prime continuous at t=1.}\quad y(1+\pi)=?',ans,[(m,'return forcing amplitude'),(0,'reset response after the switch'),(4*m,'double response twice'),(-2*m,'wrong step-response sign')],[T('Before the switch the solution is zero. A finite step causes no jump in y or y prime.'),r'y(t)='+L(r)+r'\quad(t\ge1)'],[ck('post-switch forced residual',s.diff(r,x,2)+r,m),ck('state continuity at switch',r.subs(x,1)),ck('velocity continuity at switch',s.diff(r,x).subs(x,1)),ck('evaluation',r.subs(x,1+pi),ans)],['Piecewise classical solution; y and y prime continuous at t=1.'],['Integrating the equation over a shrinking interval around the switch gives zero derivative jump; continuity and the post-switch equation determine the response.'],'finite-step-forcing-matched-initial-data')

@reg('hard','impulse-jump','ode-distributional-impulse','jump-condition','synthesis','Distinguishes an impulse-induced velocity jump from a finite step in forcing.')
def h_impulse(m):
 r=m*(x-1)*s.exp(-(x-1));ans=m/s.E
 return pack(m,r'y\prime\prime+2y\prime+y='+L(m)+r'\delta(t-1),\ y(0)=y\prime(0)=0.\quad y(2)=?\quad'+T('Here delta is a unit Dirac impulse.'),ans,[(m,'omit decay after impulse'),(m*s.E,'wrong decay direction'),(2*m/s.E,'double the jump'),(m/s.E**2,'count one extra decay time')],[T('The state stays continuous and y prime jumps upward by m at t=1.'),r'y(t)='+L(r)+r'\quad(t>1)'],[ck('homogeneous equation after impulse',s.diff(r,x,2)+2*s.diff(r,x)+r),ck('continuous state',r.subs(x,1)),ck('required derivative jump',s.diff(r,x).subs(x,1),m),ck('evaluation',r.subs(x,2),ans)],['Causal distributional solution; it is zero before t=1.'],['A jump in y would create a delta derivative absent from the right side, so y is continuous. Integrating across the impulse fixes the derivative jump.'],'Dirac-input-derivative-jump-and-decay')

@reg('hard','rotating-linear-system','ode-complex-system-mode','complex-variable','reframing','Combines a planar system into one complex equation and interprets rotation with decay.')
def h_rotation(m):
 u=s.exp(-x)*s.cos(m*x);v=s.exp(-x)*s.sin(m*x);point=pi/m;ans=-s.exp(-pi/m)
 return pack(m,r'u\prime=-u-'+L(m)+r'v,\quad v\prime='+L(m)+r'u-v,\quad (u(0),v(0))=(1,0).\quad u('+L(point)+r')=?',ans,[(s.exp(-pi/m),'miss rotation sign'),(-s.exp(-pi),'use wrong elapsed decay time'),(-1,'ignore damping'),(-s.exp(-2*pi/m),'double damping')],[r'z=u+iv\ \Longrightarrow\ z\prime=(-1+'+L(m)+r'i)z',r'z(t)=e^{(-1+'+L(m)+r'i)t}'],[ck('first system residual',s.diff(u,x)+u+m*v),ck('second system residual',s.diff(v,x)-m*u+v),ck('initial u',u.subs(x,0),1),ck('initial v',v.subs(x,0)),ck('evaluation',u.subs(x,point),ans)],['Real u,v and t>=0.'],['The complex change of coordinates is equivalent to the real system; constant linear systems have unique global solutions.'],'planar-rotation-decay-complex-mode')

@reg('hard','Jordan-system','ode-defective-system-mode','nilpotent-matrix-exponential','method-selection','A repeated eigenvalue with a nontrivial Jordan block produces polynomial growth in the coupling chain.')
def h_jordan(m):
 A=s.Matrix([[m,1,0],[0,m,1],[0,0,m]]);v=s.Matrix([x*x*s.exp(m*x)/2,x*s.exp(m*x),s.exp(m*x)]);ans=s.exp(m)/2
 return pack(m,r'\mathbf u\prime='+s.latex(A)+r'\mathbf u,\quad\mathbf u(0)=\begin{pmatrix}0\\0\\1\end{pmatrix}.\quad u_1(1)=?',ans,[(s.exp(m),'omit second coupling integration'),(s.exp(m)/6,'use three rather than two integrations'),(m*s.exp(m)/2,'insert eigenvalue into polynomial factor'),(s.exp(2*m)/2,'double the exponential rate')],[r'A='+L(m)+r'I+N,\quad N^3=0',r'e^{tA}=e^{'+L(m)+r't}(I+tN+t^2N^2/2)',r'u_1(t)=t^2e^{'+L(m)+r't}/2'],[ck('system residual component '+str(j),v.diff(x)[j]-(A*v)[j]) for j in range(3)]+[ck('initial component '+str(j),v[j].subs(x,0),[0,0,1][j]) for j in range(3)]+[ck('evaluation',v[0].subs(x,1),ans)],['All real t.'],['The nilpotent expansion terminates exactly; the verified vector satisfies the unique linear IVP.'],'three-stage-Jordan-chain')

@reg('hard','linear-stability-bound','ode-planar-stability-region','trace-determinant','recognition','Combines both trace and determinant inequalities and selects the relevant parameter branch.')
def h_stability(m):
 a=s.symbols('a',real=True);A=s.Matrix([[a,m],[-1,a-2*m]]);ans=m-s.sqrt(m*m-m)
 return pack(m,r'\mathbf u\prime=\begin{pmatrix}a&'+L(m)+r'\\-1&a-'+L(2*m)+r'\end{pmatrix}\mathbf u.\quad'+T('The origin is asymptotically stable exactly for a<c. Find c.'),ans,[(m+s.sqrt(m*m-m),'choose the upper determinant root'),(m,'use trace only'),(s.sqrt(m*m-m),'omit trace shift'),(-ans,'reverse threshold sign')],[r'\operatorname{tr}A=2a-'+L(2*m)+r',\quad\det A=a^2-'+L(2*m)+r'a+'+L(m),T('Stability requires trace<0 and determinant>0. Their intersection lies below the lower root.')],[ck('matrix trace',s.trace(A),2*a-2*m),ck('matrix determinant',A.det(),a*a-2*m*a+m),ck('threshold determinant',A.det().subs(a,ans))],['m>=4; real parameter a. Strict inequality is required.'],['For a real two-dimensional system both eigenvalues have negative real part iff trace<0 and determinant>0. The upper determinant branch lies above m and fails the trace condition.'],'trace-and-determinant-parameter-intersection')

@reg('hard','mixed-boundary-spectrum','ode-Sturm-Liouville-spectrum','boundary-eigenvalue-condition','synthesis','Determines a mixed-boundary eigenvalue and excludes the zero and negative branches.')
def h_spectrum(m):
 ans=pi*pi/(4*m*m);f=s.sin(pi*x/(2*m))
 return pack(m,r'y\prime\prime+\lambda y=0,\quad y(0)=0,\quad y\prime('+L(m)+r')=0.\quad'+T('Find the smallest lambda for which a nonzero real solution exists.'),ans,[(pi*pi/(m*m),'use two Dirichlet boundaries'),(0,'keep a forbidden affine solution'),(-pi*pi/(4*m*m),'use exponential instead of oscillatory branch'),(9*pi*pi/(4*m*m),'choose the next mixed-boundary mode')],[T('For positive lambda, y=C sin(sqrt(lambda)t). The derivative endpoint requires cos(sqrt(lambda)m)=0.'),r'\sqrt\lambda\,'+L(m)+r'=\pi/2\textnormal{ for the first mode.}'],[ck('eigenfunction residual',s.diff(f,x,2)+ans*f),ck('left boundary',f.subs(x,0)),ck('right boundary',s.diff(f,x).subs(x,m)),ck('nonzero witness',f.subs(x,m),1)],['m>0; nonzero solution required.'],['At lambda=0 the affine solution fails the derivative boundary unless zero. For lambda<0 the sinh branch has nonvanishing cosh derivative at the right endpoint. Positive roots are ((2k+1)pi/(2m))^2, k>=0.'],'mixed-Dirichlet-Neumann-first-eigenvalue')

@reg('hard','Wronskian-transport','ode-Abel-Wronskian','determinant-differentiation','reframing','Recovers a Wronskian without solving either homogeneous solution or knowing the zeroth-order coefficient.')
def h_wronskian(m):
 f=x**(-m);ans=2**(-m)
 return pack(m,r'y\prime\prime+\frac{'+L(m)+r'}t y\prime+q(t)y=0\quad(t>0).'+T(' Let y1 and y2 be solutions on an interval containing [1,2], and define ')+r'W=y_1y_2\prime-y_1\prime y_2.\quad W(1)=1.\quad W(2)=?',ans,[(2**m,'wrong transport sign'),(1,'assume W is constant'),(2**(-m-1),'shift exponent'),(m/2,'replace exponential transport by linear scaling')],[T('Differentiate the determinant; the q terms cancel.'),r'W\prime=-\frac{'+L(m)+r'}tW,\quad W(t)=t^{-'+L(m)+r'}'],[ck('Wronskian transport residual',s.diff(f,x)+m*f/x),ck('normalization',f.subs(x,1),1),ck('evaluation',f.subs(x,2),ans)],['q continuous on the positive interval containing [1,2]; W uses the stated order.'],['For two solutions, W prime=y1*y2 second-y1 second*y2. Substituting the ODE leaves exactly -(m/t)W. The resulting scalar IVP determines W.'],'Wronskian-transport-with-unknown-q')

@reg('olympiad','quartic-period','ode-nonlinear-period-energy-beta','energy-to-period-quadrature','synthesis','Finds a nonlinear period by an energy invariant, an improper quadrature and a beta reduction; a harmonic approximation does not answer the question.',prereq=('energy integrals','beta integral'))
def o_period(m):
 u=s.symbols('u',positive=True);E=D**2/2+m*m*Y**4/4
 ans=s.sqrt(2*pi)*s.gamma(R(1,4))/(m*s.gamma(R(3,4)))
 jac=s.diff(u**R(1,4),u)/s.sqrt(1-u)
 return pack(m,r'y\prime\prime+'+L(m*m)+r'y^3=0,\quad y(0)=1,\quad y\prime(0)=0.\quad'+T('Find the least positive period. In the choices, Gamma denotes the Euler gamma function: ')+r'\Gamma(a)=\int_0^\infty u^{a-1}e^{-u}du\ (a>0).',ans,[(ans/4,'report a quarter period'),(ans/2,'report a half period'),(2*ans,'count each leg twice'),(2*pi/m,'replace nonlinear motion by its linearized frequency'),(s.sqrt(2)*ans,'miss the kinetic-energy factor')],[r'\frac12(y\prime)^2+\frac{'+L(m*m)+r'}4y^4=\frac{'+L(m*m)+r'}4',r'T=\frac{4\sqrt2}{'+L(m)+r'}\int_0^1\frac{dy}{\sqrt{1-y^4}}',r'u=y^4\ \Longrightarrow\ T=\frac{\sqrt2}{'+L(m)+r'}B(1/4,1/2)',r'B(a,b)=\Gamma(a)\Gamma(b)/\Gamma(a+b),\quad\Gamma(1/2)=\sqrt\pi'],[ck('energy derivative along vector field',s.diff(E,Y)*D+s.diff(E,D)*(-m*m*Y**3)),ck('initial energy',E.subs({Y:1,D:0}),m*m/4),ck('beta Jacobian',jac,u**R(-3,4)*(1-u)**R(-1,2)/4),ck('four-leg beta coefficient',4*s.sqrt(2)/m/4*s.sqrt(pi)*s.gamma(R(1,4))/s.gamma(R(3,4)),ans)],['Real solution; positive integer m. The beta function in the solution is defined by its Euler integral.'],['The conserved energy confines the solution to |y|<=1 and bounded velocity, so continuation is global. Velocity is strictly negative from y=1 to y=-1. The turning-point singularities are proportional to distance^-1/2 and are integrable. Uniqueness and reflection symmetry produce four equal quarter arcs and no earlier return to the initial state.'],'quartic-energy-period-beta-endpoint')

@reg('olympiad','power-coordinate-lifetime','ode-power-linearization-singular-boundary','nonlinear-coordinate-linearization','reframing','Discovers a power coordinate that cancels a derivative-square term, then distinguishes a zero of the transformed solution from a regular continuation.',prereq=('chain rule','maximal solution intervals'))
def o_power(m):
 Z=s.symbols('Z',positive=True)
 chain=R(3,2)*s.sqrt(Z)*D2+R(3,4)*D*D/s.sqrt(Z)
 transformed=s.simplify(chain.subs(D2,-D*D/(2*Z)-R(2,3)*m*m*Z))
 ans=pi/(2*m);u=s.cos(m*x)
 return pack(m,r'y\prime\prime+\frac{(y\prime)^2}{2y}+\frac{'+L(2*m*m)+r'}3y=0,\quad y(0)=1,\quad y\prime(0)=0.\quad'+T('Find the right endpoint of the maximal interval on which the classical solution stays positive.'),ans,[(pi/m,'continue through a zero of the transformed variable'),(pi/(4*m),'halve the first-zero time'),(2*pi/m,'return a full transformed period'),(pi/(2*m*m),'square the frequency')],[r'u=y^{3/2}\ \Longrightarrow\ u\prime\prime+'+L(m*m)+r'u=0',r'u(0)=1,\quad u\prime(0)=0,\quad u=\cos('+L(m)+r't)',r'y=\bigl(\cos('+L(m)+r't)\bigr)^{2/3}\quad\textnormal{while }\cos('+L(m)+r't)>0'],[ck('nonlinear chain-rule cancellation',transformed,-m*m*Z**R(3,2)),ck('linearized residual',s.diff(u,x,2)+m*m*u),ck('linearized initial value',u.subs(x,0),1),ck('linearized initial derivative',s.diff(u,x).subs(x,0)),ck('first endpoint is transformed zero',u.subs(x,ans))],['Positive classical y is required; real powers use the positive branch.'],['The coordinate map is smooth and invertible for y>0. Cos(mt)>0 exactly up to its first forward zero pi/(2m), and y tends to zero there. Its derivative is -(2m/3)sin(mt)cos(mt)^(-1/3), which diverges at that endpoint. Thus the positive classical solution cannot extend across it.'],'power-three-halves-linearization-singular-lifetime')

@reg('olympiad','Pinney-energy','ode-inverse-cube-isotonic-invariant','squared-coordinate-and-energy','reframing','Combines the inverse-cube energy with a squared dependent variable to expose a forced oscillator.',prereq=('energy integral','second-order linear equation'))
def o_pinney(m):
 q=m*m*s.cos(x)**2+m**(-2)*s.sin(x)**2;ans=1/m
 energy=m*m+m**(-2)
 return pack(m,r'y\prime\prime+y=y^{-3},\quad y(0)='+L(m)+r',\quad y\prime(0)=0,\quad y>0.\quad y(\pi/2)=?',ans,[(m,'retain the initial amplitude'),(m**(-2),'return y squared'),(2/m,'double reciprocal amplitude'),(1/(2*m),'halve reciprocal amplitude'),(m*m,'return squared initial amplitude')],[r'E=(y\prime)^2+y^2+y^{-2}='+L(energy),r'q=y^2\ \Longrightarrow\ q\prime\prime+4q=2E',r'q(t)='+L(q),T('The positive square root is required.')],[ck('inverse-cube energy derivative',2*D*(-Y+Y**(-3))+2*Y*D-2*Y**(-3)*D),ck('q equation',s.diff(q,x,2)+4*q,2*energy),ck('positive-root ODE identity',2*q*s.diff(q,x,2)-s.diff(q,x)**2+4*q*q,4),ck('initial q',q.subs(x,0),m*m),ck('initial q derivative',s.diff(q,x).subs(x,0)),ck('endpoint square',q.subs(x,pi/2),ans**2)],['The solution is the positive branch for all real t.'],['q>=min(m^2,m^-2)>0. For y=sqrt(q), multiplying y second+y-y^-3 by 4q^(3/2) gives 2q q second-(q prime)^2+4q^2-4, verified to vanish. Initial data and local uniqueness on y>0 identify this global solution.'],'inverse-cube-force-square-coordinate')

@reg('olympiad','switched-Riccati','fractional-linear-iteration','flow-composition-matrix','synthesis','Composes two distinct nonlinear time-one maps, recognizes a Mobius iteration, and closes it by a Fibonacci matrix identity.',prereq=('separable flows','matrix powers','Fibonacci recurrence'))
def o_switch(m):
 f=s.Integer(0)
 for j in range(int(m)):f=(f+1)/(f+2)
 M=s.Matrix([[1,1],[1,2]])**int(m);ans=s.fibonacci(2*m)/s.fibonacci(2*m+1)
 z=s.symbols('z',nonnegative=True);decay=z/(1+z*x)
 return pack(m,T('For every integer j=0,...,')+L(m-1)+r',\quad y\prime=\begin{cases}1,&2j<t<2j+1,\\-y^2,&2j+1<t<2j+2,\end{cases}\quad y(0)=0.'+T('The solution is continuous at each switch. Find ')+r'y('+L(2*m)+r').',ans,[(s.fibonacci(m)/s.fibonacci(m+1),'use only m Fibonacci indices'),(s.fibonacci(2*m-1)/s.fibonacci(2*m),'shift the cycle count'),(s.fibonacci(2*m+1)/s.fibonacci(2*m),'invert the final ratio'),(m/(m+1),'replace nonlinear iterations by a linear count'),(s.fibonacci(2*m)/s.fibonacci(2*m+2),'use the wrong denominator index')],[r'y\mapsto y+1\mapsto\frac{y+1}{y+2}',r'\binom{p_{j+1}}{q_{j+1}}=\begin{pmatrix}1&1\\1&2\end{pmatrix}\binom{p_j}{q_j},\quad(p_0,q_0)=(0,1)',r'(p_j,q_j)=(F_{2j},F_{2j+1}),\quad F_0=0,\ F_1=1,\ F_{n+1}=F_n+F_{n-1}'],[ck('decay flow residual',s.diff(decay,x)+decay**2),ck('decay flow initial value',decay.subs(x,0),z),ck('finite flow iteration versus Fibonacci',f,ans),ck('matrix power numerator',M[0,1],s.fibonacci(2*m)),ck('matrix power denominator',M[1,1],s.fibonacci(2*m+1))],['Piecewise classical, continuous solution on [0,2m]; all time-one map inputs are nonnegative.'],['Nonnegative states remain nonnegative during both subintervals, so denominators never vanish. The matrix maps the ratio p/q to (p+q)/(p+2q). Two applications of the Fibonacci recurrence prove the displayed vector induction; finite exact iteration independently verifies every published parameter.'],'piecewise-affine-and-Riccati-flow-Mobius-power')

@reg('olympiad','periodic-product-average','ode-periodic-logarithmic-conservation','periodic-total-derivatives','reframing','Extracts a mixed nonlinear average without solving the orbit, by combining a logarithmic derivative with a state derivative.',prereq=('periodic integration','logarithmic derivative'))
def o_lv(m):
 Fu=X*(m-2*Y);Fv=Y*(3*X-4);ans=2*m/3
 identity=m*s.cancel(Fv/Y)/6-Fu/2
 return pack(m,r'u\prime=u('+L(m)+r'-2v),\quad v\prime=v(3u-4).\quad'+T('Assume (u,v) is a positive nonconstant T-periodic solution. Find ')+r'\frac1T\int_0^T u(t)v(t)\,dt.',ans,[(m/3,'omit the loss coefficient four'),(4*m/3,'omit the interaction coefficient two'),(m/2,'replace the u mean by one'),(2*m,'omit the interaction coefficient three'),(m*m/6,'interchange the growth and loss coefficients')],[r'(\log v)\prime=3u-4\ \Longrightarrow\ \langle u\rangle=4/3',r'u\prime='+L(m)+r'u-2uv\ \Longrightarrow\ \langle uv\rangle=\frac{'+L(m)+r'}2\langle u\rangle',T('Both total derivatives integrate to zero over one period.')],[ck('mixed average exact derivative identity',identity,X*Y-ans),ck('logarithmic derivative',s.cancel(Fv/Y),3*X-4)],['A positive nonconstant periodic orbit is assumed; T>0 is its period.'],['Positivity makes log v differentiable and periodic. Integrating the verified identity uv-2m/3=(m/6)(log v) prime-u prime/2 annihilates both boundary terms. This proves the average for every orbit satisfying the hypothesis, without any assumption about its period or shape.'],'periodic-predator-prey-mixed-product-average')

@reg('olympiad','periodic-Floquet-multiplier','ode-nonlinear-Poincare-linearization','log-average-and-variational-flow','synthesis','Uses an unknown positive periodic orbit to compute a return-map derivative exactly, combining a nonlinear average with a variational equation.',prereq=('variational equation','Poincare map'))
def o_floquet(m):
 a=m+s.sin(x);F=a*Y-Y*Y;variational=s.diff(F,Y);ans=s.exp(-2*pi*m)
 return pack(m,r'y\prime=('+L(m)+r'+\sin t)y-y^2.\quad'+T('Let y star be a positive 2pi-periodic solution. Let P map the value y(0) to y(2pi). Find ')+r'P\prime(y_*(0)).',ans,[(s.exp(2*pi*m),'reverse stability exponent'),(s.exp(-4*pi*m),'retain the quadratic derivative but omit growth'),(s.exp(-pi*m),'use half a forcing period'),(1,'assume every periodic solution is neutrally stable'),(s.exp(-2*pi/m),'invert mean growth')],[r'(\log y_*)\prime='+L(m)+r'+\sin t-y_*\ \Longrightarrow\ \int_0^{2\pi}y_*\,dt=2\pi\cdot'+L(m),r'\eta\prime=('+L(m)+r'+\sin t-2y_*)\eta,\quad\eta(0)=1',r'P\prime(y_*(0))=\exp\!\left(\int_0^{2\pi}('+L(m)+r'+\sin t-2y_*)dt\right)'],[ck('derivative of vector field',variational,a-2*Y),ck('variational exponent elimination',variational,-a+2*s.cancel(F/Y)),ck('one-period growth integral',s.integrate(a,(x,0,2*pi)),2*pi*m)],['The specified positive periodic solution is assumed; derivative is with respect to initial data at fixed initial time zero.'],['The smooth polynomial field has differentiable dependence on initial data on a neighborhood of the compact periodic trajectory over one period. Integrating its logarithmic derivative gives the orbit average. The verified exponent identity then converts the variational integral to -2pi*m because the logarithmic boundary term vanishes.'],'positive-periodic-logistic-return-map-multiplier')

@reg('olympiad','resonant-boundary-compatibility','ode-Fredholm-boundary-compatibility','orthogonality-and-particular-witness','synthesis','Finds a solvability obstruction for a resonant boundary problem and supplies a solution to establish sufficiency.',prereq=('integration by parts','resonance','boundary value problems'))
def o_fredholm(m):
 ans=2*(-1)**m/m;c=s.symbols('c',real=True);f=x/m**2-c*x*s.cos(m*x)/(2*m)
 return pack(m,r'y\prime\prime+'+L(m*m)+r'y=t+c\sin('+L(m)+r't),\quad y(0)=y(\pi)=0.\quad'+T('For which real c does a solution exist?'),ans,[(0,'ignore the resonance obstruction'),(-ans,'reverse the endpoint sign'),(2*(-1)**m,'omit the frequency divisor'),((-1)**m/m,'miss the mean square factor one half'),(2*(-1)**m/m**2,'divide by frequency twice')],[T('Multiply by sin(mt) and integrate by parts twice. Both boundary terms vanish.'),r'0=\int_0^\pi t\sin('+L(m)+r't)dt+c\int_0^\pi\sin^2('+L(m)+r't)dt',r'0=-\frac{\pi(-1)^{'+L(m)+r'}}{'+L(m)+r'}+c\frac\pi2',r'y(t)=\frac{t}{'+L(m*m)+r'}-\frac{ct\cos('+L(m)+r't)}{'+L(2*m)+r'}'+T(' satisfies the equation and, for this c, both boundaries.')],[ck('resonance projection first term',s.integrate(x*s.sin(m*x),(x,0,pi)),-pi*(-1)**m/m),ck('resonance projection normalization',s.integrate(s.sin(m*x)**2,(x,0,pi)),pi/2),ck('particular residual',s.diff(f,x,2)+m*m*f,x+c*s.sin(m*x)),ck('left boundary',f.subs(x,0)),ck('right boundary at compatible c',f.subs({x:pi,c:ans}))],['Real twice continuously differentiable solution on [0,pi]; m positive integer.'],['The test function sin(mt) solves the adjoint homogeneous equation and vanishes at both endpoints. The boundary expression y prime*sin(mt)-m*y*cos(mt) vanishes because y has zero endpoints. Thus the projection is necessary. The explicit particular solution with compatible c verifies sufficiency; adding any multiple of sin(mt) gives the nonuniqueness.'],'resonant-Dirichlet-forcing-orthogonality')

@reg('olympiad','sharp-lifetime-comparison','ode-Riccati-comparison-sharp-bound','bounded-angle-comparison','proof','Turns a differential inequality into a bounded angle, then proves optimality by constructing a saturating solution.',prereq=('differential inequalities','maximal intervals'))
def o_comparison(m):
 ans=pi/(2*m);f=m*s.tan(m*x);z=s.symbols('z',real=True)
 return pack(m,T('A real C1 function on [0,T) satisfies ')+r'y(0)=0,\quad y\prime(t)\ge y(t)^2+'+L(m*m)+r'.\quad'+T('Find the least universal upper bound on T; equality of the bound must be attainable.'),ans,[(pi/m,'use the full range of arctangent rather than its forward range'),(pi/(4*m),'halve the sharp angle bound'),(1/m,'replace arctangent by its tangent-line estimate'),(2*pi/m,'use an oscillation period'),(pi/(2*m*m),'square the rate')],[r'\theta(t)=\arctan(y(t)/'+L(m)+r')\ \Longrightarrow\ \theta\prime=\frac{'+L(m)+r'y\prime}{'+L(m*m)+r'+y^2}\ge '+L(m),r'\theta(t)\ge '+L(m)+r't,\qquad\theta(t)<\pi/2',r'y(t)='+L(m)+r'\tan('+L(m)+r't)'+T(' attains the bound on its maximal forward interval.')],[ck('angle derivative',s.diff(s.atan(z/m),z),m/(m*m+z*z)),ck('saturating solution residual',s.diff(f,x)-f*f-m*m),ck('saturating initial value',f.subs(x,0))],['T>0; inequality holds pointwise for every t in [0,T). The question asks for a bound on such intervals, not an identical lifetime for all inequalities.'],['The positive angle derivative implies theta(t)>=mt. Since arctangent of a finite real number is strictly below pi/2, every t<T is below pi/(2m), hence T<=pi/(2m). The tangent witness is C1 throughout that half-open interval and diverges at its endpoint, so no smaller universal upper bound works.'],'Riccati-inequality-angle-lifetime-sharpness')

@reg('olympiad','nonlinear-radial-asymptotic','ode-nonlinear-radial-decay-invariant','radius-squared-reduction','reframing','Cancels the rotational part of a nonlinear system and resolves an asymptotic coefficient rather than only proving decay.',prereq=('Lyapunov function','scalar separable equations'))
def o_radial(m):
 Fu=-X-m*Y-X*(X*X+Y*Y);Fv=m*X-Y-Y*(X*X+Y*Y);q=m*m*s.exp(-2*x)/(1+m*m*(1-s.exp(-2*x)));ans=m*m/(1+m*m)
 return pack(m,r'u\prime=-u-'+L(m)+r'v-u(u^2+v^2),\quad v\prime='+L(m)+r'u-v-v(u^2+v^2),\quad(u(0),v(0))=('+L(m)+r',0).\quad\lim_{t\to\infty}e^{2t}(u^2+v^2)=?',ans,[(m*m,'retain the linearized initial coefficient'),(m/(m+1),'use radius rather than radius squared'),(1/(1+m*m),'drop initial energy from the numerator'),(m*m/(m*m-1),'reverse nonlinear damping sign'),(1,'mistake the limiting coefficient for a universal constant')],[r'E=u^2+v^2\ \Longrightarrow\ E\prime=-2E(1+E),\quad E(0)='+L(m*m),r'E(t)=\frac{'+L(m*m)+r'e^{-2t}}{1+'+L(m*m)+r'(1-e^{-2t})}',T('Multiplying by the linear decay factor leaves a finite nonlinear renormalization.')],[ck('radial Lie derivative',2*X*Fu+2*Y*Fv,-2*(X*X+Y*Y)*(1+X*X+Y*Y)),ck('scalar solution residual',s.diff(q,x)+2*q*(1+q)),ck('initial radial energy',q.subs(x,0),m*m),ck('renormalized asymptotic limit',s.limit(s.exp(2*x)*q,x,s.oo),ans)],['Forward solution t>=0.'],['The polynomial vector field is locally Lipschitz. E prime<=0 bounds the state for all forward times, which prevents finite escape and proves global continuation. The scalar IVP is unique, so its verified positive formula is u squared+v squared. Its denominator stays at least one for t>=0.'],'nonlinear-planar-radius-decay-renormalization')

@reg('olympiad','ground-state-variance','ode-factorization-ground-state','square-completion-and-moment','synthesis','Proves the least eigenvalue by a nonnegative square, identifies all equality cases, then evaluates a normalized moment.',prereq=('integration by parts','Gaussian integrals','spectral lower bounds'))
def o_ground(m):
 f=s.exp(-m*x*x/2);ans=1/(2*m);density=s.exp(-m*x*x)
 cross=Y*Y+2*x*Y*D
 local=(D+m*x*Y)**2-(D*D+m*m*x*x*Y*Y-m*Y*Y)
 return pack(m,r'-y\prime\prime+'+L(m*m)+r't^2y=\lambda y\quad(t\in\mathbb R).\quad'+T('Among nonzero real smooth solutions for which the function and every derivative decay faster than every inverse power, choose the smallest possible lambda. Find ')+r'\frac{\int_{\mathbb R}t^2y(t)^2dt}{\int_{\mathbb R}y(t)^2dt}.',ans,[(1/m,'use variance of y instead of y squared'),(1/(4*m),'double the Gaussian exponent twice'),(m/2,'invert the frequency scale'),(s.Rational(1,2),'ignore frequency dependence'),(2/m,'confuse the second moment with its doubled value')],[r'\int_{\mathbb R}(y\prime+'+L(m)+r'ty)^2dt=(\lambda-'+L(m)+r')\int_{\mathbb R}y^2dt\ge0',r'\lambda_{\min}='+L(m)+r',\quad y=C e^{-'+L(m)+r't^2/2}',r'0=\int_{\mathbb R}(t e^{-'+L(m)+r't^2})\prime dt=\int_{\mathbb R}(1-'+L(2*m)+r't^2)e^{-'+L(m)+r't^2}dt'],[ck('pointwise square completion total derivative',local,m*cross),ck('ground state eigenfunction residual',-s.diff(f,x,2)+m*m*x*x*f,m*f),ck('Gaussian moment derivative identity',s.diff(x*density,x),(1-2*m*x*x)*density)],['Schwartz means smooth with the function and all derivatives decaying faster than every inverse power; y is nonzero and real.'],['Rapid decay makes every integration by parts legitimate with zero boundary terms. Multiplying the ODE by y and completing the square gives lambda>=m. The nonzero Gaussian witness is Schwartz and attains m. Equality forces y prime+mt*y=0 pointwise, so every minimizing solution is a nonzero Gaussian multiple. Integrating the displayed derivative gives the moment ratio without an assumed Gaussian normalization formula.'],'whole-line-oscillator-factorization-equality-moment')

@reg('olympiad','Schwarzian-IVP','ode-Schwarzian-log-derivative-chain','successive-logarithmic-reductions','reframing','Reduces a third-order nonlinear quotient equation through its logarithmic derivative and controls the branch needed for uniqueness.',prereq=('logarithmic derivatives','Riccati equation'))
def o_schwarzian(m):
 f=s.tanh(m*x);fp=s.diff(f,x);q=-2*m*s.tanh(m*x);ans=s.tanh(m)
 return pack(m,r'\frac{y\prime\prime\prime}{y\prime}-\frac32\left(\frac{y\prime\prime}{y\prime}\right)^2=-'+L(2*m*m)+r',\quad y(0)=0,\ y\prime(0)='+L(m)+r',\ y\prime\prime(0)=0.\quad'+T('Take the real solution with y prime>0. Find y(1).'),ans,[(s.tan(m),'replace hyperbolic with circular tangent'),(m*s.tanh(1),'linearize the inner scale'),(s.tanh(2*m),'double the logarithmic-derivative rate'),(s.tanh(m)/m,'divide by the initial slope twice'),(m*s.tanh(m),'retain an extra amplitude factor')],[r'q=y\prime\prime/y\prime\ \Longrightarrow\ q\prime-q^2/2=-'+L(2*m*m),r'q(0)=0\ \Longrightarrow\ q=-'+L(2*m)+r'\tanh('+L(m)+r't)',r'(\log y\prime)\prime=q\ \Longrightarrow\ y\prime='+L(m)+r'\operatorname{sech}^2('+L(m)+r't),\quad y=\tanh('+L(m)+r't)'],[ck('Riccati reduction solution',s.diff(q,x)-q*q/2,-2*m*m),ck('logarithmic derivative identity',s.diff(fp,x)/fp,q),ck('initial value',f.subs(x,0)),ck('initial slope',fp.subs(x,0),m),ck('initial second derivative',s.diff(f,x,2).subs(x,0)),ck('evaluation',f.subs(x,1),ans)],['Real t; require y prime>0, so all quotients and log y prime are defined.'],['Differentiating q=y second/y prime gives q prime=y third/y prime-q squared. Thus the original equation is equivalent to the displayed Riccati equation. Its smooth IVP is unique; the recovered derivative is strictly positive for every finite real t. Integrating with the initial value determines y globally.'],'third-order-Schwarzian-to-Riccati-log-derivative')

@reg('olympiad','Darboux-oscillator','ode-Darboux-intertwining-potential','intertwining-operator','reframing','Recognizes a variable-coefficient potential as an operator transform of a free oscillator and normalizes the resulting IVP.',prereq=('operator composition','hyperbolic derivative identities'))
def o_darboux(m):
 f=m*s.sin(m*x)+s.tanh(x)*s.cos(m*x);at=pi/(4*m);h=s.tanh(at);ans=s.sqrt(2)*(m+h)/2
 z=s.Function('z')(x);Az=s.diff(z,x)-s.tanh(x)*z
 intertwined=s.diff(Az,x,2)+(m*m+2/s.cosh(x)**2)*Az-(s.diff(s.diff(z,x,2)+m*m*z,x)-s.tanh(x)*(s.diff(z,x,2)+m*m*z))
 return pack(m,r'y\prime\prime+('+L(m*m)+r'+2\operatorname{sech}^2t)y=0,\quad y(0)=0,\quad y\prime(0)='+L(m*m+1)+r'.\quad y('+L(at)+r')=?\quad'+T('Here sech t=1/cosh t.'),ans,[(s.sqrt(2)*(m-h)/2,'use the wrong intertwining sign'),(s.sqrt(2)*(2*m+h)/2,'double only the oscillator derivative'),(s.sqrt(2)*(m+2*h)/2,'double only the potential term'),(s.sqrt(2)*(m+h),'omit the sine and cosine value factor'),(s.sqrt(2)*(m+h)/(2*m),'divide normalization by the frequency')],[r'(D^2+'+L(m*m)+r'+2\operatorname{sech}^2t)(D-\tanh t)=(D-\tanh t)(D^2+'+L(m*m)+r')',r'y=-(D-\tanh t)\cos('+L(m)+r't)='+L(f),T('This function has the stated two initial data; evaluate at the given point.')],[ck('operator intertwining identity',intertwined),ck('variable-potential residual',s.diff(f,x,2)+(m*m+2/s.cosh(x)**2)*f),ck('initial state',f.subs(x,0)),ck('initial derivative',s.diff(f,x).subs(x,0),m*m+1),ck('evaluation',f.subs(x,at),ans)],['D denotes differentiation in t; sech t=1/cosh t. All coefficients are smooth for real t.'],['The displayed operator identity follows by the product rule and (tanh t) prime=sech squared t. Applying it to a free oscillator produces a solution of the variable-potential equation. The checked initial data and uniqueness of the smooth linear IVP identify it on all real t.'],'Darboux-one-soliton-oscillator-intertwining')

def display_statement(statement):
 pieces=re.split(r'(\\textnormal\{[^{}]*\}|\\quad\s*)',statement)
 lines=[]
 for piece in pieces:
  piece=piece.strip()
  if not piece or piece.startswith(r'\quad'):continue
  if piece.startswith(r'\textnormal{') and piece.endswith('}'):
   lines.extend(T(part) for part in textwrap.wrap(piece[len(r'\textnormal{'):-1],width=44))
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
 report={'counts':counts,'candidateCount':len(rows),'activeImportedCount':0,'quarantine':quarantine,'uniqueIds':True,'uniqueSemanticHashes':True,'executedCheckCount':sum(len(r['automatedChecks']) for r in rows),'humanReviewed':False,'analyticArguments':'Human-readable analytic certificates are AI-authored, distinct from executed symbolic checks.','difficultyReview':'AI-assisted editorial admission; 12 Olympiad constructions independently reviewed by a second AI agent. No human or formal proof review is claimed.','relatedIdeaGroupCount':len({f['relatedIdeaGroupId'] for f in catalog()}),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 return report

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(Path(__file__).parent));args=ap.parse_args();generate(args.out)
