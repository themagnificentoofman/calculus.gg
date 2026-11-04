"""Portable finite pack. Immutable compilation is guarded; verify reruns math."""
from pathlib import Path
from functools import lru_cache
import json,hashlib,sys,subprocess
BASE=Path(__file__).resolve().parent
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest_bytes(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@lru_cache(None)
def data():
 manifest=json.loads((BASE/'delivery-manifest.json').read_text())
 for name,sha in manifest['files'].items():assert digest_bytes(BASE/name)==sha,('source or data changed',name)
 rows=json.loads((BASE/'candidates.json').read_text());cats=json.loads((BASE/'catalog.json').read_text())
 return rows,cats
def catalog():return data()[1]
def build(fid,index):
 rows,cats=data();f=next(c for c in cats if c['familyId']==fid)
 assert type(index)is int and 0<=index<f['instanceCount']
 # Immutable revisions can retain a source finite index; the catalog maps it.
 case=f['finiteDomain'][index]
 if f.get('kind')=='immutable-revision':raw=next(r for r in rows if r.get('problemId')==case['problemId'])
 else:raw=next(r for r in rows if r['familyId']==fid and r['parameters']['instance']==index)
 return json.loads(json.dumps(raw))
def verify(raw):
 data()
 run=subprocess.run([sys.executable,str(BASE/'verify_one.py')],input=json.dumps(raw),text=True,capture_output=True)
 assert run.returncode==0,run.stderr or run.stdout
 return json.loads(run.stdout)['verified'] is True
if __name__=='__main__':
 rows,_=data()
 for r in rows:verify(r)
 print(json.dumps({'verified':len(rows),'sourceAndDataDigests':'passed'}))
