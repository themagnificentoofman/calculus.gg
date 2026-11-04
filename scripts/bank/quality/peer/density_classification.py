"""Independent exact centroid and actual-choice qualitative classification."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,re,sys
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def value(t):
 m=re.fullmatch(r'\\frac\{(\d+)\}\{(\d+)\}',t);return Q(*map(int,m.groups()))if m else Q(t)
def main(source,originals,served,output):
 source,originals,served,output=map(Path,[source,originals,served,output]);assert not output.exists()
 old={r['problemId']:r for r in map(json.loads,originals.read_text().splitlines())};visible={r['problemId']:r for r in map(json.loads,served.read_text().splitlines())};records=[]
 for r in map(json.loads,source.read_text().splitlines()):
  n=int(re.search(r'\\rho\(x,y\)=x\^\{(\d+)\}',r['statement'])[1]);assert n>0
  mass=Q(1,n+1);moment=Q(1,n+2);answer=moment/mass
  values=[value(c['math'])for c in r['choices']];assert len(set(values))==4
  assert [c['choiceId']for c,v in zip(r['choices'],values)if Q(1,2)<v<1]==[r['answerChoiceId']]
  assert next(v for c,v in zip(r['choices'],values)if c['choiceId']==r['answerChoiceId'])==answer
  prior=old[r['sourcePreview']['problemId']];current=visible[prior['problemId']]
  assert digest(prior)==r['sourcePreview']['canonicalRawHash']and digest(current)==r['sourcePreview']['servedRawHash']
  for k in ['statement','choices','answerChoiceId','solutionSteps']:assert r[k]==current[k]
  assert value(r['solutionSteps'][-1])==answer and r['difficulty']=='easy'
  records.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':digest(r),'sourcePreview':r['sourcePreview'],
   'independentAnswer':str(answer),'mass':str(mass),'firstMoment':str(moment),'literalPairDifferences':[str(a-b)for a,b in itertools.combinations(values,2)],
   'completeTaskReviewed':True,'qualitativeProof':'Pair x with1-x in the centered first moment: integral from1/2to1 of(x-1/2)(x^n-(1-x)^n)dx is strictly positive for n>0. Positive mass strictly inside(0,1) gives mean<1. These inequalities uniquely select the literal option; independent monomial integrals give the same value.',
   'recommendedDifficulty':'easy','qualifiedOlympiad':False,'passed':True})
 assert len(records)==10
 output.write_text(json.dumps({'inputSha256':sha(source),'originalsSha256':sha(originals),'servedSha256':sha(served),'reviewerCodeSha256':sha(Path(__file__)),
  'author':'ode_final_review','reviewer':'root','records':records,'instances':10,'literalPairs':60,'scope':'Complete exact elementary centroid and qualitative elimination review; source-bound Easy classification, no new ideas or player calibration.'},indent=2)+'\n');print(json.dumps({'passed':10,'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
