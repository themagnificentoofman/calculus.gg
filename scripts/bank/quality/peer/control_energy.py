"""Independent endpoint-kernel projection and literal-option checks."""
from pathlib import Path
import hashlib,itertools,json,sys
import sympy as s
from literal_choices import parse,same,distinct
from rational_intervals import certificate

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def main(path,out):
 data=Path(path).read_bytes();rows=[r for r in map(json.loads,data.splitlines()) if r['familyId'].endswith('oscillator-minimum-control-energy')];results=[]
 for r in rows:
  w=s.Integer(r['parameters']['w']);q=s.Rational(r['parameters']['q']);T=s.pi/(q*w);t=s.symbols('t',real=True)
  h1=s.sin(w*(T-t))/w;h2=s.cos(w*(T-t));A=s.integrate(h1*h1,(t,0,T));B=s.integrate(h2*h2,(t,0,T));C=s.integrate(h1*h2,(t,0,T));D=s.simplify(A*B-C*C)
  answer=s.simplify(B/D);alpha=s.simplify(B/D);beta=s.simplify(-C/D)
  assert s.simplify(alpha*A+beta*C)==1 and s.simplify(alpha*C+beta*B)==0
  assert s.simplify(alpha*alpha*A+2*alpha*beta*C+beta*beta*B-answer)==0
  values=[parse(c['math']) for c in r['choices']];matches=[j for j,v in enumerate(values) if same(v,answer)]
  assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
  assert all(distinct(a,b) for a,b in itertools.combinations(values,2))
  trial=3*(t/T)**2-2*(t/T)**3;forcing=s.diff(trial,t,2)+w*w*trial;upper=s.integrate(s.expand(forcing*forcing),(t,0,T));lower=1/A
  certificates=[{'choiceId':r['choices'][j]['choiceId'],'choiceMinusLower':certificate(v-lower),'upperMinusChoice':certificate(upper-v)} for j,v in enumerate(values)]
  assert all(c[k]['sign']!='unresolved' for c in certificates for k in ['choiceMinusLower','upperMinusChoice'])
  surviving=[c['choiceId'] for c in certificates if c['choiceMinusLower']['sign']!='negative' and c['upperMinusChoice']['sign']!='negative']
  demoted=surviving==[r['answerChoiceId']]
  results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'sourceContentHash':r['contentHash'],'independentAnswer':s.srepr(answer),'sixLiteralChoicePairsDistinct':True,'kernelNorms':list(map(s.srepr,[A,B,C])),'elementarySingleConstraintLowerAndCubicTrialUpper':[str(s.N(lower,20)),str(s.N(upper,20))],'exactRationalBoundCertificates':certificates,'choicesSurvivingThoseBounds':surviving,'correctChoiceId':r['answerChoiceId'],'recommendedDifficulty':'hard' if demoted else 'olympiad','qualifiedOlympiad':not demoted,'passed':True})
 report={'reviewer':'root-independent-review','author':'integration_research','inputSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parserSha256':hashlib.sha256(Path(__file__).with_name('literal_choices.py').read_bytes()).hexdigest(),'intervalVerifierSha256':hashlib.sha256(Path(__file__).with_name('rational_intervals.py').read_bytes()).hexdigest(),'instances':len(rows),'passed':len(results),'results':results,'analyticReview':'Duhamel gives two independent continuous endpoint kernels in L2. Their Gram matrix is positive definite because sine and cosine are linearly independent on a positive interval. The solved kernel combination meets both constraints. Every other admissible forcing differs by a function orthogonal to both kernels, so Pythagoras proves the global minimum and attainment. No author constructor imported. Cauchy-Schwarz gives 1/A as a lower bound; the feasible cubic trajectory gives an upper bound. Every literal choice is compared using exact rational interval arithmetic, Machin pi enclosures and integer-root radical enclosures. Indices4,6,9 are Hard because these elementary bounds isolate the correct option.','scope':'All finite endpoint constraints, norm answers, literal options and elementary-bound difficulty dispositions independently checked. Uniform final display overlay is included; final-ID pool form screen remains required. AI review, not human certification.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'instances':len(rows),'passed':len(results),'boundsIsolateCorrect':[r['index'] for r in results if r['choicesSurvivingThoseBounds']==[r['correctChoiceId']]]}))
if __name__=='__main__':main(*sys.argv[1:])
