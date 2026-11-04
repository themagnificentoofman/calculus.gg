"""Portable constructor v2: explicit finite extension with independent solution checks.

Frozen version1 sources are imported read-only. Its private bounded build recipes
are evaluated only at the two explicit additional parameters in this version.
"""
from pathlib import Path
import os,sys,json,copy,hashlib,re,importlib.util
BASE=Path(__file__).resolve().parent
os.environ['BANK_AUDIT_CONTENT_DIR']=str(BASE/'frozen_content')
sys.path.insert(0,str(BASE));import lower_core as core
s=core.s;R=s.Rational
sys.path.insert(0,str(BASE/'frozen_review'));import common
def extended_role(record):
 m=record['provenance']['authoring']['builderParameters']['m']
 assert type(m)is int and 4<=m<=13
 return record['familyId'],s.Integer(m),m-4
common.role=extended_role
import differentiation_solutions,limits_solutions
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);mo=importlib.util.module_from_spec(sp);sp.loader.exec_module(mo);return mo
sys.path.insert(0,str(BASE/'frozen_supplemental'))
supp=load('lower_supplemental_solutions',BASE/'frozen_supplemental/solutions.py')
checks=load('lower_supplemental_checks',BASE/'frozen_supplemental/substantive_checks.py')
la=load('lower_limits_additions',BASE/'frozen_content/limits_additions.py')
da=load('lower_diff_additions',BASE/'frozen_content/differentiation_additions.py')
_original_da_pack=da.pack
def capture_da_pool(*args,**kwargs):
 result=_original_da_pack(*args,**kwargs);result['_completeAuthoredPool']=list(args[3]);return result
da.pack=capture_da_pool
ORIGINAL=json.loads((BASE/'original-records.json').read_text())
REFERENCE={r['familyId']:r for r in ORIGINAL}
LOWER={}
for r in ORIGINAL:
 if r['difficulty']!='olympiad':LOWER.setdefault(r['familyId'],r)
REPLACE={
'm3-differentiation-easy-accumulation-derivative',
'm3-limits-easy-rational-sequence-shift',
'm3-limits-medium-factorial-ratio-fixed-shift',
'm3-limits-medium-root-test-scale',
'm3-limits-medium-two-sided-square-root'}
def normalize(v):
 # Only gathered containers are flattened; inner cases/matrix rows are retained.
 out=[];stack=[];i=0
 while i<len(v):
  mt=re.match(r'\\(begin|end)\{([^}]+)\}',v[i:])
  if mt:
   kind,env=mt.groups()
   if kind=='begin':stack.append(env)
   else:
    assert stack and stack[-1]==env,(stack,env,v)
    stack.pop()
   if env!='gathered':out.append(mt.group())
   i+=len(mt.group());continue
  if v.startswith('\\\\',i):
   if stack and stack[-1]=='gathered':out.append(r'\quad');i+=2;continue
   if not stack:out.append('\\');i+=2;continue
  out.append(v[i]);i+=1
 value=supp.notation(''.join(out))
 value=value.replace(r'\textnormal{ at x=1.}',r'\textnormal{ at }x=1.')
 value=value.replace(r'\textnormal{There is a sharp c such that the function has a continuous first derivative at zero exactly when alpha>c. Find c.}',r'\textnormal{Find the sharp threshold }c\textnormal{ such that the function has a continuous first derivative at zero exactly when }\alpha>c.')
 return value
def proof_source(fid,m):
 source=REFERENCE[fid];r=copy.deepcopy(source);r['provenance']['authoring']['builderParameters']['m']=m
 if fid in common.FAMILIES:
  p=common.source_payload(fid,m);r['choices']=[{'choiceId':'correct','math':common.frozen.latex(p['answer'])}];r['answerChoiceId']='correct'
  proof=({'differentiation':differentiation_solutions,'limits':limits_solutions}[source['topic']]).solve(r)
  pool=[(a,b) for a,b in p['options'] if b!='correct']
  return p,proof['solutionSteps'],proof['checks'],pool
 if fid in la.FAMILIES:
  token=la.CHECKS.set([])
  try:p=la.FAMILIES[fid]['build'](s.Integer(m))
  finally:la.CHECKS.reset(token)
  steps,ans=supp.limits(r,s.Integer(m),fid.split('-',3)[3]);assert s.simplify(ans-p['answer'])==0
  return p,steps,checks.limits(s.Integer(m),fid.split('-',3)[3],r),p['pool']
 if fid in da.FAMILIES:
  p=da.FAMILIES[fid]['build'](s.Integer(m));steps,ans=supp.differentiation(r,s.Integer(m),fid.split('-',3)[3]);assert s.simplify(ans-p['answer'])==0
  return p,steps,checks.differentiation(s.Integer(m),fid.split('-',3)[3],r),p['_completeAuthoredPool']
 raise KeyError(fid)
