"""New finite-domain authoring bridge; never broadens frozen admission."""
from pathlib import Path
from functools import lru_cache
import importlib.util,sys,re
import sympy as s
from common import tex,digest
BASE=Path(__file__).resolve().parent
VENDOR=BASE/'frozen_v37'
sys.path.insert(0,str(VENDOR))
spec=importlib.util.spec_from_file_location('quality_series_frozen_v37',VENDOR/'coverage.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
sys.path.remove(str(VENDOR))
FAMILIES={f['familyId']:f for f in frozen.FAMILIES if f['editorialStatus']=='admitted' and f['topic']=='series'}
x,y,t,u,z=s.symbols('x y t u z',real=True);k,n=s.symbols('k n',integer=True,positive=True);R=s.Rational
def T(v):
 assert not any(c in v for c in ['^','_','\\'])
 return r'\textnormal{'+v+'}'
def ck(label,a,b):
 q=s.Integer(0) if a==b else s.simplify(s.expand_func(a-b));assert q==0,(label,q)
 return {'description':label,'left':tex(a),'right':tex(b),'result':'exact equality'}
def role(record):
 i=record['parameters']['instance'];m=record['parameters']['m'];assert i in (8,9) and m==i+4
 return record['familyId'],s.Integer(m),i
@lru_cache(None)
def source_payload(fid,m):return FAMILIES[fid]['build'](s.Integer(m))
def expected(record):
 fid,m,_=role(record);p=source_payload(fid,int(m));return p['answer'],p
def result(record,steps,checks=(),issues=(),notes=()):
 A,_=expected(record)
 assert checks and not any(re.search(r'(?<![A-Za-z])m(?![A-Za-z])',v) for v in steps)
 return {'solutionSteps':list(steps)+([tex(A)] if steps[-1]!=tex(A) else []),'checks':list(checks),'issues':list(issues),'notes':list(notes),'answerMath':tex(A)}
