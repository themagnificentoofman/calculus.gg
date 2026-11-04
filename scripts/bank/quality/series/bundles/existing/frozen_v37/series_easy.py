"""Five independent elementary series decisions; original finite authored catalog.
No source imports, network access, unrestricted parsing, or model calls at runtime.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,re,textwrap
from pathlib import Path
import sympy as s
x=s.symbols('x',positive=True);R=s.Rational
FAMILIES={}
def L(a):return s.latex(s.sympify(a),fold_short_frac=False)
def T(a):return r'\textnormal{'+a+'}'
def H(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ck(name,a,b=0):
 d=s.simplify(a-b);assert d==0,(name,d);return {'name':name,'passed':True}
def require(name,truth):
 assert bool(truth),name
 return {'name':name,'passed':True}
def reg(slug,group,method,why,prereq=()):
 def dec(fn):
  fid='m3-series-easy-'+slug.lower()
  FAMILIES[fid]=dict(familyId=fid,topic='series',difficulty='easy',relatedIdeaGroupId=group,primaryTechnique=method,alternativeTechniques=[],reasoningDemand='recognition',difficultyRationale=why,prerequisites=list(prereq),sourceRecordIds=[],editorialStatus='admitted',build=fn)
  return fn
 return dec

def p_certificate(p,label):
 F=s.log(x) if p==1 else (x**(1-p)-1)/(1-p)
 I=s.limit(F,x,s.oo)
 checks=[ck(label+' integral primitive',s.diff(F,x),x**(-p)),ck(label+' primitive basepoint',F.subs(x,1)),require(label+' positive decreasing comparison function',s.diff(x**(-p),x).is_negative is True)]
 if p>1:checks.append(ck(label+' convergent improper integral',I,1/(p-1)))
 else:checks.append(require(label+' divergent improper integral',I==s.oo))
 return checks

def record(statement,answer,options,steps,checks,domain,analytic,shape,kind='categorical'):
 assert checks and all(c['passed'] for c in checks)
 return dict(statement=statement,answer=answer,options=options,solutionSteps=steps,automatedChecks=checks,domain=domain,analyticCertificate=analytic,structuralSignature=shape,answerForm='categorical-classification' if kind=='categorical' else 'exact-real',kind=kind)

def category_pair_options(first_word,second_word,expected):
 out=[]
 for a,b in itertools.product([first_word,second_word],repeat=2):
  code=a+'|'+b
  if code==expected:why='correct'
  elif first_word=='converges':why='Apply the positive p-series threshold to the wrong side of one'
  elif code=='absolute|absolute':why='Mistake alternating convergence for absolute convergence'
  elif code=='conditional|conditional':why='Stop at the alternating test despite a convergent absolute-value series'
  else:why='Reverse which absolute-value benchmark converges'
  out.append((code,r'\left('+T(a)+r',\ '+T(b)+r'\right)',why))
 return out

@reg('p-series-pair','positive-p-series-threshold','p-series-classification','Classifies positive power series on both sides of the exponent-one boundary, including the boundary itself.',('p-series test',))
def p_pair(m):
 pairs=[(R(1,2),R(1,3)),(1,2),(2,1),(R(3,2),R(5,2)),(R(3,4),1),(R(4,3),R(2,3)),(R(3,5),R(7,6)),(R(7,4),R(9,4))]
 p,q=map(s.sympify,pairs[int(m)-4]);a='converges' if p>1 else 'diverges';b='converges' if q>1 else 'diverges'
 return record(r'A=\sum_{n=1}^\infty\frac1{n^{'+L(p)+r'}},\qquad B=\sum_{n=1}^\infty\frac1{n^{'+L(q)+r'}}.\quad'+T('Choose the ordered classification (A,B).'),a+'|'+b,category_pair_options('converges','diverges',a+'|'+b),[T('A positive p-series converges exactly when its exponent exceeds one.'),r'p_A='+L(p)+r',\quad p_B='+L(q),T('A '+a+'; B '+b+'.')],p_certificate(p,'A')+p_certificate(q,'B'),['Both displayed series start at n=1 and have positive real terms.'],['For p>0, t^-p is positive and decreasing on [1,infinity), so the integral comparison gives convergence exactly when its integral is finite. The displayed antiderivative and improper limit are checked separately for each exponent, including the logarithmic p=1 boundary.'],'paired-positive-p-series-threshold')

@reg('alternating-absolute-conditional','alternating-versus-absolute-convergence','alternating-test-and-absolute-values','Distinguishes absolute from conditional convergence after checking alternating-series hypotheses, rather than treating any sign alternation as absolute convergence.',('alternating series test','absolute convergence'))
def alternating_pair(m):
 pairs=[(R(1,2),1),(R(3,4),R(3,2)),(2,R(1,2)),(R(3,2),2),(1,R(3,4)),(R(3,5),R(7,5)),(R(9,5),1),(R(11,5),R(8,5))]
 p,q=map(s.sympify,pairs[int(m)-4]);a='absolute' if p>1 else 'conditional';b='absolute' if q>1 else 'conditional'
 checks=p_certificate(p,'absolute A')+p_certificate(q,'absolute B')+[ck('A alternating magnitude tends to zero',s.limit(x**(-p),x,s.oo)),ck('B alternating magnitude tends to zero',s.limit(x**(-q),x,s.oo))]
 return record(r'A=\sum_{n=1}^\infty\frac{(-1)^{n-1}}{n^{'+L(p)+r'}},\quad B=\sum_{n=1}^\infty\frac{(-1)^{n-1}}{n^{'+L(q)+r'}}.\quad'+T('Classify (A,B). Absolute means the sum of absolute values converges; conditional means the series converges but the sum of absolute values diverges.'),a+'|'+b,category_pair_options('absolute','conditional',a+'|'+b),[T('In both series the positive magnitudes decrease to zero, so the alternating-series test gives convergence.'),T('Taking absolute values gives positive p-series, which converge exactly for exponent greater than one.'),T('A is '+a+'; B is '+b+'.')],checks,['All exponents displayed are positive; each alternating series starts at n=1.'],['The positive-term derivatives and zero magnitude limits verify the alternating-test hypotheses. Integral comparison separately determines absolute convergence. If the positive comparison series diverges, the alternating series is therefore conditional; no unproved rearrangement is used.'],'alternating-powers-absolute-versus-conditional')

@reg('direct-comparison-information','direct-series-comparison-logical-strength','direct-comparison','Reads the direction of a nonnegative comparison and distinguishes a forced conclusion from insufficient information.',('comparison test',))
def comparison(m):
 i=int(m)-4;upper=i%4 in (0,2)
 p=m/8 if i%4==0 else m/16 if i%4==1 else m/4
 if upper and p>1:answer='forced-convergence'
 elif not upper and p<=1:answer='forced-divergence'
 else:answer='both-possible'
 bound=r'0\le a_n\le\frac1{n^{'+L(p)+r'}}' if upper else r'a_n\ge\frac1{n^{'+L(p)+r'}}'
 options=[('forced-convergence',T('Convergence is forced.'),'Use a convergent lower bound or a divergent upper bound to infer convergence'),('forced-divergence',T('Divergence is forced.'),'Use a divergent upper bound or a convergent lower bound to infer divergence'),('both-possible',T('Either behavior is possible.'),'Overlook a decisive nonnegative comparison'),('no-sequence',T('No such sequence exists.'),'Mistake a convergence conclusion for inconsistency of the term bounds')]
 checks=p_certificate(p,'benchmark');steps=[T('First classify the positive benchmark series using its exponent and then check the direction of the inequality.')]
 if answer=='forced-convergence':steps.append(T('A nonnegative series bounded above by a convergent series must converge.'))
 elif answer=='forced-divergence':steps.append(T('A series bounded below by a divergent positive series must diverge.'))
 elif upper:
  steps.extend([r'a_n=0'+T(' gives convergence.'),r'a_n=n^{-'+L(p)+r'}'+T(' satisfies the same bound and gives divergence.')])
 else:
  steps.extend([r'a_n=n^{-'+L(p)+r'}'+T(' gives convergence.'),r'a_n=1'+T(' satisfies the same bound and gives divergence.')])
 return record(T('A real sequence satisfies ')+bound+T(' for every integer n>=1. What follows about ')+r'\sum_{n=1}^\infty a_n'+T(' from this bound alone?'),answer,options,steps,checks,['All terms are nonnegative by the displayed bound; no other hypothesis is supplied.'],['For nonnegative series, bounded increasing partial sums imply convergence. An upper bound by a convergent benchmark bounds every partial sum; a lower bound by a divergent benchmark forces unbounded partial sums. For an upper bound with p<=1, zero and the benchmark give opposite behaviors. For a lower bound with p>1, the benchmark and the constant sequence one give opposite behaviors; n^-p<=1 for every n>=1. These witnesses establish insufficiency, not merely failure of one proof method.'],'comparison-direction-versus-insufficient-information')

def numeric_options(answer,pool,m,shape):
 a=s.sympify(answer);clean=[]
 for value,label in pool:
  value=s.sympify(value)
  if s.simplify(value-a)==0 or any(s.simplify(value-w)==0 for w,_ in clean):continue
  clean.append((value,label))
 buckets={}
 for triple in itertools.combinations(clean,3):
  rank=sum(bool(s.N(w,90)<s.N(a,90)) for w,_ in triple);buckets.setdefault(rank,[]).append(triple)
 ranks=sorted(buckets);i=int(m)-4;target=ranks[(i+int(H(shape)[:8],16))%len(ranks)];bucket=buckets[target];chosen=bucket[(i+int(H([shape,target])[8:16],16))%len(bucket)]
 vals=[a]+[v for v,_ in chosen]
 for u,v in itertools.combinations(vals,2):
  d=s.simplify(u-v);assert d.is_zero is False or d.equals(0) is False,'unresolved choice equivalence'
 return [(s.srepr(v),L(v),why,v) for v,why in [(a,'correct')]+list(chosen)]

@reg('Taylor-coefficient-derivative','power-series-coefficient-derivative','coefficient-to-derivative','Converts a coefficient in a convergent power series at a nonzero center into the corresponding derivative, retaining the factorial.',('Taylor coefficients',))
def Taylor_coefficient(m):
 n=int(m);c=(-1)**m*(m-3)/(m+2);ans=s.factorial(m)*c;shape='convergent-power-series-specified-coefficient-derivative';z=s.symbols('z');term=c*(z-2)**m
 pool=[(c,'return the coefficient without its factorial'),(m*c,'multiply by the order instead of its factorial'),(s.factorial(m-1)*c,'use the previous factorial'),(s.factorial(m+1)*c,'use the next factorial'),(s.factorial(m)**2*c,'apply the factorial conversion twice'),(-ans,'reverse the given coefficient sign'),((m+2)*ans,'omit the coefficient denominator')]
 checks=[ck('specified monomial derivative at center',s.diff(term,z,n).subs(z,2),ans)]
 for k in [0,1,n-1,n+1,n+2]:checks.append(ck('other power vanishes after evaluation k='+str(k),s.diff((z-2)**k,z,n).subs(z,2)))
 return record(r'f(x)=\sum_{k=0}^\infty a_k(x-2)^k'+T(' converges for |x-2|<1, and ')+r'a_{'+L(m)+r'}='+L(c)+r'.\quad f^{('+L(m)+r')}(2)=?',s.srepr(ans),numeric_options(ans,pool,m,shape),[r'a_n=\frac{f^{(n)}(2)}{n!}',r'f^{('+L(m)+r')}(2)='+L(s.factorial(m))+r'\left('+L(c)+r'\right)='+L(ans)],checks,['The power series has positive radius of convergence at center two, explicitly given as at least one.'],['Inside its interval of convergence a power series can be differentiated any finite number of times term by term. At the center, terms below order n have vanished by differentiation, terms above order n retain a positive power of x-2, and the order-n term contributes n factorial times its coefficient. The monomial checks verify this conversion without assuming values of unspecified coefficients.'],shape,'numeric')

@reg('linearity-given-convergent-sums','linearity-of-convergent-series','partial-sum-linearity','Uses linearity of convergent series from supplied sums; no formula for individual terms or assumption of absolute convergence is needed.',('limits of finite linear combinations',))
def linearity(m):
 A=m-2;B=m+1;u=s.Integer(2);v=-m;ans=-m*m+m-4;shape='linear-combination-of-two-given-convergent-series';aa=s.symbols('a0:4');bb=s.symbols('b0:4')
 pool=[(u*A-v*B,'reverse the subtraction sign'),(A+v*B,'omit the coefficient two'),(u*A+B,'omit the second coefficient'),(u*(A+B),'apply the first coefficient to both sums'),((u*A)*(v*B),'multiply the two contributions instead of adding'),(u*A+2*v*B,'apply the second coefficient twice'),(A+B,'omit both coefficients')]
 return record(T('The two real series converge, with ')+r'\sum_{n=1}^\infty a_n='+L(A)+r',\qquad\sum_{n=1}^\infty b_n='+L(B)+r'.\quad\sum_{n=1}^\infty(2a_n-'+L(m)+r'b_n)=?',s.srepr(ans),numeric_options(ans,pool,m,shape),[T('Take the same finite partial-sum endpoint in both series and distribute the coefficients.'),r'\sum_{n=1}^\infty(2a_n-'+L(m)+r'b_n)=2\left('+L(A)+r'\right)-'+L(m)+r'\left('+L(B)+r'\right)='+L(ans)],[ck('finite partial-sum linearity',sum(u*a+v*b for a,b in zip(aa,bb)),u*sum(aa)+v*sum(bb)),ck('given sums substituted into linear combination',u*A+v*B,ans)],['Both real series are explicitly assumed convergent; absolute convergence is not required.'],['For every finite N the linear-combination partial sum equals two times the first partial sum minus m times the second. Taking the limit preserves a finite linear combination because both component limits exist. This does not rearrange either series or multiply infinite series.'],shape,'numeric')

def display(statement):
 parts=re.split(r'(\\textnormal\{[^{}]*\}|\\quad\s*)',statement);lines=[]
 for p in parts:
  p=p.strip()
  if not p or p.startswith(r'\quad'):continue
  if p.startswith(r'\textnormal{') and p.endswith('}'):lines.extend(T(q) for q in textwrap.wrap(p[12:-1],width=30))
  else:lines.append(p)
 return statement if len(lines)<2 else r'\begin{gathered}'+r'\\'.join(lines)+r'\end{gathered}'
def catalog():return [{k:v for k,v in r.items() if k!='build'} for r in FAMILIES.values()]
def build(fid,index):
 if fid not in FAMILIES:raise ValueError('unknown family')
 if type(index) is not int or not 0<=index<8:raise ValueError('index must be integer0..7')
 meta=FAMILIES[fid];p=meta['build'](s.Integer(index+4));answer=p.pop('answer');options=p.pop('options');kind=p.pop('kind');choices=[]
 for opt in options:
  code,math=opt[:2];why='correct' if code==answer else opt[2]
  choices.append(dict(choiceId='ch_'+H(code)[:16],math=math,misconception=why))
 correct='ch_'+H(answer)[:16];assert sum(c['choiceId']==correct for c in choices)==1 and len(choices)==4 and len({c['choiceId'] for c in choices})==4
 turn=int(H([fid,index])[:8],16)%4;choices=choices[turn:]+choices[:turn]
 p['statement']=display(p['statement']);p['solutionSteps']=[display(q) for q in p['solutionSteps']]
 semantic=H({'familyId':fid,'parameter':index+4,'statement':p['statement']});r={k:v for k,v in meta.items() if k!='build'}
 r.update(p,schemaVersion=2,problemId='cn_m3_'+semantic[:20],problemRevision=1,parameters={'m':index+4},parameterDomain={'m':list(range(4,12))},semanticHash=semantic,choices=choices,answerChoiceId=correct,normalizedStructure=p['structuralSignature'],estimatedSolveSeconds=65,source={'kind':'independently-authored','thirdPartyProblemAdapted':False,'license':'LicenseRef-CalculusNinja-Original','attribution':'Original Calculus Ninja content, AI-assisted; analytic arguments and executed checks distinguished.'},validation={'status':'verified','route':'exact-antiderivative-and-limit-or-finite-algebraic-certificate','engine':'SymPy '+s.__version__,'humanReviewed':False,'formalProof':False,'analyticCertificateMachineProved':False,'editorialReview':'AI-assisted; not human review','numericalAgreementUsedAsProof':False,'parameterCheck':True,'uniqueCorrectOption':True,'numericRankAudit':'not-applicable-categorical' if kind=='categorical' else 'all-feasible-rank-selector'})
 r['pedagogy']={k:r[k] for k in ['relatedIdeaGroupId','structuralSignature','primaryTechnique','alternativeTechniques','prerequisites','answerForm','difficultyRationale','sourceRecordIds']};r['pedagogy'].update(constructionId=fid,reasoningDemand=[r['reasoningDemand']],responseFormat='multiple-choice');r['contentHash']=H(r);return r
def verify(r):
 try:
  m=r['parameters']['m'];return type(m)is int and r==build(r['familyId'],m-4)
 except (KeyError,ValueError,AssertionError,TypeError):return False

def generate(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];quarantine=[];audits=[]
 for meta in catalog():
  ranks=[];lengths=[];outcomes=[]
  for i in range(8):
   try:
    r=build(meta['familyId'],i);rows.append(r);raw=FAMILIES[meta['familyId']]['build'](s.Integer(i+4));outcomes.append(raw['answer']);opts=raw['options'];alens=[len(o[1]) for o in opts];aidx=next(j for j,o in enumerate(opts) if o[0]==raw['answer']);lengths.append((alens[aidx]>max(n for j,n in enumerate(alens) if j!=aidx),alens[aidx]<min(n for j,n in enumerate(alens) if j!=aidx)))
    if raw['kind']=='numeric':
     vals=[o[3] for o in opts];ranks.append(sum(bool(v<vals[aidx]) for j,v in enumerate(vals) if j!=aidx))
   except Exception as e:quarantine.append({'familyId':meta['familyId'],'index':i,'error':repr(e)})
  audits.append({'familyId':meta['familyId'],'correctNumericRanks':ranks or 'N/A-categorical','classificationOutcomes':outcomes if not ranks else 'numeric','alwaysSoleLongestTex':all(a for a,b in lengths),'alwaysSoleShortestTex':all(b for a,b in lengths)})
 assert len({r['problemId'] for r in rows})==len(rows)
 report={'families':len(catalog()),'instances':len(rows),'counts':{'series/easy':{'families':len(catalog()),'instances':len(rows)}},'quarantine':quarantine,'executedCheckCount':sum(len(r['automatedChecks']) for r in rows),'activeImportedCount':0,'humanReviewed':False,'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'optionAudit':audits}
 (out/'catalog.json').write_text(json.dumps(catalog(),indent=2)+'\n');(out/'candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));(out/'verification-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(Path(__file__).parent));args=ap.parse_args();generate(args.out)
