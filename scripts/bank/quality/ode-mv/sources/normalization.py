"""Conservative advanced-headroom equivalence, distinct from lower fluency exposure.
Parameter-specific lower-level calculations retain their existing identities.
Exact/cosmetic duplicates are blocked at every level by the parent release gate.
"""
import json
import sympy as s
from common import H

def normalized_lineage(fid,p):
 v={k:s.sympify(x) if not isinstance(x,list) else x for k,x in p.items()};slug=fid.split('equations-',1)[-1].split('multivariable-',1)[-1]
 inv=p;why='No scalar, coordinate, permutation or finite-prefix equivalence was identified within this explicitly reviewed finite domain; retain displayed structural parameters.'
 if slug=='rotating-instability':inv={'ratio':str(v['a']/v['w'])};why='Time normalization leaves only the rotating-frame rate ratio.'
 elif slug=='weighted-string-first-eigenvalue':inv={'angularWindowRatio':str(v['n']/v['k'])};why='Gauge and angular coordinate reduce to a constant-coefficient Dirichlet interval; equal angular lengths differ only by translation.'
 elif slug=='homoclinic-mass':inv={'canonical':'positive-cubic-homoclinic'};why='All coefficient pairs reduce by amplitude and time scaling to the same cubic homoclinic profile.'
 elif slug=='critical-radial-bubble':inv={'dimension':str(v['n'])};why='Initial height is removable by the critical amplitude/radius scaling; spatial dimension and critical exponent remain.'
 elif slug=='isochronous-shear':inv={'absoluteShear':str(abs(v['c'])),'energy':str(v['h'])};why='Changing the shear sign is a spatial reflection; fixed-shape energy and absolute shear remain.'
 elif slug in ('polynomial-root-moment','global-Riccati-threshold','spectral-potential-derivative'):inv={'powerOrMode':str(v['n'])};why='Coefficient or interval length is removable by the stated amplitude/time coordinate normalization; polynomial power or nodal mode remains.'
 elif slug=='logarithmic-uniqueness-borderline':inv={'tests':sorted(v['tests'])};why='Permuting the same four tested exponent pairs does not create a new mathematical item.'
 elif slug=='small-loop-geometric-phase':inv={'commutatorProduct':str(v['a']*v['b'])};why='Diagonal coordinate conjugacy removes individual shear scales while preserving their commutator product.'
 elif slug=='inverse-period-potential':inv={'energyPeriodProduct':str(v['a']*v['e'])};why='Energy and coordinate normalization leave the dimensionless period-slope times evaluation-energy product.'
 elif slug=='bistable-front-speed':inv={'reflectedEquilibrium':str(min(v['a'],1-v['a']))};why='Time scaling removes reaction rate and front reflection interchanges the interior equilibrium with its complement.'
 elif slug=='Robin-Lyapunov-infimum':inv={'boundaryLengthProduct':str(v['h']*v['ell'])};why='Scaling the interval to unit length leaves this dimensionless Robin parameter.'
 elif slug=='minimum-peak-acceleration':inv={'velocityRatio':str(v['V']*v['Tend']/v['D'])};why='Normalize time and displacement; the terminal velocity-to-displacement ratio remains.'
 elif slug=='competing-parabolic-ridges':
  lo,hi=sorted([abs(v['a']),abs(v['b'])]);inv={'coefficientRatio':str(hi/lo)};why='Coordinate sign reflections and exchange remove signs/order; output scaling removes the common coefficient.'
 elif slug=='positive-matrix-cone-integral':inv={'determinantPower':str(v['p'])};why='Positive congruence changes any precision matrix to identity, leaving only the determinant-weight exponent.'
 elif slug=='elliptic-torsion-sharp-functional':inv={'aspectRatio':str(max(v['a'],v['b'])/min(v['a'],v['b']))};why='Uniform geometric scaling and coordinate exchange leave the ellipse aspect ratio; anisotropic energy prevents removing that ratio.'
 elif slug=='eccentric-annulus-capacity':inv={'annulusRatio':str(v['m']/v['n'])};why='Conformal pullback and uniform annulus scaling leave only the ratio of radii.'
 elif slug=='spherical-triangle-vector-area':inv={'shape':sorted([str(v['a']/v['c']),str(v['b']/v['c'])])};why='The third vertex is unchanged by common scaling; exchanging the first two coordinates preserves the requested third moment.'
 elif slug=='saddle-level-band':inv={'canonical':'nondegenerate-saddle-band'};why='Conservative advanced count: every case has the same local indefinite-quadratic normal form; transformed ambient cutoff affects only the lower-order remainder.'
 elif slug=='sphere-quadratic-homogeneity':
  a,b,c=v['a'],v['b'],v['c'];tr=a+b+c;inv={'normalizedSecondTrace':str((a*a+b*b+c*c+4)/(tr*tr)),'normalizedDeterminant':str((a*b*c-a-c)/(tr**3))};why='Orthogonal conjugacy and uniform quadratic-form scaling leave its normalized eigenvalue multiset, encoded by trace invariants.'
 elif slug=='projective-disk-integral':inv={'vectorNormSquared':str(v['a']**2+v['b']**2)};why='Disk rotations remove the direction of the affine denominator vector but preserve its length.'
 elif slug=='minimum-enclosing-ellipse':
  a,b=sorted([v['a'],v['b']])
  if a*a>=s.Rational(1,2):inv={'canonical':'uncapped-rectangle-optimum'};why='The axial points are inactive at the enclosing-rectangle optimum; these cases have a Hard route and one affine normalized lineage.'
  else:inv={'activeSmallCoordinate':str(a)};why='In this finite domain only the smaller-coordinate cap binds; scaling the other coordinate changes area but not the active-constraint decision.'
 elif slug=='Gaussian-entropy-variational':inv={'canonical':'fixed-covariance-Gaussian-Gibbs'};why='Every positive covariance reduces by affine pushforward to the same Gaussian entropy extremizer; the log determinant is the Jacobian correction.'
 elif slug=='zonotope-volume':inv={'coefficients':sorted([str(v['a']),str(v['b'])])};why='Coordinate exchange identifies the two generator-coefficient orders; no further affine equivalence is claimed.'
 canonical=json.dumps(inv,sort_keys=True,separators=(',',':'),default=str)
 return 'q4-normalized:'+fid+':'+H(inv)[:24],inv,why
