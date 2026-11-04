"""Independent finite formulas/ODE residuals for160 lower extensions/repairs."""
from pathlib import Path
import hashlib,itertools,json,re,sys
import sympy as s
from literal_choices import parse,same,distinct
x,y,z,t,u,v=s.symbols('x y z t u v',real=True)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def solve(r):
 fid=r['familyId'];m=s.Integer(r['parameters'].get('m',r.get('provenance',{}).get('authoring',{}).get('builderParameters',{}).get('m')));slug=re.split(r'-(?:easy|medium|hard)-',fid)[1];checks=[];level=r['difficulty']
 def eq(a,b):assert s.simplify(a-b)==0;checks.append('Exact residual/identity')
 if 'multivariable' in fid:
  direct={
   'partial-hold-fixed':(2*m,'Hold y fixed and differentiate x squared times y.'),
   'mixed-partial':(2*m,'Differentiate once in each variable, then evaluate at the unit point.'),
   'directional-unit':(s.Rational(6,5)*m,'Dot the gradient at the stated point with the already normalized direction.'),
   'tangent-plane':(m*m+2,'Substitute the tangency point in the specified plane, or use the radial gradient.'),
   'linearization-two-inputs':(2*m+s.Rational(1,10)*(m+2),'Use the gradient to retain only the first-order changes in both coordinates.'),
   'rectangle-integral':(m*(m+1)/2,'Integrate each coordinate over its rectangular bounds.'),
   'triangular-region':(m*m/2,'Integrate the triangular width or use its elementary area.'),
   'polar-area':(s.pi*m*m,'The disk has radius m, not squared radius m.'),
   'chain-curve':(2*m+4*m**3,'Compose to t squared plus t to the fourth and differentiate.'),
   'divergence':(m+3,'Sum the three matching coordinate partial derivatives.'),
   'potential-endpoints':(m*m+1,'The conservative line integral is the potential difference.'),
   'box-average':((m+3)/2,'The linear function averages to its value at the box center.'),
   'gradient-max-direction':(m*s.sqrt(5),'Cauchy–Schwarz identifies the maximum directional derivative with the gradient norm.'),
   'Lagrange-circle-linear':(s.sqrt(m*m+1),'Cauchy–Schwarz on the unit circle, with parallel direction attaining the bound.'),
   'change-order':(m/(m+1),'Reverse the triangle or integrate the original power directly.'),
   'ellipse-transform':(m*s.pi,'The diagonal map to the unit disk has positive Jacobian m.'),
   'polar-moment':(s.pi/(m+1),'Include the radial Jacobian in the power integral.'),
   'Green-circulation':(2*s.pi*m*m,'Use constant curl two and the counterclockwise disk area.'),
   'divergence-flux':(4*s.pi*m**3,'Divergence three times the ball volume, with outward orientation.'),
   'surface-graph-area':(s.sqrt(m*m+2),'Integrate the constant graph area factor over the unit square.'),
   'implicit-surface-partial':(-1/m,'Implicit differentiation is valid on the positive nonzero z branch.'),
   'density-centroid':((m+1)/(m+2),'Divide the first density-weighted moment by the positive mass.'),
   'spherical-moment':(4*s.pi/(2*m+3),'Integrate the radial power with the three-dimensional radial Jacobian.'),
   'quadratic-eigenconstraint':((2*m+1+s.sqrt(5))/2,'Find the larger eigenvalue of the real symmetric quadratic-form matrix.'),
   'moving-domain-derivative':(2*s.pi*m*s.exp(m*m),'Polar coordinates followed by the fundamental theorem at the moving radius.'),
   'ellipsoid-inertia':(4*s.pi*m**3/15,'Scale one coordinate to the unit ball; symmetry gives its coordinate second moment.'),
   'simplex-beta':(s.factorial(m)*s.factorial(m+1)/s.factorial(2*m+3),'Integrate one monomial then apply the integer beta recurrence on the remaining interval.'),
   'nonconservative-hole':(2*s.pi,'Parametrize the displayed circle; numerator and denominator cancel the radius.'),
   'Stokes-tilted-surface':(s.Integer(2),'The exact differential z dz contributes zero; projected constant curl gives twice the unit-square area.'),
   'boundary-versus-interior':(m-2,'Use x squared+y squared≥2xy and xy≤1; the corner(1,1)attains the bound.'),
   'surface-flux-graph':(s.pi/m+s.pi/(2*m*m),'Dot the upward graph area vector with the field, giving1+r squared; integrate over the disk.'),
   'mixed-Hessian-coordinate':(2*(1-m),'Substitute both linear coordinates and read the uv coefficient.'),
   'path-dependent-directional':(s.Rational(1,2),'Along the specified nonlinear path, the two denominator terms coincide.'),
   'nonlinear-Jacobian':((m-1)*s.log(2)/2,'Use positive product/ratio coordinates; the single-valued inverse Jacobian is1/(2v), integrated over1≤u≤m and1≤v≤2.'),
   'Gaussian-precision':(s.pi/s.sqrt(m-1),'Complete(y+x)squared+(m−1)x squared, then use two positive Gaussian factors.'),
  }
  answer,route=direct[slug]
  if slug=='partial-hold-fixed':eq(s.diff(x*x*y+y**3,x).subs({x:m,y:1}),answer)
  if slug=='mixed-partial':eq(s.diff(x*x*y**m,x,y).subs({x:1,y:1}),answer)
  if slug=='chain-curve':eq(s.diff(t*t+t**4,t).subs(t,m),answer)
  if slug=='surface-flux-graph':eq(s.integrate(2*s.pi*t*(1+t*t),(t,0,1/s.sqrt(m))),answer)
  if slug=='nonlinear-Jacobian':
   up,vp=s.symbols('up vp',positive=True);X=s.sqrt(up*vp);Y=s.sqrt(up/vp);jac=s.det(s.Matrix([[s.diff(X,up),s.diff(X,vp)],[s.diff(Y,up),s.diff(Y,vp)]]));eq(jac,-1/(2*vp));eq(s.integrate(s.integrate(-jac,(vp,1,2)),(up,1,m)),answer)
  if slug=='Gaussian-precision':eq(m*x*x+2*x*y+y*y,(x+y)**2+(m-1)*x*x)
  if slug=='quadratic-eigenconstraint':eq(s.det(s.Matrix([[m-answer,1],[1,m+1-answer]])),0)
  if slug in ['moving-domain-derivative','nonconservative-hole','Stokes-tilted-surface','boundary-versus-interior','mixed-Hessian-coordinate']:level='medium'
  if slug=='path-dependent-directional':level='easy'
 else:
  direct={
   'field-slope':(m*m+2*m,'Evaluate the stated slope field at the known point.'),
   'rate-identification':(m,'Differentiate the exponential and divide by its nonzero value.'),
   'phase-line-stability':(-m,'The vector-field derivative at the negative equilibrium is negative.'),
   'euler-step':(m-1,'Evaluate the initial slope and advance by the stated step.'),
   'primitive-initial-value':(1+m/3,'Integrate the power and use the initial value.'),
   'doubling-data':(8*m,'Each unit time doubles a solution of this constant-rate equation.'),
   'cooling-limit':(m+10,'The negative coefficient makes the stated ambient equilibrium attracting.'),
   'mixing-inflow':(3-2*m/(m+2),'Subtract outflow concentration times flow from inflow salt rate.'),
   'constant-acceleration':(1+m/2,'Integrate the acceleration twice and apply both initial conditions.'),
   'equation-order':(m-2,'Order is the highest derivative index, independent of powers of lower derivatives.'),
   'oscillator-initial-data':(m+1,'Initial displacement and velocity give the cosine and sine coefficients.'),
   'transfer-conservation':((m+3-parse(re.search(r'At a later time \}v=(.*?)\\textnormal',r['statement']).group(1))) if slug=='transfer-conservation' else 0,'The derivative of u+v is zero; subtract the displayed later v from its initial total.'),
   'logistic-hitting':(s.log(m),'The logistic odds decay exponentially; solve the half-population hitting equation.'),
   'variable-integrating-factor':((2**(m+2)-1)/(2*(m+2)),'Multiply by t, integrate from the initial endpoint, then divide by the current t.'),
   'exact-curve':(s.sqrt(m*m+m+1),'The exact potential is t squared+ty+y squared; preserve its initial level and select t>0.'),
   'bernoulli-reciprocal':(1/(2-(m+1)*s.E),'The reciprocal satisfies a linear equation; it stays negative through the evaluation time.'),
   'homogeneous-ratio':(-s.E/(m+1),'Set v=y/t and integrate its reciprocal against logarithmic time.'),
   'harvest-bifurcation':(m*m/4,'Maximize the concave equilibrium production parabola; the double-root equilibrium is positive.'),
   'distinct-characteristic-roots':(s.exp(m)-s.E,'The characteristic roots are1,m; the initial conditions give opposite unit coefficients.'),
   'resonant-forcing':((-1)**(m+1)*m*s.pi/2,'The zero-data solution is(sin t−t cos t)/2; evaluate at the displayed multiple of pi.'),
   'critical-damping':(2*m,'Set the characteristic discriminant to zero and use the positive coefficient.'),
   'periodic-amplitude':(1/s.sqrt(m*m+1),'Solve the sine/cosine coefficient system; take the Euclidean amplitude.'),
   'riccati-particular':(m/(m-1),'Subtract the particular solution t, then solve the reciprocal perturbation; its pole lies after the requested time.'),
   'nonlinear-energy-speed':(m*m,'Energy gives velocity squared=m to the fourth−y to the fourth; the trajectory reaches y=0 and attains maximal speed.'),
   'euler-cauchy-resonance':(s.exp(2/m)/(2*m*m),'Logarithmic time and removal of the repeated exponential root leave a twice-integrated constant.'),
   'variable-second-order-basis':(m*(3-s.E),'The independent solutions t+1 and exp t satisfy the equation; initial data determine both coefficients.'),
   'remove-first-derivative':(-s.exp(-s.pi**2/(2*m*m)),'Use a Gaussian factor to cancel the first derivative and obtain a harmonic oscillator.'),
   'step-forcing':(2*m,'Before the switch the zero-data solution is zero; afterward use the shifted constant-forced oscillator.'),
   'impulse-jump':(m/s.E,'Integrating across the impulse gives a velocity jump m and continuous displacement; evolve the repeated-root equation for one time unit.'),
   'rotating-linear-system':(-s.exp(-s.pi/m),'The matrix splits into commuting damping and rotation; the requested angle is pi.'),
   'jordan-system':(s.exp(m)/2,'Remove the scalar exponential; the nilpotent chain integrates twice, giving t squared/2.'),
   'linear-stability-bound':(m-s.sqrt(m*m-m),'Trace must be negative and determinant positive; intersect both conditions, selecting the lower determinant root.'),
   'mixed-boundary-spectrum':(s.pi**2/(4*m*m),'Zero/negative eigenparameters give no nonzero solution; the first positive sine mode has a quarter-wave at the derivative endpoint.'),
   'wronskian-transport':(s.Integer(2)**(-m),'Differentiate the defined Wronskian and cancel the common q terms; integrate W prime=−mW/t.'),
  }
  answer,route=direct[slug]
  if slug=='variable-integrating-factor':f=(t**(m+2)-1)/((m+2)*t);eq(s.diff(f,t)+f/t,t**m);eq(f.subs(t,1),0);eq(f.subs(t,2),answer)
  if slug=='bernoulli-reciprocal':f=1/(t+1-(m+1)*s.exp(t));eq(s.diff(f,t)+f,t*f*f);eq(f.subs(t,0),-1/m);eq(f.subs(t,1),answer)
  if slug=='homogeneous-ratio':f=-t/(m+s.log(t));eq(s.diff(f,t),f/t+(f/t)**2);eq(f.subs(t,1),-1/m);eq(f.subs(t,s.E),answer)
  if slug=='resonant-forcing':f=(s.sin(t)-t*s.cos(t))/2;eq(s.diff(f,t,2)+f,s.sin(t));eq(f.subs(t,0),0);eq(s.diff(f,t).subs(t,0),0);eq(f.subs(t,m*s.pi),answer)
  if slug=='euler-cauchy-resonance':f=t*t*s.log(t)**2/2;eq(t*t*s.diff(f,t,2)-3*t*s.diff(f,t)+4*f,t*t);eq(f.subs(t,1),0);eq(s.diff(f,t).subs(t,1),0)
  if slug=='variable-second-order-basis':f=m*(t+1-s.exp(t-1));eq(t*s.diff(f,t,2)-(t+1)*s.diff(f,t)+f,0);eq(f.subs(t,1),m);eq(s.diff(f,t).subs(t,1),0)
  if slug=='remove-first-derivative':f=s.exp(-t*t/2)*s.cos(m*t);eq(s.diff(f,t,2)+2*t*s.diff(f,t)+(t*t+m*m+1)*f,0);eq(f.subs(t,0),1);eq(s.diff(f,t).subs(t,0),0)
  if slug in ['step-forcing','wronskian-transport']:level='medium'
 return s.simplify(answer),route,checks,level

