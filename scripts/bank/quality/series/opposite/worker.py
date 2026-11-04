"""Isolated frozen patch reconstruction; no shared author-module imports."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'frozen'))
import repairs
for line in sys.stdin:
 try:
  pid=json.loads(line)['problemId'];original=repairs.originals()[pid];patch=repairs.build_patch(original);assert repairs.verify_patch(patch,original);result={'patch':patch,'verified':True}
 except Exception as error:result={'error':str(error)}
 print(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False),flush=True)
