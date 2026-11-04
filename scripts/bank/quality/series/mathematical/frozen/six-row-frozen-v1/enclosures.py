"""Outward-rational nonzero certificates, including unsupported generic forms."""
from fractions import Fraction as F
from functools import lru_cache
from math import factorial
import sympy as s
from intervals_base import box,add,mul,neg,powi,powq,inv,pi_box,exp_box,asin_box,elliptic_box,zeta_box,dump
from intervals import log_positive,loggamma_box,cos_box,li2_box

def sin_box(a):
 out=box(0);term=a;N=65;aa=mul(a,a)
 for k in range(N):
  out=add(out,term);term=neg(mul(term,mul(aa,box(F(1,(2*k+2)*(2*k+3))))))
 rem=max(abs(a[0]),abs(a[1]))**(2*N+1)/factorial(2*N+1)
 return box(out[0]-rem,out[1]+rem)
def atan_box(a):
 # Monotonicity plus a pointwise alternating series after reciprocal/half-angle reduction.
 def point(x):
  x=F(x)
  if x<0:return neg(point(-x))
  if x>1:return add(mul(box(F(1,2)),pi_box()),neg(point(1/x)))
  if x>F(1,2):
   z=mul(box(x),inv(add(box(1),powq(box(1+x*x),F(1,2)))))
   return mul(box(2),atan_box(z))
  N=100;t=sum((-1)**k*x**(2*k+1)/F(2*k+1)for k in range(N));rem=x**(2*N+1)/F(2*N+1);return box(t-rem,t+rem)
 return point(a[0])[0],point(a[1])[1]
@lru_cache(None)
def enclose(e):
 e=s.sympify(e)
 if e.is_Rational:return box(F(int(e.p),int(e.q)))
 if e==s.pi:return pi_box()
 if e==s.E:return exp_box(box(1))
 if e.is_Add:
  v=box(0)
  for a in e.args:v=add(v,enclose(a))
  return v
 if e.is_Mul:
  v=box(1)
  for a in e.args:v=mul(v,enclose(a))
  return v
 if e.is_Pow and e.exp.is_Rational:return powq(enclose(e.base),F(int(e.exp.p),int(e.exp.q)))
 if e.func==s.exp:return exp_box(enclose(e.args[0]))
 if e.func==s.log:
  a=enclose(e.args[0]);assert a[0]>0;return log_positive(a[0])[0],log_positive(a[1])[1]
 if e.func in [s.sin,s.cos,s.tan,s.cot]:
  a=enclose(e.args[0]);sn=sin_box(a);cs=cos_box(a)
  return sn if e.func==s.sin else cs if e.func==s.cos else mul(sn,inv(cs))if e.func==s.tan else mul(cs,inv(sn))
 if e.func in [s.sinh,s.cosh,s.tanh,s.coth]:
  a=enclose(e.args[0]);pos=exp_box(a);minus=exp_box(neg(a));sn=mul(box(F(1,2)),add(pos,neg(minus)));cs=mul(box(F(1,2)),add(pos,minus))
  return sn if e.func==s.sinh else cs if e.func==s.cosh else mul(sn,inv(cs))if e.func==s.tanh else mul(cs,inv(sn))
 if e.func==s.asin:return asin_box(enclose(e.args[0]))
 if e.func==s.atan:return atan_box(enclose(e.args[0]))
 if e.func==s.elliptic_k:return elliptic_box(enclose(e.args[0]))
 if e.func==s.polylog and e.args[0]==2:return li2_box(enclose(e.args[1]))
 if e.func==s.zeta:
  q=e.args[0];assert q.is_Rational;return zeta_box(F(int(q.p),int(q.q)))
 if e.func==s.gamma:
  q=e.args[0];v=s.expand_func(e)
  if v!=e:return enclose(v)
  assert q.is_Rational and not(q.is_integer and q<=0)
  scale=s.Integer(1)
  while q<=0:scale/=q;q+=1
  return mul(enclose(scale),exp_box(loggamma_box(F(int(q.p),int(q.q)))))
 raise ValueError('No rational enclosure for '+str(e))
