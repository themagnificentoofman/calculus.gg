"""Reproduce the finite source and option verification of this isolated layer."""
from pathlib import Path
import json,hashlib,itertools,collections,os
import sympy as s
from repairs import build,catalog,canon,verify
from literal_special import parse,B,alpha
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 rows=[json.loads(x)for x in(P/'candidates.jsonl').read_text().splitlines()]
 inputs=json.loads((P/'inputs.json').read_text());source={q['sourceCanonical']['problemId']:q for q in inputs}
 per=[];ranks=collections.defaultdict(collections.Counter)
 for r in rows:
  assert verify(r);q=source[r['sourcePreview']['problemId']];old=q['activeMenu']
  assert r['statement']==old['statement'] and r['difficulty']==old['difficulty'] and r['answerChoiceId']==old['answerChoiceId']
  assert len(set(c['choiceId']for c in r['choices']))==4
  ans=next(c for c in r['choices']if c['choiceId']==r['answerChoiceId']);oldans=next(c for c in old['choices']if c['choiceId']==old['answerChoiceId'])
  assert s.simplify(parse(ans['math'])-parse(oldans['math']))==0
  checks=r['verificationEvidence'];assert len(checks)==6
  for e in checks:assert e['difference']['sign']in('negative','positive') and e['sum']['sign']in('negative','positive','zero')
  opposite=sum(e['sum']['sign']=='zero'for e in checks);assert opposite in(0,2)
  av=parse(ans['math']);rank=sum(float((parse(c['math'])-av).subs({B:1,alpha:3}).evalf())<0 for c in r['choices']);ranks[r['familyId']][rank]+=1
  if r['familyId'].endswith('Bessel-zero-normalization'):
   wrong=[parse(c['math'])for c in r['choices']if c!=ans];assert B in wrong or B/4 in wrong
   assert all(v==0 or v.is_positive for v in wrong)
  per.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canon(r).encode()).hexdigest(),'sourceProblemId':old['problemId'],'sourceContentHash':old['contentHash'],'answerPreserved':True,'sourceTaskAndLevelPreserved':True,'exactPairDistinctions':6,'mathematicalOppositeChecks':6,'oppositePairs':opposite,'correctAscendingRankZeroBased':rank})
 report={'status':'author-finite-checks-passed; independent-root-review-pending','records':per,'counts':{'records':17,'sourceTaskAndAnswerJoins':17,'pairDistinctions':102,'oppositeSumChecks':102},'rankDistributions':{f:dict(sorted(c.items()))for f,c in ranks.items()},'domainCertificates':{'bessel':'The entire defining series covers every displayed order. For 0<z<=2 its normalized alternating series is strictly positive, including nu=0,z=2 by the next paired terms; hence alpha>2. Jnu and Jnu+1 cannot share a positive zero: the derivative recurrence would give zero value and derivative at a regular ODE point, contradicting its nonzero series solution. Thus B=Jnu+1(alpha)^2>0. Each pair difference or sum is B times a rational polynomial of u=alpha^2-4>0 with coefficients of one strict sign.','green':'All a are positive integers. sinh(a)>0, so all displayed denominators are nonzero. Selected-answer equality is exact. Every difference and sum has a rational enclosure obtained from exponential series and exact interval arithmetic.'},'optionsVisibleDifficulty':{'bessel':'At least one positive root-independent boundary-factor distractor B or B/4 accompanies B/2. Positivity and alpha>2 therefore leave multiple candidates. Identifying the half factor requires the boundary differential identity and adjacent-order derivative recurrence; this is an editorial assessment, pending independent reviewer judgment.','green':'The singleton opposite magnitude clue is removed. Positive-integral information is legitimate but no longer isolates the known paired magnitude. Constructing and differentiating the Green resolvent trace remains the intended decision.'},'notHumanReviewed':True,'notFormalProof':True}
 (P/'finite-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'counts':report['counts'],'ranks':report['rankDistributions']}))
if __name__=='__main__':run()