def main(path,out):
 data=Path(path).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  try:
   answer,route,checks,level=solve(r);values=[parse(c['math']) for c in r['choices']];matches=[j for j,a in enumerate(values) if same(a,answer)]
   assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId'],str(answer)
   assert all(distinct(a,b) for a,b in itertools.combinations(values,2))
   blockers=[]
   if r'\textasciicircum{}m' in r['statement']:blockers.append('Undefined builder parameter in prose path; render actual power explicitly.')
   if '|y prime|' in r['statement']:blockers.append('Write the defined derivative mathematically instead of computer-style prose.')
   results.append({'familyId':r['familyId'],'index':r.get('instanceIndex',r['parameters'].get('instance')),'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'independentAnswer':s.srepr(answer),'checks':checks,'easiestOptionsVisibleRoute':route,'difficultyRecommended':level,'difficultyChanged':level!=r['difficulty'],'allSixLiteralChoicePairsDistinct':True,'presentationBlockers':blockers,'passed':True})
  except Exception as e:results.append({'familyId':r['familyId'],'index':r.get('instanceIndex',r['parameters'].get('instance')),'passed':False,'error':str(e)})
 report={'reviewer':'root-independent-review','author':'integration_research','inputSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parserSha256':hashlib.sha256(Path(__file__).with_name('literal_choices.py').read_bytes()).hexdigest(),'instances':len(rows),'passed':sum(r['passed'] for r in results),'results':results,'scope':'Fresh independent formulas from the literal statements, with residual/domain/attainment arguments as appropriate. No frozen author constructor or supplied independent-solution module imported. All literal choices separately parsed; all six inequivalences checked. Source-bound notation/difficulty revisions and final-family option screen remain necessary. AI editorial review, not human calibration.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if __name__=='__main__':main(*sys.argv[1:])
