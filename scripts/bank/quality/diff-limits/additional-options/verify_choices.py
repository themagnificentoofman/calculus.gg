"""Literal parse plus outward rational pair separation; no numerical guesses.
Uses the root reviewer's independently implemented interval checker. This local
execution is author verification, not another independent editorial review.
"""
from pathlib import Path
import json,hashlib,itertools
import sympy as s
from literal_numeric_extended import parse
from limits_intervals import separate
P=Path(__file__).resolve().parent
rows=list(map(json.loads,(P/'candidates.jsonl').read_text().splitlines()));source={r['problemId']:r for r in json.loads((P/'inputs.json').read_text())};out=[]
for r in rows:
 vals=[parse(c['math']) for c in r['choices']];cert=[separate(a,b) for a,b in itertools.combinations(vals,2)]
 old=source[r['sourcePreview']['problemId']];A=next(v for c,v in zip(r['choices'],vals) if c['choiceId']==r['answerChoiceId']);B=parse(next(c['math'] for c in old['choices'] if c['choiceId']==old['answerChoiceId']));assert s.simplify(s.expand_log(A-B,force=True))==0
 pairs=[(i,j) for i in range(4) for j in range(i) if s.simplify(s.expand_log(vals[i]+vals[j],force=True))==0];assert len(pairs) in [0,2]
 out.append({'familyId':r['familyId'],'instanceIndex':r['instanceIndex'],'sourceProblemId':old['problemId'],'rawSha256':hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),'answerUnchangedExactly':True,'sixLiteralPairEnclosures':cert,'oppositePairCount':len(pairs)})
report={'records':out,'counts':{'records':len(out),'literalPairs':6*len(out),'answersUnchanged':len(out)},'sourceSha256':hashlib.sha256((P/'candidates.jsonl').read_bytes()).hexdigest(),'scope':'Exact literal scalar inequalities and source-answer equality. Original proof/level review is reused by exact source binding; independent editorial review of this new menu layer remains required.'}
(P/'literal-choice-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['counts'])
