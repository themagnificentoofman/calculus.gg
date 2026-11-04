"""Portable offline exact finite overlays; isolated author modules, no admission."""
from pathlib import Path
import json,subprocess,sys,threading,atexit
P=Path(__file__).resolve().parent;WORKER=None;CACHE={};LOCK=threading.Lock()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def catalog():return json.loads((P/'catalog.json').read_text())
def close():
 global WORKER
 if WORKER is not None and WORKER.poll()is None:WORKER.terminate()
 WORKER=None
atexit.register(close)
def build(route,family,index):
 global WORKER
 if not isinstance(route,str)or not isinstance(family,str)or type(index)is not int or not any(q['route']==route and q['familyId']==family and index in q['indices']for q in catalog()):raise ValueError('Outside finite algebraic-option domain')
 key=(route,family,index)
 with LOCK:
  if key in CACHE:return json.loads(CACHE[key])
  if WORKER is None:WORKER=subprocess.Popen([sys.executable,'-B',str(P/'worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=str(P))
  WORKER.stdin.write(canonical({'route':route,'family':family,'index':index})+'\n');WORKER.stdin.flush();line=WORKER.stdout.readline()
  if not line:raise ValueError('Offline overlay worker exited: '+WORKER.stderr.read()[-2000:])
  out=json.loads(line)
  if out.get('error')or out.get('verified')is not True:raise ValueError(out.get('error','Reconstruction failed'))
  CACHE[key]=canonical(out['record']);return json.loads(CACHE[key])
def verify(route,record):
 try:return canonical(record)==canonical(build(route,record['familyId'],record['instanceIndex']))
 except (KeyError,TypeError,ValueError):return False
