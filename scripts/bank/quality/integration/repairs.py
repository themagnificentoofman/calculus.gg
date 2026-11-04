"""Explicit immutable repairs of four lower-level integration constructions.

Old constructors and statements stay frozen. Signed-area revisions deliberately
vary the sign, interval geometry and orientation; this semantic change is marked.
All other repairs change only choices/solutions, retaining mathematical identity.
"""
from . import support as c,solutions
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(c.SOURCE.parent))
import content_pipeline
s=c.s
VERSION='quality-integration-repairs-v1'
FAMILIES=['m3-integration-easy-signed-area','m3-integration-easy-substitution-affine','m3-integration-hard-trig-log','m3-integration-hard-root-quadratic']
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def catalog():return [{'familyId':fid,'indices':list(range(10)),'topic':'integration','difficulty':c.FAMILIES[fid]['difficulty'],'newIndependentIdeas':0,'constructorVersion':VERSION} for fid in FAMILIES]

def signed_case(index,m):
 cases=[(1,0,2*m),(1,0,m+1),(1,0,2*m+1),(-1,0,2*m+2),(2,m-1,m+3),(2,m-3,m+1),(-2,m-3,m+1),(1,m+3,m-1),(1,m+1,m+4),(1,m-4,m-1)]
 slope,lo,hi=map(s.Integer,cases[index]);return slope,lo,hi

