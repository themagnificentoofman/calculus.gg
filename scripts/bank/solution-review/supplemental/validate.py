"""Reproduce final-answer agreement and notation contracts for every assigned row."""
import sys,json,hashlib,importlib.util,re,copy
from pathlib import Path
import sympy as s
from reproduction_paths import source_repo,source_artifact
ROOT=Path(__file__).parent;CONTENT=source_repo()/'scripts/bank/content';sys.path.insert(0,str(CONTENT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mo=importlib.util.module_from_spec(spec);spec.loader.exec_module(mo);return mo
manifest=json.loads((ROOT/'manifest.json').read_text());bank=source_artifact();records=[json.loads(l) for l in bank.read_text().splitlines()];records=[r for r in records if r['familyId'] in manifest['families']]
# Bind optional clarifications to exact original records from the reviewed artifact.
statement_slugs=['path-dependent-directional','nonlinear-energy-speed','periodic-floquet-multiplier','sharp-lifetime-comparison','schwarzian-ivp','darboux-oscillator']
guards={r['problemId']:r['contentHash'] for r in records if any(r['familyId'].endswith('-'+q) for q in statement_slugs)}
p=ROOT/'solutions.py';body=p.read_text();body=re.sub(r'^STATEMENT_GUARDS=.*$', 'STATEMENT_GUARDS='+repr(guards),body,flags=re.M);p.write_text(body)
sol=load('new_solutions',p);mods={n:load('trusted_'+n,CONTENT/(n+'.py')) for n in set(manifest['families'].values())}
def raw_answer(record):
 name=manifest['families'][record['familyId']];mo=mods[name];fid=record['familyId'];m=s.Integer(record['provenance']['authoring']['builderParameters']['m'])
 meta=next(f for f in mo.FAMILIES if f['familyId']==fid) if isinstance(mo.FAMILIES,list) else mo.FAMILIES[fid]
 if name=='limits_additions':
  token=mo.CHECKS.set([])
  try:raw=meta['build'](m)
  finally:mo.CHECKS.reset(token)
 else:raw=meta['build'](m)
 a=raw['answer']
 if name=='series_easy' and raw['kind']=='numeric':
  if re.fullmatch(r'Integer\(-?\d+\)',a):return s.Integer(a[8:-1])
  match=re.fullmatch(r'Rational\((-?\d+), (\d+)\)',a)
  if match:return s.Rational(int(match[1]),int(match[2]))
  raise AssertionError('unexpected trusted numeric encoding')
 return a
results=[];render=[];statement_changes=[]
for r in records:
 before=copy.deepcopy(r)
 try:
  data=sol.derived_solution(r);steps=sol.corrected_solution(r);a=data['expectedResult'];b=raw_answer(r)
  if isinstance(a,str) or isinstance(b,str):assert a==b,(a,b)
  elif isinstance(a,s.Tuple):assert a==b,(a,b)
  else:assert s.simplify(s.expand_func(s.expand_log(a-b,force=True)))==0,(a,b)
  assert steps[-1]==sol.answer_math(r)
  assert all(isinstance(q,str) and q for q in steps)
  assert not any(r'\begin{gathered}' in q or r'\textasciicircum' in q or r'\textbackslash' in q for q in steps)
  assert not any(re.search(r'\bHere\b.*m\s*=',q) for q in steps)
  assert not any(r'\log' in q or r'\operatorname{atan}' in q or r'\operatorname{asin}' in q or r'\operatorname{acos}' in q for q in steps)
  assert before==r,'input mutated'
  changed=sol.corrected_statement(r)
  if changed is not None:
   forged=copy.deepcopy(r);forged['contentHash']='forged';assert sol.corrected_statement(forged)is None
   statement_changes.append({'problemId':r['problemId'],'familyId':r['familyId'],'sourceContentHash':r['contentHash'],'statement':changed,'scope':'formatting and concretization only; original mathematical meaning preserved'})
  for i,q in enumerate(steps):render.append({'problemId':r['problemId'],'kind':'solution','index':i,'math':q})
  if changed:render.append({'problemId':r['problemId'],'kind':'statement','index':0,'math':changed})
  results.append({'problemId':r['problemId'],'familyId':r['familyId'],'sourceContentHash':r['contentHash'],'passed':True,'stepCount':len(steps)})
 except Exception as e:results.append({'problemId':r['problemId'],'familyId':r['familyId'],'passed':False,'error':repr(e)})
 if len(results)%8==0:print(r['familyId'],sum(q['passed'] for q in results[-8:]),flush=True)
report={'artifactSha256':hashlib.sha256(bank.read_bytes()).hexdigest(),'moduleSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'records':len(records),'families':len({r['familyId'] for r in records}),'failures':[q for q in results if not q['passed']],'results':results,'scope':'Every rewritten result independently agrees with the trusted constructor expression; notation, exact final displayed answer, optional statement guards, and input immutability checked. Separate substantive_checks.py checks new intermediate identities.'}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/'render-input.json').write_text(json.dumps(render)+'\n');(ROOT/'statement-clarifications.json').write_text(json.dumps(statement_changes,indent=2)+'\n');print('FINISHED',len(records),len(report['failures']),len(render))
