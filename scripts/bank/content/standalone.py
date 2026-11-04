"""Exact certificate for standalone polynomial questions, not a registered family.
The author supplies an explicit rational polynomial, operation, bounds/point,
and three mathematical distractors. Every output is derived and checked.
Other standalone routes require their own reviewed verifier, never a bypass.
"""
import hashlib,json
import re
import sympy as s
VERSION='standalone-polynomial-v1'
x=s.Symbol('x',real=True)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def rational(value):
 if not isinstance(value,list) or len(value)!=2 or any(type(v)is not int or abs(v)>1000000 for v in value) or value[1]<=0:raise ValueError('Bounded exact rational required')
 return s.Rational(*value)
def build(spec):
 if set(spec)-{'revision'}!={'slug','coefficients','operation','point','upper','distractors','pedagogy','topic','difficulty'}:raise ValueError('Unknown standalone contract field')
 revision=spec.get('revision',1)
 if not isinstance(spec['slug'],str) or not re.fullmatch('[a-z][a-z0-9-]{2,79}',spec['slug']):raise ValueError('Bounded stable slug required')
 if type(revision)is not int or not 1<=revision<=1000000:raise ValueError('Invalid immutable revision')
 if not 1<=len(spec['coefficients'])<=21:raise ValueError('Polynomial degree bound')
 coeffs=list(map(rational,spec['coefficients']));f=sum(c*x**i for i,c in enumerate(coeffs));a=rational(spec['point']);b=rational(spec['upper'])
 # Derive by coefficient calculus and independently validate against SymPy.
 if spec['operation']=='definite-integral':
  if b<=a:raise ValueError('Ordered nondegenerate bounds required')
  F=sum(c*x**(i+1)/s.Integer(i+1) for i,c in enumerate(coeffs));answer=s.simplify(F.subs(x,b)-F.subs(x,a))
  assert s.simplify(s.diff(F,x)-f)==0 and s.integrate(f,(x,a,b))==answer
  statement=r'\int_{'+s.latex(a)+'}^{'+s.latex(b)+'}'+s.latex(f)+r'\,dx';steps=[r'F(x)='+s.latex(F),r'F(b)-F(a)='+s.latex(answer)]
 elif spec['operation']=='derivative-at-point':
  d=sum(i*c*x**(i-1) for i,c in enumerate(coeffs) if i);answer=s.simplify(d.subs(x,a));assert s.simplify(s.diff(f,x)-d)==0
  statement=r'\left.\frac{d}{dx}\left('+s.latex(f)+r'\right)\right|_{x='+s.latex(a)+'}';steps=[r'f\prime(x)='+s.latex(d),r'f\prime(a)='+s.latex(answer)]
 else:raise ValueError('No verifier for this operation')
 if len(spec['distractors'])!=3:raise ValueError('Three authored distractors required')
 values=[answer]+[rational(v['value']) for v in spec['distractors']]
 if len(set(values))!=4:raise ValueError('Equivalent choices')
 choices=[{'choiceId':'ch_'+digest(str(v))[:16],'math':s.latex(v),'misconception':'correct' if i==0 else spec['distractors'][i-1]['misconception']} for i,v in enumerate(values)]
 if any(not c['misconception'] for c in choices):raise ValueError('Missing misconception')
 fid='standalone-'+spec['slug'];m=spec['pedagogy'];assert m['constructionId']==fid
 p={'schemaVersion':2,'problemId':'cn_'+digest(fid)[:20],'problemRevision':revision,'familyId':fid,'templateVersion':VERSION,'parameters':{},'semanticHash':digest({'operation':spec['operation'],'coefficients':[str(c) for c in coeffs],'point':str(a),'upper':str(b)}),'statement':statement,'choices':choices,'answerChoiceId':choices[0]['choiceId'],'solutionSteps':steps,'assumptions':['Real polynomial, continuous and differentiable on the real line.'],'topic':spec['topic'],'difficulty':spec['difficulty'],'subtopic':m['relatedIdeaGroupId'],'techniqueTags':[m['primaryTechnique']]+m['alternativeTechniques'],'pedagogy':m,'provenance':{'kind':'original','sourceUrl':None,'sourceItem':None,'license':'LicenseRef-CalculusNinja-Original','attribution':'Standalone original Calculus Ninja exercise; exact rational polynomial certificate.','authoring':{'standaloneSpec':spec}},'validation':{'status':'passed','methods':['exact-rational-coefficient-calculus','independent-symbolic-operation','pairwise-exact-choice-check'],'evidence':{'verificationRoute':VERSION,'parameterDomain':{'standalone':True},'assumptionsChecked':True,'solutionDerivationChecked':True,'uniqueCorrectOption':True},'humanReviewed':False},'estimates':{'difficulty':spec['difficulty'],'solveSeconds':60,'basis':m['difficultyRationale']}}
 p['contentHash']=digest(p);return p

def verify(p):
 if p!=build(p['provenance']['authoring']['standaloneSpec']):raise ValueError('Standalone certificate/content mismatch')
 return True

if __name__=='__main__':
 import argparse
 from pathlib import Path
 ap=argparse.ArgumentParser(description='Verify an explicit standalone specification and emit a private delta artifact.')
 ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--release',required=True);ap.add_argument('--parent',required=True);args=ap.parse_args()
 if not re.fullmatch('[a-z][a-z0-9-]{2,99}',args.release):raise ValueError('Invalid release slug')
 p=build(json.loads(args.spec.read_text()));verify(p);args.out.mkdir(parents=True,exist_ok=True)
 artifact=args.out/(args.release+'.jsonl')
 if artifact.exists():raise ValueError('Do not overwrite an existing release artifact')
 artifact.write_text(canonical(p)+'\n')
 manifest={'schemaVersion':2,'releaseId':args.release,'parentRelease':args.parent,'artifact':artifact.name,'artifactSha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'approvedCount':1,'coverage':{p['topic']+'/'+p['difficulty']:1},'families':{p['familyId']:1},'humanReviewedCount':0,'templateVersion':VERSION,'publishedCount':0,'importedCount':0,'activeCount':0}
 (args.out/(args.release+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'verified':1,'problemId':p['problemId'],'revision':p['problemRevision'],'artifact':str(artifact),'imported':0,'active':0}))
