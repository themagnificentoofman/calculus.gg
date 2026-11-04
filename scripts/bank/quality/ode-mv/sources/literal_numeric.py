# Exact portable copy of root fail-closed numeric TeX parser; source SHA256 01fa4134b233dd55fbce8587c616b8f62f9ff7700516341b6dfe468c79468437
"""Small fail-closed parser for the literal numeric TeX choices in peer batches."""
import re
import sympy as s
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application

def parse(tex):
 v=tex
 for command in [r'\left',r'\right',r'\,',r'\!',r'\ ']:v=v.replace(command,'')
 v=v.replace(r'\pi',' pi ').replace(r'\Gamma',' gamma ').replace(r'\ln',' log ')
 def group(pos):
  assert v[pos]=='{',tex
  depth=1;j=pos+1
  while depth:
   assert j<len(v),tex
   depth+=(v[j]=='{')-(v[j]=='}');j+=1
  return v[pos+1:j-1],j
 while re.search(r'\\arctan\^\{([0-9]+)\}',v):
  found=re.search(r'\\arctan\^\{([0-9]+)\}',v);a,j=group(found.end());v=v[:found.start()]+'(atan('+a+'))**'+found[1]+v[j:]
 v=v.replace(r'\arctan',' atan ')
 # Replace only the outermost command; nested commands are handled on later
 # iterations. Parentheses, not braces, carry the resulting operator scope.
 while r'\frac' in v or r'\sqrt' in v:
  hits=[(v.index(cmd),cmd) for cmd in [r'\frac',r'\sqrt'] if cmd in v];i,cmd=min(hits)
  start=i+len(cmd);degree=None
  if cmd==r'\sqrt' and v[start]=='[':
   end=v.index(']',start);degree=v[start+1:end];assert degree.isdigit();start=end+1
  a,j=group(start)
  if cmd==r'\frac':b,j=group(j);replacement='(('+a+')/('+b+'))'
  else:replacement='sqrt('+a+')' if degree is None else '(('+a+')**(1/'+degree+'))'
  v=v[:i]+replacement+v[j:]
 v=v.replace('{','(').replace('}',')').replace('^','**')
 assert re.fullmatch(r'[0-9\sA-Za-z()+*/.,\-]+',v),tex
 assert set(re.findall(r'[A-Za-z]+',v)) <= {'pi','e','sqrt','gamma','log','atan'},tex
 result=parse_expr(v,local_dict={'pi':s.pi,'e':s.E,'sqrt':s.sqrt,'gamma':s.gamma,'log':s.log,'atan':s.atan},transformations=standard_transformations+(implicit_multiplication_application,))
 return s.Tuple(*result) if isinstance(result,tuple) else result

def same(a,b):
 if isinstance(a,s.Tuple) or isinstance(b,s.Tuple):return isinstance(a,s.Tuple) and isinstance(b,s.Tuple) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return s.simplify(s.expand_func(a-b))==0

def distinct(a,b):
 if isinstance(a,s.Tuple) or isinstance(b,s.Tuple):return not same(a,b) and any(distinct(x,y) for x,y in zip(a,b))
 return s.simplify(s.expand_func(a-b)).equals(0)is False
