"""Certify algebraically equal final expressions for the frozen menu repair."""
from pathlib import Path
import copy,hashlib,json,sys
import sympy as s
from differentiation_literal_choices import parse
ROOT=Path(__file__).resolve().parents[4]
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(failure_report,output):
 p=ROOT/'scripts/bank/quality/integration/algebraic-options'
 source=p/'sources/combined-candidates.jsonl'
 raws={digest(r):r for r in map(json.loads,source.read_text().splitlines())}
 failures=json.loads(Path(failure_report).read_text())['failures']
 assert len(failures)==41 and all(r['error']=='Quality admission: The explicit conclusion must match the verified correct choice.' for r in failures)
 keys={r['reviewId'].split('quality-review:integration-algebraic-',1)[1] for r in failures}
 items={}
 for j in json.loads((p/'source-joins.json').read_text()):
  key=j['route']+':'+j['familyId']+':'+str(j['index'])
  if key not in keys:continue
  raw=raws[j['rawHash']];old=raw['solutionSteps'][-1]
  new=next(c['math']for c in raw['choices']if c['choiceId']==raw['answerChoiceId'])
  a,b=parse(old),parse(new)
  positive=all(q.args[0].is_positive is True for q in a.atoms(s.log)|b.atoms(s.log))
  assert s.simplify(a-b)==0 or (positive and s.simplify(s.expand_log(a-b,force=True))==0),key
  changed=copy.deepcopy(raw);changed['solutionSteps'].append(new)
  changed.pop('contentHash',None);changed['contentHash']=digest(changed)
  items[key]={'sourceRawSha256':digest(raw),'destinationRawSha256':digest(changed),
              'oldConclusion':old,'newConclusion':new,'exactIdentity':True,
              'realLogArgumentsPositive':positive,
              'argument':'Exact algebra, positive-real log product/quotient identities and principal nonnegative radicals. Append the independently verified choice without changing any earlier derivation.'}
 assert len(items)==41
 out=Path(output)
 if out.exists():raise ValueError('Preserve previous source-bound report')
 out.write_text(json.dumps({'status':'independently-checked-meaning-preserving-presentation',
  'reviewer':'root','inputSha256':sha(source),'reviewSources':{str(q.relative_to(ROOT)):sha(q)for q in [Path(__file__),Path(__file__).with_name('differentiation_literal_choices.py')]},
  'items':items},indent=2)+'\n')
 print(json.dumps({'exactIdentities':len(items),'reportSha256':sha(out)}))
if __name__=='__main__':main(*sys.argv[1:])
