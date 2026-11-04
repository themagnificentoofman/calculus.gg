"""Outward rational certificates for real principal functions in this finite scope."""
from fractions import Fraction as Q
from functools import lru_cache
from math import factorial
import sympy as s
from rational_intervals import add,mul,power,reciprocal,sqrt_bounds,PI
from series_intervals import rounded,loginterval,expq,enclose as base
@lru_cache(None)
def atanq(q):
 if q<0:
  a=atanq(-q);return -a[1],-a[0]
 if q>1:
  a=atanq(1/q);return rounded(add(mul((Q(1,2),)*2,PI),(-a[1],-a[0])))
 if q>Q(1,2):return rounded(add(atanq(Q(1,2)),atanq((q-Q(1,2))/(1+q/2))))
 total=sum(((-1)**k*q**(2*k+1)/Q(2*k+1) for k in range(100)),Q(0));term=q**201/Q(201)
 return rounded((total,total+term))
def ataninterval(v):return atanq(v[0])[0],atanq(v[1])[1]
def sincos(v,cosine=False):
 total=(Q(0),Q(0))
 for k in range(81):
  n=2*k+(0 if cosine else 1);total=rounded(add(total,mul((Q((-1)**k,factorial(n)),)*2,power(v,n))))
 order=162 if cosine else 163;tail=max(abs(v[0]),abs(v[1]))**order/Q(factorial(order));return rounded(add(total,(-tail,tail)))
@lru_cache(None)
def enclose(v):
 v=s.sympify(v)
 if v.is_Add:
  a=(Q(0),)*2
  for t in v.args:a=rounded(add(a,enclose(t)))
  return a
 if v.is_Mul:
  a=(Q(1),)*2
  for t in v.args:a=rounded(mul(a,enclose(t)))
  return a
 if v.is_Pow:
  a,n=v.args
  if n.is_Integer:return rounded(power(enclose(a),int(n)))
  if n==s.Rational(1,2):return rounded(sqrt_bounds(enclose(a)))
  if n==s.Rational(-1,2):return rounded(reciprocal(sqrt_bounds(enclose(a))))
 if v.func==s.exp:
  a=enclose(v.args[0]);return expq(a[0])[0],expq(a[1])[1]
 if v.func==s.log:return loginterval(enclose(v.args[0]))
 if v.func==s.atan:return ataninterval(enclose(v.args[0]))
 if v.func==s.acos:
  a=enclose(v.args[0]);assert -1<a[0]<=a[1]<1
  z=mul((1-a[1],1-a[0]),reciprocal((1+a[0],1+a[1])));return rounded(mul((Q(2),)*2,ataninterval(sqrt_bounds(z))))
 if v.func in [s.asinh,s.acosh]:
  x=v.args[0]
  if v.func==s.acosh:assert enclose(x)[0]>1;return enclose(s.log(x+s.sqrt(x*x-1)))
  return enclose(s.log(x+s.sqrt(x*x+1)))
 if v.func in [s.sinh,s.cosh,s.tanh,s.coth]:
  x=v.args[0];plus=s.exp(x);minus=s.exp(-x)
  form={s.sinh:(plus-minus)/2,s.cosh:(plus+minus)/2,s.tanh:(plus-minus)/(plus+minus),s.coth:(plus+minus)/(plus-minus)}[v.func]
  return enclose(form)
 if v.func in [s.sin,s.cos]:return sincos(enclose(v.args[0]),v.func==s.cos)
 if v.func==s.tan:
  a=enclose(v.args[0]);return rounded(mul(sincos(a),reciprocal(sincos(a,True))))
 return base(v)
def certificate(v):
 lo,hi=enclose(v);return {'lower':str(lo),'upper':str(hi),'sign':'positive' if lo>0 else 'negative' if hi<0 else 'zero' if lo==hi==0 else 'unresolved'}
