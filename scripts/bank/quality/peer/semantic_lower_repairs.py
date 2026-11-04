"""Independent calculus for the40 finite semantic ODE/MV repair cases."""
from pathlib import Path
import hashlib,itertools,json,re,sys
import sympy as s
from sympy.parsing.sympy_parser import parse_expr,standard_transformations,implicit_multiplication_application
x,y,t=s.symbols('x y t',real=True);u,v=s.symbols('u v',positive=True)
SUFFIXES=['finite-blowup','repeated-root','nonlinear-Jacobian','quadratic-critical-value']
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def parse_choice(tex):
 value=tex.replace(r'\left','').replace(r'\right','').replace(r'\,','').replace(r'\!','')
 value=re.sub(r'\\ln\s*\{\s*\(\s*([0-9]+)\s*\)\s*\}',r'log(\1)',value)
 while r'\frac' in value:
  changed=re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}',r'((\1)/(\2))',value)
  if changed==value:raise ValueError('Unsupported literal option: '+tex)
  value=changed
 if not re.fullmatch(r'[0-9\s()+*/.\-log]+',value):raise ValueError('Unsupported literal choice tokens: '+tex)
 return parse_expr(value,local_dict={'log':s.log},transformations=standard_transformations+(implicit_multiplication_application,))
ROUTES={
 'finite-blowup':('medium','Separate variables, use the initial reciprocal value, and locate the first future pole. Smoothness of the vector field guarantees uniqueness up to that pole.','Direct reciprocal separation; a different endpoint computation from fixed-zero-time or sign-only examples.'),
 'repeated-root':('medium','Factor the constant-coefficient operator, use both initial conditions, and evaluate the resulting exponential times a linear factor.','The repeated characteristic root forces the linear prefactor, unlike a distinct-root exponential combination.'),
 'nonlinear-Jacobian':('hard','Use product and ratio as coordinates, prove the positive-quadrant inverse is single-valued, then integrate the inverse Jacobian over the transformed rectangle.','Unlike an affine area multiplier, the Jacobian varies with the ratio coordinate.'),
 'quadratic-critical-value':('medium','Complete two positive squares or solve the diagonal gradient system; positivity makes the critical point the global minimum.','The added incompatible squared residual prevents the old always-zero minimum; direct positive quadratic minimization remains Medium.'),
}
def main(revisions,extensions,out):
 rows=[];inputs={}
 for path in [revisions,extensions]:
  data=Path(path).read_bytes();inputs[Path(path).name]=hashlib.sha256(data).hexdigest()
  rows.extend(r for r in map(json.loads,data.splitlines()) if any(r['familyId'].endswith(k) for k in SUFFIXES))
 results=[]
 for r in rows:
  slug=next(k for k in SUFFIXES if r['familyId'].endswith(k));m=s.Integer(r['parameters']['m']);checks=[]
  def ck(label,a,b):
   assert s.simplify(a-b)==0,(slug,m,label,a,b);checks.append({'description':label,'left':s.srepr(a),'right':s.srepr(b),'result':'exact equality'})
  if slug=='finite-blowup':
   solution=1/(m-(m-1)*t);answer=m/(m-1)
   ck('Literal initial value',solution.subs(t,0),1/m);ck('Differential equation residual',s.diff(solution,t),(m-1)*solution**2);ck('First positive denominator root',m-(m-1)*answer,0)
   assert 'y\\prime='+str(m-1)+'y^2' in r['statement'] and r'\frac1{'+str(m)+'}' in r['statement']
  elif slug=='repeated-root':
   solution=t*s.exp(m*t);answer=2*s.log(2)/m
   ck('Second-order equation residual',s.diff(solution,t,2)-2*m*s.diff(solution,t)+m*m*solution,0);ck('Initial displacement',solution.subs(t,0),0);ck('Initial velocity',s.diff(solution,t).subs(t,0),1);ck('Displayed logarithmic-time evaluation',solution.subs(t,s.log(2)/m),answer)
   assert '-'+str(2*m)+r'y\prime+'+str(m*m)+'y=0' in r['statement']
  elif slug=='nonlinear-Jacobian':
   X=s.sqrt(u*v);Y=s.sqrt(u/v);jac=s.det(s.Matrix([[s.diff(X,u),s.diff(X,v)],[s.diff(Y,u),s.diff(Y,v)]]))
   ck('Inverse coordinate product',X*Y,u);ck('Inverse coordinate ratio',X/Y,v);ck('Oriented inverse Jacobian',jac,-1/(2*v));answer=s.integrate(s.integrate(-jac,(v,1,2)),(u,1,m))
   assert r'1\le xy\le'+str(m) in r['statement'] and r'1\le x/y\le2' in r['statement']
  else:
   q=(x+y-m)**2+(x-y-1)**2+x*x;answer=(m+1)**2/6
   ck('Exact positive-square completion',q,3*(x-(m+1)/3)**2+2*(y-(m-1)/2)**2+answer)
   assert '(x+y-'+str(m)+')^2+(x-y-1)^2+x^2' in r['statement']
  values=[parse_choice(c['math']) for c in r['choices']];matches=[i for i,a in enumerate(values) if s.simplify(a-answer)==0]
  assert len(matches)==1 and r['choices'][matches[0]]['choiceId']==r['answerChoiceId']
  assert all(s.simplify(a-b).equals(0)is False for a,b in itertools.combinations(values,2))
  level,route,neighbor=ROUTES[slug]
  results.append({'familyId':r['familyId'],'index':r['instanceIndex'],'parameter':int(m),'rawSha256':hashlib.sha256(canonical(r).encode()).hexdigest(),'rawContentHash':r['contentHash'],'previous':r.get('admission',{}).get('previous'),'independentAnswer':s.srepr(answer),'checks':checks,'fourLiteralChoicesIndependentlyParsed':True,'sixPairwiseInequivalenceChecksPassed':True,'difficultyRecommended':level,'easiestOptionsVisibleRoute':route,'nearestNeighbor':neighbor,'meaningfulCapacity':'Parameter-specific elementary/Hard fluency, zero additional independent groups. Existing IDs preserve exposure through semantic revision.','passed':True})
 report={'reviewer':'root-independent-review','author':'integration_research','inputs':inputs,'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'instances':len(results),'passed':len(results),'results':results,'scope':'All32 revised and8 new-extension semantic tasks independently solved from the displayed formulas. Literal options parsed separately, all six inequalities and exact residuals/completions checked. No author constructor imported; analytic uniqueness/domain arguments are prose, not formal proof. Final option-only screens remain separate.'}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if __name__=='__main__':main(*sys.argv[1:])
