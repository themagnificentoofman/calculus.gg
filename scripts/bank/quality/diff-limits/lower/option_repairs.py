"""Authored same-sign error pools for reproducible sign-pair leaks."""
import sympy as s
R=s.Rational
SLUGS={'radical-rationalization','complex-exponential-derivative','inverse-slope','implicit-circle','matching-piecewise-slopes','tangent-intercept','quotient-log','inverse-tangent-composition','implicit-product','normal-line','trigonometric-power-coefficient','removable-power','one-sided-absolute','rational-infinity','exponential-standard','logarithm-standard','trigonometric-ratio','piecewise-continuity','infinity-root-difference','second-order-trig','exponential-cancellation','nested-log-ratio','log-exponential-second-scale','Gamma-finite-shift-correction','iterated-Mobius','Gaussian-moment-derivative','root-of-unity-filter','interpolation-derivative','sharp-endpoint-derivative','product-Euler-correction'}
def pool(fid,m,A):
 q=fid.split('-',3)[3];m=s.Integer(m)
 if q not in SLUGS:return None
 if q=='radical-rationalization':
  return [(1/m,'Omit one of the two equal conjugate endpoint terms'),(1/(4*m),'Apply the conjugate factor two twice'),(1/(2*m*m),'Use the radicand base instead of its square root'),(1/(m*m),'Omit one conjugate term and use the radicand base'),(2/m,'Count the rationalized numerator twice while omitting one conjugate term'),(1/(2*(m+1)),'Evaluate the conjugate root at the next integer instead of the displayed root')]
 if q=='complex-exponential-derivative':
  real=lambda value:s.simplify(s.expand_complex(value).as_real_imag()[0])
  return [(real((1+s.I)**(m-1)),'Differentiate one fewer time'),(real((1+s.I)**(m+1)),'Differentiate one additional time'),(s.simplify(s.im(s.expand_complex((1+s.I)**m))),'Keep the imaginary instead of the real projection'),(real((1+2*s.I)**m),'Double the cosine frequency in every derivative'),(real((2+s.I)**m),'Double the exponential growth rate in every derivative'),(2*A,'Add both conjugate exponential terms without averaging'),(A/2,'Average the two conjugate exponential terms twice')]
 if q in ['inverse-slope','implicit-circle','normal-line']:
  sign=-1 if q!='inverse-slope' else 1
  return [(sign*v,why) for v,why in [(1/m**2,'Square the reciprocal-slope denominator'),(1/(m+1),'Include a coordinate offset in the slope denominator'),(1/(2*m),'Keep an extra derivative factor two'),(m,'Return the original slope magnitude'),(m**2,'Square the original slope instead of reciprocating'),(2/m,'Count the reciprocal slope twice')]]
 if q=='matching-piecewise-slopes':
  return [(m/2,'Treat the coefficient as a quadratic slope factor'),(2*m,'Count the left linear slope twice'),(m-2,'Subtract the quadratic derivative at one instead of zero'),(m+2,'Add the quadratic derivative at one instead of zero'),(m*m,'Differentiate as if the left coefficient were an exponent'),(1/m,'Match reciprocal slopes instead of slopes')]
 if q=='tangent-intercept':
  return [(1-2*m,'Use twice the tangent slope in the intercept'),(-m,'Omit the function value in the intercept'),(1-m*m,'Treat the power coefficient as a second slope factor'),(1-m/2,'Use half the tangent slope'),(-m/2,'Omit the function value and halve the slope'),(-1/m,'Return the normal-line slope rather than an intercept')]
 if q=='quotient-log':
  return [(1/(m+1)**2,'Keep the quotient-rule square without its numerator factor'),(1/m,'Omit the evaluation-point contribution in the denominator'),(1/(m+2),'Add the evaluation-point contribution twice'),(2/(m+1),'Count the logarithmic derivative twice'),(1/(2*(m+1)),'Insert an unnecessary half into the logarithmic derivative'),(m+1,'Invert the final quotient')]
 if q=='inverse-tangent-composition':
  return [(m,'Omit the outer inverse-tangent denominator'),(m*m/2,'Apply the inner chain factor twice'),(m/4,'Apply the outer denominator twice'),(1/(2*m),'Invert the inner power derivative'),(m/(1+m*m),'Insert the inner derivative into the outer function denominator'),(2*m,'Double the chain factor while omitting the outer denominator')]
 if q=='implicit-product':
  return [(-m/(1+m),'Omit one derivative contribution from the squared dependent variable'),(-R(1,2),'Omit the independent-variable factor in the denominator'),(-m/(1+4*m),'Double the squared-variable derivative contribution'),(-2*m/(1+2*m),'Count the undifferentiated dependent factor twice'),(-m/(2*(1+2*m)),'Halve the undifferentiated dependent factor'),(-1/(1+2*m),'Omit the dependent factor in the numerator'),(-m*m/(1+2*m),'Square the numerator factor')]
 if q=='trigonometric-power-coefficient':
  F=s.factorial(m+2)
  return [(-F/6,'Omit the number of choices of the cubic sine term'),(-m*s.factorial(m+1)/6,'Use the preceding derivative factorial'),(-m*F/3,'Double the cubic sine coefficient'),(-m*F/12,'Halve the cubic sine coefficient'),(-m*m*F/6,'Count the selected cubic factor twice'),(-(m+1)*F/6,'Allow one extra sine factor to supply the cubic term')]
 if q in ['removable-power','exponential-standard','logarithm-standard','trigonometric-ratio','nested-log-ratio','rational-infinity']:
  return [(1/m,'Invert the inner or leading scale'),(m/2,'Halve the first-order scale'),(s.Integer(1),'Drop the inner or leading scale'),(m*m,'Apply the inner or leading scale twice'),(2*m,'Count the first-order contribution twice'),(m+1,'Keep the constant endpoint term in the first-order coefficient')]
 if q=='one-sided-absolute':
  return [(-m,'Omit the absolute-value contribution'),(-m-1,'Use the opposite absolute-value branch'),(1-m*m,'Apply the linear coefficient twice'),(1-m/2,'Halve the linear coefficient'),(1/(1-m),'Invert the surviving coefficient'),((1-m)/2,'Apply an extra denominator factor two')]
 if q=='piecewise-continuity':
  return [(m-1,'Subtract the right constant value twice'),(m+1,'Omit the right value before solving for the constant'),(m-3,'Evaluate the right square at two instead of one'),(m+2,'Add the right value instead of subtracting it'),(2*m,'Evaluate the left linear term at two'),(s.Integer(0),'Evaluate the left linear term at zero')]
 if q=='infinity-root-difference':
  return [(m,'Omit one leading root contribution in the rationalized denominator'),(m/4,'Count the denominator factor twice'),(m*m/2,'Square the numerator coefficient'),(m/3,'Count three leading denominator contributions'),(m*m,'Square the coefficient and omit the denominator factor'),(1/m,'Invert the coefficient instead of rationalizing')]
 if q in ['second-order-trig','exponential-cancellation','log-exponential-second-scale']:
  sign=-1 if q=='log-exponential-second-scale' else 1
  return [(sign*v,why) for v,why in [(m/2,'Use only one inner-scale factor in a quadratic coefficient'),(m*m,'Omit the Taylor factorial'),(m*m/4,'Apply the Taylor half twice'),(m**3/2,'Apply a third inner-scale factor'),(m*m/6,'Use the cubic Taylor factorial'),(m**3,'Apply a third scale factor and omit the factorial')]]
 if q=='Gamma-finite-shift-correction':
  return [(-m*(m+1)/2,'Include the omitted final factor in the shift sum'),(-(m-1)*(m-2)/2,'Omit the largest retained shift'),(-m*(m-1),'Forget the triangular half'),(-m*(m-1)/4,'Apply the triangular half twice'),(-(m-1),'Use the count of shifts instead of their sum'),(-m*m*(m-1)/2,'Multiply the shift sum by the normalization exponent again')]
 if q=='interpolation-derivative':
  return [(1/(m+1),'Omit differentiating the x plus one factor'),(-s.Integer(1),'Differentiate the sampled rational function instead of its interpolant'),(1/(m*(m+1))-1,'Include one extra node factor in the interpolation normalization'),(-1/(m+1),'Cancel the factorial ratio in the opposite order'),(2/(m+1)-1,'Count the interpolation-error derivative twice'),(1/(2*(m+1))-1,'Halve the interpolation-error derivative'),(1/(m+2)-1,'Use one extra interpolation node in the normalization'),(-m/(m+2),'Use the next node count in the final quotient')]
 if q=='sharp-endpoint-derivative':
  return [((m-1)**2,'Use one fewer degree after counting interpolation nodes'),((m+1)**2,'Treat the number of nodes as the polynomial degree'),((m/2)**2,'Halve the extremizing frequency'),((2*m)**2,'Double the extremizing frequency'),(((m-1)/2)**2,'Combine a missing degree with a halved frequency'),((m+2)**2,'Count the two endpoints as additional polynomial degrees')]
 if q=='product-Euler-correction':
  return [(-m*m/6,'Omit the finite-sum endpoint correction'),(-m*m/3+m/2,'Count the quadratic logarithm contribution twice'),(-m*m/6-m/2,'Reverse the finite-sum endpoint correction'),(A/2,'Apply the logarithmic Taylor half to the whole correction, including the linear endpoint term'),(A/3,'Apply the quadratic-moment integral divisor to the whole correction'),(A/6,'Apply the cubic Taylor factorial to the entire first correction')]
 if q=='Gaussian-moment-derivative':
  sign=(-1)**(m-1)
  return [(sign*v,why) for v,why in [(s.factorial(m-1)**2,'Use the previous exponential moment'),(s.factorial(m)**2,'Use a factorial one order too high in the logarithmic derivative'),(s.factorial(m-1)*s.factorial(m+1),'Use the next exponential moment'),(s.factorial(m-2)*s.factorial(m),'Differentiate the logarithm one fewer time'),(s.factorial(m-1),'Drop the exponential moment factor'),(s.factorial(m),'Drop the logarithmic derivative factorial'),(s.factorial(m+1)**2,'Use the next factorial for both factors')]]
 if q=='root-of-unity-filter':
  return [(s.Integer(0),'Treat the derivative order as a nontrivial residue class'),(s.Integer(1),'Retain only the real exponential term'),(s.Integer(2),'Retain only two phase contributions with their phases discarded'),(s.Integer(3),'Ignore cancellation among the three phase classes')]
 if q=='iterated-Mobius':
  M=s.Matrix([[1,1],[1,2]])**int(m);c,d=M[1,0],M[1,1]
  return [(1/d,'Omit the quotient derivative square'),(1/c**2,'Use the other denominator matrix entry'),(1/(d+1)**2,'Include the evaluation-point unit twice'),(1/(d-1)**2,'Subtract the evaluation-point unit spuriously'),(1/(2*d*d),'Halve the determinant-one derivative'),(2/(d*d),'Double the determinant contribution')]
 raise AssertionError(q)

def single_literal_pair(record):
 import re
 def signed(value):
  text=re.sub(r'\s+','',value.replace(r'\left','').replace(r'\right',''))
  return (-1,text[1:]) if text.startswith('-') else (1,text)
 values=[signed(c['math']) for c in record['choices']]
 return sum(values[i][0]==-values[j][0] and values[i][1]==values[j][1] for i in range(4) for j in range(i))==1
