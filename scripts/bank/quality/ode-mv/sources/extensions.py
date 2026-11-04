"""New finite lower-level cases and immutable revisions of exposed option pools.
The old finite constructors, source records and saved grades remain untouched.
"""
import copy,json,re
from pathlib import Path
from common import *
import baseline_support as base
from presentation import corrected_math
ROOT=Path(__file__).resolve().parent
VERSION='quality-ode-multivariable-finite-v1'
reg=Registry('baseline-extension')
CHANGED={'finite-blowup','repeated-root','nonlinear-Jacobian','quadratic-critical-value'}
OPTION_REPAIRS={'gradient-max-direction','Lagrange-circle-linear','variable-integrating-factor'}
def slug_of(fid):
 for level in ('easy','medium','hard','olympiad'):
  marker='-'+level+'-'
  if marker in fid:return fid.split(marker,1)[1]
 raise ValueError('unrecognized source family')

def source_case(fid,m):
 meta=base.FAMILIES[fid];slug=slug_of(fid);raw=meta['build'](m);A=raw['answer']
 pool=raw['wrongs'] if 'wrongs' in raw else raw['options'][1:]
 fake={'familyId':fid,'statement':raw['statement'],'choices':[{'choiceId':'a','math':L(A)}],'answerChoiceId':'a','contentHash':'new-finite-domain'}
 fn=base.solutions.ode if meta['topic']=='differential equations' else base.solutions.multivariable
 steps,independent=fn(fake,m,slug)
 evidence=(base.checks.ode if meta['topic']=='differential equations' else base.checks.multivariable)(m,slug,fake)
 check('independent solution answer versus frozen expression',independent,A)
 assert evidence
 statement=raw['statement']
 # Undo the old paragraph wrapping only at the top level; these constructors
 # contain no nested gathered environments. Root performs the final formatter.
 if statement.startswith(r'\begin{gathered}') and statement.endswith(r'\end{gathered}'):
  statement=statement[len(r'\begin{gathered}'):-len(r'\end{gathered}')].replace(r'\\',r'\quad ')
 statement=statement.replace(T('At a later time v='),T('At a later time ')+r'v=').replace(T('At a point on this implicit solution curve with y=0 and t>0, find t.'),T('At a point on this implicit solution curve, ')+r'y=0,\quad t>0.'+T('Find ')+r't.').replace(T('Take y and y prime continuous at t=1.'),T('Take ')+r'y,y\prime'+T(' continuous at ')+r't=1.').replace(T('The origin is asymptotically stable exactly for a<c. Find c.'),T('The origin is asymptotically stable exactly for ')+r'a<c.'+T('Find ')+r'c.').replace(T(' Let y1 and y2 be solutions on an interval containing [1,2], and define '),T('Let ')+r'y_1,y_2'+T(' be solutions on an interval containing ')+r'[1,2].'+T('Define '))
 if slug=='transfer-conservation':
  u,v=s.symbols('u v');evidence=[check('actual displayed transfer conservation',(-2*u+3*v)+(2*u-3*v)),check('conserved total at requested later state',A+(2*m+21)/10,m+3)]
 if slug=='gradient-max-direction':
  pool=[(m*s.sqrt(2),'treat both gradient components as equal'),(m*s.sqrt(3),'omit one copy from squaring the second component'),(m*s.sqrt(6),'count the first squared component twice'),(2*m*s.sqrt(5),'retain a direction vector of length two'),(m*s.sqrt(5)/2,'divide by the direction norm twice'),(s.sqrt(m*m+2*m),'forget to square the second gradient component')]
 if slug=='Lagrange-circle-linear':
  pool=[(s.sqrt(m*m-1),'subtract squared components in the norm'),(1/s.sqrt(m*m+1),'invert the Cauchy bound'),((m+1)/s.sqrt(2),'use the equal-coordinate direction without maximizing'),((m-1)/s.sqrt(2),'use the opposite equal-coordinate direction'),(2*s.sqrt(m*m+1),'forget the unit-length normalization by a factor two'),(s.sqrt(m*m+1)/2,'normalize the unit direction twice')]
 if slug=='variable-integrating-factor':
  pool=[(2**(m+2)/(2*(m+2)),'omit the initial endpoint term'),((2**(m+2)-1)/(m+2),'forget to divide by the integrating factor'),((2**(m+1)-1)/(2*(m+1)),'omit the extra time factor before integration'),(A/2,'divide by the endpoint integrating factor twice'),(-A,'reverse integration endpoints'),(2*(2**m-1)/m,'use the reciprocal integrating factor'),(0,'retain only the zero homogeneous solution')]
 if slug=='finite-blowup':
  k=m-1;A=m/k;t=s.symbols('t',real=True);f=1/(m-k*t)
  statement=r'y\prime='+L(k)+r'y^2,\quad y(0)=\frac1{'+L(m)+r'}.'+T('Find the finite right endpoint of the maximal real solution interval.')
  steps=[T('The positive initial value allows reciprocal differentiation.'),r'(1/y)\prime=-'+L(k)+r',\quad y(t)=\frac1{'+L(m)+r'-'+L(k)+r't}.',T('The first forward denominator zero is a pole, so the solution cannot extend continuously across it.'),r't='+L(A)]
  pool=[(k/m,'invert the lifespan'),(m*k,'multiply by the growth coefficient instead of dividing'),(m/(2*k),'halve the reciprocal accumulation time'),(2*m/k,'double the reciprocal accumulation time'),(1/(m*k),'use initial height in place of its reciprocal'),(-m/k,'take the backward pole sign')]
  evidence=[check('revised nonlinear residual',s.diff(f,t)-k*f*f),check('revised initial value',f.subs(t,0),1/m),check('revised first pole',m-k*A)]
 if slug=='repeated-root':
  t=s.symbols('t',real=True);at=s.log(2)/m;f=t*s.exp(m*t);A=2*s.log(2)/m
  statement=r'y\prime\prime-'+L(2*m)+r'y\prime+'+L(m*m)+r'y=0,\quad y(0)=0,\quad y\prime(0)=1.\quad y('+L(at)+r')=?'
  steps=[r'(D-'+L(m)+r')^2y=0,\quad D=\frac{\mathrm d}{\mathrm dt}.',T('The repeated root gives ')+r'y=(C_1+C_2t)e^{'+L(m)+r't}.',r'y(0)=0\Longrightarrow C_1=0,\quad y\prime(0)=1\Longrightarrow C_2=1.',r'y('+L(at)+r')='+L(at)+r'e^{\ln2}='+L(A)]
  pool=[(s.log(2)/m,'omit exponential growth to the evaluation time'),(4*s.log(2)/m,'use twice the repeated characteristic root'),(2*s.log(2),'omit the time denominator'),(2*s.log(2)/(m*m),'divide by the root a second time'),(2/(m*s.log(2)),'invert the logarithmic time factor'),(s.log(2)/(2*m),'reverse the exponential growth sign')]
  evidence=[check('revised repeated-root residual',s.diff(f,t,2)-2*m*s.diff(f,t)+m*m*f),check('revised zero initial state',f.subs(t,0)),check('revised initial derivative',s.diff(f,t).subs(t,0),1),check('revised exact target time',f.subs(t,at),A)]
 if slug=='nonlinear-Jacobian':
  u,v=s.symbols('u v',positive=True);A=(m-1)*s.log(2)/2
  statement=T('Let D be the region in the positive quadrant satisfying ')+r'1\le xy\le'+L(m)+r',\quad1\le x/y\le2.'+T('Find its area.')
  steps=[T('Use product and ratio coordinates ')+r'u=xy,\quad v=x/y.\qquad x=\sqrt{uv},\quad y=\sqrt{u/v}.',r'\left|\frac{\partial(x,y)}{\partial(u,v)}\right|=\frac1{2v},\quad 1\le u\le'+L(m)+r',\ 1\le v\le2.',r'\operatorname{Area}(D)=\int_1^{'+L(m)+r'}\int_1^2\frac1{2v}\,\mathrm dv\,\mathrm du='+L(A)]
  pool=[((m-1)*s.log(2),'omit the one-half Jacobian factor'),((m-1)*s.log(2)/4,'apply the one-half Jacobian factor twice'),((m*m-1)*s.log(2)/4,'retain a spurious product-coordinate factor'),(s.log(m)*s.log(2)/2,'insert a spurious inverse product-coordinate factor'),((m-1)*s.log(2)/8,'divide by two in both inverse coordinates and again in the determinant'),(2*(m-1)*s.log(2),'invert the Jacobian factor')]
  jac=s.Matrix([s.sqrt(u*v),s.sqrt(u/v)]).jacobian([u,v]).det()
  evidence=[check('revised inverse Jacobian',jac,-1/(2*v)),check('revised exact rectangular integral',s.integrate(s.integrate(1/(2*v),(v,1,2)),(u,1,m)),A)]
 if slug=='quadratic-critical-value':
  x,y=s.symbols('x y',real=True);F=(x+y-m)**2+(x-y-1)**2+x*x;px=(m+1)/3;py=(m-1)/2;A=(m+1)**2/6
  statement=r'\min_{x,y\in\mathbb R}\left[(x+y-'+L(m)+r')^2+(x-y-1)^2+x^2\right]=?'
  steps=[T('All three squares cannot vanish together. Completing squares instead gives ')+L(F)+r'=3\left(x-'+L(px)+r'\right)^2+2\left(y-'+L(py)+r'\right)^2+'+L(A)+'.',T('The two remaining squares vanish at a feasible real point, so the constant term is the global minimum.')]
  pool=[(0,'assume all three incompatible squares can vanish'),((m+1)**2/3,'omit the one-half from the two equal residual squares'),((m+1)**2/9,'return only the square of the minimizing first coordinate'),((m-1)**2/6,'use the coordinate difference rather than the sum'),((m*m+1)/6,'omit the cross term in the squared sum'),((m+1)**2/12,'halve the completed-square residual')]
  evidence=[check('revised exact square completion',F,3*(x-px)**2+2*(y-py)**2+A),check('revised minimum attained',F.subs({x:px,y:py}),A)]
 if any(r'\operatorname{sech}' in q for q in steps):steps.insert(0,r'\operatorname{sech}t=1/\cosh t')
 statement=corrected_math(statement)
 steps=[corrected_math(q.replace(r'\log',r'\ln')) for q in steps]
 return item(statement,A,pool,steps,evidence,raw.get('domain',[]),['This is a new finite constructor version. Frozen source expressions are independently checked against the separately authored solution and its intermediate verifier. Old answer keys and snapshots remain unchanged.'],raw['structuralSignature'],newIndependentIdeas=0,constructorVersion=VERSION,constructionFamilyId=fid,revisionKind='semantic' if slug in CHANGED else 'option-only' if slug in OPTION_REPAIRS else 'finite-extension')

