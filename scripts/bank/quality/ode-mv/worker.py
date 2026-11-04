"""Private JSON-lines worker: trusted frozen constructors plus exact source binding."""
from pathlib import Path
import hashlib,importlib,json,os,sys
from certificate_serialization import normalize_generated
BASE=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((BASE/'copy-manifest.json').read_text())
for name,entry in manifest['sourceCopies'].items():
 if digest(BASE/name)!=entry['sha256']:raise ValueError('Frozen source changed: '+name)
for name,h in manifest['createdAssets'].items():
 if digest(BASE/name)!=h:raise ValueError('Bound source asset changed: '+name)
route=sys.argv[1]
alljoins=json.loads((BASE/'source-joins.json').read_text())['records']
joins={(q['familyId'],q['index']):q for q in alljoins if q['route']==route}
if not joins:raise ValueError('Unknown source-bound route')
os.environ['QUALITY_BASELINE_CONTENT_DIR']=str(BASE/'baseline-content')
os.environ['QUALITY_BASELINE_REVIEW_DIR']=str(BASE/'baseline-review')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(BASE/'sources'))
originals={r['problemId']:r for r in map(json.loads,(BASE/'inputs/original-revision-sources.jsonl').read_text().splitlines())}
modules={};filelines={}
for line in sys.stdin:
 try:
  request=json.loads(line)
  if request.get('route')!=route or type(request.get('index'))is not int:raise ValueError('Wrong isolated route/domain')
  entry=joins.get((request.get('family'),request['index']))
  if entry is None:raise ValueError('Outside exact bound finite domain')
  name=entry['builderModule']
  if name not in modules:modules[name]=importlib.import_module(name)
  module=modules[name]
  if entry['builderKind']=='revision':
   source=originals[entry['problemId']]
   record=module.build_revision(source)
  else:record=module.build(entry['familyId'],entry['index'])
  sourcefile=entry['sourceFile']
  if sourcefile not in filelines:filelines[sourcefile]=(BASE/sourcefile).read_text().splitlines()
  expectedline=filelines[sourcefile][entry['sourceLine']-1]
  if hashlib.sha256(expectedline.encode()).hexdigest()!=entry['sourceLineSha256']:raise ValueError('Frozen source line differs')
  expected=json.loads(expectedline)
  record,normalizations=normalize_generated(record,expected)
  if canonical(record)!=canonical(expected):raise ValueError('Reconstructed record differs from exact frozen source')
  if hashlib.sha256(canonical(record).encode()).hexdigest()!=entry['rawSha256']:raise ValueError('Source-bound raw hash differs')
  # The trusted builder executes its finite exact assertions. The independent
  # mathematical reviews are distinct copied evidence, not asserted by a flag.
  result={'verified':True,'record':record,'reconstructionNormalizations':normalizations}
 except Exception as error:result={'error':type(error).__name__+': '+str(error)}
 print(canonical(result),flush=True)
