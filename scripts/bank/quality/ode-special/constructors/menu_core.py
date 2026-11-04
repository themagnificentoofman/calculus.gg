"""Offline original-content contract; no old constructor or admission is changed."""
from __future__ import annotations
from pathlib import Path
from contextvars import ContextVar
import hashlib,json,itertools,math,re,sys
import sympy as s
R=s.Rational;pi=s.pi
x,y,t,z=s.symbols('x y t z',real=True);n,k=s.symbols('n k',integer=True,positive=True)
FAMILIES={};CHECKS=ContextVar('quality_checks',default=None)
BASE=Path(__file__).resolve().parent

def canon(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str)
def digest(obj):return hashlib.sha256(canon(obj).encode()).hexdigest()
def L(value):
 return s.latex(s.sympify(value),fold_short_frac=False).replace(r'\log',r'\ln').replace(r'\operatorname{asin}',r'\arcsin').replace(r'\operatorname{acos}',r'\arccos').replace(r'\operatorname{atan}',r'\arctan').replace(r'\operatorname{asinh}',r'\operatorname{arcsinh}').replace(r'\operatorname{acosh}',r'\operatorname{arccosh}').replace(r'\operatorname{atanh}',r'\operatorname{arctanh}')
def T(text):
 assert not any(c in text for c in ['\\','^','_']),text
 return r'\textnormal{'+text.replace('&',r'\&').replace('%',r'\%').replace('#',r'\#')+'}'
def ck(label,left,right=0):
 if isinstance(left,s.MatrixBase):res=s.simplify(left-right);ok=res.is_zero_matrix is True
 else:res=s.simplify(s.expand_func(s.sympify(left)-s.sympify(right)));ok=res==0
 assert ok,(label,res)
 CHECKS.get().append({'kind':'executed-exact-identity','description':label,'left':L(left),'right':L(right),'residual':L(res),'passed':True})
def condition(label,passed,detail):
 assert bool(passed),label
 CHECKS.get().append({'kind':'executed-domain-or-finite-check','description':label,'detail':detail,'passed':True})
def analytic(name,hypotheses,argument):
 CHECKS.get().append({'kind':'analytic-certificate','name':name,'hypotheses':list(hypotheses),'argument':list(argument),'scope':'AI editorial mathematical argument; not a formal or human proof claim'})
def register(topic,slug,group,method,decision,neighbor,domain,prerequisites=(),refs=()):
 domain=json.loads(canon(domain))
 def decorate(fn):
  fid='q1-'+topic+'-olympiad-'+slug
  assert fid not in FAMILIES
  FAMILIES[fid]={'familyId':fid,'topic':topic,'difficulty':'olympiad','relatedIdeaGroupId':group,'primaryTechnique':method,'centralDecision':decision,'nearestNeighborDistinction':neighbor,'finiteDomain':domain,'instanceCount':len(domain),'prerequisites':list(prerequisites),'sourceRecordIds':list(refs),'editorialStatus':'needs-independent-review','build':fn}
  return fn
 return decorate

def candidate(statement,answer,pool,steps,shape,answerForm='exact-real-expression',notes=()):
 return {'statement':statement,'answer':s.sympify(answer),'pool':[(s.sympify(v),reason) for v,reason in pool],'solutionSteps':steps,'structuralSignature':shape,'answerForm':answerForm,'notes':list(notes)}