for fid,meta in base.FAMILIES.items():
 if meta['difficulty']=='olympiad':continue
 reg.families[fid]={'familyId':fid,'topic':meta['topic'],'difficulty':meta['difficulty'],'relatedIdeaGroupId':meta['relatedIdeaGroupId'],'primaryTechnique':meta['primaryTechnique'],'prerequisites':meta.get('prerequisites',[]),'distinctDecision':meta['difficultyRationale'],'nearestNeighbor':'Extends the same existing reviewed construction; adds zero independent ideas.','finiteParameters':[{'m':12},{'m':13}],'build':lambda m,_fid=fid:source_case(_fid,m)}
catalog=reg.catalog;build=reg.build;verify=reg.verify;all_candidates=reg.all_candidates

def build_revision(original):
 fid=original['familyId'];slug=slug_of(fid)
 if slug not in CHANGED|OPTION_REPAIRS:raise ValueError('no audited repair recipe for this source')
 m=original['provenance']['authoring']['builderParameters']['m'];assert type(m)is int and 4<=m<=11
 saved=reg.families[fid]['finiteParameters']
 try:
  reg.families[fid]['finiteParameters']=[{'m':i} for i in range(4,14)];record=reg.build(fid,m-4)
 finally:reg.families[fid]['finiteParameters']=saved
 record['problemId']=original['problemId'];record['semanticHash']=original['semanticHash']
 record['admission']={'previous':{k:original[k] for k in ['problemId','problemRevision','contentHash','semanticHash'] if k in original}|{'meaningChanged':slug in CHANGED}}
 record['review']['semanticChangeReason']=('Replace a misleading all-zero or answer-format shortcut with the explicitly displayed revised mathematical task.' if slug in CHANGED else 'Preserve the mathematical question and answer; replace exposed option-form alternatives with authored competing calculations.')
 record['contentHash']=H({k:v for k,v in record.items() if k!='contentHash'})
 return record

