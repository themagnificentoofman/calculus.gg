"""Symbolic proofs of three original nonlinear/parameter-dependent IVP families."""
import sympy as s
from families import x,a,b,c

def formula(name):
    if name=='hidden-riccati':
        p=a*x+b/x;v=p+c/(1-c*(x-1));point=1+1/(2*c)
        rhs=lambda z:z*z-2*p*z+p*p+s.diff(p,x)
        assert s.factor(s.diff(v,x)-rhs(v))==0
        assert s.simplify(v.subs(x,1)-(a+b+c))==0
        u=s.Function('u')(x)
        equation=s.Eq(s.diff(u,x),rhs(u))
        constraints=[s.Eq(u.subs(x,1),a+b+c)]
        domain=r'0<x<1+\frac{1}{'+s.latex(c)+'}'
        steps=[r'\textnormal{Set }z=u-('+s.latex(p)+r').\quad z\prime=z^2,\quad z(1)='+s.latex(c),r'z=\frac{'+s.latex(c)+r'}{1-'+s.latex(c)+r'(x-1)}']
    elif name=='clairaut-envelope':
        v=2*s.sqrt(a*(x+c))-b*x;point=a-c;d=s.diff(v,x)
        assert s.simplify(v-(x*d+a/(d+b)+c*(d+b)))==0
        assert s.simplify(d+b-s.sqrt(a)/s.sqrt(x+c))==0
        assert s.simplify(s.diff(v,x,2)+s.sqrt(a)/(2*(x+c)**s.Rational(3,2)))==0
        u=s.Function('u')(x);du=s.diff(u,x)
        equation=s.Eq(u,x*du+a/(du+b)+c*(du+b))
        constraints=r'\textnormal{Non-affine singular branch with }u\prime+'+s.latex(b)+'>0'
        domain='x> -'+s.latex(c)
        steps=[r'\textnormal{Differentiate and exclude the affine branches: }u^{\prime\prime}\left(x+'+s.latex(c)+r'-\frac{'+s.latex(a)+r'}{(u\prime+'+s.latex(b)+r')^2}\right)=0',r'u(x)='+s.latex(v)]
    else:
        v=x**a*(c+s.log(x)**(b+2)/((b+1)*(b+2)));point=s.Integer(2)
        operator=lambda z:x*x*s.diff(z,x,2)+(1-2*a)*x*s.diff(z,x)+a*a*z
        forcing=x**a*s.log(x)**b
        assert s.simplify(s.expand(operator(v)-forcing))==0
        assert s.simplify(v.subs(x,1)-c)==0
        # Substitute each permitted integer exponent before the initial point;
        # generic log-power substitution produces a spurious 0/0 in SymPy.
        assert all(s.simplify(s.diff(v,x).subs(b,power).subs(x,1)-a*c)==0 for power in range(1,17))
        u=s.Function('u')(x);equation=s.Eq(operator(u),forcing)
        constraints=[s.Eq(u.subs(x,1),c),s.Eq(s.diff(u,x).subs(x,1),a*c)];domain='x>0'
        steps=[r'\textnormal{Set }t=\log x,\quad u=x^{'+s.latex(a)+r'}v(t).\quad v^{\prime\prime}=t^{'+s.latex(b)+'}',r'v(t)='+s.latex(c)+r'+\frac{t^{'+s.latex(b+2)+r'}}{('+s.latex(b+1)+')('+s.latex(b+2)+')}']
    return v,point,equation,constraints,domain,steps

CACHE={}
def prepare(name):
    if name not in CACHE:CACHE[name]=formula(name)
    return CACHE[name]

def build(name,params):
    v,point,equation,constraints,domain,steps=prepare(name)
    mapping={a:params['a'],b:params['b'],c:params['c']}
    # Render from the symbolic expressions, with replacement only for the
    # explicitly delimited coefficient symbols in authored explanatory TeX.
    def replace(text):
        import re
        return re.sub(r'(?<![A-Za-z\\])([abc])(?![A-Za-z])',lambda m:str(params[m[1]]),text)
    answer=s.simplify(v.subs(x,point).subs(mapping))
    rendered_constraints=r',\quad '.join(s.latex(e.subs(mapping)) for e in constraints) if isinstance(constraints,list) else replace(constraints)
    statement=r'\textnormal{Find }u('+s.latex(point.subs(mapping))+r')\textnormal{ for }'+s.latex(equation.subs(mapping))+r',\quad '+rendered_constraints+r',\quad '+replace(domain)
    return {'expression':s.srepr(equation.subs(mapping))+';'+rendered_constraints+';'+replace(domain)+';'+s.srepr(point.subs(mapping)),
        'statement':statement,'answer':answer,'steps':[replace(step) for step in steps]+[r'u('+s.latex(point.subs(mapping))+')='+s.latex(answer)],
        'assumptions':['Real branch on the stated domain.','Riccati/linear IVPs use uniqueness on the displayed interval; Clairaut explicitly selects the non-affine positive-derivative branch.']}
