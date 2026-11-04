"""Independent finite random-level calculation and literal-choice enclosures."""
from pathlib import Path
import functools,hashlib,itertools,json,re,sys
import sympy as s
import mpmath as mp
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application
mp.mp.dps=55

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def parse(tex):
 v=tex.replace(r'\left','').replace(r'\right','').replace(r'\pi',' pi ').replace(r'\sqrt{2}',' sqrt(2) ')
 while r'\frac' in v:
  nv=re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}',r'((\1)/(\2))',v)
  assert nv!=v,tex;v=nv
 assert re.fullmatch(r'[0-9\sEpisqrt()+*/.\-]+',v),tex
 return parse_expr(v,local_dict={'pi':s.pi,'sqrt':s.sqrt,'E':s.elliptic_e},transformations=standard_transformations+(implicit_multiplication_application,))
@functools.lru_cache(None)
def elliptic_enclosure(param):
 p=mp.mpf(str(s.N(param,54)));N=8192;step=mp.pi/(2*N);mid=sum(mp.sqrt(1-p*mp.sin(i*step)**2) for i in range(1,N));last=mp.sqrt(1-p)
 # Integrand decreases on this interval: left/right Riemann sums enclose it.
 return step*(mid+last)-mp.mpf('1e-45'),step*(mid+1)+mp.mpf('1e-45')
def enclosure(v):
 e=list(v.atoms(s.elliptic_e));assert len(e)==1
 coefficient=s.cancel(v/e[0]);assert coefficient>0
 c=mp.mpf(str(s.N(coefficient,54)));lo,hi=elliptic_enclosure(e[0].args[0]);return c*lo-mp.mpf('1e-40'),c*hi+mp.mpf('1e-40')
def main(path,out):
 data=Path(path).read_bytes();rows=list(map(json.loads,data.splitlines()));results=[]
 for r in rows:
  k=s.Integer(r['parameters']['k']);assert 2<=k<=11
  assert 'C\\cos('+str(k)+'y)+D\\sin('+str(k)+'y)' in r['statement']
  answer=2*s.sqrt(2)*s.pi*k*s.elliptic_e(1-1/k**2)
  choices=[parse(c['math']) for c in r['choices']];matches=[i for i,v in enumerate(choices) if s.simplify(v-answer)==0]
  assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
  bounds=[enclosure(v) for v in choices]
  for a,b in itertools.combinations(bounds,2):assert a[1]<b[0] or b[1]<a[0]
  rank=sum(b[1]<bounds[matches[0]][0] for b in bounds)
  results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'contentHash':r['contentHash'],'independentAnswer':s.srepr(answer),'literalChoicesParsed':True,'choiceEnclosures':[[mp.nstr(z,25) for z in b] for b in bounds],'sixPairsDisjoint':True,'correctAscendingRank':rank,'passed':True})
 report={'reviewer':'root-independent-review','author':'integration_research','inputSha256':hashlib.sha256(data).hexdigest(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(rows),'passed':len(results),'results':results,'analyticReview':['Before reading the author proof, independently derive VarF=2 and independent gradient variances1,k². The density at zero is1/(2sqrt(pi)); polar Gaussian coordinates give E|gradient|=sqrt(2/pi)kE(1−1/k²). Multiply by square area4pi².','Independent Rayleigh amplitudes are positive and unequal almost surely, so zero is a regular value on the periodic torus. Coordinate-projection intersection counts bound every regular-level length by4pi(k+1). Coarea band averages converge and remain bounded, justifying dominated convergence and expectation exchange.','The literal choices use the defined elliptic parameter. Monotone left/right8192-part Riemann sums certify separation of all six choice pairs;55-digit arithmetic has explicit padding, but this is not a formal interval-arithmetic proof. No author constructor or answer field used as an oracle.'],'optionsVisibleDifficulty':'Olympiad: deriving the expectation requires random-level regularity, an integrable geometric bound, Gaussian independence and anisotropic angular integration. The standard Kac–Rice shortcut is valid when its hypotheses are verified.','nearestNeighbor':'Cone-probability questions integrate a fixed angular region; this requires expected curve length via coarea. k changes the dimensionless gradient anisotropy, not a scalar multiplier.','scope':'Mathematics only; known spacing/critical-value wording fixes and final canonical option screen remain separate admission gates. AI review, not human certification.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['results','analyticReview']}))
if __name__=='__main__':main(*sys.argv[1:])
