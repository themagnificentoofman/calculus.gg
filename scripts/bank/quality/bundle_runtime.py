"""Offline persistent isolation for byte-frozen constructor bundles.

Bundles use ordinary absolute Python imports. One subprocess per bundle keeps
their helper modules separate without rewriting reviewed source. This is never
included in the serving Worker and makes no network or model calls.
"""
from pathlib import Path
import atexit,json,subprocess,sys
BASE=Path(__file__).resolve().parent
WORKERS={};CACHE={}
ROUTES={
 'series-advanced':('advanced','advanced','verify_advanced','verify','passed'),
 'series-capacity':('capacity','capacity','capacity','verify','passed'),
 'series-hankel':('hankel','hankel','hankel','verify','passed'),
 'series-revisions':('existing','revisions','revisions','verify','passed-finite-mathematics-and-lineage'),
 'series-lower':('existing','lower_extensions','lower_extensions','verify','passed'),
}
def close():
 for worker in WORKERS.values():
  if worker.poll()is None:worker.terminate()
atexit.register(close)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def build(route,family,index):
 if route not in ROUTES or type(index)is not int:raise ValueError('Unregistered isolated constructor')
 key=(route,family,index)
 if key in CACHE:return json.loads(CACHE[key])
 bundle=ROUTES[route][0]
 if bundle not in WORKERS:
  WORKERS[bundle]=subprocess.Popen([sys.executable,str(BASE/'bundle_worker.py'),bundle],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 worker=WORKERS[bundle]
 worker.stdin.write(canonical({'route':route,'family':family,'index':index})+'\n');worker.stdin.flush()
 line=worker.stdout.readline()
 if not line:raise ValueError('Isolated constructor exited without a verified record')
 response=json.loads(line)
 if response.get('error'):raise ValueError(response['error'])
 if response.get('verified')is not True:raise ValueError('Isolated verification did not pass')
 CACHE[key]=canonical(response['record']);return json.loads(CACHE[key])
def verify(route,record,index):return canonical(record)==canonical(build(route,record['familyId'],index))
