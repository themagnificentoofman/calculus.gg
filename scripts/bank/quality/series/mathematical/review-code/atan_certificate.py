"""Exact rational tangent normalization with explicit principal-branch bounds."""
import sympy as s
from literal_math import parse
from enclosures import enclose,pi_box,dump

def normalized_tangent(expression):
 e=s.expand(expression);p=e.coeff(s.pi);assert (2*p).is_Integer
 z=s.I**int(2*p);rest=e-p*s.pi
 for angle in e.atoms(s.atan):
  q=angle.args[0];c=e.coeff(angle);assert q.is_Rational and c.is_Integer
  z*= (1+s.I*q)**int(c);rest-=c*angle
 assert s.expand(rest)==0
 z=s.simplify(s.expand_complex(z));re,im=z.as_real_imag();assert re.is_Rational and im.is_Rational
 iv=enclose(e);assert iv[0]>0 and iv[1]<pi_box()[0]/2
 assert re>0 and im>0
 t=s.cancel(im/re)
 return t,{'method':'exact tangent addition through rational complex products plus principal-branch interval','rationalTangent':str(t),'angleEnclosure':dump(iv),'branch':'The complete angle lies strictly between0 and pi/2, where tangent is one-to-one and increasing.','identity':'exp(i atan(q)) has the direction of1+iq; multiplying these directions gives the exact tangent of the sum. The branch interval removes periodic ambiguity.'}
