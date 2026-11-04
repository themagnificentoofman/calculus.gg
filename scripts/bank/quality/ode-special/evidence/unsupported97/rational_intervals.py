"""Exact rational enclosures for finite algebraic/pi editorial certificates.

No floating point or author expressions are used. Unsupported expressions fail
closed. Machin's identity and alternating-series remainders enclose pi; integer
square roots enclose radicals. This is a small checker, not a proof assistant.
"""
from fractions import Fraction as Q
from functools import lru_cache
from math import isqrt
import sympy as s

def add(a,b):return (a[0]+b[0],a[1]+b[1])
def mul(a,b):
 values=[x*y for x in a for y in b];return min(values),max(values)
def reciprocal(a):
 assert a[0]*a[1]>0,'Interval crosses zero'
 return 1/a[1],1/a[0]
def power(a,n):
 if n<0:return power(reciprocal(a),-n)
 result=(Q(1),Q(1))
 for _ in range(n):result=mul(result,a)
 return result
def atan_reciprocal(n,terms=48):
 total=sum((Q((-1)**k,(2*k+1)*n**(2*k+1)) for k in range(terms)),Q(0))
 next_term=Q((-1)**terms,(2*terms+1)*n**(2*terms+1))
 return min(total,total+next_term),max(total,total+next_term)
PI=add(mul((Q(16),Q(16)),atan_reciprocal(5)),mul((Q(-4),Q(-4)),atan_reciprocal(239)))
def sqrt_bounds(a):
 assert a[0]>=0
 scale=10**45
 def lower(v):return Q(isqrt(v.numerator*scale*scale//v.denominator),scale)
 lo,hi=lower(a[0]),lower(a[1])+Q(1,scale)
 assert lo*lo<=a[0] and hi*hi>=a[1]
 return lo,hi
@lru_cache(None)
def enclose(expr):
 expr=s.sympify(expr)
 if expr.is_Rational:return (Q(int(expr.p),int(expr.q)),)*2
 if expr==s.pi:return PI
 if expr.is_Add:
  result=(Q(0),Q(0))
  for term in expr.args:result=add(result,enclose(term))
  return result
 if expr.is_Mul:
  result=(Q(1),Q(1))
  for term in expr.args:result=mul(result,enclose(term))
  return result
 if expr.is_Pow:
  base,exponent=expr.args
  if exponent.is_Integer:return power(enclose(base),int(exponent))
  if exponent==s.Rational(1,2):return sqrt_bounds(enclose(base))
 raise ValueError('Unsupported exact interval expression: '+str(expr))
def certificate(expr):
 lo,hi=enclose(s.simplify(expr))
 return {'lower':str(lo),'upper':str(hi),'sign':'positive' if lo>0 else 'negative' if hi<0 else 'zero' if lo==hi==0 else 'unresolved'}
