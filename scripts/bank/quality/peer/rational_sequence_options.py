"""Independent literal limits and misconception values for ten common-form menus."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,re,sys
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def power(tex):
 m=re.fullmatch(r'\\left\(\\frac\{(\d+)\}\{(\d+)\}\\right\)\^\{(\d+)\}',tex)
 assert m,tex
 a,b,n=map(int,m.groups());assert a>0 and b>0 and n>0
 return Q(a,b)**n
def fraction(tex):
 m=re.fullmatch(r'\\frac\{(\d+)\}\{(\d+)\}',tex)
 return Q(*map(int,m.groups()))if m else Q(tex)
def main(source,prior,output):
 source,prior,output=map(Path,[source,prior,output])
 if output.exists():raise ValueError('Preserve prior peer report')
 old={r['problemId']:r for r in map(json.loads,prior.read_text().splitlines())};records=[]
 for r in map(json.loads,source.read_text().splitlines()):
  m=re.fullmatch(r'\\lim_\{n\\to\\infty\}\\left\(\\frac\{(\d+)n\+(\d+)\}\{(\d+)n\+(\d+)\}\\right\)\^\{(\d+)\}',r['statement']);assert m
  a,b,c,d,n=map(int,m.groups());assert min(a,b,c,d,n)>0
  expected=Q(a,c)**n
  routes={
   'correct':expected,
   'Invert the limiting leading-coefficient ratio.':Q(c,a)**n,
   'Use the constant terms instead of the leading coefficients.':Q(b,d)**n,
   'Evaluate the sequence at n=1 instead of taking its limit.':Q(a+b,c+d)**n,
   'Invert the sequence value at n=1 instead of taking the limit.':Q(c+d,a+b)**n,
   'Combine the denominator constant with its coefficient of n before taking the limit.':Q(a,c+d)**n,
  }
  values=[power(q['math'])for q in r['choices']]
  assert len(set(values))==4 and len(set(len(q['math'])for q in r['choices']))==1
  for q,v in zip(r['choices'],values):assert v==routes[q['misconception']]
  assert next(v for q,v in zip(r['choices'],values)if q['choiceId']==r['answerChoiceId'])==expected
  original=old[r['sourcePreview']['problemId']]
  assert digest(original)==r['sourcePreview']['canonicalRawHash'] and original['contentHash']==r['sourcePreview']['sourceContentHash']
  assert original['statement']==r['statement'] and original['solutionSteps'][:-1]==r['solutionSteps'][:-1]
  assert fraction(original['solutionSteps'][-1])==power(r['solutionSteps'][-1])==expected
  records.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':digest(r),
   'sourcePreview':r['sourcePreview'],'independentAnswer':str(expected),
   'literalStatementData':{'leadingNumerator':a,'constantNumerator':b,'leadingDenominator':c,'constantDenominator':d,'power':n},
   'derivation':'Divide numerator and denominator by n. Positive c makes every positive-index denominator nonzero and the limiting denominator nonzero; continuity of the fixed positive integer power yields(a/c)^power.',
   'sixLiteralPairDifferences':[str(values[i]-values[j])for i,j in itertools.combinations(range(4),2)],
   'namedMistakesIndependentlyMatched':3,'equalLiteralChoiceLengths':True,'equivalentConclusionAndEarlierDerivationPreserved':True,
   'recommendedDifficulty':'easy','qualifiedOlympiad':False,'newIndependentIdeas':0,'passed':True})
 assert len(records)==10
 output.write_text(json.dumps({'author':'limits_final_repair','reviewer':'root','inputSha256':sha(source),'priorSourceSha256':sha(prior),'reviewerCodeSha256':sha(Path(__file__)),
  'instances':10,'literalPairs':60,'records':records,'scope':'Independent exact literal finite limits, all misconception routes and conclusion identity. Final actual-ID/served family screen and admission remain separate; no human or formal certification.'},indent=2)+'\n')
 print(json.dumps({'passed':10,'literalPairs':60,'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
