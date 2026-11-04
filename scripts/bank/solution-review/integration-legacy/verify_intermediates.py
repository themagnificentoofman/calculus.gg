import os
from pathlib import Path
import json,sys,hashlib,importlib.util,time,sqlite3
import sympy as s
BASE=Path(__file__).parent
ROOT=Path(os.environ.get('BANK_AUDIT_REPO',Path(__file__).resolve().parents[4]))
sys.path.insert(0,str(ROOT/'scripts/bank'))
import pipeline as old
from families import FAMILIES
from special_ode import build as special_build
from io3_solutions import params
from export_io3 import recompute,eq,rows,exact_parse
x=s.symbols('x',real=True);t=s.symbols('t',positive=True);R=s.Rational
checks=[]
def equal(name,a,b=0):
 assert s.simplify(s.expand_func(a-b))==0,(name,a,b)
 checks.append({'check':name,'passed':True})
# Every immutable edge record is tied back to the exact answer-expression ID.
edges=json.loads((BASE/'legacy-edge-records.json').read_text());families={f['id']:f for f in FAMILIES};values={}
con=sqlite3.connect('file:'+os.environ['BANK_AUDIT_LEGACY_DB']+'?mode=ro',uri=True)
for (meta,) in con.execute('select metadata_json from cbank_shared'):
 d=json.loads(meta);bv=d['validation']['evidence'].get('basisResults')
 if bv is not None:values[d['familyId']]=[exact_parse(q) for q in bv]
for fid,rs in edges.items():
 f=families[fid]
 for r in rs:
  if f['kind']=='special-ode':a=special_build(fid,r['parameters'])['answer']
  else:a=s.expand(sum(r['parameters'][key]*v for key,v in zip(('a','b','c'),values[fid])))
  assert r['answerChoiceId']=='ch_'+old.digest(s.srepr(a))[:16],(fid,r['parameters'])
 checks.append({'check':fid+' four immutable edge answers','passed':True})
# Independently execute the original finite analytic-identity checks for all io3 instances.
spec=importlib.util.spec_from_file_location('io3_source',ROOT/'scripts/bank/content/integration.py');source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
family_checks={};started=time.monotonic()
for r in rows:
 slug=r['familyId'][4:];seed=r['parameters']['instance'];captured=[];token=source.EXACT_CHECK_LOG.set(captured)
 try:raw=source.FAMILIES[slug]['build'](seed)
 finally:source.EXACT_CHECK_LOG.reset(token)
 assert eq(recompute(slug,params(r)),raw['answer']),(slug,seed)
 family_checks.setdefault(r['familyId'],{'instances':0,'executedSourceIdentityChecks':0})['instances']+=1
 family_checks[r['familyId']]['executedSourceIdentityChecks']+=len(captured)
 if seed==7:print(slug+' checked',flush=True)
