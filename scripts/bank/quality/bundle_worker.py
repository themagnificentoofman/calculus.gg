"""Line-delimited private helper for bundle_runtime; no author input is executed."""
from pathlib import Path
import importlib,json,sys
from bundle_runtime import ROUTES,canonical
bundle=sys.argv[1]
if bundle not in {v[0] for v in ROUTES.values()}:raise ValueError('Unknown reviewed bundle')
folder=Path(__file__).resolve().parent/'series'/'bundles'/bundle
sys.path.insert(0,str(folder))
for line in sys.stdin:
 try:
  request=json.loads(line);route=ROUTES.get(request.get('route'))
  if not route or route[0]!=bundle:raise ValueError('Constructor belongs to another isolated bundle')
  raw=importlib.import_module(route[1]).build(request['family'],request['index'])
  report=getattr(importlib.import_module(route[2]),route[3])(raw)
  if not isinstance(report,dict) or report.get('status')!=route[4] or report.get('sourceContentHash')!=raw.get('contentHash') or not report.get('checks'):raise ValueError('Finite reconstruction verification is incomplete')
  result={'record':raw,'verified':True}
 except Exception as error:result={'error':str(error)}
 print(canonical(result),flush=True)
