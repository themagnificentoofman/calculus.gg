"""Portable finite inventory, literal notation and per-family option diagnostics."""
from pathlib import Path
import json,hashlib,re,collections
from option_audit import audit,features,score
P=Path(__file__).resolve().parent

def main():
 rows=list(map(json.loads,(P/'candidates.jsonl').read_text().splitlines()));families=[];flags=[];literal=[];keys=[]
 for fid in sorted({r['familyId'] for r in rows}):
  rs=[r for r in rows if r['familyId']==fid];report=audit(rs);tests=report['allRules'];replicated=[r for r in tests if r['development']['chanceFilledExpectedAccuracy'] is not None and r['heldOut']['chanceFilledExpectedAccuracy'] is not None and min(r['development']['chanceFilledExpectedAccuracy'],r['heldOut']['chanceFilledExpectedAccuracy'])>=.65]
  families.append({'familyId':fid,'instances':len(rs),'normalizedCapacityKeys':len({r['parameters']['normalizedCapacityKey'] for r in rs}),'optionScreen':report,'replicated65PercentRules':replicated})
  if replicated:flags.append({'familyId':fid,'rules':replicated})
  for r in rs:
   assert r['solutionSteps'][-1]==next(c['math'] for c in r['choices'] if c['choiceId']==r['answerChoiceId'])
   keys.append({'problemId':r['problemId'],'sourceContentHash':r['contentHash'],'familyId':fid,'instanceIndex':r['instanceIndex'],'normalizedCapacityKey':fid+'::'+r['parameters']['normalizedCapacityKey'],'purposefulCase':r['parameters']['purposefulCase']})
   for kind,vals in [('statement',[r['statement']]),('choices',[c['math'] for c in r['choices']]),('solutions',r['solutionSteps'])]:
    for n,t in enumerate(vals):
     for pattern in [r'[_^][0-9]{2,}',r'(?<![A-Za-z\\])(?:quad|qquad)\b',r'\\log\b',r'Here [a-z] =']:
      if re.search(pattern,t):literal.append({'problemId':r['problemId'],'kind':kind,'index':n,'pattern':pattern,'text':t})
 assert len(keys)==len({q['normalizedCapacityKey'] for q in keys}), 'Repeated normalized keys'
 out={'status':'diagnostic-review-required' if flags or literal else 'passed-bounded-author-screen','artifactSHA256':hashlib.sha256((P/'candidates.jsonl').read_bytes()).hexdigest(),'instances':len(rows),'families':families,'replicatedFlags':flags,'literalNotationIssues':literal,'normalizedItems':keys,'normalizedItemsCount':len(keys),'independentDifficultyVerdict':'Parent owns source-bound blind/options-visible qualification. These are proposed capacity keys, not an admission claim.','scope':'Per-family fixed-rule development/held-out screen, exact final-choice text, explicit finite keys and conservative literal TeX lint. This does not prove absence of all option cues or establish analytic proofs.','humanReviewed':False}
 (P/'inventory-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'instances':len(rows),'groups':len(families),'replicatedFlags':[(f['familyId'],[(q['feature'],q['mode']) for q in f['rules']]) for f in flags],'literalIssues':len(literal)}))
if __name__=='__main__':main()
