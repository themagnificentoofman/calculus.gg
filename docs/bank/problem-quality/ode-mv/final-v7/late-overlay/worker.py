"""Isolated immutable constructor reconstruction; never a serving dependency."""
from pathlib import Path
import hashlib,importlib,json,os,sys
BASE=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def H(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
manifest=json.loads((BASE/'file-manifest.json').read_text())
for name,sha in manifest['files'].items():
 if hashlib.sha256((BASE/name).read_bytes()).hexdigest()!=sha:raise ValueError('Bound asset changed: '+name)
route=sys.argv[1];joins={(q['familyId'],q['index']):q for q in json.loads((BASE/'source-joins.json').read_text())['records'] if q['route']==route}
if not joins:raise ValueError('Unknown route')
folders={q['constructorFolder'] for q in joins.values()};assert len(folders)==1;folder=BASE/next(iter(folders));sys.path.insert(0,str(folder));os.environ['PYTHONDONTWRITEBYTECODE']='1'
modules={};data={}
for line in sys.stdin:
 try:
  q=json.loads(line)
  if q.get('route')!=route or type(q.get('index'))is not int:raise ValueError('Invalid finite route/index')
  entry=joins.get((q.get('family'),q['index']))
  if entry is None:raise ValueError('Outside frozen finite domain')
  name=entry['builderModule']
  if name not in modules:modules[name]=importlib.import_module(name)
  record=modules[name].build(entry['familyId'],entry['index'])
  if entry['sourceFile'] not in data:data[entry['sourceFile']]=[json.loads(line) for line in (BASE/entry['sourceFile']).read_text().splitlines()] if entry['sourceFile'].endswith('.jsonl') else json.loads((BASE/entry['sourceFile']).read_text())
  expected=data[entry['sourceFile']][entry['sourceRecordIndex']]
  if H(record)!=entry['rawSha256'] or canonical(record)!=canonical(expected):raise ValueError('Reconstructed record differs from immutable source')
  response={'record':record,'verified':True,'reconstructionNormalizations':[]}
 except Exception as error:response={'error':type(error).__name__+': '+str(error)}
 print(canonical(response),flush=True)
