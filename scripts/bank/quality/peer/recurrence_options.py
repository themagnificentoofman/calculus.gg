"""Independent integer recurrence, convergence, choice routes and visible shortcut."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,itertools,json,math,re,sys
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def main(source,originals,presentations,output):
 source,originals,presentations,output=map(Path,[source,originals,presentations,output]);assert not output.exists()
 old={r['problemId']:r for r in map(json.loads,originals.read_text().splitlines())};visible=json.loads(presentations.read_text());records=[]
 for r in map(json.loads,source.read_text().splitlines()):
  match=re.fullmatch(r'a_0=0,\\quad a_\{n\+1\}=\\sqrt\{(\d+)\+a_n\}\.\\quad\\lim a_n=\?',r['statement']);assert match
  C=int(match[1]);d=math.isqrt(1+4*C);assert d*d==1+4*C;m=Q(1+d,2);assert m.denominator==1 and m>1
  assert (m-1)**2<C<m*m and m*(m-1)==C
  routes={'correct':m,'Take the absolute value of the negative fixed-point root.':Q(d-1,2),
   'Omit division by two in the positive quadratic root.':1+d,
   'Return the square root of the discriminant without the final addition and division.':d,
   'Return the radicand constant instead of solving the fixed-point equation.':C,
   'Treat the initial value as the limiting value without applying the recurrence.':0,
   'Divide the positive quadratic root by two a second time.':Q(1+d,4),
   'Divide the magnitude of the negative quadratic root by two a second time.':Q(d-1,4)}
  values=[Q(c['math'])for c in r['choices']];assert all(v.denominator==1 for v in values)and len(set(values))==4
  for c,v in zip(r['choices'],values):assert v==routes[c['misconception']]
  survivors=[c['choiceId']for c,v in zip(r['choices'],values)if v>0 and v*v>C and(v<1 or(v-1)**2<C)]
  assert survivors==[r['answerChoiceId']]and r['difficulty']=='medium'
  original=old[r['sourcePreview']['problemId']];assert digest(original)==r['sourcePreview']['canonicalRawHash'];assert r['statement']==original['statement']
  steps=visible[original['problemId']]['steps']if original['problemId']in visible else original['solutionSteps']
  assert r['solutionSteps']==steps and Q(steps[-1])==m
  records.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':digest(r),'independentAnswer':str(m),'constant':C,
   'sourcePreview':r['sourcePreview'],'literalPairDifferences':[str(a-b)for a,b in itertools.combinations(values,2)],
   'domainAndConvergence':'For u in[0,m], g(u)=sqrt(C+u) is increasing and maps the interval into itself. Since a1>a0, monotonicity of g gives increasing bounded iterates. Continuity gives L²-L-C=0 and positivity chooses m.',
   'optionsVisibleRoute':'Let B=sqrt(C)+1. B²-(C+B)=sqrt(C)>0, so[0,B] is invariant with a uniform strict upper bound g(B)<B. The limit exceeds a1=sqrt(C). The open unit interval(sqrt(C),sqrt(C)+1) contains exactly the integer m, which is the only displayed survivor.',
   'recommendedDifficulty':'medium','qualifiedOlympiad':False,'presentationInherited':True,'passed':True})
 assert len(records)==10
 output.write_text(json.dumps({'inputSha256':sha(source),'originalsSha256':sha(originals),'presentationsSha256':sha(presentations),'reviewerCodeSha256':sha(Path(__file__)),
  'author':'limits_final_repair','reviewer':'root','records':records,'instances':10,'literalPairs':60,'scope':'Independent complete finite elementary convergence/answer/option review; exact source and current presentation preserved. Medium is editorial, not player calibration.'},indent=2)+'\n');print(json.dumps({'passed':10,'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
