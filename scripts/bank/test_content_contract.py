#!/usr/bin/env python3
import sys,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(0,str(Path(__file__).parent/'content'))
import standalone
from content_pipeline import verify,build
class StandaloneContract(unittest.TestCase):
 def spec(self):
  return {'slug':'certificate-test','coefficients':[[0,1],[3,1],[1,2]],'operation':'definite-integral','point':[0,1],'upper':[2,1],'distractors':[{'value':[6,1],'misconception':'Omit the quadratic contribution'},{'value':[28,3],'misconception':'Double the quadratic contribution'},{'value':[11,3],'misconception':'Divide by the interval length'}],'pedagogy':{'constructionId':'standalone-certificate-test','relatedIdeaGroupId':'polynomial-area','structuralSignature':'quadratic-area','primaryTechnique':'power-rule','alternativeTechniques':[],'prerequisites':['polynomial-antiderivatives'],'reasoningDemand':['execution'],'answerForm':'rational','difficultyRationale':'Verifier test fixture, not new curricular coverage.','sourceRecordIds':[],'responseFormat':'multiple-choice'},'topic':'integration','difficulty':'easy'}
 def test_round_trip(self):
  p=standalone.build(self.spec());self.assertTrue(verify(p));self.assertEqual(p['choices'][0]['math'],r'\frac{22}{3}');self.assertFalse(p['validation']['humanReviewed'])
 def test_tamper(self):
  p=standalone.build(self.spec());p['solutionSteps'][-1]='0';p.pop('contentHash');p['contentHash']=standalone.digest(p)
  with self.assertRaises(ValueError):verify(p)
 def test_equivalent_distractor(self):
  spec=self.spec();spec['distractors'][0]['value']=[44,6]
  with self.assertRaises(ValueError):standalone.build(spec)
 def test_bad_domain(self):
  for a,b in [([2,1],[2,1]),([3,1],[2,1]),([1,0],[2,1])]:
   spec=self.spec();spec['point']=a;spec['upper']=b
   with self.assertRaises(ValueError):standalone.build(spec)
 def test_no_untrusted_expression_execution(self):
  spec=self.spec();spec['coefficients']=['__import__("os")']
  with self.assertRaises(ValueError):standalone.build(spec)
 def test_unknown_route(self):
  spec=self.spec();spec['operation']='prove-arbitrary-analytic-theorem'
  with self.assertRaises(ValueError):standalone.build(spec)
class ConstructedContract(unittest.TestCase):
 def test_analytic_and_residual_routes_preserve_executable_evidence(self):
  for family in ['io3-reciprocal-quartic','m3-differential-equations-easy-field-slope']:
   p=build(family,0);self.assertTrue(verify(p));self.assertTrue(p['validation']['evidence']['executedChecks']);self.assertTrue(p['validation']['evidence']['analyticCertificate'])
   q=copy.deepcopy(p);q['answerChoiceId']=next(c['choiceId'] for c in q['choices'] if c['choiceId']!=q['answerChoiceId']);q.pop('contentHash');q['contentHash']=standalone.digest(q)
   with self.assertRaises(ValueError):verify(q)
 def test_parameter_domain_is_not_extended_by_rehashing(self):
  for index in [-1,8,1.5,True]:
   with self.assertRaises(ValueError):build('io3-reciprocal-quartic',index)
 def test_routine_priority_proposals_move_to_hard(self):
  p=build('io3-inverse-moment',0);self.assertEqual(p['difficulty'],'hard');self.assertFalse(p['provenance']['authoring']['priorityMinimumEligible'])
 def test_editorial_quarantine_is_not_admitted_by_automated_math(self):
  with self.assertRaisesRegex(ValueError,'admission unresolved'):build('m3-series-easy-squared-telescope',0)
 def test_categorical_and_extended_real_routes_remain_exact(self):
  for family,index in [('m3-series-easy-p-series-pair',0),('m3-series-easy-ratio-test-data',1)]:
   p=build(family,index);self.assertTrue(verify(p));self.assertFalse(p['validation']['humanReviewed'])
   q=copy.deepcopy(p);q['choices'][0]['math']='42';q.pop('contentHash');q['contentHash']=standalone.digest(q)
   with self.assertRaises(ValueError):verify(q)
  p=build('m3-series-easy-ratio-test-data',1);self.assertEqual(p['pedagogy']['answerForm'],'extended-real');self.assertEqual(next(c['math'] for c in p['choices'] if c['choiceId']==p['answerChoiceId']),r'\infty')
 def test_analytic_labels_and_readable_product_derivation(self):
  p=build('m3-limits-olympiad-irrational-rotation-correlation',0);self.assertTrue(p['validation']['evidence']['verificationRoute']);self.assertTrue(p['validation']['evidence']['analyticCertificate'])
  p=build('m3-differentiation-hard-log-product',7);self.assertTrue(verify(p));self.assertLess(max(map(len,p['solutionSteps'])),1000);self.assertIn('H_m^2-H_m^{(2)}',p['solutionSteps'][-1])
if __name__=='__main__':unittest.main()
