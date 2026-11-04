"""Portable complete finite generation and separately encoded mathematical audit."""
import json,hashlib
from pathlib import Path
import advanced
from verify_advanced import verify
ROOT=Path(__file__).resolve().parent
def main():
 rows=[];reports=[];fail=[]
 for meta in advanced.catalog():
  for i in meta['finiteInstanceIndices']:
   try:
    row=advanced.build(meta['familyId'],i);report=verify(row);rows.append(row);reports.append(report)
   except Exception as e:fail.append({'familyId':meta['familyId'],'instanceIndex':i,'error':repr(e)})
  print(meta['familyId'],len(rows),'verified;',len(fail),'failures',flush=True)
 (ROOT/'advanced-candidates.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
 result={'status':'passed' if not fail else 'failed','families':len(advanced.catalog()),'instances':len(rows),'executedChecks':sum(r['executedCheckCount'] for r in reports),'failures':fail,'results':reports,'sourceFiles':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['advanced.py','advanced_replacements.py','common.py','verify_advanced.py','generate_advanced.py']},'humanReviewed':False,'formalProof':False}
 (ROOT/'advanced-verification.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'advanced-catalog.json').write_text(json.dumps(advanced.catalog(),indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='results'}));return bool(fail)
if __name__=='__main__':raise SystemExit(main())