def repair_pool(fid,m,A,pool):
 import option_repairs
 fixed=option_repairs.pool(fid,m,A)
 if fixed is not None:return fixed
 if fid.endswith('-linearization'):
  return [(m+q,why) for q,why in [(1/m,'Omit the derivative factor one half'),(1/(2*m*m),'Use the input point in place of its square root'),(-1/(2*m),'Reverse the displacement sign'),(1/(4*m),'Apply the derivative half twice'),(2/m,'Count both the displacement and derivative twice'),(1/(2*(m+1)),'Evaluate the derivative at the next integer root'),(1/(m-1),'Use the previous integer root and omit the derivative half')]]
 if fid.endswith('-inverse-second'):
  return [(-2/m**2,'Omit one inverse-slope factor'),(-2/m,'Keep only one inverse-slope factor'),(2/m**3,'Reverse the inverse curvature sign'),(-4/m**3,'Count the second derivative twice'),(-1/m**3,'Halve the supplied second derivative'),(-2/m**4,'Insert a fourth inverse-slope factor')]
 if fid.endswith('-implicit-inverse-exponential'):
  shape=s.exp(-2*m)/(m+1)**3
  return [(c*shape,why) for c,why in [(-(m+1),'Omit the extra derivative of the linear factor'),(-2*(m+1),'Differentiate both product terms as identical'),(-2*(m+2),'Count the inverse-chain contribution twice'),(-(m+2)/2,'Apply an extra half to the second derivative'),(m+2,'Reverse the inverse curvature sign'),(-(m+2)*(m+1),'Omit one inverse-slope denominator')]]
 if fid.endswith('-Riemann-sum'):
  return [(s.log(m+1)/m**2,'Apply the inner scale divisor twice'),(2*s.log(m+1)/m,'Double the integration interval contribution'),(s.log(m)/m,'Omit the upper-endpoint constant one'),(s.log(m+2)/m,'Shift the upper endpoint one step too far'),(s.log(m+1)/(m+1),'Use the endpoint value as the substitution scale'),(s.log(m+1)/(m-1),'Decrease the inner linear scale by one')]
 if fid.endswith('-implicit-second'):
  d=2*m+1;u=m+2
  return [(-2*(d*d+u*u)/d**3,'Omit the mixed first-derivative contribution'),(-2*(d*d-u*d)/d**3,'Omit the squared first derivative'),(-2*(d*d+u*d+u*u)/d**3,'Reverse the mixed derivative sign'),(-(d*d-2*u*d+2*u*u)/d**3,'Lose the second derivative of the quadratic first term'),(A/2,'Apply an extra half to the second differentiation'),(2*A,'Count both mixed product terms twice'),(-A,'Reverse the implicit denominator sign')]
 if fid.endswith('-supremum-pointwise-mismatch'):
  shape=m**(-m/(m-1))
  return [(c*shape,why) for c,why in [(1,'Keep only the first critical-point monomial'),(m-2,'Subtract one extra monomial contribution'),(m,'Add instead of subtracting the smaller monomial'),(m+1,'Add both monomial derivative coefficients'),(2*(m-1),'Count the critical height twice'),((m-1)/2,'Halve the maximizing height')]]
 if fid.endswith('-Lp-maximum-limit'):
  return [((m-1)**m/m**(m+1),'Use the previous exponent critical point'),((m+1)**m/(m+2)**(m+1),'Use the next exponent critical point'),(m**m/(m+1)**m,'Omit the complementary endpoint factor'),(m**(m-1)/(m+1)**m,'Use the derivative rather than the function exponent'),(2*A,'Count the same peak contribution twice'),(A/2,'Halve the limiting peak height')]
 return pool
def format_options(fid,m,opts,A):
 if fid.endswith('-linearization'):
  for o in opts:o['math']=str(m)+r'+\left('+core.L(s.sympify(o['expression'])-m)+r'\right)'
 elif fid.endswith('-inverse-second'):
  for o in opts:o['math']=r'\frac{'+core.L(s.simplify(s.sympify(o['expression'])*m**3))+r'}{'+str(m)+r'^3}'
 elif fid.endswith('-implicit-inverse-exponential'):
  factor=s.exp(-2*m)/(m+1)**3
  for o in opts:o['math']=r'\frac{('+core.L(s.simplify(s.sympify(o['expression'])/factor))+r')e^{-'+str(2*m)+r'}}{'+str(m+1)+r'^3}'
 elif fid.endswith('-implicit-second'):
  d=2*m+1
  for o in opts:
   q=s.sympify(o['expression']);num=s.simplify(q*d**3)
   o['math']=r'\frac{'+core.L(num)+r'}{'+str(d)+r'^3}'
 elif fid.endswith('-supremum-pointwise-mismatch'):
  shape=m**(-m/(m-1))
  for o in opts:
   q=s.sympify(o['expression']);coef=s.simplify(q/shape)
   o['math']=r'\left('+core.L(coef)+r'\right)'+str(m)+r'^{-'+core.L(m/(m-1))+r'}'
 elif fid.endswith('-Lp-maximum-limit'):
  forms=[(A,r'\frac{'+str(m)+r'^{'+str(m)+r'}}{'+str(m+1)+r'^{'+str(m+1)+r'}}'),
   ((m-1)**m/m**(m+1),r'\frac{'+str(m-1)+r'^{'+str(m)+r'}}{'+str(m)+r'^{'+str(m+1)+r'}}'),
   ((m+1)**m/(m+2)**(m+1),r'\frac{'+str(m+1)+r'^{'+str(m)+r'}}{'+str(m+2)+r'^{'+str(m+1)+r'}}'),
   (m**m/(m+1)**m,r'\frac{'+str(m)+r'^{'+str(m)+r'}}{'+str(m+1)+r'^{'+str(m)+r'}}'),
   (m**(m-1)/(m+1)**m,r'\frac{'+str(m)+r'^{'+str(m-1)+r'}}{'+str(m+1)+r'^{'+str(m)+r'}}'),
   (2*A,r'\frac{2\cdot'+str(m)+r'^{'+str(m)+r'}}{'+str(m+1)+r'^{'+str(m+1)+r'}}'),
   (A/2,r'\frac{'+str(m)+r'^{'+str(m)+r'}}{2\cdot'+str(m+1)+r'^{'+str(m+1)+r'}}')]
  for o in opts:
   q=s.sympify(o['expression']);matches=[v for a,v in forms if s.simplify(a-q)==0];assert matches;o['math']=matches[0]
 return opts