def choose_options(answer,pool,index,fid,mandatory=(),nome_parameters=None):
 accepted=[]
 for wrong,why in pool:
  if s.simplify(wrong-answer)==0 or any(s.simplify(wrong-v)==0 for v,_ in accepted):continue
  accepted.append((wrong,why))
 assert len(accepted)>=3,(fid,index,'insufficient mathematically distinct authored mistakes')
 # Select only authored misconception triples. One identifiable opposite pair
 # can leak the answer after an elementary sign check, so use zero or two pairs.
 universe=[(answer,'correct')]+accepted
 opposites=set()
 for i,(left,_) in enumerate(universe):
  for j,(right,_) in enumerate(universe[:i]):
   if s.simplify(left+right)==0:opposites.add((j,i))
 def literal_sign(value):
  text=re.sub(r'\s+','',L(value).replace(r'\left','').replace(r'\right',''))
  return (-1,text[1:]) if text.startswith('-') else (1,text)
 literal=[literal_sign(v) for v,_ in universe]
 literal_opposites={(j,i) for i in range(len(universe)) for j in range(i) if literal[i][0]==-literal[j][0] and literal[i][1]==literal[j][1]}
 required={i for i,(v,_) in enumerate(universe) if i and s.srepr(v) in mandatory}
 eligible=[]
 for indices in itertools.combinations(range(1,len(universe)),3):
  chosen={0,*indices}
  pair_count=sum(i in chosen and j in chosen for i,j in opposites)
  if pair_count!=1 and sum(i in chosen and j in chosen for i,j in literal_opposites)!=1 and required.issubset(chosen):eligible.append((indices,pair_count))
 assert eligible,(fid,index,'No authored triple avoids a singleton opposite-pair clue')
 keyed=lambda item:digest([fid,index,[s.srepr(universe[j][0]) for j in item[0]],'authored-triple'])
 # Preserve the previous deterministic authored menu whenever it already passes.
 # Only failed coupling menus need a different triple.
 baseline=None
 try:
  av=float(s.N(answer,40));low=[j for j in range(1,len(universe)) if float(s.N(universe[j][0],40))<av];high=[j for j in range(1,len(universe)) if float(s.N(universe[j][0],40))>av]
  reqlo=[j for j in low if j in required];reqhi=[j for j in high if j in required]
  oldranks=[j for j in range(4) if len(low)>=j>=len(reqlo) and len(high)>=3-j>=len(reqhi)]
  count=oldranks[index%len(oldranks)]
  oldkey=lambda j:digest([fid,index,s.srepr(universe[j][0])])
  indices=tuple(sorted(reqlo+sorted([j for j in low if j not in required],key=oldkey)[:count-len(reqlo)]+reqhi+sorted([j for j in high if j not in required],key=oldkey)[:3-count-len(reqhi)]))
  baseline=next((v for v in eligible if v[0]==indices),None)
 except (TypeError,ValueError,ZeroDivisionError):pass
 try:
  val=float(s.N(answer,40))
  ranks={item[0]:sum(float(s.N(universe[j][0],40))<val for j in item[0]) for item in eligible}
  feasible=sorted(set(ranks.values()));wanted=feasible[index%len(feasible)]
  chosen=min([v for v in eligible if ranks[v[0]]==wanted],key=keyed)
 except (TypeError,ValueError):chosen=min(eligible,key=keyed)
 if baseline is not None:chosen=baseline
 selected=[universe[j] for j in chosen[0]]
 selected_pair_count=chosen[1]
 values=[(answer,'correct')]+selected
 distinctions=[{'kind':'executed-cross-option-coupling-check','oppositePairs':selected_pair_count,'rule':'No unique opposite-sign pair identifies an answer candidate; only existing authored misconception triples are selected.','passed':selected_pair_count!=1}]
 for i,(a,_) in enumerate(values):
  for b,_ in values[i+1:]:
   d=s.simplify(a-b)
   if d!=0 and d.is_zero is False:
    distinctions.append({'kind':'executed-SymPy-nonzero-difference','difference':L(d),'passed':True})
   elif nome_parameters and s.srepr(a) in nome_parameters and s.srepr(b) in nome_parameters:
    pa=R(nome_parameters[s.srepr(a)]);pb=R(nome_parameters[s.srepr(b)])
    assert 0<pa<1 and 0<pb<1 and pa!=pb
    assert s.simplify(a-s.exp(-pi*s.elliptic_k(1-pa)/s.elliptic_k(pa)))==0
    assert s.simplify(b-s.exp(-pi*s.elliptic_k(1-pb)/s.elliptic_k(pb)))==0
    distinctions.append({'kind':'analytic-elliptic-nome-strict-monotonicity','parameters':[str(pa),str(pb)],'argument':'K(p) is finite positive and strictly increasing on(0,1), by pointwise strict increase of its positive integral kernel. Thus K(1-p)/K(p) strictly decreases, and exp(-pi times that ratio) strictly increases. Exact distinct rational parameters therefore give inequivalent options.','passed':True})
   else:
    elliptics=list(d.atoms(s.elliptic_k));subs={v:s.Symbol('K'+str(j),positive=True) for j,v in enumerate(elliptics)}
    valid=bool(elliptics) and all(v.args[0].is_Rational and 0<v.args[0]<1 for v in elliptics)
    transformed=s.simplify(d.xreplace(subs)) if valid else d
    assert valid and transformed.is_zero is False,(fid,index,'unproved option distinction',d)
    distinctions.append({'kind':'analytic-positive-integral-choice-certificate','parameters':[str(v.args[0]) for v in elliptics],'argument':'For every actual rational parameter0<p<1, K(p)=integral0to(pi/2)(1-p sin squared(theta))^(-1/2) is finite and strictly positive. Replacing each such value by a positive symbol leaves a provably nonzero algebraic difference.','reducedDifference':L(transformed),'passed':True})
 opts=[{'choiceId':'ch_'+digest(s.srepr(v))[:16],'math':L(v),'misconception':why,'expression':s.srepr(v)} for v,why in values]
 correct=opts[0]['choiceId'];opts.sort(key=lambda v:digest([fid,index,v['choiceId'],'display-independent-permutation']))
 return opts,correct,distinctions

