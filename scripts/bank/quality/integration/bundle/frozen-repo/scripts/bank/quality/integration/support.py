"""Trusted authoring helpers for concrete, self-contained solution repairs."""
from pathlib import Path
from functools import lru_cache
import importlib.util,sys,json,hashlib,re,os
import sympy as s
BASE=Path(__file__).resolve().parent
# New finite extension: the old constructor/review files remain unchanged.
def _source_root():
 explicit=os.environ.get('BANK_AUDIT_CONTENT_DIR')
 if explicit:return Path(explicit).resolve()
 for ancestor in BASE.parents:
  candidate=ancestor/'scripts/bank/content'
  if (candidate/'coverage.py').exists():return candidate
 return Path('/Users/zhenxg/Documents/Codex/2026-11-03/sign/work/solution-audit/scripts/bank/content')
SOURCE=_source_root()
BANK=Path(os.environ.get('BANK_AUDIT_ARTIFACT','/Users/zhenxg/Documents/Codex/2026-11-03/sign/work/milestone3/.bank-data/milestone3/release-v3/cn-2026-11-03-ideas-v3.jsonl')).resolve()
sys.path.insert(0,str(SOURCE))
spec=importlib.util.spec_from_file_location('coverage_frozen_solution_audit',SOURCE/'coverage.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
for name in ['integral','derivative','limit','algebra']:
 old=getattr(frozen,name)
 def capture(*args,_old=old,_name=name,**kwargs):
  result=_old(*args,**kwargs);result['_input']={'kind':_name,'args':args,'kwargs':kwargs};return result
 setattr(frozen,name,capture)
FAMILIES={f['familyId']:f for f in frozen.FAMILIES if f['editorialStatus']=='admitted' and f['topic'] in ['integration','differentiation','limits','series']}
x,y,t,u,z=s.symbols('x y t u z',real=True);k,n=s.symbols('k n',integer=True,positive=True);R=s.Rational

def tex(expr):
 v=s.latex(s.sympify(expr),fold_short_frac=False)
 return v.replace(r'\log',r'\ln').replace(r'\operatorname{atan}',r'\arctan').replace(r'\operatorname{asin}',r'\arcsin').replace(r'\operatorname{acos}',r'\arccos').replace(r'\operatorname{asinh}',r'\operatorname{arsinh}').replace(r'\operatorname{acosh}',r'\operatorname{arcosh}').replace(r'\operatorname{atanh}',r'\operatorname{artanh}')
def T(v):
 assert not any(c in v for c in ['^','_','\\']), 'Mathematics must be a math step, not ASCII inside prose: '+v
 escapes={'{':r'\{','}':r'\}','&':r'\&','%':r'\%','$':r'\$','#':r'\#'}
 return r'\textnormal{'+''.join(escapes.get(c,c) for c in v)+'}'
def eq(a,b):
 if a==b:return True
 q=s.simplify(s.expand_func(a-b));return q.is_zero_matrix is True if isinstance(q,s.MatrixBase) else q==0

def ck(label,a,b):
 assert eq(a,b),label+': '+str(a)+' != '+str(b)
 return {'description':label,'left':tex(a),'right':tex(b),'result':'exact equality'}

def role(record):
 fid=record['familyId'];i=record['parameters']['instance']
 assert type(i) is int and 0<=i<10
 value=record['provenance']['authoring']['builderParameters']['m']
 assert value==i+4
 return fid,s.Integer(value),i
@lru_cache(None)
def source_payload(fid,m):return FAMILIES[fid]['build'](s.Integer(m))

def expected(record):
 fid,m,_=role(record);p=source_payload(fid,int(m));A=p['answer']
 correct=next(c['math'] for c in record['choices'] if c['choiceId']==record['answerChoiceId'])
 # This task never changes an answer; compare the trusted constructor's actual expression.
 assert frozen.latex(A)==correct, 'Active answer differs from frozen constructor: '+fid
 return A,p

def result(record,steps,checks=(),issues=(),notes=()):
 A,_=expected(record)
 assert steps and all(isinstance(v,str) and v for v in steps)
 # The final displayed result is the verified original exact expression, not a free symbol.
 final=tex(A)
 if steps[-1]!=final:steps=list(steps)+[final]
 assert not any(re.search(r'(?<![A-Za-z])m(?![A-Za-z])',v) for v in steps), 'unreplaced builder parameter'
 assert not any('F(b)-F(a)' in v or 'Here ' in v for v in steps)
 return {'solutionSteps':steps,'checks':list(checks),'issues':list(issues),'notes':list(notes),'answerMath':tex(A),'reviewType':'AI-assisted editorial review plus exact mathematical checks; not human review'}

def integral_input(record):
 A,p=expected(record);raw=p.get('_input');assert raw and raw['kind']=='integral'
 expr,F,lo,hi,_,wrongs,idea=raw['args'][:7]
 return A,expr,F,lo,hi

def antiderivative_steps(record,idea=None,pre=()):
 A,expr,F,lo,hi=integral_input(record);xx=frozen.x
 loF=s.limit(F,xx,lo,dir='+') if lo in (0,-s.oo) else F.subs(xx,lo)
 hiF=s.limit(F,xx,hi,dir='-') if hi==s.oo else F.subs(xx,hi)
 steps=list(pre)
 if idea:steps.append(T(idea))
 steps += [r'F(x)='+tex(F)+r',\qquad F\prime(x)='+tex(expr)]
 if lo==0 and not F.subs(xx,0).is_finite:
  steps += [r'\lim_{a\to0^+}F(a)='+tex(loF)]
 if hi==s.oo:steps += [r'\lim_{b\to\infty}F(b)='+tex(hiF),r'\int_{'+tex(lo)+r'}^{\infty}'+tex(expr)+r'\,\mathrm dx='+tex(hiF)+r'-\left('+tex(loF)+r'\right)='+tex(A)]
 else:steps += [r'\int_{'+tex(lo)+'}^{'+tex(hi)+'}'+tex(expr)+r'\,\mathrm dx=F\left('+tex(hi)+r'\right)-'+(r'\lim_{a\to0^+}F(a)' if lo==0 and not F.subs(xx,0).is_finite else r'F\left('+tex(lo)+r'\right)')+'='+tex(hiF)+r'-\left('+tex(loF)+r'\right)='+tex(A)]
 return result(record,steps,[ck('The displayed derivative equals the integrand',s.diff(F,xx),expr),ck('The concrete endpoint evaluation equals the original answer',hiF-loF,A)],['undefined-builder-parameter','unbound-generic-endpoints'])
