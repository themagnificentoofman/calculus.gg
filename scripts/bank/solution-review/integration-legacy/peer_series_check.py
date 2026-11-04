from pathlib import Path
import json,hashlib
import sympy as s
BASE=Path(__file__).parent;src=BASE.parent/'coverage/series_solutions.py';common=BASE.parent/'coverage/common.py'
z=s.symbols('z',real=True);a=s.symbols('a',positive=True);k,m=s.symbols('k m',integer=True,positive=True);F=s.Function('F');v=s.symbols('v');checks=[]
def ck(name,left,right=0):
 diff=s.simplify(s.combsimp(s.expand_func(left-right)));assert diff==0,(name,diff);checks.append({'check':name,'passed':True,'residual':'0'})
c=lambda j:1/(j*j*s.binomial(2*j,j))
ck('General inverse-binomial coefficient recurrence',c(k+1)/c(k),k*k/((2*k+2)*(2*k+1)))
ck('Nonconstant ODE coefficient vanishes from recurrence',4*(2*k+2)*(2*k+1)*c(k+1)-4*k*k*c(k))
ck('Constant ODE coefficient',4*2*c(1),4)
G=2*s.asin(z/2)**2;ck('Arcsine candidate ODE',(4-z*z)*s.diff(G,z,2)-z*s.diff(G,z),4);ck('Arcsine initial value',G.subs(z,0));ck('Arcsine initial derivative',s.diff(G,z).subs(z,0))
for n in range(4,12):ck('Actual principal arcsine branch '+str(n),s.asin(s.sin(s.pi/n)),s.pi/n)
ck('Theta product and inverse-argument derivative',s.diff(a**(-s.Rational(1,2))*F(1/a),a),-F(1/a)/(2*a**s.Rational(3,2))-s.Subs(s.Derivative(F(v),v),v,1/a)/a**s.Rational(5,2))
ck('Theta weighted Gaussian derivative',s.diff(s.exp(-s.pi*a*k*k),a),-s.pi*k*k*s.exp(-s.pi*a*k*k))
ck('Hypergeometric beta normalization for symbolic index and parameter',s.rf(s.Rational(1,2),k)/s.factorial(k+m),s.gamma(k+s.Rational(1,2))*s.gamma(m+s.Rational(1,2))/s.gamma(k+m+1)/(s.sqrt(s.pi)*s.gamma(m+s.Rational(1,2))))
C=lambda t:s.pi*s.pi/6-s.pi*t/2+t*t/4
t=s.symbols('t',real=True);ck('Fourier quadratic zero constant coefficient',s.integrate(C(t),(t,0,2*s.pi)),0)
ck('Fourier fourth-power frequency reduction',(3*C(0)-4*C(2*z)+C(4*z))/8,s.pi*z/4)
ck('Harmonic square integrated kernel',s.diff(s.log(1-z)**2/2,z),-s.log(1-z)/(1-z))
for n in [4,11]:
 H=sum(s.Rational(1,j) for j in range(1,n));H2=sum(s.Rational(1,j*j) for j in range(1,n));tri=sum(s.harmonic(j)/j for j in range(1,n));ck('Finite harmonic shifted triangle '+str(n),tri,(H*H+H2)/2)
report={'scope':'Read-only bounded peer review of all 12 Olympiad series branches plus common.py and immutable first-instance statements. Selected identities checked symbolically; not a rerun of the owning agent full artifact validation.','sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'commonSha256':hashlib.sha256(common.read_bytes()).hexdigest(),'checks':checks,'checkCount':len(checks),'incorrectAnswerOrEssentialAnalyticGapFound':False,'findings':[{'family':'binary-tangent-telescope','finding':'Strict angle bound excludes its own m=4 cotangent endpoint at 1/4; replace strict upper bound by a weak one.','impact':'False wording, no pole or answer error.'},{'family':'hypergeometric-beta','finding':'Gamma function is introduced in solution but not defined by the source statement; add Euler Gamma definition.','impact':'Missing special-function definition.'},{'family':'hypergeometric-beta','finding':'Raw source uses superscript (k), source definition uses an overbar, and solution uses subscript k for the same rising factorial. Explicitly map the conventions or normalize the source display under its content-hash guard.','impact':'Ambiguous notation; no formula change required.'},{'family':'elliptic-central-binomial-square','finding':'State k>=1 for the Wallis recurrence, with k=0 separately defined.','impact':'Optional domain precision.'}],'analyticBridgesReviewed':['Inverse-binomial coefficient ratio gives radius two; the ODE coefficient remains nonzero between zero and every actual argument; principal inverse sine is valid for the stated acute angles.','Theta transformation differentiation is locally uniform on positive parameter compacts, and its denominator is positive by its zero lattice term.','Hypergeometric beta representation has correct normalization and nonnegative coefficients; resulting endpoint exponents are integrable.','Harmonic-over-shift separates the zero shift before reciprocal-square summation; all regrouped terms are nonnegative.','Logarithms of the Euler product are real, absolutely summable and taken at a positive limiting product.','Fourier-fourth-sine evaluates both scaled frequencies within one valid period.','Elliptic expansion uses the parameter convention and a uniform bound below one.','Harmonic-square generating shifts and derivatives are justified by polynomial growth on compact interior subdisks.','Totient regrouping has an exact finite gcd-partition proof and nonnegative Tonelli terms.'],'humanReviewed':False,'otherAgentFilesEdited':False}
(BASE/'advanced-series-peer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'formulaBlockers':0,'report':str(BASE/'advanced-series-peer-audit.json')}))