def build_record(fid,index):
 f=FAMILIES[fid];assert type(index)is int and 0<=index<f['instanceCount'];case=f['finiteDomain'][index];level=case.get('difficulty',f['difficulty'])
 token=CHECKS.set([])
 try:
  p=f['build'](case);checks=list(CHECKS.get())
 finally:CHECKS.reset(token)
 assert checks and any(c['kind'].startswith('executed-') for c in checks)
 opts,correct,distinctions=choose_options(p['answer'],p['pool'],index,fid,p.get('mandatoryWrongExpressions',()),p.get('nomeParameters'))
 steps=list(p['solutionSteps']);steps.append(L(p['answer'])) if steps[-1]!=L(p['answer']) else None
 meta={k:v for k,v in f.items() if k not in ['build','finiteDomain']}
 return {'familyId':fid,'topic':f['topic'],'difficulty':level,'parameters':{'instance':index,'case':case},'statement':p['statement'],'choices':opts,'answerChoiceId':correct,'answerMath':L(p['answer']),'answerExpression':s.srepr(p['answer']),'solutionSteps':steps,'assumptions':case.get('assumptions',[]),'pedagogy':{'constructionId':fid,'relatedIdeaGroupId':f['relatedIdeaGroupId'],'structuralSignature':p['structuralSignature'],'primaryTechnique':f['primaryTechnique'],'alternativeTechniques':[],'prerequisites':f['prerequisites'],'reasoningDemand':['strategy-selection','hypothesis-checking','synthesis'],'answerForm':p['answerForm'],'difficultyRationale':case.get('difficultyRationale',f['centralDecision']),'nearestNeighborDistinction':f['nearestNeighborDistinction'],'sourceRecordIds':f['sourceRecordIds'],'responseFormat':'multiple-choice'},'editorialStatus':'needs-independent-review','provenance':{'kind':'original','license':'LicenseRef-CalculusNinja-Original','attribution':'Independently authored original construction and explanation; mathematical theorem references are reference-only. AI-assisted, no human certification claimed.','lineage':{'group':f['relatedIdeaGroupId'],'construction':fid,'caseId':case['caseId']}},'validation':{'status':'mathematically-checked-pending-independent-editorial-review','methods':['independently-encoded-intermediate-identities','finite-domain-and-case-checks','exact-pairwise-choice-inequivalence'],'evidence':{'checks':checks,'pairwiseOptionChecks':distinctions,'notes':p['notes'],'sourceHash':source_hash()}},'reviewMetadata':meta}

def source_hash():
 paths={BASE/'core.py',BASE/'advanced.py'}|{Path(sys.modules[f['build'].__module__].__file__).resolve() for f in FAMILIES.values()}
 return digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
def catalog():return [{k:v for k,v in f.items() if k!='build'} for f in FAMILIES.values()]
def verify(record):
 expected=build_record(record['familyId'],record['parameters']['instance'])
 assert canon(record)==canon(expected),'Record is not identical to the source-bound reconstruction'
 return True
