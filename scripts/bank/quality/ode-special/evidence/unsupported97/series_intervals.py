"""Independent rational enclosures for the finite series option repair.
Log, exp, cosine and dilogarithm use explicit Taylor tails. Positive real
log-Gamma uses recurrence and the signed first-neglected-term bound in
https://dlmf.nist.gov/5.11.ii (checked2026-11-04), after shifting above32.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import factorial
import sympy as s
from rational_intervals import PI,add,mul,power,reciprocal,sqrt_bounds
SCALE=10**45
def rounded(a):return Q(a[0].numerator*SCALE//a[0].denominator,SCALE),Q(-((-a[1].numerator*SCALE)//a[1].denominator),SCALE)
def exact(v):return Q(int(v.p),int(v.q))
@lru_cache(None)
def logq(q):
 assert q>0
 shift=0
 while q>=2:q/=2;shift+=1
 while q<1:q*=2;shift-=1
 def core(v):
  y=(v-1)/(v+1);total=sum((2*y**(2*j+1)/Q(2*j+1) for j in range(65)),Q(0));tail=2*abs(y)**131/(131*(1-y*y));return total-tail,total+tail
 return rounded(add(core(q),mul((Q(shift),)*2,core(Q(2)))))
def loginterval(a):assert a[0]>0;return rounded((logq(a[0])[0],logq(a[1])[1]))
@lru_cache(None)
def loggamma(q):
 assert q>0
 count=max(0,33-q.numerator//q.denominator);z=q+count
 base=add(mul((z-Q(1,2),)*2,logq(z)),(-z,-z));base=add(base,mul((Q(1,2),)*2,loginterval(rounded(mul((Q(2),)*2,PI)))))
 for k in range(1,9):
  term=exact(s.bernoulli(2*k))/(2*k*(2*k-1)*z**(2*k-1));base=add(base,(term,term))
 tail=exact(s.bernoulli(18))/(18*17*z**17);base=add(base,(min(Q(0),tail),max(Q(0),tail)))
 for j in range(count):base=add(base,mul((Q(-1),)*2,logq(q+j)))
 return rounded(base)
@lru_cache(None)
def expq(q):
 n=0
 while abs(q)>1:q/=2;n+=1
 total=sum((q**j/Q(factorial(j)) for j in range(81)),Q(0));tail=3*abs(q)**81/Q(factorial(81));a=rounded((total-tail,total+tail))
 for _ in range(n):a=rounded(mul(a,a))
 return a
@lru_cache(None)
def enclose(expr):
 expr=s.sympify(expr)
 if expr.is_Rational:return (exact(expr),)*2
 if expr==s.pi:return rounded(PI)
 if expr==s.E:return expq(Q(1))
 if expr.is_Add:
  value=(Q(0),)*2
  for a in expr.args:value=rounded(add(value,enclose(a)))
  return value
 if expr.is_Mul:
  value=(Q(1),)*2
  for a in expr.args:value=rounded(mul(value,enclose(a)))
  return value
 if expr.is_Pow:
  a,b=expr.args
  if b.is_Integer:return rounded(power(enclose(a),int(b)))
  if b==s.Rational(1,2):return rounded(sqrt_bounds(enclose(a)))
  if b==s.Rational(-1,2):return rounded(reciprocal(sqrt_bounds(enclose(a))))
 if expr.func==s.exp:
  a=enclose(expr.args[0]);return expq(a[0])[0],expq(a[1])[1]
 if expr.func==s.cos:
  a=enclose(expr.args[0]);value=(Q(0),)*2
  for j in range(51):value=rounded(add(value,mul((Q((-1)**j,factorial(2*j)),)*2,power(a,2*j))))
  tail=max(abs(a[0]),abs(a[1]))**102/Q(factorial(102));return rounded(add(value,(-tail,tail)))
 if expr.func==s.log:
  a=expr.args[0]
  if a.func==s.gamma and a.args[0].is_Rational:return loggamma(exact(a.args[0]))
  expanded=s.expand_log(expr,force=True)
  if expanded!=expr:return enclose(expanded)
  return loginterval(enclose(a))
 if expr.func==s.polylog:
  degree,z=expr.args;assert degree==2 and z.is_Rational and 0<z<1;z=exact(z);total=sum((z**k/(k*k) for k in range(1,81)),Q(0));return rounded((total,total+z**81/(81*81*(1-z))))
 raise ValueError('Unsupported certified expression '+str(expr))
