"""One route per subprocess; no imports from the mutable parent checkout."""
from pathlib import Path
import hashlib,importlib,json,os,sys
BASE=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((BASE/'copy-manifest.json').read_text())
for name,entry in manifest['sourceCopies'].items():
 if digest(BASE/name)!=entry['sha256']:raise ValueError('Frozen source changed: '+name)
for name,h in manifest['createdAssets'].items():
 if digest(BASE/name)!=h:raise ValueError('Bound package asset changed: '+name)
route=sys.argv[1];joins={(q['familyId'],q['index']):q for q in json.loads((BASE/'source-joins.json').read_text())['records']if q['route']==route}
if not joins:raise ValueError('Unknown source-bound route')
repo=BASE/'frozen-repo';os.environ['BANK_AUDIT_CONTENT_DIR']=str(repo/'scripts/bank/content');os.environ['BANK_AUDIT_ARTIFACT']=str(repo/'scripts/bank/quality/integration/historical-originals.jsonl');os.environ['PYTHONDONTWRITEBYTECODE']='1'
if route=='integration-new':sys.path.insert(0,str(BASE/'sources/advanced'))
elif route=='integration-sign':sys.path.insert(0,str(BASE/'sources/sign'))
elif route in ['integration-moments','integration-hilbert']:sys.path.insert(0,str(BASE/'sources/headroom'))
else:sys.path.insert(0,str(repo/'scripts/bank'))
modules={};filelines={}
for line in sys.stdin:
 try:
  request=json.loads(line)
  if request.get('route')!=route or type(request.get('index'))is not int:raise ValueError('Wrong isolated route/domain')
  entry=joins.get((request.get('family'),request['index']))
  if entry is None:raise ValueError('Outside exact bound finite domain')
  name=entry['builderModule']
  if name not in modules:modules[name]=importlib.import_module(name)
  record=modules[name].build(entry['familyId'],entry['index'])
  sourcefile=entry['sourceFile']
  if sourcefile not in filelines:filelines[sourcefile]=(BASE/sourcefile).read_text().splitlines()
  source=filelines[sourcefile][entry['sourceLine']-1]
  if hashlib.sha256(source.encode()).hexdigest()!=entry['sourceLineSha256']:raise ValueError('Frozen source line differs')
  expected=json.loads(source)
  if canonical(record)!=canonical(expected):raise ValueError('Reconstructed record differs from exact frozen source')
  if hashlib.sha256(canonical(record).encode()).hexdigest()!=entry['rawSha256']:raise ValueError('Source-bound canonical raw hash differs')
  result={'verified':True,'record':record,'evidence':{'sourceLineSha256':entry['sourceLineSha256'],'rawSha256':entry['rawSha256'],'canonicalByteParity':True,'normalizations':[],'scope':'Trusted constructor exact assertions plus frozen raw equality; independent mathematical review is separately bound in source-joins.'}}
 except Exception as error:result={'error':type(error).__name__+': '+str(error)}
 print(canonical(result),flush=True)