def answer_value(fid,value):
 if fid.endswith('-complex-exponential-derivative'):
  result=s.simplify(s.expand_complex(value));assert result.is_real is True
  return result
 return value
def statement_value(fid,value):
 if fid.endswith('-curvature-parametric'):
  return r'\textnormal{For this plane curve, let }\kappa(t)\textnormal{ denote its curvature. }'+value
 return value
def extension(fid,index):
 m=s.Integer(index+(10 if fid in la.FAMILIES else 12));m0=int(m)
 p,steps,evidence,pool=proof_source(fid,m0);A=answer_value(fid,p['answer']);pool=repair_pool(fid,m,A,pool)
 new='q2-'+fid;opts,correct,pairs=core.choose_options(A,pool,index,new);opts=format_options(fid,m,opts,A)
 original=LOWER[fid];ped=copy.deepcopy(original['pedagogy'])
 ped.update(constructionId=original['pedagogy']['constructionId'],difficultyRationale=original['pedagogy']['difficultyRationale']+' This version adds only two explicitly checked finite parameters; it adds no new mathematical idea.')
 out={'familyId':new,'topic':original['topic'],'difficulty':original['difficulty'],'parameters':{'instance':index,'case':{'m':m0,'caseId':f'extension-m-{m0}','purpose':'A checked additional finite fluency case of the same construction.'}},'statement':normalize(statement_value(fid,p['statement'])),'choices':opts,'answerChoiceId':correct,'answerExpression':s.srepr(A),'answerMath':next(o['math'] for o in opts if o['choiceId']==correct),'solutionSteps':[normalize(q) for q in steps],'pedagogy':ped,'provenance':{'kind':'original-constructor-extension','lineage':{'construction':original['pedagogy']['constructionId'],'originalFamilyId':fid,'sameRelatedIdea':True,'newIdeaCredit':0},'sourceContentHash':original['contentHash']},'validation':{'status':'mathematically-checked-pending-independent-review','evidence':{'independentIntermediateChecks':evidence,'pairwiseOptionChecks':pairs,'sourceFiles':source_digests()}},'editorialStatus':'needs-independent-review'}
 out['solutionSteps'].append(out['answerMath']) if out['solutionSteps'][-1]!=out['answerMath'] else None
 return out
def source_digests():
 return {str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for sub in ['frozen_content','frozen_review','frozen_supplemental'] for p in sorted((BASE/sub).glob('*')) if p.is_file()}
def catalog():
 return [{'familyId':'q2-'+fid,'originalFamilyId':fid,'topic':r['topic'],'difficulty':r['difficulty'],'instanceCount':2,'finiteDomain':[{'instance':i,'m':i+(10 if fid in la.FAMILIES else 12)} for i in range(2)]} for fid,r in sorted(LOWER.items()) if fid not in REPLACE]
def build(fid,index):
 assert fid.startswith('q2-') and type(index)is int and 0<=index<2
 return extension(fid[3:],index)
def verify(raw):assert core.canon(raw)==core.canon(build(raw['familyId'],raw['parameters']['instance']));return True
if __name__=='__main__':
 rows=[];errors=[]
 for f in catalog():
  for i in range(f['instanceCount']):
   try:rows.append(build(f['familyId'],i))
   except Exception as e:errors.append({'familyId':f['familyId'],'index':i,'error':repr(e)})
 (BASE/'extensions-candidates.json').write_text(json.dumps(rows,indent=2))
 (BASE/'extensions-errors.json').write_text(json.dumps(errors,indent=2))
 print(json.dumps({'families':len(catalog()),'rows':len(rows),'errors':errors}))
