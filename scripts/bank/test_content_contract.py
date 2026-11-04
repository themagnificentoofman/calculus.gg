#!/usr/bin/env python3
import sys,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(0,str(Path(__file__).parent/'content'))
import standalone
from content_pipeline import verify
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
if __name__=='__main__':unittest.main()