def build(fid,index):
 if fid not in FAMILIES or type(index)is not int or not 0<=index<10:raise ValueError('Outside reviewed repair domain')
 f=c.FAMILIES[fid];m=s.Integer(index+4);raw=c.source_payload(fid,int(m));answer=raw['answer'];x=c.frozen.x;meaning=False
 if fid.endswith('signed-area'):
  slope,lo,hi=signed_case(index,m);function=slope*(x-m);F=slope*(x-m)**2/2;answer=s.simplify(F.subs(x,hi)-F.subs(x,lo));meaning=index not in [0]
  total_area=s.integrate(abs(function),(x,min(lo,hi),max(lo,hi)))
  pool=[(answer,'correct'),(total_area,'Add unsigned areas instead of signed integral'),(F.subs(x,hi),'Keep only the upper endpoint of the chosen primitive'),(-F.subs(x,lo),'Keep only the lower-endpoint contribution'),(-answer,'Reverse the endpoint subtraction'),((hi-lo)*function.subs(x,hi),'Replace a linear graph by its upper-endpoint rectangle'),(slope*(hi-lo)**2/2,'Subtract endpoint heights instead of adding them in the trapezoid rule'),(slope*(hi**2-lo**2)/2,'Omit the horizontal translation in the integrand'),(answer/slope,'Lose the slope multiplier'),(answer/2,'Apply the triangular factor one-half twice'),(2*answer,'Omit the triangular factor one-half')]
  statement=r'\int_{'+c.tex(lo)+r'}^{'+c.tex(hi)+'}'+c.tex(function)+r'\,\mathrm{d}x'
  checks=[c.ck('Independent direct integration of the displayed affine expression',s.integrate(function,(x,lo,hi)),answer),c.ck('Differentiate the displayed chosen primitive',s.diff(F,x),function)]
  steps=[c.T('A definite integral keeps the signs of the contributions and the orientation of its bounds.'),r'F(x)='+c.tex(F)+r',\qquad F\prime(x)='+c.tex(function),r'F('+c.tex(hi)+r')-F('+c.tex(lo)+r')='+c.tex(F.subs(x,hi))+r'-\left('+c.tex(F.subs(x,lo))+r'\right)='+c.tex(answer),c.tex(answer)]
  assumptions=['The displayed affine function is continuous for all real values; the integral uses the indicated oriented bounds.']
 else:
  if fid.endswith('substitution-affine'):
   pool=[(answer,'correct'),(m*m/3+1,'Omit the cross term when expanding the square'),(m*m/3+m/2+1,'Forget the factor two in the cross term'),(m*m/3+2*m+1,'Fail to divide the linear term by two when integrating'),(m*m/3+m+s.Rational(1,3),'Apply the cubic denominator to the constant term'),(m*m/2+m+1,'Use the wrong power denominator for the quadratic term'),(m/3+m+1,'Fail to square the coefficient of the quadratic term'),(m*answer,'Omit the substitution Jacobian')]
  elif fid.endswith('trig-log'):
   pool=[(answer,'correct'),(-1/m**2,'Forget the exponent shift in the primitive'),(-1/(m+2)**2,'Insert an extra power into the transformed integrand'),(-1/((m+1)*(m+2)),'Replace the logarithm by its endpoint linear approximation as an exact identity'),(-2/(m+1)**2,'Count the same logarithmic-moment contribution twice'),(-1/(2*(m+1)**2),'Apply an unwarranted half-period factor'),(-1/(m*(m+1)),'Differentiate the logarithm but use the old exponent in the second primitive'),(-1/(m+1)**3,'Introduce an extra denominator in the second integration step')]
  else:
   r=s.sqrt(2);L=s.log(1+r);pool=[(answer,'correct'),(m*m*(r+L)/2,'Reverse the sign of the logarithmic part'),(m*m*(r-2*L)/2,'Double the logarithmic coefficient'),(m*m*(r-L)/4,'Retain an extra factor one-half'),(m*m*(r-L),'Lose the double-angle factor one-half'),(m*(r-L)/2,'Lose one scale factor in the substitution'),(m*m*(2*r-L)/2,'Double only the algebraic endpoint term'),(m*m*(r-L/2)/2,'Halve only the logarithmic coefficient')]
  statement=raw['statement'];assumptions=raw['domain']
  dummy={'familyId':fid,'parameters':{'instance':index},'provenance':{'authoring':{'builderParameters':{'m':int(m)}}},'choices':[{'choiceId':'correct','math':c.frozen.latex(answer)}],'answerChoiceId':'correct'}
  solved=solutions.solve(dummy);steps=solved['solutionSteps'];checks=solved['checks']
 unique=[]
 for value,why in pool:
  value=s.simplify(value)
  if not any(c.eq(value,prior) for prior,_ in unique):unique.append((value,why))
 if len(unique)<4:raise ValueError('Insufficient distinct misconception routes')
 selected,audit=c.frozen.select_options(unique,m)
 choices=[{'choiceId':'ch_'+hashlib.sha256(canonical(s.srepr(v)).encode()).hexdigest()[:16],'math':c.frozen.latex(v),'misconception':why,'expression':s.srepr(v)} for v,why in selected]
 assert s.simplify(selected[0][0]-answer)==0
 for i,(a,_) in enumerate(selected):
  for b,_ in selected[i+1:]:assert not c.eq(a,b)
 result={'familyId':fid,'topic':'integration','difficulty':f['difficulty'],'parameters':{'instance':index,'m':int(m)},'parameterDomain':{'indices':list(range(10))},'instanceIndex':index,'statement':statement,'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':steps,'assumptions':assumptions,'pedagogy':{'constructionId':fid,'relatedIdeaGroupId':f['relatedIdeaGroupId'],'structuralSignature':raw['structuralSignature'],'primaryTechnique':f['primaryTechnique'],'alternativeTechniques':f['alternativeTechniques'],'prerequisites':f['prerequisites'],'reasoningDemand':[f['reasoningDemand']],'answerForm':'exact-expression','difficultyRationale':f['difficultyRationale'],'sourceRecordIds':[],'responseFormat':'multiple-choice'},'verificationEvidence':checks,'optionAudit':audit,'verificationRoute':VERSION,'newIndependentIdeas':0,'constructorVersion':VERSION,'reviewStatus':'candidate-awaiting-independent-review'}
 if index<8:
  old=content_pipeline.build(fid,index)
  result['previous']={'problemId':old['problemId'],'revision':old['problemRevision'],'sourceContentHash':old['contentHash'],'semanticHash':old['semanticHash'],'meaningChanged':meaning,'semanticChangeReason':'Replace repeatedly symmetric zero-result intervals with purposeful signed/oriented affine-area cases.' if meaning else None}
 return result

def verify(record):return canonical(record)==canonical(build(record['familyId'],record['instanceIndex']))
def all_candidates():
 for fid in FAMILIES:
  for index in range(10):yield build(fid,index)
if __name__=='__main__':
 rows=list(all_candidates());Path(sys.argv[1]).write_text(''.join(canonical(r)+'\n' for r in rows));print(canonical({'candidates':len(rows),'immutableRevisions':sum('previous' in r for r in rows),'newIndependentIdeas':0,'newInstances':sum('previous' not in r for r in rows)}))