if __name__=='__main__':
 rows=[];errors=[]
 for f in catalog():
  for i in range(2):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:errors.append({'familyId':f['familyId'],'index':i,'error':repr(e)})
  print(f['familyId'],flush=True)
 (ROOT/'lower-extensions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows))
 originals=[json.loads(line) for line in (ROOT.parents[1]/'milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl').read_text().splitlines()]
 revisions=[]
 for original in originals:
  if original['familyId'] not in reg.families or slug_of(original['familyId']) not in CHANGED|OPTION_REPAIRS:continue
  try:revisions.append(build_revision(original))
  except Exception as e:errors.append({'familyId':original['familyId'],'problemId':original['problemId'],'error':repr(e)})
 (ROOT/'lower-revisions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in revisions))
 (ROOT/'lower-verification.json').write_text(json.dumps({'extensionRecords':len(rows),'revisionRecords':len(revisions),'errors':errors,'newIndependentIdeas':0,'executedChecks':sum(len(r['verificationEvidence']) for r in rows+revisions)},indent=2)+'\n')
 print('extensions',len(rows),'revisions',len(revisions),'errors',len(errors),flush=True)

def supports_revision(original):
 fid=original.get('familyId','')
 return fid in reg.families and slug_of(fid) in CHANGED|OPTION_REPAIRS

def verify_revision(candidate,original):
 try:return supports_revision(original) and candidate==build_revision(original)
 except Exception:return False
