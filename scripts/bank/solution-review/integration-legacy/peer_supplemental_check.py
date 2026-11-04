from pathlib import Path
import sympy as s,json,hashlib
base=Path(__file__).parent;target=base.parent/'supplemental/solutions.py'
t=s.symbols('t',real=True);m=s.symbols('m',positive=True);h=s.Function('h')(t);q=s.Function('q')(t);y=s.Function('y')(t);u=s.symbols('u',real=True);checks=[]
def ck(name,value):
 r=s.simplify(s.expand_trig(s.expand(value)));assert r==0,(name,r);checks.append({'check':name,'residual':'0','passed':True})
T=s.tanh(t);sech2=1-T*T
A=lambda f:s.diff(f,t)-T*f
L=lambda f:s.diff(f,t,2)+(m*m+2*sech2)*f
ck('Darboux operator identity on an arbitrary differentiable test function',L(A(h))-A(s.diff(h,t,2)+m*m*h))
yp=m*s.sin(m*t)+s.tanh(t)*s.cos(m*t)
ck('Darboux IVP residual',s.diff(yp,t,2)+(m*m+2*sech2)*yp);ck('Darboux initial value',yp.subs(t,0));ck('Darboux initial derivative',s.diff(yp,t).subs(t,0)-(m*m+1))
ck('Ground-state square completion pointwise identity',(s.diff(y,t)+m*t*y)**2-(s.diff(y,t)**2+m*m*t*t*y*y-m*y*y)-m*s.diff(t*y*y,t))
Y=s.symbols('Y',positive=True);V,W=s.symbols('V W',real=True)
ck('Positive power-coordinate chain identity',s.Rational(3,2)*s.sqrt(Y)*W+s.Rational(3,4)*V*V/s.sqrt(Y)+m*m*Y**s.Rational(3,2)-s.Rational(3,2)*s.sqrt(Y)*(W+V*V/(2*Y)+2*m*m*Y/3))
for n in [4,11]:
 q=n*n*s.cos(t)**2+s.Rational(1,n*n)*s.sin(t)**2
 ck('Pinney squared-solution equation '+str(n),2*q*s.diff(q,t,2)-s.diff(q,t)**2+4*q*q-4)
 c=1+n*n*u*(1-u);F=2/(n*s.sqrt(n*n+4))*s.atanh(n*(2*u-1)/s.sqrt(n*n+4))
 ck('Two-centre rational primitive '+str(n),s.diff(F,u)-1/c)
 c0=2*(-1)**n/s.Integer(n);f=t/n**2-c0*t*s.cos(n*t)/(2*n)
 ck('Boundary compatibility explicit particular '+str(n),s.diff(f,t,2)+n*n*f-t-c0*s.sin(n*t));ck('Boundary compatibility left endpoint '+str(n),f.subs(t,0));ck('Boundary compatibility right endpoint '+str(n),f.subs(t,s.pi))
z=s.symbols('z');
for n in range(4,12):
 P=z**n-n*z+n-1;Q=sum((n-1-j)*z**j for j in range(n-1));ck('Winding factorization '+str(n),P-(z-1)**2*Q)
 R0=1+s.Rational(1,n);critical=s.Rational(n-1,n-2);R1=(R0+critical)/2
 coeff=[(n-1-j)*R1**j for j in range(n-1)]
 assert all(coeff[j]>coeff[j+1]>0 for j in range(n-2));checks.append({'check':'Winding coefficient decrease for an explicit enlarged radius '+str(n),'passed':True})
x,y,z=s.symbols('x y z',real=True)
ck('Vandermonde identity on zero-sum plane',((x-y)**2*(y-z)**2*(z-x)**2-(x*x+y*y+z*z)**3/2+27*x*x*y*y*z*z).subs(z,-x-y))
report={'scope':'Bounded independent read-only review; all 12 advanced ODE and all 12 advanced multivariable branches read, plus six statement-clarification families checked against immutable artifact. Selected high-risk displayed identities checked independently below. Not a fresh 944-instance full validation.','sourceSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'checks':checks,'checkCount':len(checks),'incorrectFinalFormulaFound':False,'findings':[{'type':'undefined-result-label','families':['simplex-beta','Gaussian-wedge','planar-log-potential','two-centre-resolvent','log-simplex-moment','squared-log-disk'],'finding':'Source integral is unnamed but I is used without introduction.','ownerResponse':'Targeted I definition added; owner also naming area/volume labels.'},{'type':'missing-theorem-base-value','family':'log-simplex-moment','finding':'Gamma recurrence alone does not determine trigamma at one; supply its convergent reciprocal-square series or initial value pi^2/6.','ownerResponse':'Owner agreed and added trigamma series.'}],'statementClarificationsMeaningPreserved':['path-dependent-directional','nonlinear-energy-speed','periodic-floquet-multiplier','sharp-lifetime-comparison','schwarzian-ivp','darboux-oscillator'],'theoremBridgesReviewed':['Positive-power transform is invertible exactly while the original unknown stays positive.','Ground-state square completion uses the stated rapid decay and the Gaussian attains equality.','Pinney squared solution stays strictly positive.','The winding root bound uses an enlarged radius, avoiding any boundary-root gap; the argument principle then supplies winding two.','Log-partition Hessian positive definiteness plus an explicit stationary point proves its unique global minimum.','Anisotropic integral is compared above and below by the same power, including logarithmic divergence at the threshold.','Feynman parameter interchange is nonnegative and the displayed inverse-hyperbolic primitive has argument strictly inside its real domain.'],'humanReviewed':False,'filesModifiedOutsideOwnDirectory':False}
(base/'supplemental-peer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'formulaBlockers':0,'report':str(base/'supplemental-peer-audit.json')}))
