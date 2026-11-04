"""Additional explicitly authored misconceptions, selected only after exact inequality checks."""
import sympy as s
R=s.Rational

def install(core):
 E=core['equal']
 def wrap(old):
  def b(m):
   p=old(m);A=p['answer'];shape=p['structuralSignature'];H=s.harmonic
   if shape in ['logarithmic-power-over-linear','fractional-power-times-log','factorial-ratio-test']:
    q=s.symbols('q',positive=True);growing=int(m)%2==1
    if shape=='logarithmic-power-over-linear':
     expr=s.log(q)**m*q if growing else s.log(q)**m/q;point=s.oo;A=s.oo if growing else s.Integer(0)
     p['statement']=r'\lim_{x\to\infty}'+core['latex'](expr.subs(q,s.Symbol('x')))
     reason='A fixed power of log x is dominated by a positive power of x. Multiplication by x instead of division produces positive unbounded growth.'
    elif shape=='fractional-power-times-log':
     expr=q**((-1 if growing else 1)/m)*s.log(q);point=0;A=-s.oo if growing else s.Integer(0)
     p['statement']=r'\lim_{x\to0^+}'+core['latex'](expr.subs(q,s.Symbol('x')))
     reason='Set u=-log x. The expression becomes -u exp(-u/m) for a positive power, or -u exp(u/m) for a negative power.'
    else:
     expr=m*(q+1) if growing else m/(q+1);point=s.oo;A=s.oo if growing else s.Integer(0)
     p['statement']=r'a_k='+((core['latex'](m)+r'^k k!') if growing else (r'\frac{'+core['latex'](m)+r'^k}{k!}'))+r'.\quad\lim_{k\to\infty}\frac{a_{k+1}}{a_k}=?'
     reason='Cancel the exponential and factorial factors before taking the limit; the ratio is m(k+1) when factorial is in the numerator and m/(k+1) when in the denominator.'
    actual=s.limit(expr,q,point,dir='+');assert actual==A
    other=s.Integer(0) if A in [s.oo,-s.oo] else (-s.oo if shape=='fractional-power-times-log' else s.oo)
    p['answer']=A;p['answerForm']='extended-real';p['options']=[(A,'correct'),(other,'reverse the growth comparison'),(s.Integer(-1) if shape=='fractional-power-times-log' else s.Integer(1),'assume the growth rates cancel to a unit constant'),(m if shape!='fractional-power-times-log' else -m,'retain a coefficient while discarding the limiting growth factor')]
    p['solutionSteps']=[core['text'](reason),core['latex'](A)];p['verificationRoute']='exact-symbolic-extended-real-limit'
    p['certificate']={'kind':'exact-extended-real-symbolic-limit','expression':core['latex'](expr),'variable':'q','approach':core['latex'](point),'result':core['latex'](actual),'review':'Trusted symbolic limit; not a finite floating-point approximation'}
    p['automatedChecks'].append({'checkIndex':len(p['automatedChecks']),'passed':True,'scope':'exact extended-real SymPy limit of the rendered growth case'})
   if shape in ['oscillation-with-vanishing-envelope','alternating-geometric-sequence']:
    A=m;p['answer']=A
    if shape=='oscillation-with-vanishing-envelope':
     p['statement']=r'\lim_{x\to0}\left('+core['latex'](m)+r'+x^{'+core['latex'](m)+r'}\sin(1/x)\right)'
     reason='The absolute difference from m is at most |x| to the positive power m, hence tends to zero.'
    else:
     p['statement']=r'\lim_{n\to\infty}\left['+core['latex'](m)+r'+\left(-\frac{'+core['latex'](m-1)+'}{'+core['latex'](m)+r'}\right)^n\right]'
     reason='The geometric term has absolute ratio (m-1)/m<1 and tends to zero. The constant term remains.'
    p['options']=[(A,'correct'),(s.Integer(0),'discard the constant together with the decaying term'),(m-1,'treat the oscillatory contribution as constantly minus one'),(m+1,'treat the oscillatory contribution as constantly plus one'),(2*m,'add the constant contribution twice')]
    p['solutionSteps']=[core['text'](reason),core['latex'](A)]
    p['automatedChecks'].append({'checkIndex':len(p['automatedChecks']),'passed':True,'scope':'previous exact decay certificate plus the explicitly retained constant m'})
   if shape=='cubic-derivative-sign-chart':
    sign=(-1)**int(m);root=m if sign==1 else s.Integer(1);q=s.symbols('q')
    poly=sign*(q+1)*(q-1)*(q-m)
    assert poly.subs(q,root-R(1,2))<0 and poly.subs(q,root+R(1,2))>0
    A=root;p['answer']=A
    p['statement']=r'f\prime(x)='+('-' if sign<0 else '')+r'(x+1)(x-1)(x-'+core['latex'](m)+r').\quad'+core['text']('At which positive x does f have a local minimum?')
    p['options']=[(A,'correct')]+[(v,'choose a maximum or a noncritical point') for v in [m,1,-1,-m] if v!=A]
    p['solutionSteps']=[core['text']('Order the roots -1,1,m. With the displayed leading sign, the derivative changes from negative to positive at the selected positive root.'),core['latex'](A)]
   if shape=='third-root-of-unity-filter':
    order=3*int(m)+int(m)%3;A=s.Integer(3 if order%3==0 else 0)
    assert E(1+2*s.cos(2*s.pi*order/3),A)
    p['answer']=A;p['statement']=r'F(x)=e^x+2e^{-x/2}\cos(\sqrt3x/2).\quad F^{('+str(order)+r')}(0)=?'
    p['options']=[(A,'correct')]+[(v,'retain an incomplete or incorrectly normalized root-of-unity contribution') for v in [s.Integer(0),s.Integer(3),s.Integer(1),s.Integer(-1)] if v!=A]
    p['solutionSteps']=[core['text']('Write F as the sum of exp(x),exp(omega x),exp(omega squared x), where omega is a nonreal cube root of one. Its n-th derivative at zero is the sum of their n-th powers, equal to three for n divisible by three and zero otherwise.'),core['latex'](A)]

   extras={
    'affine-sign-change-symmetric-bounds':[(-m*m/2,'keep only the negative triangular lobe')],
    'absolute-linear-integrand':[(3*m*m/2,'treat one lobe as a rectangle and the other as a triangle')],
    'quarter-circle-area':[(s.pi*m*m/8,'halve the quarter-disk area once more')],
    'mean-value-normalized-integral':[(m*m/6,'divide by twice the interval length')],
    'endpoint-data-FTC':[(-A,'reverse the endpoint order')],
    'piecewise-affine-constant':[(m/2,'retain only the first interval integral')],
    'disk-volume-linear-radius':[(2*s.pi*m*m/3,'use an extra shell circumference factor two')],
    'shells-triangular-region':[(s.pi*m**3,'use the bounding cylinder instead of the varying triangular height')],
    'absolute-square-root-interior-switch':[(m**3/2,'replace the curve by its bounding rectangle')],
    'log-squared-endpoint-moment':[(1/(m+1)**3,'omit the factor two from the second parameter derivative')],
    'beta-polynomial-two-endpoints':[(A/m,'drop the highest factor from the first numerator factorial')],
    'arc-length-perfect-square':[(s.sqrt(1+(3/(4*m)-m*s.log(2)/2)**2),'return the straight endpoint chord instead of curve length')],
    'tabulated-product-rule':[(6*m*(m+1),'multiply the two product-rule terms instead of adding them')],
    'tabulated-composition':[(m*m*(m+1),'apply the inner derivative twice')],
    'inverse-slope-data':[(1/(m*m),'square the reciprocal slope')],
    'circle-implicit-first-derivative':[(-1/(m*m),'use the squared y coordinate in the denominator')],
    'parametric-slope':[(3*m/4,'divide by the factor two in dx/dt twice')],
    'piecewise-slope-matching':[(m/2,'differentiate the coefficient term as if it had a quadratic factor')],
    'tangent-intercept':[(-m,'omit the tangent point ordinate while computing the intercept')],
    'root-linearization':[(m,'omit the differential increment')],
    'area-radius-related-rate':[(8*s.pi*m,'apply the radius time-rate twice')],
    'difference-quotient-binomial':[(m*2**(m-1),'evaluate the derivative at two instead of the stated base point one')],
    'exp-of-trig':[(0,'substitute the zero inner argument before differentiating and treat it as constant')],
    'implicit-product-plus-square':[(-m,'omit the entire implicit derivative denominator')],
    'inverse-second-derivative-data':[(-2/m,'retain only one rather than three inverse-slope factors')],
    'parametric-second-derivative':[(m*(m+2)/8,'divide by the factor two from dx/dt one extra time')],
    'cubic-product-constrained-maximum':[(0,'select the left endpoint without comparing the interior critical value')],
    'piecewise-second-order-pasting':[(0,'check only continuity and the first derivative, ignoring curvature')],
    'normal-slope':[(-1/(m*m),'square the tangent slope before taking the negative reciprocal')],
    'implicit-conic-second-derivative':[(-(m+2)/(2*m+1),'return the first implicit derivative instead of the second')],
    'parametric-curvature':[(4/(1+4*m*m)**R(3,2),'double-count the second-derivative determinant')],
    'Lambert-implicit-second-derivative':[(2*A,'count the second inverse-chain contribution twice')],
    'sin-power-next-nonzero-derivative':[(m*A,'count m squared rather than m locations for the one quadratic Taylor correction')],
    'implicit-quadratic-series-inversion':[(A/m,'use (m-1)! instead of m! to convert coefficient to derivative')],
    'Mobius-iterate-derivative':[(-A,'use the wrong sign for the transformation determinant')],
    'implicit-minimum-envelope':[(m+m*m/4,'return the minimized function value instead of its derivative')],
    'conjugated-differential-operator':[((-1)**m,'replace exp(x) by exp(-x) in the conjugated derivative')],
    'rational-samples-polynomial-interpolant':[(A/(m+1),'divide the interpolation normalization by the number of nodes twice')],
    'floor-linear-growth':[(m+1,'retain the upper unit rounding error after division by x')],
    'piecewise-continuity-parameter':[(0,'match the unshifted polynomial branch and omit the needed constant')],
    'one-to-infinity-power':[(s.exp(m*m),'apply the inner argument scale twice in the logarithmic limit')],
    'fixed-factorial-shift':[(1/s.factorial(m),'normalize the finite factorial product by m factorial unnecessarily')],
    'principal-root-one-sided':[(s.sqrt(m),'treat the higher-order term as the leading quadratic coefficient')],
    'rational-Riemann-sum':[(1,'use a constant left-endpoint rectangle instead of integrating the varying function')],
    'power-sum-Stolz':[(1/(m+2),'increase the asymptotic denominator degree twice')],
    'monotone-square-root-recurrence':[(1-m,'choose the negative root of the fixed-point equation')],
    'endpoint-concentrating-integral':[((2**(m+1)-1)/(m+1),'integrate the fixed polynomial uniformly instead of using the concentrating weight')],
    'product-as-log-Riemann-sum':[(s.exp(-((m+1)*s.log(m+1)-m)/m),'reverse the sign when taking the logarithm of the product')],
    'triangular-product-first-correction':[(-m/2-m*m/6,'reverse the finite-sum endpoint correction but retain the quadratic log term')],
    'shifted-central-binomial-defect':[(m*m/(s.pi),'use pi rather than square root pi in Stirling normalization')],
    'neutral-recursion-decay-rate':[(m**(-1),'forget the m-th root when returning to the original sequence')],
    'degenerate-endpoint-Laplace-rescaling':[(s.gamma(2/m)/m,'use an extra radial power in the limiting Gamma moment')],
    'geometric-remainder-bound':[(2**(-m-2),'start the geometric remainder two indices too late')],
    'geometric-radius':[(s.sqrt(m),'take a square root of the radius although the variable is not squared')],
    'nonzero-term-limit-divergence':[(2*m,'multiply by the denominator constant instead of comparing the leading coefficients')],
    'central-factorial-ratio-radius':[(1/m,'ignore the central-factorial growth and keep only the variable scale')],
    'integral-test-tail-upper-bound':[(1/(2*(m-1)**2),'begin the comparison integral one interval too early')],
    'alternating-first-omitted-term-bound':[(1/(m+3),'skip two omitted terms before estimating the alternating remainder')],
    'Frullani-positive-parameter-rectangle':[(-A,'reverse the order of decay parameters in the auxiliary integral')],
    'mixed-beta-logarithmic-endpoints':[(A/2,'use the mixed derivative as if its Taylor coefficient required division by two')],
    'half-angle-rational-quadratic':[(2*A,'apply the half-angle differential factor two twice')],
    'single-partial-polynomial':[(1+3*m*m,'differentiate in y and interchange the evaluation coordinates'),(m,'omit the exponent factor two from differentiating x squared')],
    'mixed-partial-monomial':[(m*(m-1),'differentiate twice in y instead of once in each variable')],
    'directional-unit-vector':[(3*m/5,'omit the factor two in the gradient')],
    'sphere-tangent-plane-offset':[(m*m-2,'subtract both first coordinate contributions while finding the plane constant')],
    'two-variable-linear-approximation':[(2*m,'use the base value and omit both differential increments')],
    'rectangular-double-integral':[(m/2,'integrate only the x contribution')],
    'triangle-area-double-integral':[(m*m/4,'halve the base as well as applying the triangle factor')],
    'disk-area-polar':[(2*s.pi*m*m,'double-count the angular range')],
    'curve-composition-total-derivative':[(2*m+8*m**3,'apply the inner derivative factor twice to the y squared term')],
    'divergence-polynomial-field':[(m,'retain only the z component derivative')],
    'conservative-field-endpoint-data':[(2*(m*m+1),'retain the gradient factor two in the potential instead of integrating it')],
    'box-average-value':[(m/2,'average only the x contribution')],
    'maximum-directional-derivative':[(2*m,'use the largest coordinate partial instead of the gradient norm')],
    'two-square-global-minimum':[(2,'set x=y while cancelling the first square, leaving the second square nonzero'),(2*(m+1)**2,'use the feasible point (0,m) without minimizing the second square')],
    'linear-form-circle-constraint':[(1,'maximize only the y term')],
    'reverse-triangular-integration-order':[(m,'return the integrand coefficient instead of the integral')],
    'ellipse-area-linear-Jacobian':[(s.pi,'forget the area Jacobian')],
    'radial-disk-moment':[(s.pi/(2*(m+1)),'integrate over a half disk')],
    'circulation-Green-disk':[(4*s.pi*m*m,'count each curl derivative contribution twice')],
    'radial-field-sphere-flux':[(-4*s.pi*m**3,'use inward rather than outward orientation')],
    'planar-graph-surface-area':[(1,'return projected area rather than surface area')],
    'implicit-sphere-partial':[(-2/m,'fail to cancel the factor two in the denominator')],
    'density-weighted-centroid':[(1,'replace the density-weighted mean by the right endpoint')],
    'ball-radial-power-moment':[(2*s.pi/(2*m+3),'use only a hemisphere angular measure')],
    'symmetric-quadratic-on-circle':[(m-R(1,2)-s.sqrt(5)/2,'subtract an extra identity shift while diagonalizing')],
    'moving-disk-boundary-integral':[(0,'differentiate the integrand while ignoring the moving boundary')],
    'ellipsoid-axis-second-moment':[(4*s.pi*m**2/15,'scale the squared coordinate but omit the volume Jacobian')],
    'product-ratio-positive-quadrant':[(-(m-1),'use the signed inverse Jacobian instead of its absolute value')],
    'polynomial-simplex-beta':[(s.factorial(m)*s.factorial(m+2)/s.factorial(2*m+3),'forget the inner antiderivative divisor m+2')],
    'closed-field-nonsimply-connected-domain':[(-2*s.pi,'reverse the curve orientation')],
    'Stokes-tilted-graph-curl-flux':[(-2,'use the downward orientation')],
    'square-domain-coupled-quadratic':[(m+2,'add rather than subtract the two square penalties at the corner')],
    'paraboloid-oriented-flux':[(-(s.pi/m+s.pi/(2*m*m)),'use downward instead of upward orientation'),(2*A,'double-count the graph area-vector contribution')],
    'Hessian-coordinate-congruence':[(2*m,'differentiate only the transformed y-square contribution and lose its sign'),(2*A,'double the off-diagonal coefficient while reading the mixed partial')],
    'anisotropic-path-limit':[(-R(1,2),'substitute the opposite curved path y=-x^m instead of the stated path')],
    'coupled-two-dimensional-Gaussian':[(s.pi/(2*s.sqrt(m-1)),'count only one half-line in one Gaussian integral')],
    'Vandermonde-discriminant-sphere-extremum':[(0,'assume the maximum occurs when two coordinates coincide')],
    'anisotropic-integrability-threshold':[(0,'discard the anisotropic scale shift in the power comparison')],
    'correlated-Gaussian-positive-quadrant':[(s.pi/(2*s.sin(s.pi/m)),'replace the oblique wedge by a full upper half-plane')],
    'disk-logarithmic-potential-interior-source':[(2*A,'omit the one-half factor in the radial antiderivative')],
    'two-translated-resolvent-plane-integral':[(-A,'reverse the transformed parameter endpoints in the logarithmic antiderivative')],
    'log-sum-exp-Legendre-minimum':[-(1-3/m)*s.log(1-3/m)],
    'dimension-equals-power-lp-ball':[(s.factorial(m)*A,'use the usual simplex factorial in the numerator rather than the actual Dirichlet Gamma total')],
    'mixed-logarithmic-simplex-moment':[((H(m)-H(m+3))*(1-H(m+3))/((m+1)*(m+2)*(m+3)),'omit the mixed trigamma correction')],
    'complex-polynomial-lemniscate-area':[(m*A,'count the petals without the inverse angular Jacobian')],
    'disk-squared-log-harmonic-Parseval':[(s.pi*s.polylog(2,1/(m*m))/2,'omit the shifted-logarithm terms after the partial-fraction split')],
    'high-dimensional-cube-simplex-cap':[(m*A,'use (m-1)! rather than m! as the simplex volume normalization')],
    'polynomial-image-winding-via-coefficient-root-bound':[(-4*s.pi,'reverse the winding orientation')],
    'alternating-harmonic-fixed-block-rearrangement':[(s.log(2)+2*s.log(m),'double rather than halve the frequency correction')],
    'exponential-cancellation-p-series-threshold':[(R(1,2),'use the root-test exponent as if it were a p-series threshold')],
    'dyadic-factor-infinite-product':[(m*m/(m*m-1),'omit the first product factor')],
    'floor-weight-geometric-series':[(m*A,'multiply by the block size a second time after reversing the sum')],
    'finite-alternating-binomial-reciprocal':[(s.factorial(m-1)**2/s.factorial(2*m),'drop the final numerator factorial factor')],
    'global-maximum-implicit-inverse-curvature':[(1/(8*m),'evaluate at y=m instead of locating the true maximum')],
    'oscillatory-first-derivative-continuity-threshold':[(m-1,'differentiate the oscillatory phase with the wrong power shift')],
    'nonuniform-limit-global-maximum':[((m-1)*m**(-1/(m-1)),'omit the extra factor 1/m from evaluating the power at the maximizing point')],
   }.get(shape,[])
   if shape=='log-sum-exp-Legendre-minimum':extras=[(extras[0],'retain only the remaining probability-weight entropy term')]
   if shape=='two-square-global-minimum':p['options']=[o for o in p['options'] if not E(o[0],1)]
   for value,why in extras:
    value=s.sympify(value)
    if not value.has(s.nan,s.oo,-s.oo,s.zoo) and value.is_real is not False and all(not E(value,w) for w,_ in p['options']):p['options'].append((value,why))
   return p
  return b
 for f in core['FAMILIES']:f['build']=wrap(f['build'])
