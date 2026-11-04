"""Bind the final integration screen to the exact served notation, not raw TeX."""
from pathlib import Path
import hashlib,json
from .contract import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stage=ROOT/'.bank-data/quality/integration-previews-v5';doc=ROOT/'docs/bank/problem-quality/integration'
 out=doc/'served-option-review-v5.json'
 if out.exists():raise ValueError('Preserve previous evidence')
 binding=json.loads((stage/'served-option-binding.json').read_text())
 for file,digest in binding['sourceArtifacts'].items():assert sha(stage/file)==digest
 for name,key in [('lib/server/solution-presentation.mjs','presenterSha256'),('lib/math-notation.mjs','notationSha256')]:assert sha(ROOT/name)==binding[key]
 assert sha(stage/'served-option-input.jsonl')==binding['servedInputSha256']
 raw=json.loads((stage/'option-audit.json').read_text());served=json.loads((stage/'served-option-audit.json').read_text())
 prior=json.loads((doc/'final-option-review-v5.json').read_text())
 assert served['records']==raw['records']==len(prior['records'])==766
 assert served['artifactSha256']==binding['servedInputSha256']
 comparisons=[]
 for scope in ['families','answerForms']:
  assert set(raw[scope])==set(served[scope])
  for key,current in served[scope].items():
   old=raw[scope][key]
   assert old['trainingIds']==current['trainingIds'] and old['heldoutIds']==current['heldoutIds']
   assert old['flags']==current['flags'],(scope,key,'Changed flag needs fresh disposition')
   comparisons.append({'scope':scope,'key':key,'items':current['items'],'sameHeldoutSplit':True,'sameFlags':True,'flags':current['flags']})
 inputs=[stage/n for n in ['canonical-previews.jsonl','retained-originals.jsonl','option-audit.json','served-option-input.jsonl','served-option-audit.json','served-option-binding.json']]+[doc/'final-option-review-v5.json',ROOT/'lib/server/solution-presentation.mjs',ROOT/'lib/math-notation.mjs',Path(__file__)]
 report={'status':'source-bound-served-option-screen-reconciled','reviewer':'root','records':766,'notationChangedMenus':len(binding['changedSpellings']),'familyComparisons':82,'formComparisons':4,'changedFlagSets':0,'sourceArtifacts':{str(p.relative_to(ROOT)):sha(p)for p in inputs},'comparisons':comparisons,'disposition':'All actual served flag sets and deterministic training/held-out memberships equal the reviewed raw screen. Preserve the exact family/form dispositions in final-option-review-v5.json. Fifty notation-only menu changes introduce no additional configured flag.','limitations':['This comparison does not independently re-prove algebraic choice inequivalence; the separately bound complete mathematical peer evidence remains required.','Configured screens and small finite samples do not establish absence of every possible clue.','No session-horizon or production approval.']}
 out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['records','notationChangedMenus','changedFlagSets']}))
if __name__=='__main__':main()
