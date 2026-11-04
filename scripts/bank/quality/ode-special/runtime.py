"""Offline source-bound differentiation/limits constructor isolation. Never a serving dependency."""
from pathlib import Path
import atexit,json,subprocess,sys,threading
BASE=Path(__file__).resolve().parent
WORKERS={};CACHE={};EVIDENCE={};LOCKS={};START=threading.Lock()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def catalog():return json.loads((BASE/'catalog.json').read_text())
def close():
 for worker in WORKERS.values():
  if worker.poll()is None:worker.terminate()
 WORKERS.clear()
atexit.register(close)
def build(route,family,index):
 if not isinstance(route,str) or not isinstance(family,str) or type(index)is not int:raise ValueError('Invalid finite constructor key')
 allowed={(q['route'],q['familyId'],i) for q in catalog() for i in q['indices']}
 key=(route,family,index)
 if key not in allowed:raise ValueError('Outside bound route/family/finite-index domain')
 with START:
  if route not in LOCKS:LOCKS[route]=threading.Lock()
 with LOCKS[route]:
  if key in CACHE:return json.loads(CACHE[key])
  if route not in WORKERS:
   WORKERS[route]=subprocess.Popen([sys.executable,'-B',str(BASE/'worker.py'),route],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,cwd=str(BASE))
  worker=WORKERS[route]
  worker.stdin.write(canonical({'route':route,'family':family,'index':index})+'\n');worker.stdin.flush()
  line=worker.stdout.readline()
  if not line:
   raise ValueError('Isolated bundle worker exited: '+worker.stderr.read()[-3000:])
  response=json.loads(line)
  if response.get('error'):raise ValueError(response['error'])
  if response.get('verified')is not True:raise ValueError('Bound reconstruction did not pass')
  EVIDENCE[key]=response.get('reconstructionNormalizations',[])
  CACHE[key]=canonical(response['record']);return json.loads(CACHE[key])
def verify(route,record,index):
 try:return canonical(record)==canonical(build(route,record['familyId'],index))
 except (ValueError,KeyError,TypeError):return False
def reconstruction_evidence(route,family,index):
 return json.loads(canonical(EVIDENCE.get((route,family,index),[])))

def require_reviews():
 manifest=json.loads((BASE/'review-manifest.json').read_text())
 if manifest['counts']['pending'] or manifest['status']!='complete-independent-peer-joins':raise ValueError('Independent finite review joins are pending; admission is blocked')
 return True
