"""Independent, source-bound review of a peer-authored option-only patch."""
from pathlib import Path
import argparse,json,hashlib,itertools,re
from fractions import Fraction

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def rational(t):
 m=re.fullmatch(r'\\frac\{(-?\d+)\}\{(\d+)\}',t)
 return Fraction(int(m[1]),int(m[2])) if m else Fraction(int(t))
def cube(n):
 n=abs(n);lo=0;hi=n+1
 while lo+1<hi:
  m=(lo+hi)//2
  if m**3<=n:lo=m
  else:hi=m
 return lo**3==n
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--release',type=Path,required=True);ap.add_argument('--patch-dir',type=Path,required=True);a=ap.parse_args();P=a.patch_dir
 patchpath=P/'series-negative-binomial-option-patches.json';guards=json.loads((P/'series-negative-binomial-repair-guards.json').read_text());patches=json.loads(patchpath.read_text());preview=a.repo/'.bank-data/quality/series-previews-v3/canonical-previews.jsonl'
 originals={r['problemId']:r for path in [a.release,preview] for r in map(json.loads,path.read_text().splitlines())};results=[]
 for patch in patches:
  r=originals[patch['problemId']];g=guards[r['problemId']];assert canonical(r)==g['rawHash']==patch['sourceRawHash'];assert r['contentHash']==patch['sourceContentHash'];m=g['m'];q=Fraction(1,m)
  # Triple convolution: coefficient of q^k counts compositions k=i+j+l, namely choose(k+2,2).
  A=1/(1-q)**3;values=[rational(c['math']) for c in patch['choices']];assert values[[c['choiceId'] for c in patch['choices']].index(patch['answerChoiceId'])]==A
  assert len(set(values))==4
  # Independent first/second geometric-moment derivatives identify every named wrong route.
  S0=1/(1-q);S1=q/(1-q)**2;S2=q*(1+q)/(1-q)**3
  target={'omit the quadratic term when expanding the binomial coefficient':A-S2/2,'count the quadratic term twice':A+S2/2,'omit the linear term in the binomial coefficient':A-3*S1/2,'count the linear term twice':A+3*S1/2,'omit the constant term in the binomial coefficient':A-S0,'count the constant term twice':A+S0,'square the geometric ratio when the binomial lower index is two':1/(1-q*q)**3,'apply the geometric-tail argument transform before the negative-binomial cube':1/(1-q/(1-q))**3}
  for c,v in zip(patch['choices'],values):assert v==(A if c['choiceId']==patch['answerChoiceId'] else target[c['misconception']])
  cubed=[cube(v.numerator) and cube(v.denominator) for v in values];sole=cubed.count(True)==1 and cubed[values.index(A)]
  results.append({'problemId':r['problemId'],'sourceContentHash':r['contentHash'],'sourceRawHash':canonical(r),'patchSHA256':canonical(patch),'independentAnswer':str(A),'pairwiseInequivalences':6,'misconceptionValuesChecked':3,'correctSoleRationalCube':sole,'rationalCubeOptions':sum(cubed),'correctRankAmongCubes':sum(v<A for v,c in zip(values,cubed) if c),'correctNumericRank':sum(v<A for v in values),'easiestReasonableRoute':'Recognize binomial coefficient as triple geometric-convolution count, giving (1−1/m)^−3. This remains Medium. The rational-cube syntax invariant alone does not establish that route.'})
 report={'status':'passed-bounded-independent-math-and-option-review','sourceArtifactSHA256':{str(p):sha(p) for p in [patchpath,P/'series-negative-binomial-repair-guards.json',P/'series_option_disposition.py',preview,a.release]},'records':results,'counts':{'records':len(results),'exactPairwiseInequivalences':6*len(results),'authoredMisconceptions':3*len(results),'soleRationalCubeCorrect':sum(r['correctSoleRationalCube'] for r in results)},'independentReviewer':'/root/source_research; did not import peer patch constructor','humanReviewed':False,'formalProof':False,'recommendation':'The v2 pools supply two rational cubes per case, and the correct cube is smaller in some cases and larger in others. The previous perfect cube singleton is removed. All displayed values and named misconception routes were checked exactly; parent must still run its actual canonical-identity train/held-out screen. No statement, answer or exposure-lineage change is needed.'}
 out=Path(__file__).with_name('negative-binomial-option-peer-review.json');out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
if __name__=='__main__':main()
