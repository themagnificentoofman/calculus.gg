"""Record independent statement-first solutions; disclosed prior Hilbert-method context."""
from pathlib import Path
import argparse,json,re,hashlib
import sympy as s

def clean(t):return re.sub(r'\s+','',t.replace('\\ ',''))
def tex(e):return clean(s.latex(s.simplify(s.expand_func(e))))
def rational(t):
 t=clean(t);m=re.fullmatch(r'\\frac\{(-?\d+)\}\{(\d+)\}',t)
 if m:return s.Rational(int(m[1]),int(m[2]))
 assert re.fullmatch(r'-?\d+',t),t;return s.Integer(t)
def pair(t):
 t=clean(t).replace(r'\left(', '').replace(r'\right)', '');a,b=t.split(',',1);return rational(a),rational(b)
def raw(r):return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();records=[]
 for r in map(json.loads,(a.source_dir/'moment-candidates.jsonl').read_text().splitlines()):
  mass=s.Rational(r['parameters']['mass']);b=s.Rational(r['parameters']['firstMoment']);l=b/mass-mass/2;rr=l+mass;u=(mass-mass**2/2-b)/(1-mass);v=u+1-mass;minimum=(rr**3-l**3)/3;maximum=(u**3+1-v**3)/3;matches=[c['choiceId'] for c in r['choices'] if pair(c['math'])==(minimum,maximum)];assert len(matches)==1
  records.append({'problemId':r['problemId'],'rawSHA256':raw(r),'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'independentAnswer':[str(minimum),str(maximum)],'matchingDisplayedChoice':matches[0],'minimizerInterval':[str(l),str(rr)],'maximizerOuterEndpoints':[str(u),str(v)],'route':'Use the mass and first moment to locate one filled interval for the minimum and two endpoint intervals for the maximum. Quadratic sign certificates annihilate the two constraint terms and prove both extrema globally.'})
 for r in map(json.loads,(a.source_dir/'hilbert-candidates.jsonl').read_text().splitlines()):
  p=s.Rational(r['parameters']['shape']);C=s.simplify(s.expand_func(s.gamma(p/2)**2/s.gamma(p)));target=r'\left('+tex(C)+r',\textnormal{no}\right)';matches=[c['choiceId'] for c in r['choices'] if clean(c['math'])==target];assert len(matches)==1,(p,target)
  records.append({'problemId':r['problemId'],'rawSHA256':raw(r),'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'independentAnswer':[s.srepr(C),'no'],'matchingDisplayedChoice':matches[0],'route':'With x=exp(u) and g(u)=exp(u/2)f(exp(u)), the quadratic form becomes convolution with k(t)=(2cosh(t/2))^(−p). Its integral is Beta(p/2,p/2). Cauchy-Schwarz bounds each translation correlation; normalized long interval indicators give sharpness. Equality would force a nonzero L2 function to be invariant under a nonzero translation, impossible.'})
 out={'disclosure':'Statements and actual choices inspected before supplied solutionSteps or analyticCertificate. The parent already disclosed the intended Hilbert Mellin/Schur method, so this is not blind to the central technique. No author constructor or answer field was used in these first solves.','records':records};a.out.write_text(json.dumps(out,indent=2)+'\n');print('recorded independent first solves',len(records))
if __name__=='__main__':main()
