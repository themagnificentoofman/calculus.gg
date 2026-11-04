"""Sixteen unchanged-task Medium revisions and two presentation-only overlays.
Source guarded, original problem identities/semantic identities/options retained.
No application import and no mutation of earlier constructors or artifacts.
"""
from pathlib import Path
import json,hashlib,copy,re,itertools
import sympy as s
from literal_numeric import parse
P=Path(__file__).resolve().parent
BETA='m3-integration-hard-improper-rational-beta';LOG='m3-integration-hard-logarithmic-moment';ACC='m3-integration-easy-accumulation-from-derivative'
VERSION='quality-integration-lower-reviewed-v1'
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def raw(r):return hashlib.sha256(canonical(r).encode()).hexdigest()
def key(r):return r['familyId'],r['parameters'].get('extension',r['parameters'].get('instance'))
ORIGINAL={key(r):r for r in map(json.loads,(P/'integration-lower-originals.jsonl').read_text().splitlines())}
def supports(r):return key(r) in ORIGINAL and raw(r)==raw(ORIGINAL[key(r)])
def tex(v):return s.latex(v).replace(r'\log',r'\ln')
def derive(r):
 fid=r['familyId'];statement=r['statement'];checks=[];x,t=s.symbols('x t',positive=True)
 def ck(name,a,b):
  assert s.simplify(a-b)==0,(name,a,b);checks.append({'description':name,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
 if fid==BETA:
  m=int(re.search(r'x\^\{(\d+)\}',statement)[1]);assert [int(q) for q in re.findall(r'\^\{(\d+)\}',statement)]==[m,m+2]
  u=s.symbols('u',positive=True);integrand=x**m/(1+x)**(m+2);primitive=x**(m+1)/((m+1)*(1+x)**(m+1));ans=s.Rational(1,m+1)
  ck('Derivative of chosen primitive',s.diff(primitive,x),integrand);ck('Exact substitution including Jacobian',integrand.subs(x,u/(1-u))/(1-u)**2,u**m)
  ck('Improper upper limit',s.limit(primitive,x,s.oo),ans);ck('Lower endpoint',s.limit(primitive,x,0,dir='+'),0)
  steps=[r'u=\frac{x}{1+x},\qquad x=\frac{u}{1-u},\qquad\mathrm dx=\frac{\mathrm du}{(1-u)^2}',r'x:0\to\infty\quad\Longrightarrow\quad u:0\to1',rf'\frac{{x^{{{m}}}}}{{(1+x)^{{{m+2}}}}}\,\mathrm dx=u^{{{m}}}\,\mathrm du',rf'\int_0^1u^{{{m}}}\,\mathrm du=\left[\frac{{u^{{{m+1}}}}}{{{m+1}}}\right]_0^1='+tex(ans),tex(ans)]
  conditions='At zero the original integrand is bounded by a constant times x^m; at infinity it is bounded by x^-2. Here m is the concrete positive integer exponent parsed from the statement, so both endpoints converge. The increasing substitution maps the improper interval to (0,1).'
  route='Set u=x/(1+x), carry the Jacobian, and evaluate a single monomial on [0,1]. The positive endpoint limits are routine; no beta-function theorem is needed.'
  nearest='Unlike mixed-log endpoint moments, this rational task becomes one monomial after a single familiar fractional substitution; the Beta label does not add a decision.'
 else:
  assert fid==LOG;m=int(re.search(r'x\^\{(\d+)\}',statement)[1]);n=m+1;ans=s.Rational(2,n**3)
  transformed=t*t*s.exp(-n*t);primitive=-s.exp(-n*t)*(t*t/s.Integer(n)+2*t/s.Integer(n*n)+s.Rational(2,n**3))
  ck('Log substitution with oriented bounds',((x**m*s.log(x)**2)*x).subs(x,s.exp(-t)),transformed)
  ck('Differentiate exponential-moment primitive',s.diff(primitive,t),transformed)
  ck('Upper moment endpoint',s.limit(primitive,t,s.oo),0);ck('Lower moment endpoint',primitive.subs(t,0),-ans)
  steps=[r't=-\ln x,\qquad x=e^{-t},\qquad\mathrm dx=-e^{-t}\,\mathrm dt',rf'\int_0^1x^{{{m}}}(\ln x)^2\,\mathrm dx=\int_0^\infty t^2e^{{-{n}t}}\,\mathrm dt',rf'J_k=\int_0^\infty t^ke^{{-{n}t}}\,\mathrm dt,\qquad k=0,1,2',rf'J_0=\frac1{{{n}}},\qquad J_k=\frac{{k}}{{{n}}}J_{{k-1}}\quad(k=1,2)',r'\textnormal{Integration by parts gives the recurrence. The endpoint terms vanish because a positive exponential dominates each polynomial.}',rf'J_2=\frac2{{{n}}}\frac1{{{n}}}\frac1{{{n}}}='+tex(ans),tex(ans)]
  conditions='At the lower logarithmic endpoint, t=-ln(x) transforms the integral into a quadratic polynomial times an exponential with strictly positive decay rate. The first two integration-by-parts boundary terms vanish at zero and infinity, proving convergence as well as the displayed recurrence.'
  route='Use t=-ln(x), then integrate the quadratic exponential moment by parts twice. The visible polynomial degree is two for every finite case; exponent size changes arithmetic, not the method.'
  nearest='The mixed logarithmic-endpoint family needs a nontrivial series decomposition; this single-endpoint squared logarithm requires only a fixed two-step integration-by-parts chain.'
 assert m==r['provenance']['authoring']['builderParameters']['m']
 choices=[parse(c['math']) for c in r['choices']];correct=choices[next(i for i,c in enumerate(r['choices']) if c['choiceId']==r['answerChoiceId'])]
 ck('Literal correct option equals independent result',correct,ans)
 for a,b in itertools.combinations(choices,2):assert s.simplify(a-b).equals(0)is False
 return {'m':m,'answer':ans,'steps':steps,'checks':checks,'conditions':conditions,'route':route,'nearestNeighbor':nearest,'sixLiteralChoicePairsDistinct':True}
def build_revision(original):
 assert supports(original);r=copy.deepcopy(original);fid=r['familyId'];source=raw(original)
 if fid==ACC:
  m=r['parameters']['m'];r['statement']=r'\textnormal{Let }F\textnormal{ be continuously differentiable on }[1,3].\quad '+rf'F(1)={m},\quad F(3)={m*m+1}.\quad\textnormal{{Find }}\int_1^3F\prime(x)\,\mathrm dx.'
  r['review']={'presentationOnly':True,'meaningChanged':False,'previousCandidateRawHash':source,'previousConstructorVersion':original['constructorVersion'],'recommendedDifficulty':'easy','newIndependentIdeas':0,'sourceRebind':'Only move the already stated function and interval out of prose; every number, bound, choice, answer, solution and parameter is unchanged.'}
 else:
  d=derive(original);r['difficulty']='medium';r['solutionSteps']=d['steps'];r['statement']=r['statement'].replace(r'\log',r'\ln')
  r['estimates']={'difficulty':'medium','solveSeconds':150,'basis':d['route']+' Separate AI-assisted options-visible review; player calibration pending.'}
  r['pedagogy']['difficultyRationale']=d['route'];r['provenance']['authoring']['admittedDifficulty']='medium'
  r['admission']={'previous':{k:original[k] for k in ['problemId','problemRevision','contentHash','semanticHash']}|{'meaningChanged':False}}
  r['review']={'status':'source-bound-candidate-awaiting-parent-admission','humanReviewed':False,'formalProof':False,'qualifiedOlympiad':False,'recommendedDifficulty':'medium','relatedIdeaGroupId':r['pedagogy']['relatedIdeaGroupId'],'easiestOptionsVisibleRoute':d['route'],'difficultyRationale':d['route'],'nearestNeighbor':d['nearestNeighbor'],'preservePreviousLineage':True,'semanticChangeReason':'Unchanged mathematical task and choices; conservative difficulty correction and explicit independently checked worked solution. Natural logarithm notation made explicit.','previousSourceRawHash':source}
  r['verificationEvidence']=d['checks'];r['analyticReview']=d['conditions'];r['revisionKind']='difficulty-and-explanation'
 r['constructorVersion']=VERSION
 if 'contentHash' in r:r['contentHash']=raw({k:v for k,v in r.items() if k!='contentHash'})
 return r
def verify_revision(r,original):
 try:return supports(original) and r==build_revision(original)
 except Exception:return False
def catalog():return [{'familyId':fid,'indices':sorted(i for f,i in ORIGINAL if f==fid),'newIndependentIdeas':0,'revisionKind':'presentation-only' if fid==ACC else 'difficulty-and-explanation'} for fid in [BETA,LOG,ACC]]
def build(fid,index):
 if type(index)is not int or (fid,index) not in ORIGINAL:raise ValueError('Outside the frozen18-record revision domain')
 return build_revision(ORIGINAL[(fid,index)])
def all_candidates():
 for fid,i in ORIGINAL:yield build(fid,i)
def verify(r):
 try:return r==build(*key(r))
 except Exception:return False
if __name__=='__main__':
 rows=list(all_candidates());assert len(rows)==18
 (P/'integration-lower-revisions.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
 report=[]
 for r in rows:
  old=ORIGINAL[key(r)];entry={'familyId':r['familyId'],'index':key(r)[1],'rawHash':raw(r),'previousRawHash':raw(old),'problemId':old.get('problemId'),'sourceContentHash':old.get('contentHash'),'sourceSemanticHash':old.get('semanticHash'),'recommendedDifficulty':r.get('review',{}).get('recommendedDifficulty'),'questionMeaningUnchanged':True,'choicesAnswerAndParametersUnchanged':all(old[k]==r[k] for k in ['choices','answerChoiceId','parameters']),'newIndependentIdeas':0}
  if r['familyId']!=ACC:
   d=derive(old);entry.update(exactChecks=d['checks'],sixLiteralChoicePairsDistinct=True,analyticConditions=d['conditions'],easiestOptionsVisibleRoute=d['route'],nearestNeighbor=d['nearestNeighbor'])
  else:entry.update(exactChecks=[{'description':'The FTC endpoint difference equals the unchanged literal correct choice','passed':parse(next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId']))==r['parameters']['m']**2+1-r['parameters']['m']}],allSolutionStepsUnchanged=old['solutionSteps']==r['solutionSteps'])
  report.append(entry)
 output={'records':report,'scope':'Independent literal derivations for all16 original beta/log-moment tasks, plus exact unchanged-math rebind of two presentation-only extension overlays. No frozen app/source file modified.','counts':{'unchangedTaskMediumRevisions':16,'presentationOnlyExtensionOverlays':2,'independentExactChecks':sum(len(q['exactChecks']) for q in report),'literalChoiceInequalities':96},'sourceSha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['integration_lower_revisions.py','integration-lower-originals.jsonl','literal_numeric.py','integration-lower-revisions.jsonl']},'APIs':'catalog/build/all_candidates/verify(record)->bool; supports(original)/build_revision(original)/verify_revision(candidate,original)->bool. Preserve prior IDs, semanticHashes, and canonical exposure aliases.'}
 (P/'integration-lower-revision-review.json').write_text(json.dumps(output,indent=2)+'\n');print(output['counts'])
