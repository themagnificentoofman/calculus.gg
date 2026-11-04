"""Fail-closed literal parser for the97 reviewed scalar special-function menus."""
import re
import sympy as s
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application
alpha=s.Symbol('alpha',positive=True);B=s.Symbol('B',positive=True)
functions={q:getattr(s,q) for q in ['sqrt','log','atan','acos','asinh','acosh','sin','cos','tan','sinh','cosh','tanh','coth']}
functions.update({'pi':s.pi,'e':s.E,'alpha':alpha,'B':B,'elliptice':s.elliptic_e,'dilog':lambda x:s.polylog(2,x)})
def parse(tex):
 v=tex
 # Inputs from JSON carry standard single TeX backslashes, never executable code.
 for a,b in [('operatorname{arccosh}','acosh'),('operatorname{arcsinh}','asinh'),('operatorname{acosh}','acosh'),('operatorname{asinh}','asinh'),('operatorname{Li}_{2}','dilog')]:v=v.replace('\\'+a,' '+b+' ')
 v=re.sub(r'J\^\{2\}_\{\d+\}\\left\(\\alpha\\right\)', ' B ',v)
 for command in [r'\left',r'\right',r'\,',r'\!',r'\ ']:v=v.replace(command,'')
 # Function powers have their usual function-value scope.
 def brace(pos):
  assert v[pos]=='{',tex
  n=1;j=pos+1
  while n:
   assert j<len(v),tex;n+=(v[j]=='{')-(v[j]=='}');j+=1
  return v[pos+1:j-1],j
 for fn in ['sinh','cosh','tanh','coth','sin','cos','tan','arctan','arccos']:
  while True:
   m=re.search(r'\\'+fn+r'\^\{(\d+)\}',v)
   if not m:break
   a,j=brace(m.end());name={'arctan':'atan','arccos':'acos'}.get(fn,fn);v=v[:m.start()]+'('+name+'('+a+'))**'+m[1]+v[j:]
 for fn in ['sinh','cosh','tanh','coth','arctan','arccos','sin','cos','tan','log','ln','alpha','pi']:
  v=v.replace('\\'+fn,' '+{'arctan':'atan','arccos':'acos','ln':'log'}.get(fn,fn)+' ')
 v=re.sub(r'\bE(?=\s*\()', 'elliptice',v).replace(r'\cdot','*')
 while r'\frac' in v or r'\sqrt' in v:
  i,cmd=min((v.index(cmd),cmd) for cmd in [r'\frac',r'\sqrt'] if cmd in v);start=i+len(cmd);a,j=brace(start)
  if cmd==r'\frac':b,j=brace(j);replacement='(('+a+')/('+b+'))'
  else:replacement='sqrt('+a+')'
  v=v[:i]+replacement+v[j:]
 v=v.replace('{','(').replace('}',')').replace('^','**')
 assert re.fullmatch(r'[0-9\sA-Za-z()+*/.,\-]+',v),(tex,v)
 assert set(re.findall(r'[A-Za-z]+',v))<=set(functions),(tex,v)
 result=parse_expr(v,local_dict=functions,transformations=standard_transformations+(implicit_multiplication_application,))
 assert not isinstance(result,tuple),tex
 return result
