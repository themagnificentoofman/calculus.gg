"""Portable original-content helpers. Never reads or writes application state."""
from __future__ import annotations
import hashlib, itertools, json
import sympy as s
R=s.Rational
def L(x):
 return s.latex(s.sympify(x)).replace(r'\log',r'\ln').replace(r'\operatorname{atanh}',r'\operatorname{arctanh}').replace(r'\operatorname{asinh}',r'\operatorname{arcsinh}').replace(r'\operatorname{acosh}',r'\operatorname{arccosh}')
def T(x): return r'\textnormal{'+x+'}'
def H(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def eq(a,b=0):
 d=s.simplify(s.trigsimp(s.expand_func(a-b)))
 return bool(d.is_zero_matrix) if isinstance(d,s.MatrixBase) else (d==0 or s.simplify(s.expand_trig(s.expand(d)))==0)
def check(name,a,b=0):
 if not eq(a,b):raise AssertionError(name+': '+str(s.simplify(a-b)))
 return {'name':name,'method':'exact-symbolic-identity','left':s.srepr(s.sympify(a)),'right':s.srepr(s.sympify(b))}
def truth(name,value):
 if value is not True:raise AssertionError(name)
 return {'name':name,'method':'exact-finite-condition','holds':True}

class Registry:
 def __init__(self,topic):self.topic=topic;self.families={}
 def register(self,slug,group,decision,nearest,domains,technique,prerequisites=(),difficulty='olympiad'):
  def decorator(fn):
   fid='q4-'+self.topic.replace(' ','-')+'-'+slug
   self.families[fid]=dict(familyId=fid,topic=self.topic,difficulty=difficulty,relatedIdeaGroupId=group,primaryTechnique=technique,prerequisites=list(prerequisites),distinctDecision=decision,nearestNeighbor=nearest,finiteParameters=domains,build=fn)
   return fn
  return decorator
 def catalog(self):return [{k:v for k,v in f.items() if k!='build'}|{'instanceCount':len(f['finiteParameters']),'editorialStatus':'candidate-awaiting-independent-review'} for f in self.families.values()]
 def build(self,fid,index):
  meta=self.families[fid]
  if type(index)!=int or not 0<=index<len(meta['finiteParameters']):raise ValueError('outside explicit finite domain')
  params=meta['finiteParameters'][index]
  p=meta['build'](**{k:s.sympify(v) for k,v in params.items()})
  answer=s.sympify(p.pop('answer'));pool=p.pop('pool');checks=p.pop('checks')
  assert checks and not answer.has(s.nan,s.zoo,s.oo,-s.oo,s.Integral,s.Sum,s.Limit)
  clean=[]
  for value,label in pool:
   value=s.sympify(value)
   if value.has(s.nan,s.zoo,s.oo,-s.oo) or eq(value,answer) or any(eq(value,v) for v,_ in clean):continue
   assert value.is_real is not False
   clean.append((value,label))
  assert len(clean)>=3,(fid,index,'insufficient distinct misconception alternatives')
  # Finite authored alternatives only. Pick among feasible answer ranks; this is
  # an anti-tell constraint, never a source of newly manufactured wrong values.
  groups={}
  for combo in itertools.combinations(clean,3):
   try:rank=sum(float(s.N(v-answer,30))<0 for v,_ in combo)
   except (TypeError,ValueError):continue
   groups.setdefault(rank,[]).append(combo)
  ranks=sorted(groups)
  if ranks:
   rank=ranks[index%len(ranks)];combos=groups[rank];selected=combos[(index//len(ranks))%len(combos)]
  else:selected=clean[:3];rank=None
  values=[(answer,'correct')]+list(selected)
  choices=[dict(choiceId='ch_'+H(s.srepr(v))[:16],math=L(v),misconception=why) for v,why in values]
  answer_id=choices[0]['choiceId'];rotation=int(H([fid,params])[:8],16)%4;choices=choices[rotation:]+choices[:rotation]
  for j,(a,_) in enumerate(values):
   for b,_ in values[:j]:assert not eq(a,b)
  record={k:v for k,v in meta.items() if k not in ('build','finiteParameters')}
  steps=p.pop('solutionSteps');assert steps
  record.update(p,parameters=params,parameterDomain={'finite':meta['finiteParameters']},instanceIndex=index,choices=choices,answerChoiceId=answer_id,solutionSteps=steps+[L(answer)],exactAnswer=s.srepr(answer),verificationEvidence=checks,optionAudit={'authoredPoolSize':len(clean),'feasibleCorrectRanks':[r+1 for r in ranks],'chosenCorrectRank':None if rank is None else rank+1,'genericAdditiveOffsets':False},source={'kind':'independently-authored','thirdPartyProblemAdapted':False,'license':'LicenseRef-CalculusNinja-Original','attribution':'Original mathematical construction and wording, AI-assisted. References supply theorem context only.'},review={'status':'candidate-awaiting-independent-review','humanReviewed':False,'formalProof':False,'analyticObligationsMachineProved':False},schemaVersion=2)
  record['pedagogy']=dict(constructionId=fid,relatedIdeaGroupId=meta['relatedIdeaGroupId'],structuralSignature=p['structuralSignature'],primaryTechnique=meta['primaryTechnique'],alternativeTechniques=p.get('alternativeTechniques',[]),prerequisites=meta['prerequisites'],reasoningDemand=['reframing','proof of applicability'],answerForm='exact-real',difficultyRationale=meta['distinctDecision'],sourceRecordIds=p.get('sourceRecordIds',[]),responseFormat='multiple-choice')
  record['semanticHash']=H([fid,params,p['statement']]);record['problemId']='cn_q4_'+record['semanticHash'][:20];record['contentHash']=H(record)
  return record
 def verify(self,record):
  try:return record==self.build(record['familyId'],record['instanceIndex'])
  except (ValueError,KeyError,AssertionError,TypeError):return False
 def all_candidates(self):
  for fid,f in self.families.items():
   for i in range(len(f['finiteParameters'])):yield self.build(fid,i)

def item(statement,answer,pool,steps,checks,conditions,analytic,signature,**kwargs):
 return dict(statement=statement,answer=answer,pool=pool,solutionSteps=steps,checks=checks,conditions=conditions,analyticCertificate=analytic,structuralSignature=signature,**kwargs)
