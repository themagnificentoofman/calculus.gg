"""Reconstruct reviewed finite content and verify exact offline source bindings.

The admission flag and hash supplied by an input record are never an oracle.
Registered constructors re-run their mathematics; a separate reviewed report
binds the exact finite raw item and final adapter. Frozen M3 routes are intact.
"""
from pathlib import Path
import atexit,hashlib,importlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
VERSION='reviewed-quality-constructions-v1'
MODULES={'adapted-pilot':'scripts.bank.quality.adapted.pilot','series-options':'scripts.bank.quality.series.options.runtime','series-opposite-options':'scripts.bank.quality.series.opposite.runtime'}
_registry=None
_bridge=None

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def file_hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def bound_file(relative,digest):
 path=(ROOT/relative).resolve()
 if not path.is_relative_to(ROOT) or not path.is_file() or file_hash(path)!=digest:raise ValueError('Missing or changed reviewed source: '+relative)
 return path

def bind_supplemental_reports(entry):
 supplemental=entry.get('supplementalReports',[])
 if not isinstance(supplemental,list) or len(supplemental)>16:raise ValueError('Invalid supplemental review list')
 for report in supplemental:
  if not isinstance(report,dict) or not isinstance(report.get('purpose'),str) or not report['purpose'].strip():raise ValueError('Supplemental review scope required')
  bound_file(report['path'],report['sha256'])
 editorial=entry.get('editorialSupplement')
 if editorial is not None:
  if not isinstance(editorial,dict) or editorial.get('rawSha256')!=entry.get('rawSha256'):raise ValueError('Editorial supplement must bind the exact raw item')
  bound_file(editorial['report'],editorial['reportSha256'])

def registry():
 global _registry
 if _registry is None:
  result=json.loads((ROOT/'scripts/bank/quality/reviewed.json').read_text())
  if result.get('version')!=VERSION or result.get('status')!='independently-reviewed' or not result.get('sourceDigests'):raise ValueError('Quality review registry is incomplete')
  for file,digest in result['sourceDigests'].items():bound_file(file,digest)
  _registry=result
 return _registry

def normalize(raw,admission):
 global _bridge
 if _bridge is None:
  _bridge=subprocess.Popen(['node',str(ROOT/'scripts/bank/quality/adapt.mjs')],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
  atexit.register(lambda:_bridge.terminate() if _bridge.poll() is None else None)
 _bridge.stdin.write(json.dumps({'rawCanonical':canonical(raw),'admission':admission},ensure_ascii=False)+'\n');_bridge.stdin.flush()
 result=json.loads(_bridge.stdout.readline())
 if result.get('error'):raise ValueError(result['error'])
 return result['record']

def build(review_id):
 entry=registry()['items'].get(review_id)
 if not entry or entry.get('reviewId')!=review_id or not entry.get('contentHash'):raise ValueError('Unknown or unbound review identity')
 from . import bundle_runtime,finite_runtime
 route=entry.get('module');mod_name=MODULES.get(route)
 if not mod_name and route not in bundle_runtime.ROUTES and route not in finite_runtime.ROUTES:raise ValueError('Unregistered reviewed constructor')
 if type(entry.get('index'))is not int or entry['index'] not in entry.get('finiteDomain',{}).get('indices',[]):raise ValueError('Outside reviewed finite domain')
 for prefix in ['report','optionAudit']:
  bound_file(entry['review'][prefix if prefix=='report' else 'optionAuditReport'],entry['review'][prefix+'Sha256'])
 # New evidence can restrict or strengthen clearance without rewriting an
 # already immutable record's earlier evidence. Every supplement is itself
 # exact-source-bound, and the central registry is frozen at admission.
 bind_supplemental_reports(entry)
 if entry.get('adaptation'):bound_file(entry['adaptation']['sourceRegister'],entry['adaptation']['sourceRegisterSha256'])
 if mod_name:
  module=importlib.import_module(mod_name)
  raw=module.build(entry['familyId'],entry['index'])
  if module.verify(raw) is not True:raise ValueError('Independent finite verification failed')
 elif route in finite_runtime.ROUTES:raw=finite_runtime.build(route,entry['familyId'],entry['index'])
 else:
  # The isolated worker reconstructs the exact finite raw item and requires
  # its complete mathematical report before returning it. The adapter also
  # checks the independently reviewed source digest and final destination.
  raw=bundle_runtime.build(route,entry['familyId'],entry['index'])
 return normalize(raw,entry)

def verify(record):
 if record.get('templateVersion')!=VERSION:raise ValueError('Unsupported quality version')
 params=record.get('parameters',{})
 if set(params)!={'instance'}:raise ValueError('Unexpected quality parameters')
 expected=build(record.get('provenance',{}).get('authoring',{}).get('reviewId'))
 if canonical(record)!=canonical(expected):raise ValueError('Reviewed quality reconstruction mismatch: '+record.get('problemId','unknown'))
 return True