# New explanatory bridges, beyond unchanged answer agreement.
a,b=s.symbols('a b',positive=True);z=s.symbols('z');f=1/(((z-a)**2+b*b)*((z+a)**2+b*b))
equal('Cauchy first explicit residue',s.residue(f,z,a+s.I*b),1/(8*s.I*a*b*(a+s.I*b)))
equal('Cauchy second explicit residue',s.residue(f,z,-a+s.I*b),1/(8*s.I*a*b*(a-s.I*b)))
equal('Cauchy residue sum gives integral',2*s.pi*s.I*(1/(8*s.I*a*b*(a+s.I*b))+1/(8*s.I*a*b*(a-s.I*b))),s.pi/(2*b*(a*a+b*b)))
q=x*x-x+R(1,6);rminus=R(1,2)-s.sqrt(3)/6;rplus=R(1,2)+s.sqrt(3)/6
equal('quadrature node polynomial',(x-rminus)*(x-rplus),q)
equal('quadrature defect integral',s.integrate(q*q,(x,0,1)),R(1,180))
for j in range(4):equal('quadrature degree '+str(j),s.integrate(x**j,(x,0,1)),(rminus**j+rplus**j)/2)
for r in rows:
 slug=r['familyId'][4:];p=params(r)
 if slug=='bernoulli-product':
  m,n=int(p['m']),int(p['n']);lhs=s.integrate(s.bernoulli(m,x)*s.bernoulli(n,x),(x,0,1));rhs=-R(m,n+1)*s.integrate(s.bernoulli(m-1,x)*s.bernoulli(n+1,x),(x,0,1));equal('Bernoulli recurrence '+str((m,n)),lhs,rhs)
  equal('Bernoulli final endpoint '+str((m,n)),s.integrate(s.bernoulli(1,x)*s.bernoulli(m+n-1,x),(x,0,1)),s.bernoulli(m+n)/(m+n))
 if slug=='principal-value':
  d=s.symbols('d',positive=True);Q=p['q'];equal('PV transformed cutoff ratio '+str(Q),s.limit(((1+d)**Q-1)/(1-(1-d)**Q),d,0),1)
 if slug=='abel-recovery':equal('Abel finite polynomial reduction '+str(p['n']),2*s.integrate((1-x*x)**p['n'],(x,0,1))/s.pi,recompute(slug,p))
 if slug=='variational-energy':
  k=p['k'];g=s.sinh(k*x)/s.sinh(k);equal('energy candidate differential equation '+str(k),s.diff(g,x,2),k*k*g);equal('energy candidate left endpoint '+str(k),g.subs(x,0),0);equal('energy candidate right endpoint '+str(k),g.subs(x,1),1);equal('energy boundary value '+str(k),(g*s.diff(g,x)).subs(x,1)-(g*s.diff(g,x)).subs(x,0),recompute(slug,p))
 if slug=='moment-projection':
  m,c=p['m'],p['c'];mu=1/(m+1);V=1/(2*m+1)-mu*mu;g=1+(c-mu)/V*(x**m-mu);equal('projection mean '+str(m),s.integrate(g,(x,0,1)),1);equal('projection moment '+str(m),s.integrate(x**m*g,(x,0,1)),c);equal('projection norm '+str(m),s.integrate(g*g,(x,0,1)),recompute(slug,p))
for j in range(10):equal('Bessel angular sine moment '+str(j),s.integrate(s.sin(x)**(2*j),(x,0,s.pi))/s.pi,s.factorial(2*j)/(4**j*s.factorial(j)**2))
# Legacy primitive conventions and explicitly stated asymptotic constants.
equal('trig primitive sine',s.diff(-s.cos(x),x),s.sin(x));equal('trig primitive cosine',s.diff(s.sin(x),x),s.cos(x));equal('trig primitive double frequency',s.diff(-s.cos(2*x)/2,x),s.sin(2*x))
F=s.exp(x)
for j in range(1,4):F=x**j*s.exp(x)-j*F;equal('chosen exponential primitive '+str(j),s.diff(F,x),x**j*s.exp(x))
for f,value in [(x*x*(x+1)**2,s.Integer(1)),(x**3*(x+2)**2,R(11,4)),(x*x*(x+3)**3,R(44,3))]:equal('second Riemann explicit endpoint',s.diff(f,x).subs(x,1)/12,value)
for power,value in [(2,-R(5,6)),(3,R(7,4)),(4,-s.Integer(2))]:equal('radial logarithm coefficient '+str(power),s.series(s.log(1+x)**power,x,0,6).removeO().expand().coeff(x,5),value)
report={'legacyEdgeRecordsChecked':sum(map(len,edges.values())),'legacyFamiliesChecked':len(edges),'io3FiniteInstancesChecked':len(rows),'io3FamilyChecks':family_checks,'newBridgeCheckCount':len(checks),'checks':checks,'elapsedSeconds':round(time.monotonic()-started,3),'analyticTheorems':'Fubini/Tonelli, dominated convergence, Gaussian/beta reflection, Fourier identities, ODE uniqueness and asymptotic remainder bounds retain explicitly stated hypotheses and mathematical proof obligations; not claimed to be machine-proved measure theory.','humanReviewed':False,'rootSourceEdited':False}
(BASE/'intermediate-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','io3FamilyChecks']}),flush=True)
