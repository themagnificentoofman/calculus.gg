"""Compile reviewed finite presentations; never regenerate or alter source records.
Usage: python scripts/bank/solution-review/compile.py IMMUTABLE.jsonl
"""
from pathlib import Path
import hashlib,importlib.util,json,sys,copy
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
EXPECTED='1ede867c4db4d21a5e147824604ac9dd63241d3031371c465125975ab2d99677'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def compile_reviews(artifact):
 if hashlib.sha256(artifact.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('Unreviewed finite source artifact')
 modules=[('coverage-v1',load('review_coverage',BASE/'coverage/solutions.py')),('supplemental-v1',load('review_supplemental',BASE/'supplemental/solutions.py')),('io3-v1',load('review_io3',BASE/'integration-legacy/io3_solutions.py'))]
 result={};families={};changes=0
 for line in artifact.read_text().splitlines():
  p=json.loads(line);before=copy.deepcopy(p);matched=[(name,module) for name,module in modules if module.supports(p)]
  if len(matched)!=1:raise ValueError(('Review coverage overlap/gap',p['problemId'],[n for n,_ in matched]))
  name,module=matched[0];steps=module.corrected_solution(p)
  # Two independently displayed symmetry identities, with no algebra change.
  if p['familyId']=='m3-integration-easy-odd-even':
   steps=[part for step in steps for part in step.split(r',\qquad ')]
  answer=next(c['math'] for c in p['choices'] if c['choiceId']==p['answerChoiceId'])
  # The independently checked derivation is retained; present its result as an
  # explicit final choice expression rather than a prose/auxiliary-I equality.
  if steps[-1]!=answer:steps=[*steps,answer]
  statement=getattr(module,'corrected_statement',lambda p:None)(p)
  assert p==before,'Review mutated immutable input'
  entry={'sourceContentHash':p['contentHash'],'revision':p['problemRevision'],'familyId':p['familyId'],'auditId':name,'steps':steps}
  if statement and statement!=p['statement']:entry['statement']=statement;changes+=1
  result[p['problemId']]=entry;families[p['familyId']]=families.get(p['familyId'],0)+1
 assert len(result)==2504 and len(families)==313 and set(families.values())=={8}
 destination=ROOT/'lib/server/solution-reviews/finite.json'
 destination.write_text(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n')
 print(json.dumps({'records':len(result),'families':len(families),'statementClarifications':changes,'outputSha256':hashlib.sha256(destination.read_bytes()).hexdigest()}))
if __name__=='__main__':compile_reviews(Path(sys.argv[1]))
