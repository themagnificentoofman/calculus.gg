"""Original advanced families, with exact identities and independent finite algebra.
No external problem statements are copied. Difficulty refers to discovering the
identity without being given the substitution/theorem in the statement.
"""
from math import factorial,comb
from fractions import Fraction

def add_olympiad(add,integral,derivative,limit,series,ode,multi,x,y,n,s):
    R=s.Rational; pi=s.pi
    # Every verifier here checks an exact identity; no numerical evidence is used.
    def attach(fn):
        # add() appends the definition; return access via function globals.
        from families import FAMILIES
        FAMILIES[-1].update(fn)
    kernels=[];expected=[]
    for aa,bb,cc in [(2,3,2),(3,4,3),(4,3,4)]:
        kernels.append(x**(aa-1)/(1+x)**(aa+bb)*(-s.log(x/(1+x)))**cc)
        expected.append(s.factorial(cc)*sum((-1)**k*s.binomial(bb-1,k)/R((aa+k)**(cc+1)) for k in range(bb)))
    integral('transformed-beta-log','olympiad',kernels,expected,hi=s.oo,tags=['parameter-differentiation','improper-integral','substitution'])
    u=s.symbols('u',positive=True)
    def transformed(k):
        transformed=s.simplify(k.subs(x,u/(1-u))/(1-u)**2)
        return s.integrate(s.expand(transformed),(u,0,1))
    attach({'verify':transformed,'assumptions':['Positive integer beta exponents guarantee both transformed endpoint integrals converge.']})
    kernels=[];expected=[]
    for aa,bb,cc in [(2,2,1),(3,2,2),(2,3,3)]:
        f=x**aa*(1+x)**bb;fr=(1-x)**aa*(2-x)**bb
        kernels.append((x*(1-x))**cc*f/(f+fr));expected.append(R(factorial(cc)**2,2*factorial(2*cc+1)))
    integral('concealed-reflection','olympiad',kernels,expected,tags=['symmetry','beta-integral'])
    attach({'verify':lambda k:s.integrate(s.cancel(k+k.subs(x,1-x)),(x,0,1))/2,'assumptions':['Each denominator is a sum of nonnegative factors, never simultaneously zero on [0,1].']})
    kernels=[];expected=[]
    for aa,bb,cc in [(1,2,2),(2,3,3),(3,4,4)]:
        kernels.append(x**(aa-1)*(1-x**bb)**cc/(-s.log(x)))
        expected.append(-sum((-1)**k*s.binomial(cc,k)*s.log(aa+bb*k) for k in range(cc+1)))
    integral('frullani-cancellation','olympiad',kernels,expected,tags=['frullani','improper-integral','cancellation'])
    def frullani(k):
        numerator=s.Poly(s.cancel(k*(-s.log(x))),x)
        terms=numerator.terms();assert sum(v for (_,),v in terms)==0
        assert min(power[0] for power,_ in terms)>=0
        # Pair each term with x^0. Frullani on [0,1] is proved by
        # integrating t^(p-1) over p between 1 and exponent+1 (Fubini).
        return -sum(coef*s.log(power[0]+1) for power,coef in terms)
    attach({'verify':frullani,'assumptions':['The numerator vanishes at 1; grouped Frullani differences converge at both endpoints.']})
    kernels=[s.exp(m*x)*(s.exp(x)-1)**4/x**4 for m in (1,2,3)]
    expected=[R(factorial(6),factorial(10))*sum((-1)**(4-k)*comb(4,k)*(m+k)**10 for k in range(5)) for m in (1,2,3)]
    derivative('removable-exponential-derivative','olympiad',kernels,expected,point=0,order=6,tags=['finite-differences','analytic-extension'])
    attach({'verify':lambda k:s.series(k,x,0,7).removeO().expand().coeff(x,6)*factorial(6),'promptAssumptions':'Use the analytic extension at x = 0.'})
    functions=[s.Function('u_'+str(i))(x) for i in range(1,4)];pairs=[(2,2),(3,2),(2,3)]
    def inverse_coefficient(p,q):
        v=s.Integer(0)
        for _ in range(6):v=s.series(x*(1+v)**p/(1-v)**q,x,0,7).removeO().expand()
        return v.coeff(x,6)*factorial(6)
    expected=[factorial(5)*sum(comb(6*p,j)*comb(6*q+4-j,5-j) for j in range(6)) for p,q in pairs]
    derivative('implicit-inverse-series','olympiad',functions,expected,point=0,order=6,tags=['lagrange-inversion','implicit-differentiation'])
    definitions=r'\quad '+r',\quad '.join(s.latex(s.Eq(v,x*(1+v)**p/(1-v)**q)) for v,(p,q) in zip(functions,pairs))+r',\quad u_1(0)=u_2(0)=u_3(0)=0'
    attach({'verify':lambda k,ps=pairs,fs=functions:inverse_coefficient(*ps[fs.index(k)]),'promptMath':definitions,'promptAssumptions':'Use the unique analytic branches near zero.','assumptions':['The implicit-function derivative with respect to u equals one at (0,0); |u_i|<1 locally.']})
    kernels=[];expected=[]
    for bb,cc in [(4,1),(5,2),(6,3)]:
        kernels.append(s.exp(cc*x)*s.prod(1-2*x*s.cos(2*pi*k/bb)+x*x for k in range(1,bb)))
        expected.append(factorial(6)*sum(R(min(j+1,bb,2*bb-1-j)*cc**(6-j),factorial(6-j)) for j in range(7)))
    derivative('roots-of-unity-product','olympiad',kernels,expected,point=0,order=6,tags=['roots-of-unity','coefficient-extraction'])
    attach({'verify':lambda k:s.series(s.expand(k),x,0,7).removeO().expand().coeff(x,6)*factorial(6)})
    z=s.symbols('z');kernels=[];expected=[]
    for bb,cc in [(6,2),(7,3),(8,4)]:
        kernels.append(sum((-1)**(5-k)*comb(5,k)*(1+k*x)**bb*s.log(1+k*x)**cc for k in range(6))/x**5)
        expected.append(s.diff(s.prod(z-j for j in range(5)),z,cc).subs(z,bb))
    limit('finite-difference-log-limit','olympiad',kernels,expected,tags=['finite-differences','parameter-differentiation'])
    attach({'verify':lambda k:s.series(k*x**5,x,0,6).removeO().expand().coeff(x,5),'promptAssumptions':'Take the real branch near zero.'})
    # Explicit product-limit theorem, with an exact uniform remainder bound:
    # 0<=f(t)<=1/c on [0,1], u=f(k/n)/n^2, sum u^2<=1/(c^2 n^3).
    j=s.symbols('j',integer=True,positive=True);N=s.symbols('N',integer=True,positive=True)
    kernels=[];expected=[];weights=[]
    for aa,bb,cc in [(2,2,1),(3,2,2),(2,3,3)]:
        f=x**aa*(1-x)**bb/(cc+x);weights.append(f)
        kernels.append(N*(s.Product(1+f.subs(x,j/N)/N**2,(j,1,N))-1))
        J=s.log(R(cc+1,cc));js=[J]
        for m in range(1,aa+bb+1):js.append(R(1,m)-cc*js[-1])
        expected.append(sum((-1)**k*comb(bb,k)*js[aa+k] for k in range(bb+1)))
    limit('riemann-product-limit','olympiad',kernels,expected,point=s.oo,tags=['uniform-asymptotics','riemann-sums','partial-fractions'])
    attach({'variable':N,'verify':lambda k:s.integrate(weights[kernels.index(k)],(x,0,1)),'assumptions':['For the defined product, u=f(j/N)/N^2 is nonnegative and at most 1/N^2; sum(u^2)<=1/N^3. The logarithm remainder and exponential remainder vanish after multiplication by N.']})
    # Capture each list by default arguments: later family definitions must not
    # change the checker's source kernels or expected integral.
    from families import FAMILIES
    FAMILIES[-1]['verify']=lambda k,ks=kernels,ws=weights:s.integrate(ws[ks.index(k)],(x,0,1))
    kernels=[];expected=[]
    for aa,bb,cc in [(2,2,1),(3,2,2),(2,3,3)]:
        f=x**aa*(x+cc)**bb;area=s.integrate(f,(x,0,1))
        kernels.append(N**2*(s.Sum(f.subs(x,j/N),(j,1,N))/N-area-f.subs(x,1)/(2*N)))
        expected.append(s.diff(f,x).subs(x,1)/12)
    limit('second-order-riemann-limit','olympiad',kernels,expected,point=s.oo,tags=['euler-maclaurin','faulhaber'])
    attach({'variable':N,'verify':lambda k:s.limit(k.doit().expand(),N,s.oo)})
    kernels=[];expected=[]
    from sympy.functions.combinatorial.numbers import stirling
    for aa,bb,cc in [(1,5,2),(2,6,3),(3,7,4)]:
        kernels.append(n**cc/s.prod(n+aa+j for j in range(bb+1)))
        expected.append(sum(stirling(cc,j,kind=2)*factorial(j)*factorial(aa+j-1)*factorial(bb-j-1) for j in range(cc+1))/s.Integer(factorial(bb)*factorial(aa+bb-1)))
    series('stirling-beta-series','olympiad',kernels,expected,tags=['generating-functions','beta-integral'])
    def rational_series(k):
        numerator,denominator=s.fraction(k)
        poles=s.solve(denominator,n)
        residues=[(int(-p),s.cancel(k*(n-p)).subs(n,p)) for p in poles]
        assert all(m>0 for m,_ in residues) and sum(co for _,co in residues)==0
        assert s.cancel(k-sum(co/(n+m) for m,co in residues))==0
        return -sum(co*s.harmonic(m-1) for m,co in residues)
    attach({'verify':rational_series,'convergenceProof':'Degree of the denominator exceeds numerator degree by at least two. Partial fractions have zero total residue; exact harmonic tails cancel.'})
    kernels=[];expected=[];weights=[]
    for aa,bb,cc in [(1,2,2),(2,3,3),(3,4,4)]:
        r=R(aa,aa+bb);weights.append(x**(cc-1)/(1-r+r*x))
        kernels.append(r**n*s.Sum((-1)**j*s.binomial(n,j)/(j+cc),(j,0,n)))
        J=s.log(1+R(aa,bb))
        for m in range(1,cc):J=R(1,m)-R(bb,aa)*J
        expected.append(R(aa+bb,aa)*J)
    series('binomial-beta-series','olympiad',kernels,expected,tags=['binomial-transform','tonelli','geometric-series'])
    attach({'verify':lambda k,ks=kernels,ws=weights:s.integrate(ws[ks.index(k)],(x,0,1)),'convergenceProof':'The inner binomial sum is the nonnegative beta integral. Tonelli sums it to t^(c-1)/(1-r+rt); 0<r<1 gives an integrable bound.'})
    kernels=[];expected=[]
    def B(t):t=s.frac(t);return t*t-t+R(1,6)
    for aa,bb,cc in [(1,6,2),(1,8,3),(2,10,3)]:
        kernels.append((s.cos(2*pi*aa*n/bb)-s.cos(2*pi*cc*n/bb))**2/n**2)
        expected.append(pi*pi*(R(1,6)+(B(R(2*aa,bb))+B(R(2*cc,bb)))/2-B(R(aa-cc,bb))-B(R(aa+cc,bb))))
    series('fourier-cosine-square','olympiad',kernels,expected,start=1,tags=['fourier-series','trigonometric-identities'])
    # Independent residue-class summation via the trigamma reflection formula.
    pairs=[(1,6,2),(1,8,3),(2,10,3)]
    def fourier(k,ks=kernels,ps=pairs):
        aa,bb,cc=ps[ks.index(k)]
        result=0
        for residue in range(1,bb):
            weight=(s.cos(2*pi*aa*residue/bb)-s.cos(2*pi*cc*residue/bb))**2
            result+=weight*pi*pi/(2*bb*bb*s.sin(pi*residue/bb)**2)
        return s.trigsimp(s.expand_trig(result))
    attach({'verify':fourier,'convergenceProof':'Squared cosine differences are at most 4; comparison with sum 4/n^2 proves absolute convergence.'})
    # Nonlinear and parameter-dependent ODEs have their own symbolic residual
    # checks and do not use the linear-superposition certificate.
    for name in ['hidden-riccati','clairaut-envelope','euler-double-resonance']:
        add(name,'differential equations','olympiad','special-ode',[x,x*x,x**3],None,tags={'hidden-riccati':['riccati','nonlinear-substitution'],'clairaut-envelope':['singular-solutions','envelopes'],'euler-double-resonance':['euler-cauchy','resonance']}[name])
    kernels=[];expected=[]
    for aa,bb,cc in [(2,3,2),(2,4,3),(3,4,2)]:
        kernels.append(x**(aa-1)*y**(bb-1)/(1+x+y)**(aa+bb+cc));expected.append(R(factorial(aa-1)*factorial(bb-1)*factorial(cc-1),factorial(aa+bb+cc-1)))
    multi('unbounded-dirichlet-integral','olympiad','double',kernels,expected,yhi=s.oo,xhi=s.oo,tags=['jacobian','dirichlet-integral','improper-integral'])
    kernels=[];expected=[]
    for aa,bb,cc in [(1,2,1),(1,3,2),(2,3,1)]:
        kernels.append((x+y)**(2*aa)*(x-y)**(2*bb)*(x*x+y*y)**cc)
        expected.append(pi*R(factorial(2*aa)*factorial(2*bb),2**(aa+bb)*factorial(aa)*factorial(bb)*factorial(aa+bb)*(aa+bb+cc+1)))
    multi('rotated-disk-moment','olympiad','disk',kernels,expected,tags=['rotation','polar-coordinates','symmetry'])
    def disk(k):
        result=0
        for (i,j),coef in s.Poly(s.expand(k),x,y).terms():
            if i%2 or j%2:continue
            result+=coef*s.gamma(R(i+1,2))*s.gamma(R(j+1,2))/s.gamma(R(i+j+4,2))
        return s.simplify(result)
    attach({'verify':disk,'assumptions':['Integrate over the closed unit disk x^2+y^2 <= 1.']})
    kernels=[s.log(1+x*x+y*y)**cc for cc in (2,3,4)]
    expected=[R(factorial(4)*factorial(6)*factorial(cc)*stirling(5,cc,kind=1,signed=True),factorial(2)*factorial(3)) for cc in (2,3,4)]
    multi('radial-log-mixed-derivative','olympiad','partial',kernels,expected,dx=4,dy=6,px=0,py=0,tags=['coefficient-extraction','stirling-numbers'])
    def radial(k,ks=kernels):
        cc=ks.index(k)+2;logpoly=sum((-1)**(j+1)*x**j/R(j) for j in range(1,6))
        coefficient=s.expand(logpoly**cc).coeff(x,5)
        return coefficient*comb(5,2)*factorial(4)*factorial(6)
    attach({'verify':radial})
