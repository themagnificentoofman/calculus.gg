"""Independent triangular-flow norm, literal choices and options-visible bounds."""
from pathlib import Path
import hashlib,itertools,json,re,sys
import sympy as s
from differentiation_literal_choices import parse
from limits_intervals import enclose
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(v):
 lo,hi=enclose(s.simplify(v).rewrite(s.exp));return {'lower':str(lo),'upper':str(hi)},lo,hi
def main(source,output):
 source,output=Path(source),Path(output)
 if output.exists():raise ValueError('Preserve previous review')
 K,t=s.symbols('K t',positive=True)
 M=s.Matrix([[1,K*t],[0,1]])
 G=M.T*M;v=(s.sqrt(4+K*K*t*t)+K*t)/2
 assert s.simplify(G.det()-1)==0
 assert s.simplify(v*v+v**-2-s.trace(G))==0
 lograte=s.simplify(s.diff(s.log(s.exp(-t)*v),t))
 assert s.simplify(lograte-(-1+K/s.sqrt(4+K*K*t*t)))==0
 assert s.simplify(s.diff(lograte,t)+K**3*t/(4+K*K*t*t)**s.Rational(3,2))==0
 records=[];blockers=[]
 for r in map(json.loads,source.read_text().splitlines()):
  m=re.search(r'\\begin\{pmatrix\}-1&(.*?)\\\\0&-1\\end\{pmatrix\}',r['statement']);assert m
  k=parse(m[1]);assert k>2
  d=s.sqrt(k*k-4);time=d/k;big=(k+d)/2;small=(k-d)/2;expected=big*s.exp(-time)
  values=[parse(c['math'])for c in r['choices']]
  routes={'correct':expected,'growth':big*s.exp(time),'small':small*s.exp(-time),'small-growth':small*s.exp(time),
   'reciprocal-time':big*s.exp(-1/time),'reciprocal-growth':big*s.exp(1/time),
   'small-reciprocal-time':small*s.exp(-1/time),'small-reciprocal-growth':small*s.exp(1/time),
   'decay-time-one':(k+s.sqrt(k*k+4))/(2*s.E),
   'reciprocal-norm':(k/time+s.sqrt(k*k/time**2+4))*s.exp(-1/time)/2,
   'reciprocal-growth-norm':(k/time+s.sqrt(k*k/time**2+4))*s.exp(1/time)/2}
  for c,value in zip(r['choices'],values):assert s.simplify(value-routes[c['namedRoute']])==0,(r['instanceIndex'],c)
  assert s.simplify(next(v for c,v in zip(r['choices'],values)if c['choiceId']==r['answerChoiceId'])-expected)==0
  if r['instanceIndex']in[2,5,8]:assert r['difficulty']=='hard'
  else:
   assert 'decay-time-one'in[c['namedRoute']for c in r['choices']]
   _,dl,dh=bounds(expected-routes['decay-time-one']);assert dl>0
  pair_certificates=[]
  for i,j in itertools.combinations(range(4),2):
   cert,lo,hi=bounds(values[i]-values[j]);assert lo>0 or hi<0
   pair_certificates.append({'choiceIds':[r['choices'][i]['choiceId'],r['choices'][j]['choiceId']],**cert})
  # Test the actual options using a fixed vector at t=1 and a triangle bound.
  lower=s.sqrt(1+k*k)/s.E;upper=k*s.exp(-1+1/k)
  comparisons=[];survivors=[]
  for c,value in zip(r['choices'],values):
   low,ll,lh=bounds(value-lower);high,ul,uh=bounds(value-upper)
   excluded=lh<0 or ul>0
   if not excluded:survivors.append(c['choiceId'])
   comparisons.append({'choiceId':c['choiceId'],'minusLower':low,'minusUpper':high,'excluded':excluded})
  isolated=survivors==[r['answerChoiceId']]
  if isolated and r['difficulty']=='olympiad':blockers.append({'familyId':r['familyId'],'index':r['instanceIndex'],'reason':'The column lower bound and triangle-norm upper bound isolate the literal answer; classify at Hard or repair choices and independently reassess.'})
  records.append({'familyId':r['familyId'],'index':r['instanceIndex'],'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),
   'independentAnswer':str(expected),'criticalTime':str(time),'literalPairs':pair_certificates,
   'domainArgument':'The shear K is positive and greater than2. Gram determinant1 and trace2+K²t² give the larger singular value. Its logarithmic derivative decreases from K/2−1>0 to−1, giving the unique global maximum at sqrt(K²−4)/K. A corresponding unit eigenvector attains it.',
   'optionsVisibleBounds':{'lower':str(lower),'upper':str(upper),'derivation':'At t=1 use the unit vector e2 to obtain sqrt(1+K²)/e. The triangle inequality gives ||I+KtN||≤1+Kt, whose exponentially damped maximum is K*exp(−1+1/K).','comparisons':comparisons,'survivingChoices':survivors,'isolatesCorrect':isolated},
   'mathematicsPassed':True,'passed':not(isolated and r['difficulty']=='olympiad')})
 assert len(records)==10
 output.write_text(json.dumps({'status':'mathematics-passed-visible-options-blocked'if blockers else'independent-mathematics-and-visible-bounds-reviewed',
  'inputSha256':sha(source),'reviewer':'root','author':'ode_final_review','reviewSources':{p.name:sha(p)for p in [Path(__file__),Path(__file__).with_name('differentiation_literal_choices.py'),Path(__file__).with_name('limits_intervals.py'),Path(__file__).with_name('series_intervals.py'),Path(__file__).with_name('rational_intervals.py')]},
  'instances':10,'literalPairs':60,'records':records,'classificationBlockers':blockers,
  'scope':'Independent finite norm/optimization and literal-option review, including the actual norm at time1 and actual norm at reciprocal critical time. Seven advanced menus survive the elementary L/U bound; three prior Hard ceilings remain. This is editorial review, not player calibration.'},indent=2)+'\n')
 print(json.dumps({'mathematicsPassed':len(records),'literalPairs':60,'classificationBlockers':len(blockers),'reportSha256':sha(output)}))
if __name__=='__main__':main(*sys.argv[1:])
