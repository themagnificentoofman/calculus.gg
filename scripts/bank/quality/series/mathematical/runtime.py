"""Offline finite option-patch reconstruction; never a gameplay dependency."""
from pathlib import Path
import atexit,hashlib,json,subprocess,sys,threading
BASE=Path(__file__).resolve().parent
WORKERS={};CACHE={};LOCKS={};START=threading.Lock()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def catalog():return json.loads((BASE/'catalog.json').read_text())
def _join(route,family,index):
 if not isinstance(route,str) or not isinstance(family,str) or type(index)is not int:raise ValueError('Invalid finite patch key')
 matches=[r for r in json.loads((BASE/'source-joins.json').read_text())if(r['route'],r['familyId'],r['instanceIndex'])==(route,family,index)]
 if len(matches)!=1:raise ValueError('Outside exact route/family/index domain')
 return matches[0]
def source(route,family,index):
 j=_join(route,family,index)
 r=next(r for r in map(json.loads,(BASE/'full-source-records.jsonl').read_text().splitlines())if r['problemId']==j['sourcePreview']['problemId'])
 if digest(r)!=j['sourcePreview']['canonicalRawSHA256']:raise ValueError('Source guard mismatch')
 return r
def review(route,family,index):return _join(route,family,index)
def presentation(route,family,index):
 j=_join(route,family,index);src=j['sourcePreview']
 p=next(r for r in json.loads((BASE/'source-presentations.json').read_text())['records']if r['problemId']==src['problemId'])
 if(p['sourceRevision'],p['sourceContentHash'],p['sourceSemanticHash'])!=(src['problemRevision'],src['contentHash'],src['semanticHash']):raise ValueError('Presentation source guard mismatch')
 return p
def close():
 for w in WORKERS.values():
  if w.poll()is None:w.terminate()
  try:w.wait(timeout=5)
  except subprocess.TimeoutExpired:w.kill();w.wait()
 WORKERS.clear()
atexit.register(close)
def build(route,family,index):
 j=_join(route,family,index);key=(route,family,index)
 with START:
  if route not in LOCKS:LOCKS[route]=threading.Lock()
 with LOCKS[route]:
  if key in CACHE:return json.loads(CACHE[key])
  if route not in WORKERS:WORKERS[route]=subprocess.Popen([sys.executable,'-B',str(BASE/'worker.py'),route],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,cwd=str(BASE))
  w=WORKERS[route];w.stdin.write(canonical({'familyId':family,'index':index,'problemId':j['sourcePreview']['problemId']})+'\n');w.stdin.flush();line=w.stdout.readline()
  if not line:raise ValueError('Isolated worker failed: '+w.stderr.read()[-4000:])
  response=json.loads(line)
  if response.get('error'):raise ValueError(response['error'])
  if response.get('verified')is not True:raise ValueError('Frozen constructor verification failed')
  patch=response['patch']
  if digest(patch)!=j['patchCanonicalSHA256']:raise ValueError('Patch differs from independently reviewed snapshot')
  CACHE[key]=canonical(patch);return json.loads(CACHE[key])
def verify(route,patch,index):
 try:return canonical(patch)==canonical(build(route,patch['familyId'],index))
 except(ValueError,KeyError,TypeError):return False
def supports(route,record):
 try:return digest(record)==_join(route,record['familyId'],record['parameters']['instance'])['sourcePreview']['canonicalRawSHA256']
 except(ValueError,KeyError,TypeError):return False
def build_patch(route,record):
 if not supports(route,record):raise ValueError('Changed or unknown canonical source')
 return build(route,record['familyId'],record['parameters']['instance'])
