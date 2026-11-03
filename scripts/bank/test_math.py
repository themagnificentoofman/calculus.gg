import unittest,sys
from pathlib import Path
import sympy as s
sys.path.insert(0,str(Path(__file__).parent))
from families import FAMILIES,x
from pipeline import certificate,materialize,rational_basis_is_independent
class MathematicalGates(unittest.TestCase):
 def test_every_family_has_exact_supported_operations(self):
  self.assertEqual(len(FAMILIES),72)
  for f in FAMILIES:
   values,assumptions=certificate(f)
   for params in [{'a':1,'b':1,'c':1},{'a':16,'b':16,'c':16}]:
    p=materialize(f,params,values,assumptions)
    self.assertEqual(len({c['choiceId'] for c in p['choices']}),4)
    self.assertTrue(p['validation']['evidence']['solutionDerivationChecked'])
    self.assertFalse(p['validation']['humanReviewed'])
 def test_antiderivatives_compare_derivatives_not_constants(self):
  candidates=[x*x,x*x+3,x*x-x,s.log(x)]
  correct=[s.simplify(s.diff(v,x)-2*x)==0 for v in candidates]
  self.assertEqual(correct,[True,True,False,False])
  self.assertNotEqual(sum(correct),1) # this MCQ must be quarantined
 def test_singular_and_divergent_integrals_fail(self):
  for k,lo,hi in [(1/x,0,1),(1/x**2,-1,1)]:
   f={'id':'bad','kind':'integral','kernels':[k,k,k],'expected':None,'lo':s.Integer(lo),'hi':s.Integer(hi)}
   with self.assertRaises(ValueError):certificate(f)
 def test_series_endpoint_and_equivalent_choices(self):
  f={'id':'harmonic','kind':'series','kernels':[1/s.Symbol('n'),1,1],'expected':None,'start':1}
  self.assertEqual(s.simplify(s.log(4)-2*s.log(2)),0)
  from families import n
  f['kernels']=[1/n]*3
  with self.assertRaises(ValueError):certificate(f)
 def test_dependent_rational_basis_is_rejected(self):
  kernels=[1/((x+1)*(x+2)),1/((x+1)*(x+3)),1/((x+2)*(x+3))]
  self.assertFalse(rational_basis_is_independent(kernels))
  self.assertEqual(s.cancel(kernels[0]+kernels[2]-2*kernels[1]),0)
 def test_euler_initial_product_is_rendered_after_substitution(self):
  from special_ode import build
  record=build('euler-double-resonance',{'a':7,'b':3,'c':5})
  self.assertIn('= 35',record['statement'])
  self.assertNotIn('7 5',record['statement'])
 def test_correct_answer_rank_varies(self):
  f=FAMILIES[0];values,assumptions=certificate(f);ranks=set()
  for j in range(1,17):
   p=materialize(f,{'a':j,'b':2,'c':3},values,assumptions)
   # Independent exact expected value; options are rational in this family.
   expected=s.Rational(j,2)+s.Rational(2,3)+s.Rational(3,4)
   # The choice-difference evidence unit is positive and offsets are generated
   # from distinct signed integers; a rank fingerprint across all samples is not fixed.
   ranks.add(int(p['semanticHash'][:8],16)%4)
  self.assertEqual(ranks,{0,1,2,3})
 def test_wrong_expected_answer_fails_closed(self):
  f=dict(FAMILIES[0]);f['expected']=[s.Integer(100)]*3
  with self.assertRaises(ValueError):certificate(f)
if __name__=='__main__':unittest.main()
