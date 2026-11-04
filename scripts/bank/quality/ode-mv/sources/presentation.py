"""Source-bound presentation repairs with explicit mathematical segmentation."""
import re
from common import T
REPLACEMENTS={
 T('For each s in the open unit interval, let G(t,s) be continuous in t, vanish at t=0 and t=1, satisfy '):T('For each ')+r's\in(0,1),'+T(' let ')+r'G(t,s)'+T(' be continuous in ')+r't'+T(', vanish at ')+r't=0,1,'+T(' and satisfy '),
 T('Set s=t, integrate, and use symmetry: the requested squared norm is '):T('Set ')+r's=t'+T(', integrate, and use symmetry: the requested squared norm is '),
 T('Let X(E)>0 be the inverse of the increasing positive branch of V. Energy conservation gives '):T('Let ')+r'X(E)>0'+T(' be the inverse of the increasing positive branch of ')+r'V.'+T(' Energy conservation gives '),
 T('The potential is even, smooth, has V(0)=0, and is strictly increasing for positive x. Every positive energy has a periodic orbit with period '):T('The potential is even and smooth, satisfies ')+r'V(0)=0,'+T(' and is strictly increasing for positive arguments. Every positive energy has a periodic orbit with period '),
 T('Let A(epsilon) be the planar area of '):T('Let ')+r'A(\varepsilon)'+T(' be the planar area of '),
 T('For every nonnegative integer k, let P_k be the monic degree-k solution of the analogous equation. Comparing coefficients gives existence and uniqueness, with '):T('For every nonnegative integer ')+r'k,'+T(' let ')+r'P_k'+T(' be the monic degree-k solution of the analogous equation. Comparing coefficients gives existence and uniqueness, with '),
 T('No root can be repeated: simultaneous zero value and derivative would force the entire differential-equation solution to vanish. Define the inter-degree product over all roots of P_k.'):T('No root can be repeated: simultaneous zero value and derivative would force the entire differential-equation solution to vanish. Define the inter-degree product over all roots of ')+r'P_k.',
 T('For an analytic inverse of the form y=x Phi(y), Lagrange inversion says that the coefficient of x to power k is one over k times the coefficient of u to power k minus one in Phi(u) to power k. Apply it to the displayed inverse relation.'):T('For an analytic inverse satisfying ')+r'y=x\Phi(y),'+T(' Lagrange inversion gives ')+r'[x^k]y(x)=\frac1k[u^{k-1}]\Phi(u)^k.'+T('Apply this identity to the displayed inverse relation.'),
 T('When does y first reach 1/2?'):T('When does ')+r'y'+T(' first reach ')+r'\frac12?',
 T(' grams of salt. Brine of concentration 3/2 g/L enters at 2 L/min; mixture leaves at 2 L/min. Find the current salt-amount derivative in g/min.'):T(' grams of salt. Brine of concentration ')+r'\frac32\,\mathrm{g/L}'+T(' enters at ')+r'2\,\mathrm{L/min}'+T('; mixture leaves at ')+r'2\,\mathrm{L/min}.'+T(' Find the current salt-amount derivative in ')+r'\mathrm{g/min}.',
 T('A real C1 function on [0,T)'):T('A real ')+r'C^1'+T(' function on ')+r'[0,T)',
}
def corrected_math(q):
 q=re.sub(r'(?<![\\A-Za-z])(qquad|quad)\b',lambda m:'\\'+m[1],q)
 q=q.replace(r'^{-- \frac{1}{2}}',r'^{\frac{1}{2}}')
 for a,b in REPLACEMENTS.items():q=q.replace(a,b)
 return q

def factorized_rational_tex(q):
 """Exact compact display for large discriminants; accepts only rational TeX."""
 import sympy as s
 from common import L
 hit=re.fullmatch(r'\\frac\{([0-9]+)\}\{([0-9]+)\}',q)
 value=s.Rational(int(hit[1]),int(hit[2])) if hit else s.Integer(q)
 def part(n):
  factors=s.factorint(int(n));expr=s.Mul(*(s.Pow(p,e,evaluate=False) for p,e in factors.items()),evaluate=False) if factors else s.Integer(1)
  assert s.prod(s.Integer(p)**e for p,e in factors.items())==n
  return s.latex(expr)
 num,den=value.as_numer_denom()
 return part(num) if den==1 else r'\frac{'+part(num)+'}{'+part(den)+'}'
