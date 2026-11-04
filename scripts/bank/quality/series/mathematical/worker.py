"""One process per byte-frozen option constructor, avoiding import collisions."""
from pathlib import Path
import hashlib,importlib,json,sys
BASE=Path(__file__).resolve().parent
ROUTES={'domain-six':('six-row-frozen-v1','patches','option-patches.json'),'bracket-eighty':('eighty-row-frozen-v1','bracket_patches','bracket-option-patches.json'),'support-seventy-six':('last76-frozen-v1','support_patches','support-option-patches.json')}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
folder,module,artifact=ROUTES[sys.argv[1]];root=BASE/'frozen'/folder
manifest=json.loads((root/'manifest.json').read_text())
for name,expected in manifest['files'].items():
 if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen file changed: '+name)
sys.path.insert(0,str(root));author=importlib.import_module(module)
expected={r['problemId']:r for r in json.loads((root/artifact).read_text())}
originals=author.originals()
for line in sys.stdin:
 try:
  request=json.loads(line);r=originals[request['problemId']]
  if(r['familyId'],r['parameters']['instance'])!=(request['familyId'],request['index']):raise ValueError('Finite source identity mismatch')
  patch=author.build_patch(r)
  if canonical(patch)!=canonical(expected[r['problemId']]):raise ValueError('Serialized patch parity failed')
  result={'patch':patch,'verified':author.verify_patch(patch,r)}
 except Exception as e:result={'error':type(e).__name__+': '+str(e)}
 print(canonical(result),flush=True)
