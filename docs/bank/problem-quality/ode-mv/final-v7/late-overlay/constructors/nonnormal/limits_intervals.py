"""Outward rational finite-choice inequalities, including positive real powers."""
from fractions import Fraction as Q
from functools import lru_cache
import sympy as s
from series_intervals import enclose as base,loginterval,expq,rounded
from rational_intervals import add,mul,power
@lru_cache(None)
def enclose(v):
 if v==s.EulerGamma:
  n=10000;H=sum((Q(1,k) for k in range(1,n+1)),Q(0));lo,hi=loginterval((Q(n),)*2)
  # Integral comparison bounds the positive tail H_n-ln(n)-gamma by1/n.
  return rounded((H-hi-Q(1,n),H-lo))
 if v.is_Add:
  a=(Q(0),)*2
  for t in v.args:a=rounded(add(a,enclose(t)))
  return a
 if v.is_Mul:
  a=(Q(1),)*2
  for t in v.args:a=rounded(mul(a,enclose(t)))
  return a
 if v.is_Pow:
  a,b=v.args
  if b.is_Integer:return rounded(power(enclose(a),int(b)))
  assert b.is_Rational and a.is_positive is True,'Only positive real rational powers'
  c=Q(int(b.p),int(b.q));lo,hi=mul((c,c),loginterval(enclose(a)));return expq(lo)[0],expq(hi)[1]
 return base(v)
def separate(a,b):
 if isinstance(a,s.Tuple) or isinstance(b,s.Tuple):
  assert isinstance(a,s.Tuple) and isinstance(b,s.Tuple) and len(a)==len(b)
  for x,y in zip(a,b):
   try:return {'component':str(x-y),'enclosure':separate(x,y)}
   except AssertionError:pass
  raise AssertionError('No tuple component separated')
 if a in [s.oo,-s.oo] or b in [s.oo,-s.oo]:
  assert a!=b and (a in [s.oo,-s.oo] or a.is_finite is True) and (b in [s.oo,-s.oo] or b.is_finite is True)
  return {'extendedRealDistinct':True}
 lo,hi=enclose(s.simplify(s.expand_func(a-b)));assert lo>0 or hi<0,('Overlapping exact enclosures',a,b,lo,hi)
 return {'lower':str(lo),'upper':str(hi)}
