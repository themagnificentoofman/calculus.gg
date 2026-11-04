"""Small outward-rounded rational enclosures for reviewed finite expression forms.
No floating-point agreement is used as an equality or inequivalence proof.
"""
from fractions import Fraction as F
from functools import lru_cache
from math import factorial,isqrt
import sympy as s
SCALE=10**35

def down(x):x=F(x);return F(x.numerator*SCALE//x.denominator,SCALE)
def up(x):x=F(x);return F(-((-x.numerator*SCALE)//x.denominator),SCALE)
def box(a,b=None):return (down(a),up(a if b is None else b))
def add(a,b):return box(a[0]+b[0],a[1]+b[1])
def mul(a,b):v=[x*y for x in a for y in b];return box(min(v),max(v))
def inv(a):assert a[0]*a[1]>0;return box(1/a[1],1/a[0])
def neg(a):return (-a[1],-a[0])
def powi(a,n):
 if n<0:return inv(powi(a,-n))
 if n==0:return box(1)
 if n%2==0 and a[0]<0<a[1]:return box(0,max(abs(a[0]),abs(a[1]))**n)
 return box(min(a[0]**n,a[1]**n),max(a[0]**n,a[1]**n))
def root_point(v,n):
 assert v>=0
 k=s.integer_nthroot((v.numerator*SCALE**n)//v.denominator,n)[0]
 return F(int(k),SCALE),F(int(k)+1,SCALE)
def powq(a,p):
 p=F(p)
 if p.denominator==1:return powi(a,p.numerator)
 assert a[0]>=0
 lo=root_point(a[0],p.denominator)[0];hi=root_point(a[1],p.denominator)[1]
 return powi((lo,hi),p.numerator)
@lru_cache(None)
def pi_box():
 def atan(x,N=70):
  val=sum((-1)**k*x**(2*k+1)/F(2*k+1) for k in range(N));rem=x**(2*N+1)/F(2*N+1)
  return box(val-rem,val+rem)
 return add(mul(box(16),atan(F(1,5))),mul(box(-4),atan(F(1,239))))
def exp_point(x):
 x=F(x)
 if x<0:return inv(exp_point(-x))
 N=max(90,int(x)+50);term=box(1);total=term
 for k in range(1,N+1):term=mul(term,box(x/k));total=add(total,term)
 nxt=mul(term,box(x/(N+1)));tail=nxt[1]/(1-x/F(N+2))
 return box(total[0],total[1]+tail)
def exp_box(a):return exp_point(a[0])[0],exp_point(a[1])[1]
def log_point(x):
 assert x>0
 y=(x-1)/(x+1)
 if y<0:return neg(log_point(1/x))
 N=500;total=box(0);yp=box(y);yy=box(y*y)
 for k in range(N):total=add(total,mul(yp,box(F(2,2*k+1))));yp=mul(yp,yy)
 tail=2*yp[1]/(F(2*N+1)*(1-y*y));return box(total[0],total[1]+tail)
def log_box(a):assert a[0]>0;return log_point(a[0])[0],log_point(a[1])[1]
def asin_box(a):
 assert 0<=a[0]<=a[1]<1
 N=500;aa=mul(a,a);power=a;coef=F(1);total=box(0)
 for j in range(N):
  total=add(total,mul(power,box(coef/F(2*j+1))));power=mul(power,aa);coef*=F(2*j+1,2*j+2)
 tail=power[1]/(F(2*N+1)*(1-aa[1]));return box(total[0],total[1]+tail)
def elliptic_box(a):
 assert 0<=a[0]<=a[1]<1
 N=500;power=box(1);coef=F(1);total=box(0)
 for j in range(N):
  total=add(total,mul(power,box(coef*coef)));power=mul(power,a);coef*=F(2*j+1,2*j+2)
 total=box(total[0],total[1]+power[1]/(1-a[1]));return mul(mul(box(F(1,2)),pi_box()),total)
def zeta_box(p):
 p=F(p);assert p>1;N=128;total=box(0)
 for k in range(1,N+1):total=add(total,powq(box(k),-p))
 low=mul(powq(box(N+1),1-p),box(1/(p-1)))[0];high=mul(powq(box(N),1-p),box(1/(p-1)))[1]
 return box(total[0]+low,total[1]+high)
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
 if e.func==s.log:return log_box(enclose(e.args[0]))
 if e.func==s.asin:return asin_box(enclose(e.args[0]))
 if e.func==s.elliptic_k:return elliptic_box(enclose(e.args[0]))
 if e.func==s.zeta and e.args[0].is_Rational:return zeta_box(F(int(e.args[0].p),int(e.args[0].q)))
 if e.func==s.gamma:
  v=s.expand_func(e)
  if v!=e:return enclose(v)
 raise ValueError('Unsupported finite expression: '+str(e))
def disjoint(a,b):return a[1]<b[0] or b[1]<a[0]
def dump(a):return [str(q) for q in a]
