"""Bound the immutable Gamma/PV option-repair draft; no app writes."""
from pathlib import Path
import argparse,json,hashlib,itertools
import sympy as s

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--baseline',type=Path,default=Path(__file__).with_name('integration-olympiad-baseline.jsonl'));ap.add_argument('--out',type=Path,default=Path(__file__).with_name('integration-option-peer-v1.json'));a=ap.parse_args()
 rows=list(map(json.loads,a.input.read_text().splitlines()));old={r['problemId']:r for r in map(json.loads,a.baseline.read_text().splitlines())};reports=[]
 for r in rows:
  src=old[r['previous']['problemId']];assert src['contentHash']==r['previous']['sourceContentHash'];p=src['provenance']['authoring']['builderParameters'];vals=[s.sympify(c['expression']) for c in r['choices']];i=r['instanceIndex'];notes=[]
  if r['familyId']=='io3-gamma-unit-average':
   aa=s.Rational(*p['a']);target=aa*s.log(aa)-aa+s.log(2*s.pi)/2
   assert s.simplify(s.expand_log(vals[0]-target,force=True))==0
   assert all(s.simplify(s.expand_log(u-v,force=True)).equals(0) is False for u,v in itertools.combinations(vals,2))
   if i in [2,6]:notes.append('The moment-monotonicity/log-convexity interval isolates the current answer; revise options or classify this instance below Olympiad.')
  else:
   pp,qq=p['p'],p['q'];rr=s.Rational(pp,qq);assert s.Rational(1,4)<rr<s.Rational(1,2)
   assert vals[0][0]==s.Symbol('divergent') and s.simplify(vals[0][1]-s.pi/qq*s.cot(s.pi*rr))==0
   assert len({(str(v[0]),str(v[1])) for v in vals})==4
   # Acute theta distinct from pi/4 proves cot != tan without numerical equality tests.
   notes.append('All r=p/q lie in(1/4,1/2). The transformed integral lies strictly between0 andpi/q, excluding every tan alternative after ordinary divergence is established. The old length tell is repaired, but this bound shortcut remains.')
  lengths=[len(c['math']) for c in r['choices']];reports.append({'problemId':src['problemId'],'sourceContentHash':src['contentHash'],'familyId':r['familyId'],'instanceIndex':i,'rawSHA256':hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'exactAnswerAndFourInequivalentChoices':True,'formatLengths':lengths,'correctUniquelyShortest':lengths[0]<min(lengths[1:]),'correctUniquelyLongest':lengths[0]>max(lengths[1:]),'findings':notes,'passedUnconditionally':not notes})
 # Independent exact transformed PV endpoint at r=1/4.
 u=s.symbols('u',positive=True);assert s.cancel(4*(1-u*u)/(1-u**4)-4/(1+u*u))==0
 assert s.integrate(4/(1+u*u),(u,0,1))==s.pi
 # Rational exp bounds and elementary 3.14<pi<22/7 verify the two Gamma interval screens.
 certificates=[]
 for aa in [2,4]:
  N=80;t=2*aa;elo=sum(s.Rational(t)**j/s.factorial(j) for j in range(N));ehi=elo+s.Rational(t)**N/s.factorial(N)/(1-s.Rational(t,N+1));plo=s.Rational(157,50);phi=s.Rational(22,7);factor=s.Integer(aa)**(2*aa)
  lower=s.factorial(aa-1)**2;upper=s.factorial(aa-1)*s.factorial(aa)
  assert 2*plo*factor>lower*ehi and 2*phi*factor<upper*elo
  assert 4*plo*factor>upper*ehi and plo*plo*factor>upper*ehi and 2/plo*factor<lower*elo
  certificates.append({'a':aa,'lowerLogBound':'ln('+str(s.factorial(aa-1))+')','upperLogBound':'one half ln('+str(upper)+')','exactIntervalCertificate':'After exponentiation, the correct normalization lies inside and all selected wrong normalizations lie outside. Verified using rational Taylor bounds for exp(2a) and157/50<pi<22/7.'})
 report={'status':'changes-needed','reviewId':'integration-options-independent-v1','inputSHA256':hashlib.sha256(a.input.read_bytes()).hexdigest(),'codeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':reports,'GammaBoundCertificates':certificates,'PVBoundCertificate':'For0<t<1, the numerator t^(r-1)-t^(-r) decreases strictly withr. At r=1/2 it is zero; at r=1/4 the substitutiont=u^4 gives4/(1+u²), whose integral ispi. All current p/q are strictly between these endpoints.','reviewType':'Independent mathematical/editorial check of parent-authored repairs; no human or formal review','productionWrites':0}
 a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'records':len(rows),'exactChoiceChecksPassed':len(rows),'status':report['status']}))
if __name__=='__main__':main()
