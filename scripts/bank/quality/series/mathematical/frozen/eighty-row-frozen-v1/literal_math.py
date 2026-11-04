"""Fail-closed numeric TeX reader for this finite option audit; no author imports."""
import re
import sympy as s
FUNCTIONS={'ln':s.log,'log':s.log,'sin':s.sin,'cos':s.cos,'tan':s.tan,'cot':s.cot,'sinh':s.sinh,'cosh':s.cosh,'coth':s.coth,'tanh':s.tanh,'arcsin':s.asin,'arccos':s.acos,'arctan':s.atan,'Gamma':s.gamma,'zeta':s.zeta,'dilog':lambda z:s.polylog(2,z),'K':s.elliptic_k,'exp':s.exp}
class Reader:
 def __init__(self,text):
  self.original=text
  text=text.replace(r'\operatorname{Li}_{2}',r'\dilog').replace(r'\operatorname{atan}',r'\arctan')
  for t in [r'\left',r'\right',r'\,',r'\!',r'\ ',r'\quad',r'\;']:text=text.replace(t,'')
  self.t=re.findall(r'\\[A-Za-z]+|[0-9]+|[A-Za-z]|[^\s]',text);self.p=0
 def peek(self):return self.t[self.p]if self.p<len(self.t)else None
 def pop(self):
  z=self.peek();assert z is not None,self.original;self.p+=1;return z
 def accept(self,x):
  if self.peek()==x:self.p+=1;return True
  return False
 def group(self,left,right):
  assert self.pop()==left
  values=[self.expression()]
  while self.accept(','):values.append(self.expression())
  assert self.pop()==right,self.original
  return values[0]if len(values)==1 else s.Tuple(*values)
 def expression(self):
  z=self.product()
  while self.peek()in ['+','-']:
   op=self.pop();q=self.product();z=z+q if op=='+'else z-q
  return z
 def product(self):
  z=self.power()
  while self.peek()not in [None,')','}',']',',','+','-']:
   if self.accept('*')or self.accept(r'\cdot')or self.accept(r'\times'):z*=self.power()
   elif self.accept('/'):z/=self.power()
   else:z*=self.power()
  return z
 def power(self):
  sign=1
  while self.peek()in ['+','-']:
   if self.pop()=='-':sign=-sign
  z=self.atom()
  if self.accept('^'):z=z**self.argument()
  return sign*z
 def argument(self):
  if self.peek()=='{':return self.group('{','}')
  if self.peek()=='(':return self.group('(',')')
  # A TeX macro with no braces consumes a single token/digit, not a whole number.
  if self.peek()and self.peek().isdigit()and len(self.peek())>1:
   full=self.pop();self.t.insert(self.p,full[1:]);return s.Integer(full[0])
  return self.atom()
 def atom(self):
  v=self.peek()
  if v=='{':return self.group('{','}')
  if v=='(':return self.group('(',')')
  v=self.pop()
  if v.isdigit():return s.Integer(v)
  if v in ['e','\\pi','\\infty']:return {'e':s.E,r'\pi':s.pi,r'\infty':s.oo}[v]
  if v==r'\frac':
   a=self.argument();b=self.argument();return a/b
  if v==r'\sqrt':
   n=s.Integer(2)
   if self.peek()=='[':n=self.group('[',']')
   return self.argument()**(1/n)
  name=v[1:]if v.startswith('\\')else v
  if name in FUNCTIONS:
   p=None
   if self.accept('^'):p=self.argument()
   a=self.argument();value=FUNCTIONS[name](a);return value if p is None else value**p
  raise ValueError('Unsupported literal token '+repr(v)+' in '+self.original)
def parse(text):
 if r'\textnormal' in text:raise ValueError('Categorical option has no additive inverse')
 q=Reader(text);v=q.expression();assert q.peek()is None,(text,q.peek());assert not v.free_symbols;return v
