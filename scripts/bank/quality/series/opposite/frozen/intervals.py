"""Explicit outward-rational certificates for the five finite option families."""
from fractions import Fraction as F
from functools import lru_cache
from math import factorial
import sympy as s
from intervals_base import box,add,mul,inv,neg,powi,powq,pi_box,exp_box,log_box,zeta_box,disjoint,dump
@lru_cache(None)
def log_positive(q):
 q=F(q);k=0
 while q>=2:q/=2;k+=1
 while q<1:q*=2;k-=1
 return add(log_box(box(q)),mul(box(k),log_box(box(2))))
@lru_cache(None)
def euler_box():
 N=4096;h=box(0)
 for k in range(1,N+1):h=add(h,box(F(1,k)))
 # Integral comparison for decreasing 1/x gives these strict Euler-constant bounds.
 return box(h[0]-log_positive(N+1)[1],h[1]-log_positive(N)[0])
@lru_cache(None)
def loggamma_box(q):
 q=F(q);correction=box(0)
 while q<1:correction=add(correction,neg(log_positive(q)));q+=1
 while q>=2:q-=1;correction=add(correction,log_positive(q))
 z=q-1;out=mul(box(-z),euler_box());N=110
 for k in range(2,N+1):out=add(out,mul(box((-1)**k*z**k/F(k)),zeta_box(k)))
 tail=2*abs(z)**(N+1)/(F(N+1)*(1-abs(z))) if z else F(0)
 return add(correction,box(out[0]-tail,out[1]+tail))
def cos_box(a):
 out=box(1);term=box(1);N=60;aa=mul(a,a)
 for k in range(1,N):term=neg(mul(term,mul(aa,box(F(1,(2*k-1)*(2*k))))));out=add(out,term)
 rem=max(abs(a[0]),abs(a[1]))**(2*N)/factorial(2*N)
 return box(out[0]-rem,out[1]+rem)
def li2_box(a):
 assert 0<a[0]<=a[1]<1
 out=box(0);N=100
 for k in range(1,N+1):out=add(out,mul(powi(a,k),box(F(1,k*k))))
 return box(out[0],out[1]+a[1]**(N+1)/(F((N+1)**2)*(1-a[1])))
@lru_cache(None)
def enclose(e):
 e=s.sympify(e)
 if e.is_Rational:return box(F(int(e.p),int(e.q)))
 if e==s.pi:return pi_box()
 if e==s.E:return exp_box(box(1))
 if e.is_Add:
  out=box(0)
  for a in e.args:out=add(out,enclose(a))
  return out
 if e.is_Mul:
  out=box(1)
  for a in e.args:out=mul(out,enclose(a))
  return out
 if e.is_Pow and e.exp.is_Rational:return powq(enclose(e.base),F(int(e.exp.p),int(e.exp.q)))
 if e.func==s.exp:return exp_box(enclose(e.args[0]))
 if e.func==s.log:
  a=e.args[0]
  if a.is_Rational:return log_positive(F(int(a.p),int(a.q)))
  return log_box(enclose(a))
 if e.func==s.cos:return cos_box(enclose(e.args[0]))
 if e.func==s.polylog and e.args[0]==2:return li2_box(enclose(e.args[1]))
 if e.func==s.gamma:
  q=e.args[0];v=s.expand_func(e)
  if v!=e:return enclose(v)
  assert q.is_Rational
  return exp_box(loggamma_box(F(int(q.p),int(q.q))))
 raise ValueError('Unsupported expression '+str(e))
